# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Helper functions for interacting with the cloudkms API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.kms import get_digest
from googlecloudsdk.command_lib.kms import maps

import six

API_NAME = 'cloudkms'

V1 = 'v1'
DEFAULT_VERSION = V1


class Client(object):
  """A client to access cloudkms for binauthz purposes."""

  def __init__(self, api_version=None):
    """Creates a Cloud KMS client.

    Args:
      api_version: If provided, the cloudkms API version to use.
    """
    if api_version is None:
      api_version = DEFAULT_VERSION

    self.client = apis.GetClientInstance(API_NAME, api_version)
    self.messages = apis.GetMessagesModule(API_NAME, api_version)

  def GetPublicKey(self, key_ref):
    """Retrieves the public key for given CryptoKeyVersion."""
    req = self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetPublicKeyRequest(
        name=key_ref)
    return (
        self.client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.
        GetPublicKey(req))

  def AsymmetricSign(self, key_ref, digest_algorithm, plaintext):
    """Sign a string payload with an asymmetric KMS CryptoKeyVersion.

    Args:
      key_ref: The CryptoKeyVersion relative resource name to sign with.
      digest_algorithm: The name of the digest algorithm to use in the signing
          operation. May be one of 'sha256', 'sha384', 'sha512'.
      plaintext: The plaintext bytes to sign.

    Returns:
      An AsymmetricSignResponse.
    """
    digest = get_digest.GetDigestOfFile(
        digest_algorithm, six.BytesIO(plaintext))
    req = self.messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsAsymmetricSignRequest(
        name=key_ref,
        asymmetricSignRequest=self.messages.AsymmetricSignRequest(
            digest=digest))
    return (
        self.client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.
        AsymmetricSign(req))


def GetKeyUri(key_ref):
  """Returns the URI used as the default for KMS keys.

  This should look something like '//cloudkms.googleapis.com/v1/...'

  Args:
    key_ref: A CryptoKeyVersion Resource.

  Returns:
    The string URI.
  """
  return key_ref.SelfLink().split(':', 1)[1]


def GetAlgorithmDigestType(key_algorithm):
  """Returns the digest name associated with the given CryptoKey Algorithm."""
  for digest_name in maps.DIGESTS:
    if digest_name in key_algorithm.name.lower():
      return digest_name
