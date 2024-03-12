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
"""Utility functions for Cloud KMS integration with GCE.

Collection of methods to handle Cloud KMS (Key Management Service) resources
with Google Compute Engine (GCE).
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

KMS_HELP_URL = ('https://cloud.google.com/compute/docs/disks/'
                'customer-managed-encryption')
_KMS_ARGS = [
    'kms-key', 'kms-keyring', 'kms-location', 'kms-project',
    'boot-disk-kms-key', 'boot-disk-kms-keyring', 'boot-disk-kms-location',
    'boot-disk-kms-project', 'instance-kms-key', 'instance-kms-keyring',
    'instance-kms-location', 'instance-kms-project'
]


def _GetSpecifiedKmsArgs(args):
  """Returns the first KMS related argument as a string."""
  if not args:
    return None
  specified = set()
  for keyword in _KMS_ARGS:
    if getattr(args, keyword.replace('-', '_'), None):
      specified.add('--' + keyword)
  return specified


def _GetSpecifiedKmsDict(args):
  """Returns the first KMS related argument as a string."""
  if not args:
    return None
  specified = set()
  for keyword in _KMS_ARGS:
    if keyword in args:
      specified.add(keyword)
  return specified


def _DictToKmsKey(args):
  """Returns the Cloud KMS crypto key name based on the KMS args."""
  if not args:
    return None

  def GetValue(args, key):

    def GetValueFunc():
      val = args[key] if key in args else None
      if val:
        return val
      raise calliope_exceptions.InvalidArgumentException(
          '--create-disk',
          'KMS cryptokey resource was not fully specified. Key [{}] must '
          'be specified.'.format(key))

    return GetValueFunc

  return resources.REGISTRY.Parse(
      GetValue(args, 'kms-key')(),
      params={
          'projectsId':
              args['kms-project'] if 'kms-project' in args else
              properties.VALUES.core.project.GetOrFail,
          'locationsId':
              GetValue(args, 'kms-location'),
          'keyRingsId':
              GetValue(args, 'kms-keyring'),
          'cryptoKeysId':
              GetValue(args, 'kms-key'),
      },
      collection='cloudkms.projects.locations.keyRings.cryptoKeys')


def _DictToMessage(args, messages):
  """Returns the Cloud KMS crypto key name based on the values in the dict."""
  key = _DictToKmsKey(args)
  if not key:
    return None
  return messages.CustomerEncryptionKey(kmsKeyName=key.RelativeName())


def MaybeGetKmsKey(args,
                   messages,
                   current_value,
                   boot_disk_prefix=False,
                   instance_prefix=False):
  """Gets the Cloud KMS CryptoKey reference from command arguments.

  Args:
    args: Namespaced command line arguments.
    messages: Compute API messages module.
    current_value: Current CustomerEncryptionKey value.
    boot_disk_prefix: If the key flags have the 'boot-disk' prefix.
    instance_prefix: If the key flags have the 'instance' prefix.

  Returns:
    CustomerEncryptionKey message with the KMS key populated if args has a key.
  Raises:
    ConflictingArgumentsException if an encryption key is already populated.
  """
  if boot_disk_prefix:
    key_arg = args.CONCEPTS.boot_disk_kms_key
    flag = '--boot-disk-kms-key'
  elif instance_prefix:
    key_arg = args.CONCEPTS.instance_kms_key
    flag = '--instance-kms-key'
  else:
    key_arg = args.CONCEPTS.kms_key
    flag = '--kms-key'
  key = key_arg.Parse()

  if flag in _GetSpecifiedKmsArgs(args) and not key:
    raise calliope_exceptions.InvalidArgumentException(
        flag, 'KMS cryptokey resource was not fully specified.')
  if key:
    if current_value:
      raise calliope_exceptions.ConflictingArgumentsException(
          '--csek-key-file', *_GetSpecifiedKmsArgs(args))
    return messages.CustomerEncryptionKey(kmsKeyName=key.RelativeName())
  return current_value


def MaybeGetKmsKeyFromDict(args,
                           messages,
                           current_value,
                           conflicting_arg='--csek-key-file'):
  """Gets the Cloud KMS CryptoKey reference for a boot disk's initialize params.

  Args:
    args: A dictionary of a boot disk's initialize params.
    messages: Compute API messages module.
    current_value: Current CustomerEncryptionKey value.
    conflicting_arg: name of conflicting argument

  Returns:
    CustomerEncryptionKey message with the KMS key populated if args has a key.
  Raises:
    ConflictingArgumentsException if an encryption key is already populated.
  """
  if bool(_GetSpecifiedKmsDict(args)):
    if current_value:
      raise calliope_exceptions.ConflictingArgumentsException(
          conflicting_arg, *_GetSpecifiedKmsArgs(args))
    return _DictToMessage(args, messages)
  return current_value
