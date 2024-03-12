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
import threading

from containerregistry.client import docker_creds
from containerregistry.client import docker_name
from containerregistry.client.v2_2 import docker_digest
from containerregistry.client.v2_2 import docker_http
import httplib2
import six
from six.moves import zip  # pylint: disable=redefined-builtin
import six.moves.http_client


class DigestMismatchedError(Exception):
  """Exception raised when a digest mismatch is encountered."""


class DockerImage(six.with_metaclass(abc.ABCMeta, object)):
  """Interface for implementations that interact with Docker images."""

  def fs_layers(self):
    """The ordered collection of filesystem layers that comprise this image."""
    manifest = json.loads(self.manifest())
    return [x['digest'] for x in reversed(manifest['layers'])]

  def diff_ids(self):
    """The ordered list of uncompressed layer hashes (matches fs_layers)."""
    cfg = json.loads(self.config_file())
    return list(reversed(cfg.get('rootfs', {}).get('diff_ids', [])))

  def config_blob(self):
    manifest = json.loads(self.manifest())
    return manifest['config']['digest']

  def blob_set(self):
    """The unique set of blobs that compose to create the filesystem."""
    return set(self.fs_layers() + [self.config_blob()])

  def distributable_blob_set(self):
    """The unique set of blobs which are distributable."""
    manifest = json.loads(self.manifest())
    distributable_blobs = {
        x['digest']
        for x in reversed(manifest['layers'])
        if x['mediaType'] not in docker_http.NON_DISTRIBUTABLE_LAYER_MIMES
    }
    distributable_blobs.add(self.config_blob())
    return distributable_blobs

  def digest(self):
    """The digest of the manifest."""
    return docker_digest.SHA256(self.manifest().encode('utf8'))

  def media_type(self):
    """The media type of the manifest."""
    manifest = json.loads(self.manifest())
    # Since 'mediaType' is optional for OCI images, assume OCI if it's missing.
    return manifest.get('mediaType', docker_http.OCI_MANIFEST_MIME)

  # pytype: disable=bad-return-type
  @abc.abstractmethod
  def manifest(self):
    """The JSON manifest referenced by the tag/digest.

    Returns:
      The raw json manifest
    """
  # pytype: enable=bad-return-type

  # pytype: disable=bad-return-type
  @abc.abstractmethod
  def config_file(self):
    """The raw blob bytes of the config file."""
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
    zipped = self.blob(digest)
    buf = io.BytesIO(zipped)
    f = gzip.GzipFile(mode='rb', fileobj=buf)
    unzipped = f.read()
    return unzipped

  def _diff_id_to_digest(self, diff_id):
    for (this_digest, this_diff_id) in six.moves.zip(self.fs_layers(),
                                                     self.diff_ids()):
      if this_diff_id == diff_id:
        return this_digest
    raise ValueError('Unmatched "diff_id": "%s"' % diff_id)

  def digest_to_diff_id(self, digest):
    for (this_digest, this_diff_id) in six.moves.zip(self.fs_layers(),
                                                     self.diff_ids()):
      if this_digest == digest:
        return this_diff_id
    raise ValueError('Unmatched "digest": "%s"' % digest)

  def layer(self, diff_id):
    """Like `blob()`, but accepts the `diff_id` instead.

    The `diff_id` is the name for the digest of the uncompressed layer.

    Args:
      diff_id: the 'algo:digest' of the layer being addressed.

    Returns:
      The raw compressed blob bytes of the layer.
    """
    return self.blob(self._diff_id_to_digest(diff_id))

  def uncompressed_layer(self, diff_id):
    """Same as layer() but uncompressed."""
    return self.uncompressed_blob(self._diff_id_to_digest(diff_id))

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


class Delegate(DockerImage):
  """Forwards calls to the underlying image."""

  def __init__(self, image):
    """Constructor.

    Args:
      image: a DockerImage on which __enter__ has already been called.
    """
    self._image = image

  def manifest(self):
    """Override."""
    return self._image.manifest()

  def media_type(self):
    """Override."""
    return self._image.media_type()

  def diff_ids(self):
    """Override."""
    return self._image.diff_ids()

  def fs_layers(self):
    """Override."""
    return self._image.fs_layers()

  def config_blob(self):
    """Override."""
    return self._image.config_blob()

  def blob_set(self):
    """Override."""
    return self._image.blob_set()

  def config_file(self):
    """Override."""
    return self._image.config_file()

  def blob_size(self, digest):
    """Override."""
    return self._image.blob_size(digest)

  def blob(self, digest):
    """Override."""
    return self._image.blob(digest)

  def uncompressed_blob(self, digest):
    """Override."""
    return self._image.uncompressed_blob(digest)

  def layer(self, diff_id):
    """Override."""
    return self._image.layer(diff_id)

  def uncompressed_layer(self, diff_id):
    """Override."""
    return self._image.uncompressed_layer(diff_id)

  def __str__(self):
    """Override."""
    return str(self._image)


