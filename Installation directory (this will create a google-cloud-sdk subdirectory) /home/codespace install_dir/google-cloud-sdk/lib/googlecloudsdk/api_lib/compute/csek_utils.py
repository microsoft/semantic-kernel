# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Utility functions for managing customer supplied encryption keys."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import base64
import json
import re

from googlecloudsdk.api_lib.compute import exceptions
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
import six

CSEK_HELP_URL = ('https://cloud.google.com/compute/docs/disks/'
                 'customer-supplied-encryption')
EXPECTED_RECORD_KEY_KEYS = {'uri', 'key', 'key-type'}
BASE64_RAW_KEY_LENGTH_IN_CHARS = 44
BASE64_RSA_ENCRYPTED_KEY_LENGTH_IN_CHARS = 344


class Error(exceptions.Error):
  """Base exception for Csek(customer supplied encryption keys) exceptions."""


class InvalidKeyFileException(Error):
  """There's a problem in a CSEK file."""

  def __init__(self, base_message):
    super(InvalidKeyFileException, self).__init__(
        '{0}\nFor information on proper key file format see: '
        'https://cloud.google.com/compute/docs/disks/'
        'customer-supplied-encryption#key_file'.format(base_message))


class BadPatternException(InvalidKeyFileException):
  """A (e.g.) url pattern is bad and why."""

  def __init__(self, pattern_type, pattern):
    self.pattern_type = pattern_type
    self.pattern = pattern
    super(BadPatternException, self).__init__(
        'Invalid value for [{0}] pattern: [{1}]'.format(
            self.pattern_type,
            self.pattern))


class InvalidKeyExceptionNoContext(InvalidKeyFileException):
  """Indicate that a particular key is bad and why."""

  def __init__(self, key, issue):
    self.key = key
    self.issue = issue
    super(InvalidKeyExceptionNoContext, self).__init__(
        'Invalid key, [{0}] : {1}'.format(
            self.key,
            self.issue))


class InvalidKeyException(InvalidKeyFileException):
  """Indicate that a particular key is bad, why, and where."""

  def __init__(self, key, key_id, issue):
    self.key = key
    self.key_id = key_id
    self.issue = issue
    super(InvalidKeyException, self).__init__(
        'Invalid key, [{0}], for [{1}]: {2}'.format(
            self.key,
            self.key_id,
            self.issue))


def ValidateKey(base64_encoded_string, expected_key_length):
  """ValidateKey(s, k) returns None or raises InvalidKeyExceptionNoContext."""

  if expected_key_length < 1:
    raise ValueError('ValidateKey requires expected_key_length > 1.  Got {0}'
                     .format(expected_key_length))

  if len(base64_encoded_string) != expected_key_length:
    raise InvalidKeyExceptionNoContext(
        base64_encoded_string,
        'Key should contain {0} characters (including padding), '
        'but is [{1}] characters long.'.format(
            expected_key_length,
            len(base64_encoded_string)))

  if base64_encoded_string[-1] != '=':
    raise InvalidKeyExceptionNoContext(
        base64_encoded_string,
        'Bad padding.  Keys should end with an \'=\' character.')

  try:
    base64_encoded_string_as_str = base64_encoded_string.encode('ascii')
  except UnicodeDecodeError:
    raise InvalidKeyExceptionNoContext(
        base64_encoded_string,
        'Key contains non-ascii characters.')

  if not re.match(r'^[a-zA-Z0-9+/=]*$', base64_encoded_string):
    raise InvalidKeyExceptionNoContext(
        base64_encoded_string_as_str,
        'Key contains unexpected characters. Base64 encoded strings '
        'contain only letters (upper or lower case), numbers, '
        'plusses \'+\', slashes \'/\', or equality signs \'=\'.')

  try:
    base64.b64decode(base64_encoded_string_as_str)
  except TypeError as t:
    raise InvalidKeyExceptionNoContext(
        base64_encoded_string,
        'Key is not valid base64: [{0}].'.format(t.message))


class CsekKeyBase(six.with_metaclass(abc.ABCMeta, object)):
  """A class representing for CSEK keys."""

  def __init__(self, key_material):
    ValidateKey(key_material, expected_key_length=self.GetKeyLength())
    self._key_material = key_material

  @staticmethod
  def MakeKey(key_material, key_type, allow_rsa_encrypted=False):
    """Make a CSEK key.

    Args:
      key_material: str, the key material for this key
      key_type: str, the type of this key
      allow_rsa_encrypted: bool, whether the key is allowed to be RSA-wrapped

    Returns:
      CsekRawKey or CsekRsaEncryptedKey derived from the given key material and
      type.

    Raises:
      BadKeyTypeException: if the key is not a valid key type
    """

    if key_type == 'raw':
      return CsekRawKey(key_material)

    if key_type == 'rsa-encrypted':
      if allow_rsa_encrypted:
        return CsekRsaEncryptedKey(key_material)
      raise BadKeyTypeException(
          key_type,
          'this feature is only allowed in the alpha and beta versions of this '
          'command.')

    raise BadKeyTypeException(key_type)

  @abc.abstractmethod
  def GetKeyLength(self):
    raise NotImplementedError('GetKeyLength() must be overridden.')

  @abc.abstractmethod
  def ToMessage(self, compute_client):
    del compute_client
    raise NotImplementedError('ToMessage() must be overridden.')

  @property
  def key_material(self):
    return self._key_material


