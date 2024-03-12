# -*- coding: utf-8 -*-
# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Unit tests for hash command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os

from gslib.commands import hash
from gslib.exception import CommandException
import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import SetEnvironmentForTest
from gslib.utils import shim_util

from six import add_move, MovedModule

add_move(MovedModule('mock', 'mock', 'unittest.mock'))
from six.moves import mock

_TEST_FILE_CONTENTS = b'123456\n'
_TEST_FILE_B64_CRC = 'nYmSiA=='
_TEST_FILE_B64_MD5 = '9EeyCn/L9TpdW+AT6gsVrw=='
_TEST_FILE_HEX_CRC = '9D899288'
_TEST_FILE_HEX_MD5 = 'f447b20a7fcbf53a5d5be013ea0b15af'
_TEST_COMPOSITE_ADDED_CONTENTS = b'tmp'
_TEST_COMPOSITE_B64_CRC = 'M3DYBg=='
_TEST_COMPOSITE_HEX_CRC = '3370D806'


class TestHashUnit(testcase.GsUtilUnitTestCase):
  """Unit tests for hash command."""

  def testHashContents(self):
    tmp_file = self.CreateTempFile(contents=_TEST_FILE_CONTENTS)
    stdout = self.RunCommand('hash', args=[tmp_file], return_stdout=True)
    self.assertIn('Hashes [base64]', stdout)
    self.assertIn(('\tHash (crc32c):\t\t%s' % _TEST_FILE_B64_CRC), stdout)
    self.assertIn(('\tHash (md5):\t\t%s' % _TEST_FILE_B64_MD5), stdout)

  def testHashNoMatch(self):
    try:
      self.RunCommand('hash', args=['non-existent-file'])
      self.fail('Did not get expected CommandException')
    except CommandException as e:
      self.assertIn('No files matched', e.reason)

  def testHashHexFormat(self):
    tmp_file = self.CreateTempFile(contents=_TEST_FILE_CONTENTS)
    stdout = self.RunCommand('hash', args=['-h', tmp_file], return_stdout=True)
    self.assertIn('Hashes [hex]', stdout)
    self.assertIn(('\tHash (crc32c):\t\t%s' % _TEST_FILE_HEX_CRC), stdout)
    self.assertIn(('\tHash (md5):\t\t%s' % _TEST_FILE_HEX_MD5), stdout)

  def testHashWildcard(self):
    num_test_files = 2
    tmp_dir = self.CreateTempDir(test_files=num_test_files)
    stdout = self.RunCommand('hash',
                             args=[os.path.join(tmp_dir, '*')],
                             return_stdout=True)
    # One summary line and two hash lines per file.
    num_expected_lines = num_test_files * (1 + 2)
    self.assertEqual(len(stdout.splitlines()), num_expected_lines)

  def testHashSelectAlg(self):
    tmp_file = self.CreateTempFile(contents=_TEST_FILE_CONTENTS)
    stdout_crc = self.RunCommand('hash',
                                 args=['-c', tmp_file],
                                 return_stdout=True)
    stdout_md5 = self.RunCommand('hash',
                                 args=['-m', tmp_file],
                                 return_stdout=True)
    stdout_both = self.RunCommand('hash',
                                  args=['-c', '-m', tmp_file],
                                  return_stdout=True)
    for stdout in (stdout_crc, stdout_both):
      self.assertIn(('\tHash (crc32c):\t\t%s' % _TEST_FILE_B64_CRC), stdout)
    for stdout in (stdout_md5, stdout_both):
      self.assertIn(('\tHash (md5):\t\t%s' % _TEST_FILE_B64_MD5), stdout)
    self.assertNotIn('md5', stdout_crc)
    self.assertNotIn('crc32c', stdout_md5)