class FromRegistry(DockerImage):
  """This accesses a docker image hosted on a registry (non-local)."""

  def __init__(self,
               name,
               basic_creds,
               transport,
               accepted_mimes = docker_http.MANIFEST_SCHEMA2_MIMES):
    self._name = name
    self._creds = basic_creds
    self._original_transport = transport
    self._accepted_mimes = accepted_mimes
    self._response = {}

  def _content(self,
               suffix,
               accepted_mimes = None,
               cache = True):
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
        accepted_codes=[six.moves.http_client.OK],
        accepted_mimes=accepted_mimes)
    if cache:
      self._response[suffix] = content
    return content

  def check_usage_only(self):
    # See //cloud/containers/registry/proto/v2/registry_usage.proto
    # for the full response structure.
    response = json.loads(
        self._content('tags/list?check_usage_only=true').decode('utf8')
    )
    if 'usage' not in response:
      raise docker_http.BadStateException(
          'Malformed JSON response: {}. Missing "usage" field'.format(response)
      )
    return response.get('usage')

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
      manifest = json.loads(self.manifest(validate=False))
      return (manifest['schemaVersion'] == 2 and 'layers' in manifest and
              self.media_type() in self._accepted_mimes)
    except docker_http.V2DiagnosticException as err:
      if err.status == six.moves.http_client.NOT_FOUND:
        return False
      raise

  def manifest(self, validate=True):
    """Override."""
    # GET server1/v2/<name>/manifests/<tag_or_digest>

    if isinstance(self._name, docker_name.Tag):
      path = 'manifests/' + self._name.tag
      return self._content(path, self._accepted_mimes).decode('utf8')
    else:
      assert isinstance(self._name, docker_name.Digest)
      c = self._content('manifests/' + self._name.digest, self._accepted_mimes)
      computed = docker_digest.SHA256(c)
      if validate and computed != self._name.digest:
        raise DigestMismatchedError(
            'The returned manifest\'s digest did not match requested digest, '
            '%s vs. %s' % (self._name.digest, computed))
      return c.decode('utf8')

  def config_file(self):
    """Override."""
    return self.blob(self.config_blob()).decode('utf8')

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
      wrapper_object = json.loads(content.decode('utf8'))

      if 'repositories' not in wrapper_object:
        raise docker_http.BadStateException(
            'Malformed JSON response: %s' % content)

      # TODO(user): This should return docker_name.Repository
      for repo in wrapper_object['repositories']:
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


# Gzip injects a timestamp into its output, which makes its output and digest
# non-deterministic.  To get reproducible pushes, freeze time.
# This approach is based on the following StackOverflow answer:
# http://stackoverflow.com/questions/264224/setting-the-gzip-timestamp-from-python
class _FakeTime(object):

  def time(self):
    return 1225856967.109


gzip.time = _FakeTime()


# Checks the contents of a file for magic bytes that indicate that it's gzipped
def is_compressed(name):
  return name[0:2] == b'\x1f\x8b'


