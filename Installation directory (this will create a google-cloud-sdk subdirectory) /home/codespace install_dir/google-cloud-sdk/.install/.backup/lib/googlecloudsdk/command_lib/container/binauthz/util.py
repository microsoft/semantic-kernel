# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Utilities for Binary Authorization commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from containerregistry.client import docker_name
from googlecloudsdk.core.exceptions import Error
import six
from six.moves import urllib

_BINAUTHZ_ATTESTATION_ANNOTATION_KEY = (
    'binaryauthorization.googleapis.com/attestations'
)


class BadImageUrlError(Error):
  """Raised when a container image URL cannot be parsed successfully."""


def ReplaceImageUrlScheme(image_url, scheme):
  """Returns the passed `image_url` with the scheme replaced.

  Args:
    image_url: The URL to replace (or strip) the scheme from. (string)
    scheme: The scheme of the returned URL.  If this is an empty string or
      `None`, the scheme is stripped and the leading `//` of the resulting URL
      will be stripped off.
  Raises:
    BadImageUrlError: `image_url` isn't valid.
  """
  scheme = scheme or ''
  parsed_url = urllib.parse.urlparse(image_url)

  # If the URL has a scheme but not a netloc, then it must have looked like
  # 'scheme:///foo/bar', which is invalid for the purpose of attestation.
  if parsed_url.scheme and not parsed_url.netloc:
    raise BadImageUrlError(
        "Image URL '{image_url}' is invalid because it does not have a host "
        'component.'.format(image_url=image_url))

  # If there is neither a scheme nor a netloc, this means that an unqualified
  # URL was passed, like 'gcr.io/foo/bar'.  In this case we canonicalize the URL
  # by prefixing '//', which will cause urlparse to correctly pick up the
  # netloc.
  if not parsed_url.netloc:
    parsed_url = urllib.parse.urlparse('//{}'.format(image_url))

  # Finally, we replace the scheme and generate the URL.  If we were stripping
  # the scheme, the result will be prefixed with '//', which we strip off.  If
  # the scheme is non-empty, the lstrip is a no-op.
  return parsed_url._replace(scheme=scheme).geturl().lstrip('/')


def MakeSignaturePayloadDict(container_image_url):
  """Creates a dict representing a JSON signature object to sign.

  Args:
    container_image_url: See `containerregistry.client.docker_name.Digest` for
      artifact URL validation and parsing details.  `container_image_url` must
      be a fully qualified image URL with a valid sha256 digest.

  Returns:
    Dictionary of nested dictionaries and strings, suitable for passing to
    `json.dumps` or similar.
  """
  url = ReplaceImageUrlScheme(image_url=container_image_url, scheme='')
  try:
    repo_digest = docker_name.Digest(url)
  except docker_name.BadNameException as e:
    raise BadImageUrlError(e)
  return {
      'critical': {
          'identity': {
              'docker-reference': six.text_type(repo_digest.as_repository()),
          },
          'image': {
              'docker-manifest-digest': repo_digest.digest,
          },
          'type': 'Google cloud binauthz container signature',
      },
  }


def MakeSignaturePayload(container_image_url):
  """Creates a JSON bytestring representing a signature object to sign.

  Args:
    container_image_url: See `containerregistry.client.docker_name.Digest` for
      artifact URL validation and parsing details.  `container_image_url` must
      be a fully qualified image URL with a valid sha256 digest.

  Returns:
    A bytestring representing a JSON-encoded structure of nested dictionaries
    and strings.
  """
  payload_dict = MakeSignaturePayloadDict(container_image_url)
  # `separators` is specified as a workaround to the native `json` module's
  # https://bugs.python.org/issue16333 which results in inconsistent
  # serialization in older versions of Python.
  payload = json.dumps(
      payload_dict,
      ensure_ascii=True,
      indent=2,
      separators=(',', ': '),
      sort_keys=True,
  )
  # NOTE: A newline is appended for backwards compatibility with the previous
  # payload serialization which relied on gcloud's default JSON serialization.
  return '{}\n'.format(payload).encode('utf-8')


