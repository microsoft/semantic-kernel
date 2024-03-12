# -*- coding: utf-8 -*-
# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Helper functions for dealing with encryption keys used with cloud APIs."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import base64
import binascii
from hashlib import sha256
import re
import sys

import six
from gslib.exception import CommandException
from gslib.lazy_wrapper import LazyWrapper

MAX_DECRYPTION_KEYS = 100
VALID_CMEK_RE = LazyWrapper(
    lambda: re.compile('projects/([^/]+)/'
                       'locations/([a-zA-Z0-9_-]{1,63})/'
                       'keyRings/([a-zA-Z0-9_-]{1,63})/'
                       'cryptoKeys/([a-zA-Z0-9_-]{1,63})$'))


class CryptoKeyType(object):
  """Enum of valid types of encryption keys used with cloud API requests."""
  CSEK = 'CSEK'
  CMEK = 'CMEK'


class CryptoKeyWrapper(object):
  """Class describing a crypto key used with cloud API requests.

  This class should be instantiated via the `CryptoKeyWrapperFromKey` method.
  """

  def __init__(self, crypto_key):
    """Initialize the CryptoKeyWrapper.

    Args:
      crypto_key: Base64-encoded string of a CSEK, or the name of a Cloud KMS
          CMEK.

    Raises:
      CommandException: The specified crypto key was neither a CMEK key name nor
          a valid base64-encoded string of a CSEK.
    """
    self.crypto_key = crypto_key
    # Base64-encoded CSEKs always have a length of 44 characters, whereas
    # fully-qualified CMEK names are guaranteed to be longer than 45 characters.
    if len(crypto_key) == 44:
      self.crypto_type = CryptoKeyType.CSEK
      self.crypto_alg = 'AES256'  # Only currently supported algorithm for CSEK.
      try:
        self.crypto_key_sha256 = Base64Sha256FromBase64EncryptionKey(crypto_key)
      except:
        raise CommandException(
            'Configured encryption_key or decryption_key looked like a CSEK, '
            'but it was not a valid 44-character base64 string. Please '
            'double-check your configuration and ensure the key is correct.')
    else:  # CMEK
      try:
        ValidateCMEK(crypto_key)
      except CommandException as e:
        raise CommandException(
            'Configured encryption_key or decryption_key looked like a CMEK, '
            'but the key failed validation:\n%s' % e.reason)
      self.crypto_type = CryptoKeyType.CMEK
      self.crypto_alg = None
      self.crypto_key_sha256 = None


def CryptoKeyWrapperFromKey(crypto_key):
  """Returns a CryptoKeyWrapper for crypto_key, or None for no key."""
  return CryptoKeyWrapper(crypto_key) if crypto_key else None


def FindMatchingCSEKInBotoConfig(key_sha256, boto_config):
  """Searches boto_config for a CSEK with the given base64-encoded SHA256 hash.

  Args:
    key_sha256: (str) Base64-encoded SHA256 hash of the AES256 encryption key.
    boto_config: (boto.pyami.config.Config) The boto config in which to check
        for a matching encryption key.

  Returns:
    (str) Base64-encoded encryption key string if a match is found, None
    otherwise.
  """
  if six.PY3:
    if not isinstance(key_sha256, bytes):
      key_sha256 = key_sha256.encode('ascii')
  keywrapper = CryptoKeyWrapperFromKey(
      boto_config.get('GSUtil', 'encryption_key', None))
  if (keywrapper is not None and
      keywrapper.crypto_type == CryptoKeyType.CSEK and
      keywrapper.crypto_key_sha256 == key_sha256):
    return keywrapper.crypto_key

  for i in range(MAX_DECRYPTION_KEYS):
    key_number = i + 1
    keywrapper = CryptoKeyWrapperFromKey(
        boto_config.get('GSUtil', 'decryption_key%s' % str(key_number), None))
    if keywrapper is None:
      # Reading 100 config values can take ~1ms in testing. To avoid adding
      # this tax, stop reading keys as soon as we encounter a non-existent
      # entry (in lexicographic order).
      break
    elif (keywrapper.crypto_type == CryptoKeyType.CSEK and
          keywrapper.crypto_key_sha256 == key_sha256):
      return keywrapper.crypto_key


def GetEncryptionKeyWrapper(boto_config):
  """Returns a CryptoKeyWrapper for the configured encryption key.

  Reads in the value of the "encryption_key" attribute in boto_config, and if
  present, verifies it is a valid base64-encoded string and returns a
  CryptoKeyWrapper for it.

  Args:
    boto_config: (boto.pyami.config.Config) The boto config in which to check
        for a matching encryption key.

  Returns:
    CryptoKeyWrapper for the specified encryption key, or None if no encryption
    key was specified in boto_config.
  """
  encryption_key = boto_config.get('GSUtil', 'encryption_key', None)
  return CryptoKeyWrapper(encryption_key) if encryption_key else None


def Base64Sha256FromBase64EncryptionKey(csek_encryption_key):
  if six.PY3:
    if not isinstance(csek_encryption_key, bytes):
      csek_encryption_key = csek_encryption_key.encode('ascii')
  decoded_bytes = base64.b64decode(csek_encryption_key)
  key_sha256 = _CalculateSha256FromString(decoded_bytes)
  sha256_bytes = binascii.unhexlify(key_sha256)
  sha256_base64 = base64.b64encode(sha256_bytes)
  return sha256_base64.replace(b'\n', b'')


def ValidateCMEK(key):
  if not key:
    raise CommandException('KMS key is empty.')

  if key.startswith('/'):
    raise CommandException(
        'KMS key should not start with leading slash (/): "%s"' % key)

  if not VALID_CMEK_RE().match(key):
    raise CommandException(
        'Invalid KMS key name: "%s".\nKMS keys should follow the format '
        '"projects/<project-id>/locations/<location>/keyRings/<keyring>/'
        'cryptoKeys/<key-name>"' % key)


def _CalculateSha256FromString(input_string):
  sha256_hash = sha256()
  sha256_hash.update(input_string)
  return sha256_hash.hexdigest()


def _GetAndVerifyBase64EncryptionKey(boto_config):
  """Reads the encryption key from boto_config and ensures it is base64-encoded.

  Args:
    boto_config: (boto.pyami.config.Config) The boto config in which to check
        for a matching encryption key.

  Returns:
    (str) Base64-encoded encryption key string, or None if no encryption key
    exists in configuration.

  """
  encryption_key = boto_config.get('GSUtil', 'encryption_key', None)
  if encryption_key:
    # Ensure the key has a valid encoding.
    try:
      base64.b64decode(encryption_key)
    except:
      raise CommandException(
          'Configured encryption_key is not a valid base64 string. Please '
          'double-check your configuration and ensure the key is valid and in '
          'base64 format.')
  return encryption_key
