# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Tool and utils for creating Sigstore attestations stored as a Docker images."""

import base64
import binascii
import collections
import copy
import json
from typing import List, Optional, Text

from containerregistry.client import docker_creds
from containerregistry.client import docker_name
from containerregistry.client.v2_2 import docker_digest
from containerregistry.client.v2_2 import docker_http
from containerregistry.client.v2_2 import docker_image
from containerregistry.client.v2_2 import docker_session
from containerregistry.transform.v2_2 import metadata
from googlecloudsdk.api_lib.container.images import util
from googlecloudsdk.command_lib.container.binauthz import util as binauthz_util
from googlecloudsdk.core.exceptions import Error
import httplib2


DSSE_PAYLOAD_TYPE = 'application/vnd.dsse.envelope.v1+json'
BINAUTHZ_CUSTOM_PREDICATE = (
    'https://binaryauthorization.googleapis.com/policy_verification/v0.1'
)


def _RemovePrefix(text, prefix):
  if text.startswith(prefix):
    return text[len(prefix):]
  return text


def AddMissingBase64Padding(encoded):
  return encoded + '==='[: -len(encoded) % 4]


def StandardOrUrlsafeBase64Decode(encoded):
  try:
    return base64.b64decode(encoded)
  except binascii.Error:
    # Urlsafe encodings may or may not be padded.
    return base64.urlsafe_b64decode(AddMissingBase64Padding(encoded))


def AttestationToImageUrl(attestation):
  """Extract the image url from a DSSE of predicate type https://binaryauthorization.googleapis.com/policy_verification/*.

  This is a helper function for mapping attestations back to their respective
  images. Do not use this for signature verification.

  Args:
    attestation: The attestation in base64 encoded string form.

  Returns:
    The image url referenced in the attestation.
  """
  # The DSSE spec permits either standard or URL-safe base64 encoding.
  deser_att = json.loads(StandardOrUrlsafeBase64Decode(attestation))

  deser_payload = json.loads(
      StandardOrUrlsafeBase64Decode(deser_att['payload'])
  )
  return '{}@sha256:{}'.format(
      deser_payload['subject'][0]['name'],
      deser_payload['subject'][0]['digest']['sha256'],
  )


def UploadAttestationToRegistry(
    image_url, attestation, use_docker_creds=None, docker_config_dir=None
):
  """Uploads a DSSE attestation to the registry.

  Args:
    image_url: The image url of the target image.
    attestation: The attestation referencing the target image in JSON DSSE form.
    use_docker_creds: Whether to use the Docker configuration file for
      authenticating to the registry.
    docker_config_dir: Directory where Docker saves authentication settings.
  """
  http_obj = httplib2.Http()
  # The registry name is deduced by splitting on the first '/' char. This will
  # not work properly if the image url has a scheme.
  target_image = docker_name.Digest(
      binauthz_util.ReplaceImageUrlScheme(image_url, scheme='')
  )
  # Sigstore scheme for tag based discovery.
  attestation_tag = docker_name.Tag(
      '{}/{}:sha256-{}.att'.format(
          target_image.registry,
          target_image.repository,
          _RemovePrefix(target_image.digest, 'sha256:'),
      )
  )

  creds = None
  if use_docker_creds:
    keychain = docker_creds.DefaultKeychain
    if docker_config_dir:
      keychain.setCustomConfigDir(docker_config_dir)
    creds = keychain.Resolve(docker_name.Registry(target_image.registry))
  if creds is None or isinstance(creds, docker_creds.Anonymous):
    creds = util.CredentialProvider()

  # Check if attestation image already exists and if so append a new layer.
  # Only check for Image Manifest Version 2, Schema 2 images since that format
  # predates Sigstore.
  with docker_image.FromRegistry(
      attestation_tag,
      creds,
      http_obj,
      accepted_mimes=docker_http.SUPPORTED_MANIFEST_MIMES,
  ) as v2_2_image:
    if v2_2_image.exists():
      new_image = SigstoreAttestationImage([attestation], v2_2_image)
      # TODO(b/310721968): Use etags to mitigate against read-modify-update race
      # conditions.
      docker_session.Push(attestation_tag, creds, http_obj).upload(new_image)
      return

  # Otherwise create a new image.
  new_image = SigstoreAttestationImage([attestation])
  docker_session.Push(attestation_tag, creds, http_obj).upload(new_image)


class SigstoreAttestationImage(docker_image.DockerImage):
  """Creates a new image or appends a layers on top of an existing image.

  Adheres to the Sigstore Attestation spec:
  https://github.com/sigstore/cosign/blob/main/specs/ATTESTATION_SPEC.md.
  """

  def __init__(
      self,
      additional_blobs: List[bytes],
      base: Optional[docker_image.DockerImage] = None,
  ):
    """Creates a new Sigstore style image or extends a base image.

    Args:
      additional_blobs: additional attestations to be appended to the image.
      base: optional base DockerImage.
    """
    self._additional_blobs = collections.OrderedDict(
        (docker_digest.SHA256(blob), blob) for blob in additional_blobs
    )
    if base is not None:
      self._base = base
      self._base_manifest = json.loads(self._base.manifest())
      self._base_config_file = json.loads(self._base.config_file())
    else:
      self._base = None
      self._base_manifest = {
          'mediaType': docker_http.OCI_MANIFEST_MIME,
          'schemaVersion': 2,
          'config': {
              'digest': '',  # Populated below.
              'mediaType': docker_http.CONFIG_JSON_MIME,
              'size': 0,
          },
          'layers': [],  # Populated below.
      }
      self._base_config_file = dict()

  def add_layer(self, blob: bytes) -> None:
    self._additional_blobs[docker_digest.SHA256(blob)] = blob

  def config_file(self) -> Text:
    """Override."""
    config_file = self._base_config_file
    overrides = metadata.Overrides()
    overrides = overrides.Override(created_by=docker_name.USER_AGENT)

    layers = [
        _RemovePrefix(blob_sum, 'sha256:')
        for blob_sum in self._additional_blobs.keys()
    ]

    overrides = overrides.Override(
        layers=layers,
    )

    # Override makes a deep copy of the base config file before modifying it.
    config_file = metadata.Override(
        config_file,
        options=overrides,
        architecture='',
        operating_system='',
    )

    return json.dumps(config_file, sort_keys=True)

  def manifest(self) -> Text:
    """Override."""
    manifest = copy.deepcopy(self._base_manifest)
    for blob_sum, blob in self._additional_blobs.items():
      manifest['layers'].append({
          'digest': blob_sum,
          'mediaType': DSSE_PAYLOAD_TYPE,
          'size': len(blob),
          'annotations': {
              'dev.cosignproject.cosign/signature': '',
              'predicateType': BINAUTHZ_CUSTOM_PREDICATE,
          },
      })

    config_file = self.config_file()
    utf8_encoded_config = config_file.encode('utf8')
    manifest['config']['digest'] = docker_digest.SHA256(utf8_encoded_config)
    manifest['config']['size'] = len(utf8_encoded_config)
    return json.dumps(manifest, sort_keys=True)

  def blob(self, digest: Text) -> bytes:
    """Override. Returns uncompressed blob."""
    if digest in self._additional_blobs:
      return self._additional_blobs[digest]
    if self._base:
      return self._base.blob(digest)
    raise Error('Digest not found: {}'.format(digest))

  # __enter__ and __exit__ allow use as a context manager.
  def __enter__(self):
    """Override."""
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Override."""
    return