class TestHash(testcase.GsUtilIntegrationTestCase):
  """Integration tests for hash command."""

  def testHashCloudObject(self):
    """Test hash command on a cloud object."""
    obj1 = self.CreateObject(object_name='obj1', contents=_TEST_FILE_CONTENTS)

    # Tests cloud object with -h.
    stdout = self.RunGsUtil(['hash', '-h', suri(obj1)], return_stdout=True)
    self.assertIn('Hashes [hex]', stdout)

    if self.default_provider == 'gs':
      # Hex hashes for cloud objects get converted to lowercase but their
      # meaning is the same.
      self.assertIn(('\tHash (crc32c):\t\t%s' % _TEST_FILE_HEX_CRC.lower()),
                    stdout)
    self.assertIn(('\tHash (md5):\t\t%s' % _TEST_FILE_HEX_MD5), stdout)

    # Tests cloud object as base64.
    stdout = self.RunGsUtil(['hash', suri(obj1)], return_stdout=True)
    self.assertIn('Hashes [base64]', stdout)
    if self.default_provider == 'gs':
      self.assertIn(('\tHash (crc32c):\t\t%s' % _TEST_FILE_B64_CRC), stdout)
    self.assertIn(('\tHash (md5):\t\t%s' % _TEST_FILE_B64_MD5), stdout)

  @SkipForS3('No composite object or crc32c support for S3.')
  def testHashCompositeObject(self):
    """Test hash command on a composite object (which only has crc32c)."""
    bucket = self.CreateBucket()
    obj1 = self.CreateObject(bucket_uri=bucket,
                             object_name='obj1',
                             contents=_TEST_FILE_CONTENTS)
    obj2 = self.CreateObject(bucket_uri=bucket,
                             object_name='tmp',
                             contents=_TEST_COMPOSITE_ADDED_CONTENTS)
    self.RunGsUtil(['compose', suri(obj1), suri(obj2), suri(obj1)])

    stdout = self.RunGsUtil(['hash', '-h', suri(obj1)], return_stdout=True)
    self.assertIn('Hashes [hex]', stdout)
    # Hex hashes for cloud objects get converted to lowercase but their
    # meaning is the same.
    self.assertIn(('\tHash (crc32c):\t\t%s' % _TEST_COMPOSITE_HEX_CRC.lower()),
                  stdout)

    stdout = self.RunGsUtil(['hash', suri(obj1)], return_stdout=True)
    self.assertIn('Hashes [base64]', stdout)
    self.assertIn(('\tHash (crc32c):\t\t%s' % _TEST_COMPOSITE_B64_CRC), stdout)


class TestHashShim(testcase.GsUtilUnitTestCase):

  @mock.patch.object(hash.HashCommand, 'RunCommand', new=mock.Mock())
  def test_shim_translates_basic_hash_command(self):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand('hash', ['gs://b/o1', 'gs://b/o2'],
                                           return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(('Gcloud Storage Command: {} storage hash {}'
                       ' gs://b/o1 gs://b/o2').format(
                           shim_util._get_gcloud_binary_path('fake_dir'),
                           hash._GCLOUD_FORMAT_STRING), info_lines)

  @mock.patch.object(hash.HashCommand, 'RunCommand', new=mock.Mock())
  def test_shim_translates_both_crc32c_and_md5_to_skip_nothing_flag(self):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand('hash', ['-c', '-m', 'gs://b/o'],
                                           return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            ('Gcloud Storage Command: {} storage hash {}'
             ' gs://b/o').format(shim_util._get_gcloud_binary_path('fake_dir'),
                                 hash._GCLOUD_FORMAT_STRING), info_lines)

  @mock.patch.object(hash.HashCommand, 'RunCommand', new=mock.Mock())
  def test_shim_translates_md5_flag_to_skip_crc32c(self):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand('hash', ['-m', 'gs://b/o'],
                                           return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(('Gcloud Storage Command: {} storage hash {}'
                       ' --skip-crc32c gs://b/o').format(
                           shim_util._get_gcloud_binary_path('fake_dir'),
                           hash._GCLOUD_FORMAT_STRING), info_lines)

  @mock.patch.object(hash.HashCommand, 'RunCommand', new=mock.Mock())
  def test_shim_translates_crc32c_flag_to_skip_md5(self):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand('hash', ['-c', 'gs://b/o'],
                                           return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(('Gcloud Storage Command: {} storage hash {}'
                       ' --skip-md5 gs://b/o').format(
                           shim_util._get_gcloud_binary_path('fake_dir'),
                           hash._GCLOUD_FORMAT_STRING), info_lines)