class FromTarball(DockerImage):
  """This decodes the image tarball output of docker_build for upload."""

  def __init__(
      self,
      tarball,
      name = None,
      compresslevel = 9,
  ):
    self._tarball = tarball
    self._compresslevel = compresslevel
    self._memoize = {}
    self._lock = threading.Lock()
    self._name = name
    self._manifest = None
    self._blob_names = None
    self._config_blob = None

  # Layers can come in two forms, as an uncompressed tar in a directory
  # or as a gzipped tar. We need to account for both options, and be able
  # to return both uncompressed and compressed data.
  def _content(self,
               name,
               memoize = True,
               should_be_compressed = False):
    """Fetches a particular path's contents from the tarball."""
    # Check our cache
    if memoize:
      with self._lock:
        if (name, should_be_compressed) in self._memoize:
          return self._memoize[(name, should_be_compressed)]

    # tarfile is inherently single-threaded:
    # https://mail.python.org/pipermail/python-bugs-list/2015-March/265999.html
    # so instead of locking, just open the tarfile for each file
    # we want to read.
    with tarfile.open(name=self._tarball, mode='r') as tar:
      try:
        # If the layer is compressed and we need to return compressed
        # or if it's uncompressed and we need to return uncompressed
        # then return the contents as is.
        f = tar.extractfile(str(name))
        content = f.read()  # pytype: disable=attribute-error
      except KeyError:
        content = tar.extractfile(
            str('./' + name)).read()  # pytype: disable=attribute-error
      # We need to compress before returning. Use gzip.
      if should_be_compressed and not is_compressed(content):
        buf = io.BytesIO()
        zipped = gzip.GzipFile(
            mode='wb', compresslevel=self._compresslevel, fileobj=buf)
        try:
          zipped.write(content)
        finally:
          zipped.close()
        content = buf.getvalue()
      # The layer is gzipped but we need to return the uncompressed content
      # Open up the gzip and read the contents after.
      elif not should_be_compressed and is_compressed(content):
        buf = io.BytesIO(content)
        raw = gzip.GzipFile(mode='rb', fileobj=buf)
        content = raw.read()
      # Populate our cache.
      if memoize:
        with self._lock:
          self._memoize[(name, should_be_compressed)] = content
      return content

  def _gzipped_content(self, name):
    """Returns the result of _content with gzip applied."""
    return self._content(name, memoize=False, should_be_compressed=True)

  def _populate_manifest_and_blobs(self):
    """Populates self._manifest and self._blob_names."""
    config_blob = docker_digest.SHA256(self.config_file().encode('utf8'))
    manifest = {
        'mediaType': docker_http.MANIFEST_SCHEMA2_MIME,
        'schemaVersion': 2,
        'config': {
            'digest': config_blob,
            'mediaType': docker_http.CONFIG_JSON_MIME,
            'size': len(self.config_file())
        },
        'layers': [
            # Populated below
        ]
    }

    blob_names = {}

    config = json.loads(self.config_file())
    diff_ids = config['rootfs']['diff_ids']

    for i, layer in enumerate(self._layers):
      name = None
      diff_id = diff_ids[i]
      media_type = docker_http.LAYER_MIME
      size = 0
      urls = []

      if diff_id in self._layer_sources:
        # _layer_sources contains foreign layers from the base image
        name = self._layer_sources[diff_id]['digest']
        media_type = self._layer_sources[diff_id]['mediaType']
        size = self._layer_sources[diff_id]['size']
        if 'urls' in self._layer_sources[diff_id]:
          urls = self._layer_sources[diff_id]['urls']
      else:
        content = self._gzipped_content(layer)
        name = docker_digest.SHA256(content)
        size = len(content)

      blob_names[name] = layer

      layer_manifest = {
          'digest': name,
          'mediaType': media_type,
          'size': size,
      }

      if urls:
        layer_manifest['urls'] = urls

      manifest['layers'].append(layer_manifest)

    with self._lock:
      self._manifest = manifest
      self._blob_names = blob_names
      self._config_blob = config_blob

  def manifest(self):
    """Override."""
    if not self._manifest:
      self._populate_manifest_and_blobs()
    return json.dumps(self._manifest, sort_keys=True)

  def config_file(self):
    """Override."""
    return self._content(self._config_file).decode('utf8')

  # Could be large, do not memoize
  def uncompressed_blob(self, digest):
    """Override."""
    if not self._blob_names:
      self._populate_manifest_and_blobs()
    return self._content(
        self._blob_names[digest],
        memoize=False,
        should_be_compressed=False)

  # Could be large, do not memoize
  def blob(self, digest):
    """Override."""
    if not self._blob_names:
      self._populate_manifest_and_blobs()
    if digest == self._config_blob:
      return self.config_file().encode('utf8')
    return self._gzipped_content(
        self._blob_names[digest])

  # Could be large, do not memoize
  def uncompressed_layer(self, diff_id):
    """Override."""
    for (layer, this_diff_id) in zip(reversed(self._layers), self.diff_ids()):
      if diff_id == this_diff_id:
        return self._content(layer, memoize=False, should_be_compressed=False)
    raise ValueError('Unmatched "diff_id": "%s"' % diff_id)

  def _resolve_tag(self):
    """Resolve the singleton tag this tarball contains using legacy methods."""
    repo_bytes = self._content('repositories', memoize=False)
    repositories = json.loads(repo_bytes.decode('utf8'))
    if len(repositories) != 1:
      raise ValueError('Tarball must contain a single repository, '
                       'or a name must be specified to FromTarball.')

    for (repo, tags) in six.iteritems(repositories):
      if len(tags) != 1:
        raise ValueError('Tarball must contain a single tag, '
                         'or a name must be specified to FromTarball.')
      for (tag, unused_layer) in six.iteritems(tags):
        return '{repository}:{tag}'.format(repository=repo, tag=tag)

    raise Exception('unreachable')

  # __enter__ and __exit__ allow use as a context manager.
  def __enter__(self):
    manifest_json = self._content('manifest.json').decode('utf8')
    manifest_list = json.loads(manifest_json)

    config = None
    layers = []
    layer_sources = []
    # Find the right entry, either:
    # 1) We were supplied with an image name, which we must find in an entry's
    #   RepoTags, or
    # 2) We were not supplied with an image name, and this must have a single
    #   image defined.
    if len(manifest_list) != 1:
      if not self._name:
        # If we run into this situation, fall back on the legacy repositories
        # file to tell us the single tag.  We do this because Bazel will apply
        # build targets as labels, so each layer will be labelled, but only
        # the final label will appear in the resulting repositories file.
        self._name = self._resolve_tag()

    for entry in manifest_list:
      if not self._name or str(self._name) in (entry.get('RepoTags') or []):
        config = entry.get('Config')
        layers = entry.get('Layers', [])
        layer_sources = entry.get('LayerSources', {})

    if not config:
      raise ValueError('Unable to find %s in provided tarball.' % self._name)

    # Metadata from the tarball's configuration we need to construct the image.
    self._config_file = config
    self._layers = layers
    self._layer_sources = layer_sources

    # We populate "manifest" and "blobs" lazily for two reasons:
    # 1) Allow use of this library for reading the config_file() from the image
    #   layer shards Bazel produces.
    # 2) Performance of the case where all we read is the config_file().

    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    pass


