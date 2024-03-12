# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This package provides DockerImage for examining docker_build outputs."""

from __future__ import absolute_import
from __future__ import division

from __future__ import print_function

import abc
import gzip
import io
import json
import os
import tarfile

from containerregistry.client import docker_creds
from containerregistry.client import docker_name
from containerregistry.client.v2 import docker_digest
from containerregistry.client.v2 import docker_http

import httplib2
import six
import six.moves.http_client


class DigestMismatchedError(Exception):
  """Exception raised when a digest mismatch is encountered."""


class DockerImage(six.with_metaclass(abc.ABCMeta, object)):
  """Interface for implementations that interact with Docker images."""

  def fs_layers(self):
    """The ordered collection of filesystem layers that comprise this image."""
    manifest = json.loads(self.manifest())
    return [x['blobSum'] for x in manifest['fsLayers']]

  def blob_set(self):
    """The unique set of blobs that compose to create the filesystem."""
    return set(self.fs_layers())

  def digest(self):
    """The digest of the manifest."""
    return docker_digest.SignedManifestToSHA256(self.manifest())

  # pytype: disable=bad-return-type
  @abc.abstractmethod
  def manifest(self):
    """The JSON manifest referenced by the tag/digest.

    Returns:
      The raw json manifest
    """

  # pytype: enable=bad-return-type

  def blob_size(self, digest):
    """The byte size of the raw blob."""
    return len(self.blob(digest))

  # pytype: disable=bad-return-type
  @abc.abstractmethod
  def blob(self, digest):
    """The raw blob of the layer.

    Args:
      digest: the 'algo:digest' of the layer being addressed.

    Returns:
      The raw blob bytes of the layer.
    """

  # pytype: enable=bad-return-type

  def uncompressed_blob(self, digest):
    """Same as blob() but uncompressed."""
    buf = io.BytesIO(self.blob(digest))
    f = gzip.GzipFile(mode='rb', fileobj=buf)
    return f.read()

  def diff_id(self, digest):
    """diff_id only exist in schema v22."""
    return None

  # __enter__ and __exit__ allow use as a context manager.
  @abc.abstractmethod
  def __enter__(self):
    """Open the image for reading."""

  @abc.abstractmethod
  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Close the image."""

  def __str__(self):
    """A human-readable representation of the image."""
    return str(type(self))


class FromRegistry(DockerImage):
  """This accesses a docker image hosted on a registry (non-local)."""

  def __init__(self, name,
               basic_creds,
               transport):
    self._name = name
    self._creds = basic_creds
    self._original_transport = transport
    self._response = {}

  def _content(self, suffix, cache = True):
    """Fetches content of the resources from registry by http calls."""
    if isinstance(self._name, docker_name.Repository):
      suffix = '{repository}/{suffix}'.format(
          repository=self._name.repository, suffix=suffix)

    if suffix in self._response:
      return self._response[suffix]

    _, content = self._transport.Request(
        '{scheme}://{registry}/v2/{suffix}'.format(
            scheme=docker_http.Scheme(self._name.registry),
            registry=self._name.registry,
            suffix=suffix),
        accepted_codes=[six.moves.http_client.OK])
    if cache:
      self._response[suffix] = content
    return content

  def _tags(self):
    # See //cloud/containers/registry/proto/v2/tags.proto
    # for the full response structure.
    return json.loads(self._content('tags/list').decode('utf8'))

  def tags(self):
    return self._tags().get('tags', [])

  def manifests(self):
    payload = self._tags()
    if 'manifest' not in payload:
      # Only GCR supports this schema.
      return {}
    return payload['manifest']

  def children(self):
    payload = self._tags()
    if 'child' not in payload:
      # Only GCR supports this schema.
      return []
    return payload['child']

  def exists(self):
    try:
      self.manifest(validate=False)
      return True
    except docker_http.V2DiagnosticException as err:
      if err.status == six.moves.http_client.NOT_FOUND:
        return False
      raise

  def manifest(self, validate=True):
    """Override."""
    # GET server1/v2/<name>/manifests/<tag_or_digest>
    if isinstance(self._name, docker_name.Tag):
      return self._content('manifests/' + self._name.tag).decode('utf8')
    else:
      assert isinstance(self._name, docker_name.Digest)
      c = self._content('manifests/' + self._name.digest).decode('utf8')
      # v2 removes signatures to compute the manifest digest, this is hard.
      computed = docker_digest.SignedManifestToSHA256(c)
      if validate and computed != self._name.digest:
        raise DigestMismatchedError(
            'The returned manifest\'s digest did not match requested digest, '
            '%s vs. %s' % (self._name.digest, computed))
      return c

  def blob_size(self, digest):
    """The byte size of the raw blob."""
    suffix = 'blobs/' + digest
    if isinstance(self._name, docker_name.Repository):
      suffix = '{repository}/{suffix}'.format(
          repository=self._name.repository, suffix=suffix)

    resp, unused_content = self._transport.Request(
        '{scheme}://{registry}/v2/{suffix}'.format(
            scheme=docker_http.Scheme(self._name.registry),
            registry=self._name.registry,
            suffix=suffix),
        method='HEAD',
        accepted_codes=[six.moves.http_client.OK])

    return int(resp['content-length'])

  # Large, do not memoize.
  def blob(self, digest):
    """Override."""
    # GET server1/v2/<name>/blobs/<digest>
    c = self._content('blobs/' + digest, cache=False)
    computed = docker_digest.SHA256(c)
    if digest != computed:
      raise DigestMismatchedError(
          'The returned content\'s digest did not match its content-address, '
          '%s vs. %s' % (digest, computed if c else '(content was empty)'))
    return c

  def catalog(self, page_size = 100):
    # TODO(user): Handle docker_name.Repository for /v2/<name>/_catalog
    if isinstance(self._name, docker_name.Repository):
      raise ValueError('Expected docker_name.Registry for "name"')

    url = '{scheme}://{registry}/v2/_catalog?n={page_size}'.format(
        scheme=docker_http.Scheme(self._name.registry),
        registry=self._name.registry,
        page_size=page_size)

    for _, content in self._transport.PaginatedRequest(
        url, accepted_codes=[six.moves.http_client.OK]):
      wrapper_object = json.loads(content)

      if 'repositories' not in wrapper_object:
        raise docker_http.BadStateException(
            'Malformed JSON response: %s' % content)

      for repo in wrapper_object['repositories']:
        # TODO(user): This should return docker_name.Repository instead.
        yield repo

  # __enter__ and __exit__ allow use as a context manager.
  def __enter__(self):
    # Create a v2 transport to use for making authenticated requests.
    self._transport = docker_http.Transport(
        self._name, self._creds, self._original_transport, docker_http.PULL)

    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    pass

  def __str__(self):
    return '<docker_image.FromRegistry name: {}>'.format(str(self._name))


def _in_whiteout_dir(fs, name):
  while name:
    dirname = os.path.dirname(name)
    if name == dirname:
      break
    if fs.get(dirname):
      return True
    name = dirname
  return False


_WHITEOUT_PREFIX = '.wh.'


def extract(image, tar):
  """Extract the final filesystem from the image into tar.

  Args:
    image: a docker image whose final filesystem to construct.
    tar: the open tarfile into which we are writing the final filesystem.
  """
  # Maps all of the files we have already added (and should never add again)
  # to whether they are a tombstone or not.
  fs = {}

  # Walk the layers, topmost first and add files.  If we've seen them in a
  # higher layer then we skip them.
  for layer in image.fs_layers():
    buf = io.BytesIO(image.blob(layer))
    with tarfile.open(mode='r:gz', fileobj=buf) as layer_tar:
      for member in layer_tar.getmembers():
        # If we see a whiteout file, then don't add anything to the tarball
        # but ensure that any lower layers don't add a file with the whited
        # out name.
        basename = os.path.basename(member.name)
        dirname = os.path.dirname(member.name)
        tombstone = basename.startswith(_WHITEOUT_PREFIX)
        if tombstone:
          basename = basename[len(_WHITEOUT_PREFIX):]

        # Before adding a file, check to see whether it (or its whiteout) have
        # been seen before.
        name = os.path.normpath(os.path.join('.', dirname, basename))
        if name in fs:
          continue

        # Check for a whited out parent directory
        if _in_whiteout_dir(fs, name):
          continue

        # Mark this file as handled by adding its name.
        # A non-directory implicitly tombstones any entries with
        # a matching (or child) name.
        fs[name] = tombstone or not member.isdir()
        if not tombstone:
          if member.isfile():
            tar.addfile(member, fileobj=layer_tar.extractfile(member.name))
          else:
            tar.addfile(member, fileobj=None)
