# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Helpers for CryptoKeyVersions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base


def SetState(version_ref, state):
  """Updates the state of a CryptoKeyVersion.

  Args:
      version_ref: A resources.Resource for the CryptoKeyVersion.
      state: an apitools enum for ENABLED or DISABLED state.

  Returns:
      The updated CryptoKeyVersion.
  """
  client = cloudkms_base.GetClientInstance()
  messages = cloudkms_base.GetMessagesModule()

  req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsPatchRequest(  # pylint: disable=line-too-long
      name=version_ref.RelativeName(),
      updateMask='state',
      cryptoKeyVersion=messages.CryptoKeyVersion(state=state))

  return client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.Patch(
      req)


def Get(version_ref):
  """Gets a CryptoKeyVersion.

  Args:
    version_ref: A resources.Resource for the CryptoKeyVersion.

  Returns:
    The corresponding CryptoKeyVersion.
  """
  client = cloudkms_base.GetClientInstance()
  messages = cloudkms_base.GetMessagesModule()

  req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetRequest(
      name=version_ref.RelativeName())

  return client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.Get(
      req)


def GetPublicKey(version_ref):
  """Gets the public key of a CryptoKeyVersion.

  Args:
      version_ref: A resources.Resource for the CryptoKeyVersion.

  Returns:
      The CryptoKeyVersion's PublicKey.
  """
  client = cloudkms_base.GetClientInstance()
  messages = cloudkms_base.GetMessagesModule()

  req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetPublicKeyRequest(
      name=version_ref.RelativeName())

  return client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.GetPublicKey(
      req)
