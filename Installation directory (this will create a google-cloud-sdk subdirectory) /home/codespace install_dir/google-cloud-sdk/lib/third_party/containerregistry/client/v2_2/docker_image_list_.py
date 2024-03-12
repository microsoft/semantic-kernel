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
"""This package provides DockerImageList for examining Manifest Lists."""

from __future__ import absolute_import
from __future__ import division

from __future__ import print_function

import abc
import json


from containerregistry.client import docker_creds
from containerregistry.client import docker_name
from containerregistry.client.v2_2 import docker_digest
from containerregistry.client.v2_2 import docker_http
from containerregistry.client.v2_2 import docker_image as v2_2_image

import httplib2
import six
import six.moves.http_client


class DigestMismatchedError(Exception):
  """Exception raised when a digest mismatch is encountered."""


class InvalidMediaTypeError(Exception):
  """Exception raised when an invalid media type is encountered."""


class Platform(object):
  """Represents runtime requirements for an image.

  See: https://docs.docker.com/registry/spec/manifest-v2-2/#manifest-list
  """

  def __init__(self, content = None):
    self._content = content or {}

  def architecture(self):
    return self._content.get('architecture', 'amd64')

  def os(self):
    return self._content.get('os', 'linux')

  def os_version(self):
    return self._content.get('os.version')

  def os_features(self):
    return set(self._content.get('os.features', []))

  def variant(self):
    return self._content.get('variant')

  def features(self):
    return set(self._content.get('features', []))

  def can_run(self, required):
    """Returns True if this platform can run the 'required' platform."""
    if not required:
      # Some images don't specify 'platform', assume they can always run.
      return True

    # Required fields.
    if required.architecture() != self.architecture():
      return False
    if required.os() != self.os():
      return False

    # Optional fields.
    if required.os_version() and required.os_version() != self.os_version():
      return False
    if required.variant() and required.variant() != self.variant():
      return False

    # Verify any required features are a subset of this platform's features.
    if required.os_features() and not required.os_features().issubset(
        self.os_features()):
      return False
    if required.features() and not required.features().issubset(
        self.features()):
      return False

    return True

  def compatible_with(self, target):
    """Returns True if this platform can run on the 'target' platform."""
    return target.can_run(self)

  def __iter__(self):
    # Ensure architecture and os are set (for default platform).
    self._content['architecture'] = self.architecture()
    self._content['os'] = self.os()

    return iter(six.iteritems(self._content))


class DockerImageList(six.with_metaclass(abc.ABCMeta, object)):
  """Interface for implementations that interact with Docker manifest lists."""

  def digest(self):
    """The digest of the manifest."""
    return docker_digest.SHA256(self.manifest().encode('utf8'))

  def media_type(self):
    """The media type of the manifest."""
    manifest = json.loads(self.manifest())
    # Since 'mediaType' is optional for OCI images, assume OCI if it's missing.
    return manifest.get('mediaType', docker_http.OCI_IMAGE_INDEX_MIME)

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
  def resolve_all(
      self, target = None):
    """Resolves a manifest list to a list of compatible manifests.

    Args:
      target: the platform to check for compatibility. If omitted, the target
          platform defaults to linux/amd64.

    Returns:
      A list of images that can be run on the target platform. The images are
      sorted by their digest.
    """

  # pytype: enable=bad-return-type

  def resolve(self,
              target = None):
    """Resolves a manifest list to a compatible manifest.

    Args:
      target: the platform to check for compatibility. If omitted, the target
          platform defaults to linux/amd64.

    Raises:
      Exception: no manifests were compatible with the target platform.

    Returns:
      An image that can run on the target platform.
    """
    if not target:
      target = Platform()
    images = self.resolve_all(target)
    if not images:
      raise Exception('Could not resolve manifest list to compatible manifest')
    return images[0]

  # __enter__ and __exit__ allow use as a context manager.
  @abc.abstractmethod
  def __enter__(self):
    """Open the image for reading."""

  @abc.abstractmethod
  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Close the image."""

  @abc.abstractmethod
  def __iter__(self):
    """Iterate over this manifest list's children."""


class Delegate(DockerImageList):
  """Forwards calls to the underlying image."""

  def __init__(self, image):
    """Constructor.

    Args:
      image: a DockerImageList on which __enter__ has already been called.
    """
    self._image = image
    super(Delegate, self).__init__()

  def manifest(self):
    """Override."""
    return self._image.manifest()

  def media_type(self):
    """Override."""
    return self._image.media_type()

  def resolve_all(
      self, target = None):
    """Override."""
    return self._image.resolve_all(target)

  def resolve(self,
              target = None):
    """Override."""
    return self._image.resolve(target)

  def __iter__(self):
    """Override."""
    return iter(self._image)

  def __str__(self):
    """Override."""
    return str(self._image)


