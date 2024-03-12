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
"""This package holds a handful of utilities for manipulating manifests."""

from __future__ import absolute_import
from __future__ import division

from __future__ import print_function

import base64
import json
import os
import subprocess

from containerregistry.client import docker_name


class BadManifestException(Exception):
  """Exception type raised when a malformed manifest is encountered."""


def _JoseBase64UrlDecode(message):
  """Perform a JOSE-style base64 decoding of the supplied message.

  This is based on the docker/libtrust version of the similarly named
  function found here:
    https://github.com/docker/libtrust/blob/master/util.go

  Args:
    message: a JOSE-style base64 url-encoded message.
  Raises:
    BadManifestException: a malformed message was supplied.
  Returns:
    The decoded message.
  """
  bytes_msg = message.encode('utf8')
  l = len(bytes_msg)
  if l % 4 == 0:
    pass
  elif l % 4 == 2:
    bytes_msg += b'=='
  elif l % 4 == 3:
    bytes_msg += b'='
  else:
    raise BadManifestException('Malformed JOSE Base64 encoding.')

  return base64.urlsafe_b64decode(bytes_msg).decode('utf8')


def _ExtractProtectedRegion(signature):
  """Extract the length and encoded suffix denoting the protected region."""
  protected = json.loads(_JoseBase64UrlDecode(signature['protected']))
  return (protected['formatLength'], protected['formatTail'])


def _ExtractCommonProtectedRegion(
    signatures):
  """Verify that the signatures agree on the protected region and return one."""
  p = _ExtractProtectedRegion(signatures[0])
  for sig in signatures[1:]:
    if p != _ExtractProtectedRegion(sig):
      raise BadManifestException('Signatures disagree on protected region')
  return p


def DetachSignatures(manifest):
  """Detach the signatures from the signed manifest and return the two halves.

  Args:
    manifest: a signed JSON manifest.
  Raises:
    BadManifestException: the provided manifest was improperly signed.
  Returns:
    a pair consisting of the manifest with the signature removed and a list of
    the removed signatures.
  """
  # First, decode the manifest to extract the list of signatures.
  json_manifest = json.loads(manifest)

  # Next, extract the signatures that have signed a portion of the manifest.
  signatures = json_manifest['signatures']

  # Do some basic validation of the signature input
  if len(signatures) < 1:
    raise BadManifestException('Expected a signed manifest.')
  for sig in signatures:
    if 'protected' not in sig:
      raise BadManifestException('Signature is missing "protected" key')

  # Establish the protected region and extract it from our original string.
  (format_length, format_tail) = _ExtractCommonProtectedRegion(signatures)
  suffix = _JoseBase64UrlDecode(format_tail)
  unsigned_manifest = manifest[0:format_length] + suffix

  return (unsigned_manifest, signatures)


def Sign(unsigned_manifest):
  # TODO(user): Implement v2 signing in Python.
  return unsigned_manifest




def _AttachSignatures(manifest,
                      signatures):
  """Attach the provided signatures to the provided naked manifest."""
  (format_length, format_tail) = _ExtractCommonProtectedRegion(signatures)
  prefix = manifest[0:format_length]
  suffix = _JoseBase64UrlDecode(format_tail)
  return '{prefix},"signatures":{signatures}{suffix}'.format(
      prefix=prefix,
      signatures=json.dumps(signatures, sort_keys=True),
      suffix=suffix)


def Rename(manifest, name):
  """Rename this signed manifest to the provided name, and resign it."""
  unsigned_manifest, unused_signatures = DetachSignatures(manifest)

  json_manifest = json.loads(unsigned_manifest)
  # Rewrite the name fields.
  json_manifest['name'] = name.repository
  json_manifest['tag'] = name.tag

  # Reserialize the json to a string.
  updated_unsigned_manifest = json.dumps(
      json_manifest, sort_keys=True, indent=2)

  # Sign the updated manifest
  return Sign(updated_unsigned_manifest)