def RemoveArtifactUrlScheme(artifact_url):
  """Ensures the given URL has no scheme (e.g.

  replaces "https://gcr.io/foo/bar" with "gcr.io/foo/bar" and leaves
  "gcr.io/foo/bar" unchanged).

  Args:
    artifact_url: A URL string.
  Returns:
    The URL with the scheme removed.
  """
  url_without_scheme = ReplaceImageUrlScheme(artifact_url, scheme='')
  try:
    # The validation logic in `docker_name` silently produces incorrect results
    # if the passed URL has a scheme.
    docker_name.Digest(url_without_scheme)
  except docker_name.BadNameException as e:
    raise BadImageUrlError(e)
  return url_without_scheme


def GetImageDigest(artifact_url):
  """Returns the digest of an image given its url.

  Args:
    artifact_url: An image url. e.g. "https://gcr.io/foo/bar@sha256:123"

  Returns:
    The image digest. e.g. "sha256:123"
  """
  url_without_scheme = ReplaceImageUrlScheme(artifact_url, scheme='')

  try:
    # The validation logic in `docker_name` silently produces incorrect results
    # if the passed URL has a scheme.
    digest = docker_name.Digest(url_without_scheme)
  except docker_name.BadNameException as e:
    raise BadImageUrlError(e)
  return digest.digest


def PaeEncode(dsse_type, body):
  """Pae encode input using the specified dsse type.

  Args:
    dsse_type: DSSE envelope type.
    body: payload string.

  Returns:
    Pae-encoded payload byte string.
  """
  dsse_type_bytes = dsse_type.encode('utf-8')
  body_bytes = body.encode('utf-8')
  return b' '.join([
      b'DSSEv1',
      b'%d' % len(dsse_type_bytes),
      dsse_type_bytes,
      b'%d' % len(body_bytes),
      body_bytes,
  ])


def GeneratePodSpecFromImages(images):
  """Creates a minimal PodSpec from a list of images.

  Args:
    images: list of images being evaluated.

  Returns:
    PodSpec object in JSON form.
  """
  spec = {
      'apiVersion': 'v1',
      'kind': 'Pod',
      'metadata': {
          'name': '',
      },
      'spec': {
          'containers': [{'image': image} for image in images],
      },
  }

  return spec


def AddInlineAttestationsToPodSpec(pod_spec, attestations):
  """Inlines attestations into a Kubernetes PodSpec.

  Args:
    pod_spec: The PodSpec provided by the user.
    attestations: List of attestations returned by the policy evaluator in comma
      separated DSSE form.

  Returns:
    Modified PodSpec with attestations inlined.
  """
  annotations = pod_spec['metadata'].get('annotations', {})
  existing_attestations = annotations.get(
      _BINAUTHZ_ATTESTATION_ANNOTATION_KEY, None
  )
  if existing_attestations:
    annotations[_BINAUTHZ_ATTESTATION_ANNOTATION_KEY] = ','.join(
        [existing_attestations] + attestations
    )
  else:
    annotations[_BINAUTHZ_ATTESTATION_ANNOTATION_KEY] = ','.join(attestations)
  pod_spec['metadata']['annotations'] = annotations
  return pod_spec


def AddInlineAttestationsToResource(resource, attestations):
  """Inlines attestations into a Kubernetes resource.

  Args:
    resource: The Kubernetes resource provided by the user.
    attestations: List of attestations returned by the policy evaluator in comma
      separated DSSE form.

  Returns:
    Modified Kubernetes resource with attestations inlined.
  """
  if resource['kind'] != 'Pod':
    resource['spec']['template'] = AddInlineAttestationsToPodSpec(
        resource['spec']['template'], attestations
    )
    return resource
  return AddInlineAttestationsToPodSpec(resource, attestations)
