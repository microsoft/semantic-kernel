# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
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
"""Tests for cat command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import sys

from gslib.cs_api_map import ApiSelector
from gslib.exception import NO_URLS_MATCHED_TARGET
import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.util import GenerationFromURI as urigen
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import RUN_S3_TESTS
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import SetEnvironmentForTest
from gslib.tests.util import TEST_ENCRYPTION_KEY1
from gslib.tests.util import unittest
from gslib.utils import cat_helper
from gslib.utils import shim_util

from unittest import mock


class TestCat(testcase.GsUtilIntegrationTestCase):
  """Integration tests for cat command."""

  def test_cat_range(self):
    """Tests cat command with various range arguments."""
    key_uri = self.CreateObject(contents=b'0123456789')
    # Test various invalid ranges.
    stderr = self.RunGsUtil(
        ['cat', '-r a-b', suri(key_uri)],
        return_stderr=True,
        expected_status=2 if self._use_gcloud_storage else 1)
    if self._use_gcloud_storage:
      self.assertIn(
          'Expected a non-negative integer value or a range of such values instead of',
          stderr)
    else:
      self.assertIn('Invalid range', stderr)
    stderr = self.RunGsUtil(
        ['cat', '-r 1-2-3', suri(key_uri)],
        return_stderr=True,
        expected_status=2 if self._use_gcloud_storage else 1)
    if self._use_gcloud_storage:
      self.assertIn(
          'Expected a non-negative integer value or a range of such values instead of',
          stderr)
    else:
      self.assertIn('Invalid range', stderr)
    stderr = self.RunGsUtil(
        ['cat', '-r 1.7-3', suri(key_uri)],
        return_stderr=True,
        expected_status=2 if self._use_gcloud_storage else 1)
    if self._use_gcloud_storage:
      self.assertIn(
          'Expected a non-negative integer value or a range of such values instead of',
          stderr)
    else:
      self.assertIn('Invalid range', stderr)

    # Test various valid ranges.
    stdout = self.RunGsUtil(['cat', '-r', '-', suri(key_uri)],
                            return_stdout=True)
    self.assertEqual('0123456789', stdout)
    stdout = self.RunGsUtil(
        ['cat', '-r', '1000-3000', suri(key_uri)], return_stdout=True)
    self.assertEqual('', stdout)
    stdout = self.RunGsUtil(
        ['cat', '-r', '1000-', suri(key_uri)], return_stdout=True)
    self.assertEqual('', stdout)
    stdout = self.RunGsUtil(
        ['cat', '-r', '1-3', suri(key_uri)], return_stdout=True)
    self.assertEqual('123', stdout)
    stdout = self.RunGsUtil(
        ['cat', '-r', '8-', suri(key_uri)], return_stdout=True)
    self.assertEqual('89', stdout)
    stdout = self.RunGsUtil(
        ['cat', '-r', '0-0', suri(key_uri)], return_stdout=True)
    self.assertEqual('0', stdout)
    stdout = self.RunGsUtil(
        ['cat', '-r', '-3', suri(key_uri)], return_stdout=True)
    self.assertEqual('789', stdout)

  def test_cat_version(self):
    """Tests cat command on versioned objects."""
    bucket_uri = self.CreateVersionedBucket()
    # Create 2 versions of an object.
    uri1 = self.CreateObject(bucket_uri=bucket_uri,
                             contents=b'data1',
                             gs_idempotent_generation=0)
    uri2 = self.CreateObject(bucket_uri=bucket_uri,
                             object_name=uri1.object_name,
                             contents=b'data2',
                             gs_idempotent_generation=urigen(uri1))
    stdout = self.RunGsUtil(['cat', suri(uri1)], return_stdout=True)
    # Last version written should be live.
    self.assertEqual('data2', stdout)
    # Using either version-specific URI should work.
    stdout = self.RunGsUtil(['cat', uri1.version_specific_uri],
                            return_stdout=True)
    self.assertEqual('data1', stdout)
    stdout = self.RunGsUtil(['cat', uri2.version_specific_uri],
                            return_stdout=True)
    self.assertEqual('data2', stdout)
    if RUN_S3_TESTS:
      # S3 GETs of invalid versions return 400s.
      # Also, appending between 1 and 3 characters to the version_id can
      # result in a success (200) response from the server.
      stderr = self.RunGsUtil(['cat', uri2.version_specific_uri + '23456'],
                              return_stderr=True,
                              expected_status=1)
      self.assertIn('BadRequestException: 400', stderr)
    else:
      # Attempting to cat invalid version should result in an error.
      stderr = self.RunGsUtil(['cat', uri2.version_specific_uri + '23'],
                              return_stderr=True,
                              expected_status=1)
      if self._use_gcloud_storage:
        self.assertIn(
            'The following URLs matched no objects or files:\n-{}23\n'.format(
                uri2.version_specific_uri), stderr)
      else:
        self.assertIn(NO_URLS_MATCHED_TARGET % uri2.version_specific_uri + '23',
                      stderr)

  def test_cat_multi_arg(self):
    """Tests cat command with multiple arguments."""
    bucket_uri = self.CreateBucket()
    data1 = b'0123456789'
    data2 = b'abcdefghij'
    obj_uri1 = self.CreateObject(bucket_uri=bucket_uri, contents=data1)
    obj_uri2 = self.CreateObject(bucket_uri=bucket_uri, contents=data2)
    stdout, stderr = self.RunGsUtil(
        ['cat', suri(obj_uri1),
         suri(bucket_uri) + 'nonexistent'],
        return_stdout=True,
        return_stderr=True,
        expected_status=1)
    # First object should print, second should produce an exception.
    self.assertIn(data1.decode('ascii'), stdout)
    if self._use_gcloud_storage:
      self.assertIn('The following URLs matched no objects or files', stderr)
    else:
      self.assertIn('NotFoundException', stderr)

    stdout, stderr = self.RunGsUtil(
        ['cat', suri(bucket_uri) + 'nonexistent',
         suri(obj_uri1)],
        return_stdout=True,
        return_stderr=True,
        expected_status=1)

    decoded_data1 = data1.decode('ascii')
    if self._use_gcloud_storage:
      self.assertIn(decoded_data1, stdout)
      self.assertIn('The following URLs matched no objects or files', stderr)
    else:
      # If first object is invalid, exception should halt output immediately.
      self.assertNotIn(decoded_data1, stdout)
      self.assertIn('NotFoundException', stderr)

    # Two valid objects should both print successfully.
    stdout = self.RunGsUtil(
        ['cat', suri(obj_uri1), suri(obj_uri2)], return_stdout=True)
    self.assertIn(decoded_data1 + data2.decode('ascii'), stdout)

  @SkipForS3('S3 customer-supplied encryption keys are not supported.')
  def test_cat_encrypted_object(self):
    if self.test_api == ApiSelector.XML:
      return unittest.skip(
          'gsutil does not support encryption with the XML API')
    object_contents = b'0123456789'
    object_uri = self.CreateObject(object_name='foo',
                                   contents=object_contents,
                                   encryption_key=TEST_ENCRYPTION_KEY1)

    stderr = self.RunGsUtil(['cat', suri(object_uri)],
                            expected_status=1,
                            return_stderr=True)

    self.assertIn('No decryption key matches object', stderr)

    boto_config_for_test = [('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY1)]

    with SetBotoConfigForTest(boto_config_for_test):
      stdout = self.RunGsUtil(['cat', suri(object_uri)], return_stdout=True)
      self.assertEqual(stdout.encode('ascii'), object_contents)
      stdout = self.RunGsUtil(
          ['cat', '-r', '1-3', suri(object_uri)], return_stdout=True)
      self.assertEqual(stdout, '123')


class TestShimCatFlags(testcase.GsUtilUnitTestCase):
  """Unit tests for shimming cat flags"""

  def test_shim_translates_flags(self):
    object_uri = self.CreateObject(contents='0123456789')
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand(
            'cat', ['-h', '-r', '2-4', suri(object_uri)],
            return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            'Gcloud Storage Command: {} storage cat'
            ' -d -r 2-4 {}'.format(
                shim_util._get_gcloud_binary_path('fake_dir'),
                suri(object_uri)), info_lines)


class TestCatHelper(testcase.GsUtilUnitTestCase):
  """Unit tests for cat helper."""

  def test_cat_helper_runs_flush(self):
    cat_command_mock = mock.Mock()
    cat_helper_mock = cat_helper.CatHelper(command_obj=cat_command_mock)

    object_contents = '0123456789'
    bucket_uri = self.CreateBucket(bucket_name='bucket',
                                   provider=self.default_provider)
    obj = self.CreateObject(bucket_uri=bucket_uri,
                            object_name='foo1',
                            contents=object_contents)
    obj1 = self.CreateObject(bucket_uri=bucket_uri,
                             object_name='foo2',
                             contents=object_contents)

    cat_command_mock.WildcardIterator.return_value = self._test_wildcard_iterator(
        'gs://bucket/foo*')

    stdout_mock = mock.mock_open()()

    # Mocks two functions because we need to record the order of the
    # function calls (write, flush, write, flush).
    write_flush_collector_mock = mock.Mock()
    cat_command_mock.gsutil_api.GetObjectMedia = write_flush_collector_mock
    stdout_mock.flush = write_flush_collector_mock

    cat_helper_mock.CatUrlStrings(url_strings=['url'], cat_out_fd=stdout_mock)
    mock_part_one = [
        mock.call('bucket',
                  'foo1',
                  stdout_mock,
                  compressed_encoding=None,
                  start_byte=0,
                  end_byte=None,
                  object_size=10,
                  generation=None,
                  decryption_tuple=None,
                  provider='gs'),
        mock.call()
    ]
    mock_part_two = [
        mock.call('bucket',
                  'foo2',
                  stdout_mock,
                  compressed_encoding=None,
                  start_byte=0,
                  end_byte=None,
                  object_size=10,
                  generation=None,
                  decryption_tuple=None,
                  provider='gs'),
        mock.call()
    ]
    # Needed to do these two checks because the object
    # ordering varies if run on Windows with Python 3.5.
    self.assertIn(write_flush_collector_mock.call_args_list[0:2],
                  [mock_part_one, mock_part_two])
    self.assertIn(write_flush_collector_mock.call_args_list[2:4],
                  [mock_part_one, mock_part_two])