class FromDisk(DockerImage):
  """This accesses a more efficient on-disk format than FromTarball.

  FromDisk reads an on-disk format optimized for use with push and pull.

  It is expected that the number of layers in config_file's rootfs.diff_ids
  matches: count(legacy_base.layers) + len(layers).

  Layers are drawn from legacy_base first (it is expected to be the base),
  and then from layers.

  This is effectively the dual of the save.fast method, and is intended for use
  with Bazel's rules_docker.

  Args:
    config_file: the contents of the config file.
    layers: a list of pairs.  The first element is the path to a file containing
        the second element's sha256.  The second element is the .tar.gz of a
        filesystem layer.  These are ordered as they'd appear in the manifest.
    uncompressed_layers: Optionally, a list of pairs. The first element is the
        path to a file containing the second element's sha256.
        The second element is the .tar of a filesystem layer.
    legacy_base: Optionally, the path to a legacy base image in FromTarball form
    foreign_layers_manifest: Optionally a tar manifest from the base
        image that describes the ForeignLayers needed by this image.
  """

  def __init__(self,
               config_file,
               layers,
               uncompressed_layers = None,
               legacy_base = None,
               foreign_layers_manifest = None):
    self._config = config_file
    self._manifest = None
    self._foreign_layers_manifest = foreign_layers_manifest
    self._layers = []
    self._layer_to_filename = {}
    for (name_file, content_file) in layers:
      with io.open(name_file, u'r') as reader:
        layer_name = 'sha256:' + reader.read()
      self._layers.append(layer_name)
      self._layer_to_filename[layer_name] = content_file

    self._uncompressed_layers = []
    self._uncompressed_layer_to_filename = {}
    if uncompressed_layers:
      for (name_file, content_file) in uncompressed_layers:
        with io.open(name_file, u'r') as reader:
          layer_name = 'sha256:' + reader.read()
        self._uncompressed_layers.append(layer_name)
        self._uncompressed_layer_to_filename[layer_name] = content_file

    self._legacy_base = None
    if legacy_base:
      with FromTarball(legacy_base) as base:
        self._legacy_base = base

  def _get_foreign_layers(self):
    foreign_layers = []
    if self._foreign_layers_manifest:
      manifest = json.loads(self._foreign_layers_manifest)
      if 'layers' in manifest:
        for layer in manifest['layers']:
          if layer['mediaType'] == docker_http.FOREIGN_LAYER_MIME:
            foreign_layers.append(layer)
    return foreign_layers

  def _get_foreign_layer_by_digest(self, digest):
    for foreign_layer in self._get_foreign_layers():
      if foreign_layer['digest'] == digest:
        return foreign_layer
    return None

  def _populate_manifest(self):
    base_layers = []
    if self._legacy_base:
      base_layers = json.loads(self._legacy_base.manifest())['layers']
    elif self._foreign_layers_manifest:
      # Manifest files found in tar files are actually a json list.
      # This code iterates through that collection and appends any foreign
      # layers described in the order found in the config file.
      base_layers += self._get_foreign_layers()

    # TODO(user): Update mimes here for oci_compat.
    self._manifest = json.dumps(
        {
            'schemaVersion':
                2,
            'mediaType':
                docker_http.MANIFEST_SCHEMA2_MIME,
            'config': {
                'mediaType':
                    docker_http.CONFIG_JSON_MIME,
                'size':
                    len(self.config_file()),
                'digest':
                    docker_digest.SHA256(self.config_file().encode('utf8'))
            },
            'layers':
                base_layers + [{
                    'mediaType': docker_http.LAYER_MIME,
                    'size': self.blob_size(digest),
                    'digest': digest
                } for digest in self._layers]
        },
        sort_keys=True)

  def manifest(self):
    """Override."""
    if not self._manifest:
      self._populate_manifest()
    return self._manifest

  def config_file(self):
    """Override."""
    return self._config

  # Could be large, do not memoize
  def uncompressed_blob(self, digest):
    """Override."""
    if digest not in self._layer_to_filename:
      if self._get_foreign_layer_by_digest(digest):
        return bytes([])
      else:
        # Leverage the FromTarball fast-path.
        return self._legacy_base.uncompressed_blob(digest)
    return super(FromDisk, self).uncompressed_blob(digest)

  def uncompressed_layer(self, diff_id):
    if diff_id in self._uncompressed_layer_to_filename:
      with io.open(self._uncompressed_layer_to_filename[diff_id],
                   u'rb') as reader:
        # TODO(b/118349036): Remove the disable once the pytype bug is fixed.
        return reader.read()  # pytype: disable=bad-return-type
    if self._legacy_base and diff_id in self._legacy_base.diff_ids():
      return self._legacy_base.uncompressed_layer(diff_id)
    return super(FromDisk, self).uncompressed_layer(diff_id)

  # Could be large, do not memoize
  def blob(self, digest):
    """Override."""
    if digest not in self._layer_to_filename:
      return self._legacy_base.blob(digest)
    with open(self._layer_to_filename[digest], 'rb') as reader:
      return reader.read()

  def blob_size(self, digest):
    """Override."""
    if digest not in self._layer_to_filename:
      return self._legacy_base.blob_size(digest)
    info = os.stat(self._layer_to_filename[digest])
    return info.st_size

  # __enter__ and __exit__ allow use as a context manager.
  def __enter__(self):
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    pass


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
    tar: the tarfile into which we are writing the final filesystem.
  """
  # Maps all of the files we have already added (and should never add again)
  # to whether they are a tombstone or not.
  fs = {}

  # Walk the layers, topmost first and add files.  If we've seen them in a
  # higher layer then we skip them
  for layer in image.diff_ids():
    buf = io.BytesIO(image.uncompressed_layer(layer))
    with tarfile.open(mode='r:', fileobj=buf) as layer_tar:
      for tarinfo in layer_tar:
        # If we see a whiteout file, then don't add anything to the tarball
        # but ensure that any lower layers don't add a file with the whited
        # out name.
        basename = os.path.basename(tarinfo.name)
        dirname = os.path.dirname(tarinfo.name)
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
        fs[name] = tombstone or not tarinfo.isdir()
        if not tombstone:
          if tarinfo.isfile():
            tar.addfile(tarinfo, fileobj=layer_tar.extractfile(tarinfo))
          else:
            tar.addfile(tarinfo, fileobj=None)
