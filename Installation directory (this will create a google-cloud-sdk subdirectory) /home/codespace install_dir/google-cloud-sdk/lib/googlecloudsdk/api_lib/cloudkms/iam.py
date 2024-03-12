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
"""IAM-related helpers for working with the Cloud KMS API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base
from googlecloudsdk.command_lib.iam import iam_util


def GetEkmConfigIamPolicy(ekm_config_name):
  """Fetch the IAM Policy attached to the EkmConfig.

  Args:
      ekm_config_name: A string name of the EkmConfig.

  Returns:
      An apitools wrapper for the IAM Policy.
  """
  client = base.GetClientInstance()
  messages = base.GetMessagesModule()

  req = messages.CloudkmsProjectsLocationsEkmConfigGetIamPolicyRequest(
      options_requestedPolicyVersion=iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION,
      resource=ekm_config_name)

  return client.projects_locations_ekmConfig.GetIamPolicy(req)


def SetEkmConfigIamPolicy(ekm_config_name, policy, update_mask):
  """Set the IAM Policy attached to the named EkmConfig to the given policy.

  If 'policy' has no etag specified, this will BLINDLY OVERWRITE the IAM policy!

  Args:
      ekm_config_name:  A string name of the EkmConfig.
      policy: An apitools wrapper for the IAM Policy.
      update_mask: str, FieldMask represented as comma-separated field names.

  Returns:
      The IAM Policy.
  """
  client = base.GetClientInstance()
  messages = base.GetMessagesModule()

  policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION
  if not update_mask:
    update_mask = 'version'
  elif 'version' not in update_mask:
    update_mask += ',version'

  req = messages.CloudkmsProjectsLocationsEkmConfigSetIamPolicyRequest(
      resource=ekm_config_name,
      setIamPolicyRequest=messages.SetIamPolicyRequest(
          policy=policy, updateMask=update_mask))

  return client.projects_locations_ekmConfig.SetIamPolicy(req)


def AddPolicyBindingToEkmConfig(ekm_config_name, member, role):
  """Does an atomic Read-Modify-Write, adding the member to the role."""
  messages = base.GetMessagesModule()

  policy = GetEkmConfigIamPolicy(ekm_config_name)
  iam_util.AddBindingToIamPolicy(messages.Binding, policy, member, role)
  return SetEkmConfigIamPolicy(
      ekm_config_name, policy, update_mask='bindings,etag')


def RemovePolicyBindingFromEkmConfig(ekm_config_name, member, role):
  """Does an atomic Read-Modify-Write, removing the member from the role."""
  policy = GetEkmConfigIamPolicy(ekm_config_name)
  iam_util.RemoveBindingFromIamPolicy(policy, member, role)
  return SetEkmConfigIamPolicy(
      ekm_config_name, policy, update_mask='bindings,etag')


def GetKeyRingIamPolicy(key_ring_ref):
  """Fetch the IAM Policy attached to the named KeyRing.

  Args:
      key_ring_ref: A resources.Resource naming the KeyRing.

  Returns:
      An apitools wrapper for the IAM Policy.
  """
  client = base.GetClientInstance()
  messages = base.GetMessagesModule()

  req = messages.CloudkmsProjectsLocationsKeyRingsGetIamPolicyRequest(
      options_requestedPolicyVersion=iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION,
      resource=key_ring_ref.RelativeName())

  return client.projects_locations_keyRings.GetIamPolicy(req)


def SetKeyRingIamPolicy(key_ring_ref, policy, update_mask):
  """Set the IAM Policy attached to the named KeyRing to the given policy.

  If 'policy' has no etag specified, this will BLINDLY OVERWRITE the IAM policy!

  Args:
      key_ring_ref: A resources.Resource naming the KeyRing.
      policy: An apitools wrapper for the IAM Policy.
      update_mask: str, FieldMask represented as comma-separated field names.

  Returns:
      The IAM Policy.
  """
  client = base.GetClientInstance()
  messages = base.GetMessagesModule()

  policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION
  if not update_mask:
    update_mask = 'version'
  elif 'version' not in update_mask:
    update_mask += ',version'

  req = messages.CloudkmsProjectsLocationsKeyRingsSetIamPolicyRequest(
      resource=key_ring_ref.RelativeName(),
      setIamPolicyRequest=messages.SetIamPolicyRequest(
          policy=policy, updateMask=update_mask))

  return client.projects_locations_keyRings.SetIamPolicy(req)


def AddPolicyBindingToKeyRing(key_ring_ref, member, role):
  """Does an atomic Read-Modify-Write, adding the member to the role."""
  messages = base.GetMessagesModule()

  policy = GetKeyRingIamPolicy(key_ring_ref)
  iam_util.AddBindingToIamPolicy(messages.Binding, policy, member, role)
  return SetKeyRingIamPolicy(key_ring_ref, policy, update_mask='bindings,etag')


def RemovePolicyBindingFromKeyRing(key_ring_ref, member, role):
  """Does an atomic Read-Modify-Write, removing the member from the role."""
  policy = GetKeyRingIamPolicy(key_ring_ref)
  iam_util.RemoveBindingFromIamPolicy(policy, member, role)
  return SetKeyRingIamPolicy(key_ring_ref, policy, update_mask='bindings,etag')


def GetCryptoKeyIamPolicy(crypto_key_ref):
  """Fetch the IAM Policy attached to the named CryptoKey.

  Args:
      crypto_key_ref: A resources.Resource naming the CryptoKey.

  Returns:
      An apitools wrapper for the IAM Policy.
  """
  client = base.GetClientInstance()
  messages = base.GetMessagesModule()

  req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetIamPolicyRequest(
      options_requestedPolicyVersion=iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION,
      resource=crypto_key_ref.RelativeName())

  return client.projects_locations_keyRings_cryptoKeys.GetIamPolicy(req)


def SetCryptoKeyIamPolicy(crypto_key_ref, policy, update_mask):
  """Set the IAM Policy attached to the named CryptoKey to the given policy.

  If 'policy' has no etag specified, this will BLINDLY OVERWRITE the IAM policy!

  Args:
      crypto_key_ref: A resources.Resource naming the CryptoKey.
      policy: An apitools wrapper for the IAM Policy.
      update_mask: str, FieldMask represented as comma-separated field names.

  Returns:
      The IAM Policy.
  """
  client = base.GetClientInstance()
  messages = base.GetMessagesModule()

  policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION
  if not update_mask:
    update_mask = 'version'
  elif 'version' not in update_mask:
    update_mask += ',version'

  req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysSetIamPolicyRequest(
      resource=crypto_key_ref.RelativeName(),
      setIamPolicyRequest=messages.SetIamPolicyRequest(
          policy=policy, updateMask=update_mask))

  return client.projects_locations_keyRings_cryptoKeys.SetIamPolicy(req)


def TestCryptoKeyIamPermissions(crypto_key_ref, permissions):
  """Return permissions that the caller has on the named CryptoKey."""
  client = base.GetClientInstance()
  messages = base.GetMessagesModule()

  req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysTestIamPermissionsRequest(
      resource=crypto_key_ref.RelativeName(),
      testIamPermissionsRequest=messages.TestIamPermissionsRequest(
          permissions=permissions))
  return client.projects_locations_keyRings_cryptoKeys.TestIamPermissions(req)


def AddPolicyBindingToCryptoKey(crypto_key_ref, member, role):
  """Add an IAM policy binding on the CryptoKey.

  Does an atomic Read-Modify-Write, adding the member to the role.

  Args:
    crypto_key_ref: A resources.Resource naming the CryptoKey.
    member: Principal to add to the policy binding.
    role: List of roles to add to the policy binding.

  Returns:
    The new IAM Policy.
  """
  return AddPolicyBindingsToCryptoKey(crypto_key_ref, [(member, role)])


def AddPolicyBindingsToCryptoKey(crypto_key_ref, member_roles):
  """Add IAM policy bindings on the CryptoKey.

  Does an atomic Read-Modify-Write, adding the members to the roles. Only calls
  SetIamPolicy if the policy would be different.

  Args:
    crypto_key_ref: A resources.Resource naming the CryptoKey.
    member_roles: List of 2-tuples in the form [(member, role), ...].

  Returns:
    The new IAM Policy.
  """
  messages = base.GetMessagesModule()

  policy = GetCryptoKeyIamPolicy(crypto_key_ref)
  policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION

  policy_was_updated = False
  for member, role in member_roles:
    if iam_util.AddBindingToIamPolicy(messages.Binding, policy, member, role):
      policy_was_updated = True

  if policy_was_updated:
    return SetCryptoKeyIamPolicy(
        crypto_key_ref, policy, update_mask='bindings,etag')

  return policy


def RemovePolicyBindingFromCryptoKey(crypto_key_ref, member, role):
  """Does an atomic Read-Modify-Write, removing the member from the role."""
  policy = GetCryptoKeyIamPolicy(crypto_key_ref)
  policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION

  iam_util.RemoveBindingFromIamPolicy(policy, member, role)
  return SetCryptoKeyIamPolicy(
      crypto_key_ref, policy, update_mask='bindings,etag')
