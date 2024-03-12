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
"""Utilities for OS Login subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import time


def GetKeyDictionaryFromProfile(user, oslogin_client, profile=None):
  """Return a dictionary of fingerprints/keys from the OS Login Profile."""
  if not profile:
    profile = oslogin_client.GetLoginProfile(user)
  key_dir = {}

  if not profile.sshPublicKeys:
    return {}

  for ssh_pub_key in profile.sshPublicKeys.additionalProperties:
    key_dir[ssh_pub_key.key] = ssh_pub_key.value.key

  return key_dir


def GetSecurityKeysFromProfile(user, oslogin_client, profile=None):
  """Return a list of 'private' security keys from the OS Login Profile."""
  if not profile:
    profile = oslogin_client.GetLoginProfile(user)

  sk_list = []
  if not hasattr(profile, 'securityKeys') or not profile.securityKeys:
    return []

  for security_key in profile.securityKeys:
    sk_list.append(security_key.privateKey)

  return sk_list


def GetKeysFromProfile(user, oslogin_client):
  profile = oslogin_client.GetLoginProfile(user)
  if profile.sshPublicKeys:
    return profile.sshPublicKeys.additionalProperties


def FindKeyInKeyList(key_arg, profile_keys):
  """Return the fingerprint of an SSH key that matches the key argument."""
  # Is the key value a fingerprint?
  key = profile_keys.get(key_arg)
  if key:
    return key_arg

  # Try to split the key info. If there are multiple fields, use the second one.
  key_split = key_arg.split()
  if not key_split:
    return None
  if len(key_split) == 1:
    key_value = key_split[0]
  else:
    key_value = key_split[1]

  for fingerprint, ssh_key in profile_keys.items():
    if key_value in ssh_key:
      return fingerprint


def ConvertTtlArgToExpiry(ttl):
  if not ttl:
    return None
  now = time.time()
  expiry_secs = ttl + now
  expiry_usecs = int(expiry_secs * 1000000)
  return expiry_usecs


def ConvertUsecToRfc3339(usec):
  if not usec:
    return
  usec = int(usec)
  sec = usec / 1000000
  return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(sec))
