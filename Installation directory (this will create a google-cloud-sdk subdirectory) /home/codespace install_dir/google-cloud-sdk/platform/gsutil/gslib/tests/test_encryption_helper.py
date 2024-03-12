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
"""Unit tests for encryption_helper."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import base64
import os

import six
import boto
from gslib.exception import CommandException
from gslib.tests.testcase.unit_testcase import GsUtilUnitTestCase
from gslib.tests.util import SetBotoConfigForTest
from gslib.utils.encryption_helper import Base64Sha256FromBase64EncryptionKey
from gslib.utils.encryption_helper import CryptoKeyWrapperFromKey
from gslib.utils.encryption_helper import FindMatchingCSEKInBotoConfig


class TestEncryptionHelper(GsUtilUnitTestCase):
  """Unit tests for encryption helper functions."""

  def testMaxDecryptionKeys(self):
    """Tests a config file with the maximum number of decryption keys."""
    keys = []
    boto_101_key_config = []
    # Generate 101 keys.
    for i in range(1, 102):
      try:
        keys.append(base64.encodebytes(os.urandom(32)).rstrip(b'\n'))
      except AttributeError:
        # For Python 2 compatability.
        keys.append(base64.encodestring(os.urandom(32)).rstrip(b'\n'))
      boto_101_key_config.append(
          ('GSUtil', 'decryption_key%s' % i, keys[i - 1]))
    with SetBotoConfigForTest(boto_101_key_config):
      self.assertIsNotNone(
          FindMatchingCSEKInBotoConfig(
              Base64Sha256FromBase64EncryptionKey(keys[0]), boto.config))
      self.assertIsNotNone(
          FindMatchingCSEKInBotoConfig(
              Base64Sha256FromBase64EncryptionKey(keys[99]), boto.config))
      # Only 100 keys are supported.
      self.assertIsNone(
          FindMatchingCSEKInBotoConfig(
              Base64Sha256FromBase64EncryptionKey(keys[100]), boto.config))

    boto_100_key_config = list(boto_101_key_config)
    boto_100_key_config.pop()
    with SetBotoConfigForTest(boto_100_key_config):
      self.assertIsNotNone(
          FindMatchingCSEKInBotoConfig(
              Base64Sha256FromBase64EncryptionKey(keys[0]), boto.config))
      self.assertIsNotNone(
          FindMatchingCSEKInBotoConfig(
              Base64Sha256FromBase64EncryptionKey(keys[99]), boto.config))

  def testNonSequentialDecryptionKeys(self):
    """Tests a config file with non-sequential decryption key numbering."""
    keys = []
    for _ in range(3):
      try:
        keys.append(base64.encodebytes(os.urandom(32)).rstrip(b'\n'))
      except AttributeError:
        # For Python 2 compatability.
        keys.append(base64.encodestring(os.urandom(32)).rstrip(b'\n'))
    boto_config = [('GSUtil', 'decryption_key4', keys[2]),
                   ('GSUtil', 'decryption_key1', keys[0]),
                   ('GSUtil', 'decryption_key2', keys[1])]
    with SetBotoConfigForTest(boto_config):
      # Because decryption_key3 does not exist in boto_config, decryption_key4
      # should be ignored.
      self.assertIsNone(
          FindMatchingCSEKInBotoConfig(
              Base64Sha256FromBase64EncryptionKey(keys[2]), boto.config))
      # decryption_key1 and decryption_key2 should work, though.
      self.assertIsNotNone(
          FindMatchingCSEKInBotoConfig(
              Base64Sha256FromBase64EncryptionKey(keys[0]), boto.config))
      self.assertIsNotNone(
          FindMatchingCSEKInBotoConfig(
              Base64Sha256FromBase64EncryptionKey(keys[1]), boto.config))

  def testInvalidCSEKConfigurationRaises(self):
    invalid_key = 'aP7KbmxLqDw1SWHeKvlfKOVgNRNNZc8L2sFz8ybLN==='
    with self.assertRaises(CommandException) as cm:
      CryptoKeyWrapperFromKey(invalid_key)
    self.assertIn(
        'Configured encryption_key or decryption_key looked like a CSEK',
        cm.exception.reason)

  def testInvalidCMEKConfigurationRaises(self):
    invalid_key = (
        'projects/my-project/locations/some-location/keyRings/keyring/'
        'cryptoKeyWHOOPS-INVALID-RESOURCE-PORTION/somekey')
    with self.assertRaises(CommandException) as cm:
      CryptoKeyWrapperFromKey(invalid_key)
    self.assertIn(
        'Configured encryption_key or decryption_key looked like a CMEK',
        cm.exception.reason)
