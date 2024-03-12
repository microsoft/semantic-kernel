# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Utilities that support customer encryption flows."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import collections
import enum
import hashlib
import re

from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import hash_util
from googlecloudsdk.command_lib.storage import user_request_args_factory
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.cache import function_result_cache


_CMEK_REGEX = re.compile('projects/([^/]+)/'
                         'locations/([a-zA-Z0-9_-]{1,63})/'
                         'keyRings/([a-zA-Z0-9_-]{1,63})/'
                         'cryptoKeys/([a-zA-Z0-9_-]{1,63})$')
ENCRYPTION_ALGORITHM = 'AES256'


class KeyType(enum.Enum):
  CMEK = 'CMEK'
  CSEK = 'CSEK'


EncryptionKey = collections.namedtuple(
    'EncryptionKey',
    [
        'key',  # Str. The key itself.
        'type',  # A value from KeyType.
        'sha256',  # Base64 encoded hash of `key` if CSEK, None if CMEK.
    ])


class _KeyStore:
  """Holds encryption key information.

  Attributes:
    encryption_key (Optional[EncryptionKey]): The key for encryption.
    decryption_key_index (Dict[EncryptionKey.sha256, EncryptionKey]): Indexes
      keys that can be used for decryption.
    initialized (bool): True if encryption_key and decryption_key_index
      reflect the values they should based on flag and key file values.
  """

  def __init__(self,
               encryption_key=None,
               decryption_key_index=None,
               initialized=False):
    self.encryption_key = encryption_key
    self.decryption_key_index = decryption_key_index or {}
    self.initialized = initialized

  def __eq__(self, other):
    if not isinstance(other, self.__class__):
      return NotImplemented
    return (
        self.encryption_key == other.encryption_key and
        self.decryption_key_index == other.decryption_key_index and
        self.initialized == other.initialized
    )


_key_store = _KeyStore()


def validate_cmek(raw_key):
  if not raw_key:
    raise errors.Error('Key is empty.')

  if raw_key.startswith('/'):
    raise errors.Error('KMS key should not start with leading slash (/): ' +
                       raw_key)

  if not _CMEK_REGEX.match(raw_key):
    raise errors.Error(
        'Invalid KMS key name: {}.\nKMS keys should follow the format '
        '"projects/<project-id>/locations/<location>/keyRings/<keyring>/'
        'cryptoKeys/<key-name>"'.format(raw_key))


def parse_key(raw_key):
  """Returns an EncryptionKey populated with information from raw_key."""
  raw_key_bytes = raw_key.encode('ascii')
  try:
    validate_cmek(raw_key)
    key_type = KeyType.CMEK
    sha256 = None
  except errors.Error:
    if len(raw_key) != 44:
      raise
    key_type = KeyType.CSEK
    sha256 = hash_util.get_base64_hash_digest_string(
        hashlib.sha256(base64.b64decode(raw_key_bytes)))
  return EncryptionKey(key=raw_key, sha256=sha256, type=key_type)


@function_result_cache.lru(maxsize=1)
def _read_key_store_file():
  key_store_path = properties.VALUES.storage.key_store_path.Get()
  if not key_store_path:
    return {}
  return yaml.load_path(key_store_path)


def _get_raw_key(args, key_field_name):
  """Searches for key values in flags, falling back to a file if necessary.

  Args:
    args: An object containing flag values from the command surface.
    key_field_name (str): Corresponds to a flag name or field name in the key
        file.

  Returns:
    The flag value associated with key_field_name, or the value contained in the
    key file.
  """
  flag_key = getattr(args, key_field_name, None)
  if flag_key is not None:
    return flag_key
  return _read_key_store_file().get(key_field_name)


def _index_decryption_keys(raw_keys):
  """Parses and indexes raw keys.

  Args:
    raw_keys (list[str]): The keys to index.

  Returns:
    A dict mapping key hashes to keys in raw_keys. Falsy elements of raw_keys
    and non-CSEKs are skipped.
  """
  index = {}
  if raw_keys:
    for raw_key in raw_keys:
      if not raw_key:
        continue
      key = parse_key(raw_key)
      if key.type == KeyType.CSEK:
        index[key.sha256] = key
  return index


def initialize_key_store(args):
  """Loads appropriate encryption and decryption keys into memory.

  Prefers values from flags over those from the user's key file. If _key_store
    is not already initialized, creates a _KeyStore instance and stores it in a
    global variable.

  Args:
    args: An object containing flag values from the command surface.
  """
  if _key_store.initialized:
    return

  raw_encryption_key = _get_raw_key(args, 'encryption_key')
  if getattr(args, 'clear_encryption_key', None):
    _key_store.encryption_key = user_request_args_factory.CLEAR
  elif raw_encryption_key:
    _key_store.encryption_key = parse_key(raw_encryption_key)

  raw_keys = [raw_encryption_key]
  raw_decryption_keys = _get_raw_key(args, 'decryption_keys')
  if raw_decryption_keys:
    raw_keys += raw_decryption_keys
  _key_store.decryption_key_index = _index_decryption_keys(raw_keys)

  _key_store.initialized = True


def get_decryption_key(sha256_hash, url_for_missing_key_error=None):
  """Returns a key that matches sha256_hash, or None if no key is found."""
  if _key_store.initialized:
    decryption_key = _key_store.decryption_key_index.get(sha256_hash)
  else:
    decryption_key = None
  if not decryption_key and url_for_missing_key_error:
    raise errors.Error(
        'Missing decryption key with SHA256 hash {}. No decryption key '
        'matches object {}.'.format(sha256_hash, url_for_missing_key_error))
  return decryption_key


def get_encryption_key(sha256_hash=None, url_for_missing_key_error=None):
  """Returns an EncryptionKey, None, or a CLEAR string constant.

  Args:
    sha256_hash (str): Attempts to return a CSEK key that matches this hash.
      Used for encrypting with a non-default key.
    url_for_missing_key_error (StorageUrl): If a key matching sha256_hash can
      not be found, raise an error adding this object URL to the error text.

  Returns:
    EncryptionKey: Custom or default key depending on presence of sha256_hash.
    None: Matching key to sha256_hash could not be found and
      url_for_missing_key_error was None. Or, no sha256_hash and no default key.
    user_request_args_factory.CLEAR (str): Value indicating that the
      user requested to clear an existing encryption.
  """
  if _key_store.initialized:
    if sha256_hash:
      return get_decryption_key(sha256_hash, url_for_missing_key_error)
    return _key_store.encryption_key