class CsekRawKey(CsekKeyBase):
  """Class representing raw CSEK keys."""

  def GetKeyLength(self):
    return BASE64_RAW_KEY_LENGTH_IN_CHARS

  def ToMessage(self, compute_client):
    return compute_client.MESSAGES_MODULE.CustomerEncryptionKey(
        rawKey=str(self.key_material))


class CsekRsaEncryptedKey(CsekKeyBase):
  """Class representing rsa encrypted CSEK keys."""

  def GetKeyLength(self):
    return BASE64_RSA_ENCRYPTED_KEY_LENGTH_IN_CHARS

  def ToMessage(self, compute_client):
    return compute_client.MESSAGES_MODULE.CustomerEncryptionKey(
        rsaEncryptedKey=str(self.key_material))


class BadKeyTypeException(InvalidKeyFileException):
  """A key type is bad and why."""

  def __init__(self, key_type, explanation=''):
    self.key_type = key_type
    msg = 'Invalid key type [{0}]'.format(self.key_type)
    if explanation:
      msg += ': ' + explanation
    msg += '.'
    super(BadKeyTypeException, self).__init__(msg)


class MissingCsekException(Error):

  def __init__(self, resource):
    super(MissingCsekException, self).__init__(
        'Key required for resource [{0}], but none found.'.format(resource))


def AddCsekKeyArgs(parser, flags_about_creation=True, resource_type='resource'):
  """Adds arguments related to csek keys."""
  parser.add_argument(
      '--csek-key-file',
      metavar='FILE',
      help="""\
      Path to a Customer-Supplied Encryption Key (CSEK) key file that maps
      Compute Engine {resource}s to user managed keys to be used when
      creating, mounting, or taking snapshots of disks.

      If you pass `-` as value of the flag, the CSEK is read from stdin.
      See {csek_help} for more details.
      """.format(resource=resource_type, csek_help=CSEK_HELP_URL))

  if flags_about_creation:
    parser.add_argument(
        '--require-csek-key-create',
        action='store_true',
        default=True,
        help="""\
        Refuse to create {resource}s not protected by a user managed key in
        the key file when --csek-key-file is given. This behavior is enabled
        by default to prevent incorrect gcloud invocations from accidentally
        creating {resource}s with no user managed key. Disabling the check
        allows creation of some {resource}s without a matching
        Customer-Supplied Encryption Key in the supplied --csek-key-file.
        See {csek_help} for more details.
        """.format(resource=resource_type, csek_help=CSEK_HELP_URL))


class UriPattern(object):
  """A uri-based pattern that maybe be matched against resource objects."""

  def __init__(self, path_as_string):
    if not path_as_string.startswith('http'):
      raise BadPatternException('uri', path_as_string)
    self._path_as_string = resources.REGISTRY.ParseURL(
        path_as_string).RelativeName()

  def Matches(self, resource):
    """Tests if its argument matches the pattern."""
    return self._path_as_string == resource.RelativeName()

  def __str__(self):
    return 'Uri Pattern: ' + self._path_as_string