class FromRegistry(DockerImageList):
  """This accesses a docker image list hosted on a registry (non-local)."""

  def __init__(
      self,
      name,
      basic_creds,
      transport,
      accepted_mimes = docker_http.MANIFEST_LIST_MIMES):
    self._name = name
    self._creds = basic_creds
    self._original_transport = transport
    self._accepted_mimes = accepted_mimes
    self._response = {}
    super(FromRegistry, self).__init__()

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

  def images(self):
    """Returns a list of tuples whose elements are (name, platform, image).

    Raises:
      InvalidMediaTypeError: a child with an unexpected media type was found.
    """
    manifests = json.loads(self.manifest())['manifests']
    results = []
    for entry in manifests:
      digest = entry['digest']
      base = self._name.as_repository()  # pytype: disable=attribute-error
      name = docker_name.Digest('{base}@{digest}'.format(
          base=base, digest=digest))
      media_type = entry['mediaType']

      if media_type in docker_http.MANIFEST_LIST_MIMES:
        image = FromRegistry(name, self._creds, self._original_transport)
      elif media_type in docker_http.SUPPORTED_MANIFEST_MIMES:
        image = v2_2_image.FromRegistry(name, self._creds,
                                        self._original_transport, [media_type])
      else:
        raise InvalidMediaTypeError('Invalid media type: ' + media_type)

      platform = Platform(entry['platform']) if 'platform' in entry else None
      results.append((name, platform, image))
    return results

  def resolve_all(
      self, target = None):
    results = list(self.resolve_all_unordered(target).items())
    # Sort by name (which is equivalent as by digest) for deterministic output.
    # We could let resolve_all_unordered() to return only a list of image, then
    # use image.digest() as the sort key, but FromRegistry.digest() will
    # eventually leads to another round trip call to registry. This inefficiency
    # becomes worse as the image list has more children images. So we let
    # resolve_all_unordered() to return both image names and images.
    results.sort(key=lambda name_image: str(name_image[0]))
    return [image for (_, image) in results]

  def resolve_all_unordered(
      self, target = None
  ):
    """Resolves a manifest list to a list of (digest, image) tuples.

    Args:
      target: the platform to check for compatibility. If omitted, the target
          platform defaults to linux/amd64.

    Returns:
      A list of (digest, image) tuples that can be run on the target platform.
    """
    target = target or Platform()
    results = {}
    images = self.images()
    for name, platform, image in images:
      # Recurse on manifest lists.
      if isinstance(image, FromRegistry):
        with image:
          results.update(image.resolve_all_unordered(target))
      elif target.can_run(platform):
        results[name] = image
    return results

  def exists(self):
    try:
      manifest = json.loads(self.manifest(validate=False))
      return manifest['schemaVersion'] == 2 and 'manifests' in manifest
    except docker_http.V2DiagnosticException as err:
      if err.status == six.moves.http_client.NOT_FOUND:
        return False
      raise

  def manifest(self, validate=True):
    """Override."""
    # GET server1/v2/<name>/manifests/<tag_or_digest>

    if isinstance(self._name, docker_name.Tag):
      return self._content('manifests/' + self._name.tag,
                           self._accepted_mimes).decode('utf8')
    else:
      assert isinstance(self._name, docker_name.Digest)
      c = self._content('manifests/' + self._name.digest, self._accepted_mimes)
      computed = docker_digest.SHA256(c)
      if validate and computed != self._name.digest:
        raise DigestMismatchedError(
            'The returned manifest\'s digest did not match requested digest, '
            '%s vs. %s' % (self._name.digest, computed))
      return c.decode('utf8')

  # __enter__ and __exit__ allow use as a context manager.
  def __enter__(self):
    # Create a v2 transport to use for making authenticated requests.
    self._transport = docker_http.Transport(
        self._name, self._creds, self._original_transport, docker_http.PULL)

    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    pass

  def __str__(self):
    return '<docker_image_list.FromRegistry name: {}>'.format(str(self._name))

  def __iter__(self):
    return iter([(platform, image) for (_, platform, image) in self.images()])


class FromList(DockerImageList):
  """This synthesizes a Manifest List from a list of images."""

  def __init__(self, images):
    self._images = images
    super(FromList, self).__init__()

  def manifest(self):
    list_body = {
        'mediaType': docker_http.MANIFEST_LIST_MIME,
        'schemaVersion': 2,
        'manifests': []
    }

    for (platform, manifest) in self._images:
      manifest_body = {
          'digest': manifest.digest(),
          'mediaType': manifest.media_type(),
          'size': len(manifest.manifest())
      }

      if platform:
        manifest_body['platform'] = dict(platform)
      list_body['manifests'].append(manifest_body)
    return json.dumps(list_body, sort_keys=True)

  def resolve_all(
      self, target = None):
    """Resolves a manifest list to a list of compatible manifests.

    Args:
      target: the platform to check for compatibility. If omitted, the target
          platform defaults to linux/amd64.

    Returns:
      A list of images that can be run on the target platform.
    """
    target = target or Platform()
    results = []
    for (platform, image) in self._images:
      if isinstance(image, DockerImageList):
        with image:
          results.extend(image.resolve_all(target))
      elif target.can_run(platform):
        results.append(image)

    # Use dictionary to dedup
    dgst_img_dict = {img.digest(): img for img in results}
    results = []
    # It is causing PyType to complain about the return type being
    # List[DockerImageList], so we have the pytype disable comment workaround
    # TODO(b/67895498)
    return [dgst_img_dict[dgst] for dgst in sorted(dgst_img_dict.keys())]

  # __enter__ and __exit__ allow use as a context manager.
  def __enter__(self):
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    pass

  def __iter__(self):
    return iter(self._images)