class CsekKeyStore(object):
  """Represents a map from resource patterns to keys."""

  # Members
  # self._state: dictionary from UriPattern to an instance of (a subclass of)
  # CsekKeyBase

  @classmethod
  def FromFile(cls, fname, allow_rsa_encrypted):
    """FromFile loads a CsekKeyStore from a file.

    Args:
      fname: str, the name of a file intended to contain a well-formed key file
      allow_rsa_encrypted: bool, whether to allow keys of type 'rsa-encrypted'

    Returns:
      A CsekKeyStore, if found

    Raises:
      googlecloudsdk.core.util.files.Error: If the file cannot be read or is
                                            larger than max_bytes.
    """

    content = console_io.ReadFromFileOrStdin(fname, binary=False)
    return cls(content, allow_rsa_encrypted)

  @staticmethod
  def FromArgs(args, allow_rsa_encrypted=False):
    """FromFile attempts to load a CsekKeyStore from a command's args.

    Args:
      args: CLI args with a csek_key_file field set
      allow_rsa_encrypted: bool, whether to allow keys of type 'rsa-encrypted'

    Returns:
      A CsekKeyStore, if a valid key file name is provided as csek_key_file
      None, if args.csek_key_file is None

    Raises:
      exceptions.BadFileException: there's a problem reading fname
      exceptions.InvalidKeyFileException: the key file failed to parse
        or was otherwise invalid
    """
    if args.csek_key_file is None:
      return None

    return CsekKeyStore.FromFile(args.csek_key_file, allow_rsa_encrypted)

  @staticmethod
  def _ParseAndValidate(s, allow_rsa_encrypted=False):
    """_ParseAndValidate(s) inteprets s as a csek key file.

    Args:
      s: str, an input to parse
      allow_rsa_encrypted: bool, whether to allow RSA-wrapped keys

    Returns:
      a valid state object

    Raises:
      InvalidKeyFileException: if the input doesn't parse or is not well-formed.
    """

    assert isinstance(s, six.string_types)
    state = {}

    try:
      records = json.loads(s)

      if not isinstance(records, list):
        raise InvalidKeyFileException(
            'Key file\'s top-level element must be a JSON list.')

      for key_record in records:
        if not isinstance(key_record, dict):
          raise InvalidKeyFileException(
              'Key file records must be JSON objects, but [{0}] found.'.format(
                  json.dumps(key_record)))

        if set(key_record.keys()) != EXPECTED_RECORD_KEY_KEYS:
          raise InvalidKeyFileException(
              'Record [{0}] has incorrect json keys; [{1}] expected'.format(
                  json.dumps(key_record),
                  ','.join(EXPECTED_RECORD_KEY_KEYS)))

        pattern = UriPattern(key_record['uri'])

        try:
          state[pattern] = CsekKeyBase.MakeKey(
              key_material=key_record['key'], key_type=key_record['key-type'],
              allow_rsa_encrypted=allow_rsa_encrypted)
        except InvalidKeyExceptionNoContext as e:
          raise InvalidKeyException(key=e.key, key_id=pattern, issue=e.issue)

    except ValueError as e:
      raise InvalidKeyFileException(*e.args)

    assert isinstance(state, dict)
    return state

  def __len__(self):
    return len(self.state)

  def LookupKey(self, resource, raise_if_missing=False):
    """Search for the unique key corresponding to a given resource.

    Args:
      resource: the resource to find a key for.
      raise_if_missing: bool, raise an exception if the resource is not found.

    Returns: CsekKeyBase, corresponding to the resource, or None if not found
      and not raise_if_missing.

    Raises:
      InvalidKeyFileException: if there are two records matching the resource.
      MissingCsekException: if raise_if_missing and no key is found
        for the provided resource.
    """

    assert isinstance(self.state, dict)
    search_state = (None, None)

    for pat, key in six.iteritems(self.state):
      if pat.Matches(resource):
        if search_state[0]:
          raise InvalidKeyFileException(
              'Uri patterns [{0}] and [{1}] both match '
              'resource [{2}].  Bailing out.'.format(
                  search_state[0], pat, str(resource)))

        search_state = (pat, key)

    if raise_if_missing and (search_state[1] is None):
      raise MissingCsekException(resource)

    return search_state[1]

  def __init__(self, json_string, allow_rsa_encrypted=False):
    self.state = CsekKeyStore._ParseAndValidate(json_string,
                                                allow_rsa_encrypted)


# Functions below make it easy for clients to operate on values that possibly
# either CsekKeyStores or None or else CsekKeyBases or None.  Fellow functional
# programming geeks: basically we're faking the Maybe monad.
def MaybeToMessage(csek_key_or_none, compute):
  return csek_key_or_none.ToMessage(compute) if csek_key_or_none else None


def MaybeLookupKey(csek_keys_or_none, resource):
  if csek_keys_or_none and resource:
    return csek_keys_or_none.LookupKey(resource)

  return None


def MaybeLookupKeyMessage(csek_keys_or_none, resource, compute_client):
  maybe_key = MaybeLookupKey(csek_keys_or_none, resource)
  return MaybeToMessage(maybe_key, compute_client)


def MaybeLookupKeys(csek_keys_or_none, resource_collection):
  return [MaybeLookupKey(csek_keys_or_none, r) for r in resource_collection]


def MaybeLookupKeyMessages(
    csek_keys_or_none, resource_collection, compute_client):
  return [MaybeToMessage(k, compute_client) for k in
          MaybeLookupKeys(csek_keys_or_none, resource_collection)]


def MaybeLookupKeysByUri(csek_keys_or_none, parser, uris):
  return MaybeLookupKeys(
      csek_keys_or_none,
      [(parser.Parse(u) if u else None) for u in uris])


def MaybeLookupKeyMessagesByUri(csek_keys_or_none, parser,
                                uris, compute_client):
  return [MaybeToMessage(k, compute_client) for k in
          MaybeLookupKeysByUri(csek_keys_or_none, parser, uris)]
