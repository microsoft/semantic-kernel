# -*- coding: utf-8 -*-
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Tests for rpo command."""

from __future__ import absolute_import

import os
import textwrap

from gslib.commands.rpo import RpoCommand
from gslib.exception import CommandException
from gslib.gcs_json_api import GcsJsonApi
from gslib.storage_url import StorageUrlFromString
import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForGS
from gslib.tests.testcase.integration_testcase import SkipForJSON
from gslib.tests.testcase.integration_testcase import SkipForXML
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import SetEnvironmentForTest
from gslib.utils import shim_util

from six import add_move, MovedModule

add_move(MovedModule('mock', 'mock', 'unittest.mock'))
from six.moves import mock


class TestRpoUnit(testcase.GsUtilUnitTestCase):

  def test_get_for_multiple_bucket_calls_api(self):
    bucket_uri1 = self.CreateBucket(bucket_name='rpofoo')
    bucket_uri2 = self.CreateBucket(bucket_name='rpobar')
    stdout = self.RunCommand(
        'rpo',
        ['get', suri(bucket_uri1), suri(bucket_uri2)],
        return_stdout=True)
    expected_string = textwrap.dedent("""\
      gs://rpofoo: None
      gs://rpobar: None
      """)
    self.assertEqual(expected_string, stdout)

  def test_get_with_wildcard(self):
    self.CreateBucket(bucket_name='boo1')
    self.CreateBucket(bucket_name='boo2')
    stdout = self.RunCommand('rpo', ['get', 'gs://boo*'], return_stdout=True)
    actual = '\n'.join(sorted(stdout.strip().split('\n')))
    expected_string = textwrap.dedent("""\
      gs://boo1: None
      gs://boo2: None""")
    self.assertEqual(actual, expected_string)

  def test_get_with_wrong_url_raises_error(self):
    with self.assertRaisesRegex(CommandException, 'No URLs matched'):
      self.RunCommand('rpo', ['get', 'gs://invalid*'])

  def test_set_called_with_incorrect_value_raises_error(self):
    with self.assertRaisesRegex(
        CommandException,
        r'Invalid value for rpo set. Should be one of \(ASYNC_TURBO\|DEFAULT\)'
    ):
      self.RunCommand('rpo', ['set', 'random', 'gs://boo*'])

  def test_set_called_with_lower_case_value_raises_error(self):
    with self.assertRaisesRegex(
        CommandException,
        r'Invalid value for rpo set. Should be one of \(ASYNC_TURBO\|DEFAULT\)'
    ):
      self.RunCommand('rpo', ['set', 'async_turbo', 'gs://boo*'])

  def test_invalid_subcommand_raises_error(self):
    with self.assertRaisesRegex(
        CommandException, 'Invalid subcommand "blah", use get|set instead'):
      self.RunCommand('rpo', ['blah', 'DEFAULT', 'gs://boo*'])

  def test_shim_translates_recovery_point_objective_get_command(self):
    fake_cloudsdk_dir = 'fake_dir'
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': fake_cloudsdk_dir,
      }):
        self.CreateBucket(bucket_name='fake-bucket-get-rpo-1')
        mock_log_handler = self.RunCommand(
            'rpo',
            args=['get', 'gs://fake-bucket-get-rpo-1'],
            return_log_handler=True)

        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            ('Gcloud Storage Command: {} storage'
             ' buckets list --format=value[separator=": "]'
             '(format("gs://{}", name),rpo.yesno(no="None"))'
             ' --raw').format(shim_util._get_gcloud_binary_path('fake_dir'),
                              r'{}'), info_lines)

  def test_shim_translates_recovery_point_objective_set_command(self):
    fake_cloudsdk_dir = 'fake_dir'
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': fake_cloudsdk_dir,
      }):
        self.CreateBucket(bucket_name='fake-bucket-set-rpo')
        mock_log_handler = self.RunCommand(
            'rpo',
            args=['set', 'DEFAULT', 'gs://fake-bucket-set-rpo'],
            return_log_handler=True)

        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            ('Gcloud Storage Command: {} storage'
             ' buckets update --recovery-point-objective DEFAULT').format(
                 shim_util._get_gcloud_binary_path('fake_dir')), info_lines)


class TestRpoE2E(testcase.GsUtilIntegrationTestCase):
  """Integration tests for rpo command."""

  # TODO: Delete this method once rpo get results are consistent
  # from the backend, and replace this call with
  # VerifyCommandGet(bucket_uri, 'rpo', 'DEFAULT').
  # Currently, the rpo results are inconsistent
  # and None is a valid default value for all the buckets.
  # See b/197251750#comment19
  def _verify_get_returns_default_or_none(self, bucket_uri):
    """Checks if the rpo get command returns default."""
    try:
      self.VerifyCommandGet(bucket_uri, 'rpo', 'DEFAULT')
    except AssertionError:
      self.VerifyCommandGet(bucket_uri, 'rpo', 'None')

  @SkipForXML('RPO only runs on GCS JSON API.')
  def test_get_returns_default_for_dual_region_bucket(self):
    bucket_uri = self.CreateBucket(location='nam4')
    self._verify_get_returns_default_or_none(bucket_uri)

  @SkipForXML('RPO only runs on GCS JSON API.')
  def test_get_returns_none_for_regional_bucket(self):
    bucket_uri = self.CreateBucket(location='us-central1')
    self.VerifyCommandGet(bucket_uri, 'rpo', 'None')

  @SkipForXML('RPO only runs on GCS JSON API.')
  def test_set_and_get_async_turbo(self):
    bucket_uri = self.CreateBucket(location='nam4')
    self._verify_get_returns_default_or_none(bucket_uri)
    self.RunGsUtil(['rpo', 'set', 'ASYNC_TURBO', suri(bucket_uri)])
    self.VerifyCommandGet(bucket_uri, 'rpo', 'ASYNC_TURBO')

  @SkipForXML('RPO only runs on GCS JSON API.')
  def test_set_default(self):
    bucket_uri = self.CreateBucket(location='nam4')
    self.RunGsUtil(['rpo', 'set', 'ASYNC_TURBO', suri(bucket_uri)])
    self.VerifyCommandGet(bucket_uri, 'rpo', 'ASYNC_TURBO')
    self.RunGsUtil(['rpo', 'set', 'DEFAULT', suri(bucket_uri)])
    self._verify_get_returns_default_or_none(bucket_uri)

  @SkipForXML('RPO only runs on GCS JSON API.')
  def test_set_async_turbo_fails_for_regional_buckets(self):
    bucket_uri = self.CreateBucket(location='us-central1')
    stderr = self.RunGsUtil(['rpo', 'set', 'ASYNC_TURBO',
                             suri(bucket_uri)],
                            expected_status=1,
                            return_stderr=True)
    self.assertIn('ASYNC_TURBO cannot be enabled on REGION bucket', stderr)

  @SkipForJSON('Testing XML only behavior.')
  def test_xml_fails_for_set(self):
    # Use HMAC for force XML API.
    boto_config_hmac_auth_only = [
        # Overwrite other credential types.
        ('Credentials', 'gs_oauth2_refresh_token', None),
        ('Credentials', 'gs_service_client_id', None),
        ('Credentials', 'gs_service_key_file', None),
        ('Credentials', 'gs_service_key_file_password', None),
        # Add hmac credentials.
        ('Credentials', 'gs_access_key_id', 'dummykey'),
        ('Credentials', 'gs_secret_access_key', 'dummysecret'),
    ]
    with SetBotoConfigForTest(boto_config_hmac_auth_only):
      bucket_uri = 'gs://any-bucket-name'
      stderr = self.RunGsUtil(['rpo', 'set', 'default', bucket_uri],
                              return_stderr=True,
                              expected_status=1)
      self.assertIn('command can only be with the Cloud Storage JSON API',
                    stderr)

  @SkipForJSON('Testing XML only behavior.')
  def test_xml_fails_for_get(self):
    # Use HMAC for force XML API.
    boto_config_hmac_auth_only = [
        # Overwrite other credential types.
        ('Credentials', 'gs_oauth2_refresh_token', None),
        ('Credentials', 'gs_service_client_id', None),
        ('Credentials', 'gs_service_key_file', None),
        ('Credentials', 'gs_service_key_file_password', None),
        # Add HMAC credentials.
        ('Credentials', 'gs_access_key_id', 'dummykey'),
        ('Credentials', 'gs_secret_access_key', 'dummysecret'),
    ]
    with SetBotoConfigForTest(boto_config_hmac_auth_only):
      bucket_uri = 'gs://any-bucket-name'
      stderr = self.RunGsUtil(['rpo', 'get', bucket_uri],
                              return_stderr=True,
                              expected_status=1)
      self.assertIn('command can only be with the Cloud Storage JSON API',
                    stderr)

  @SkipForGS('Testing S3 only behavior.')
  def test_s3_fails_for_set(self):
    bucket_uri = self.CreateBucket()
    stderr = self.RunGsUtil(
        ['rpo', 'set', 'DEFAULT', suri(bucket_uri)],
        return_stderr=True,
        expected_status=1)

    if self._use_gcloud_storage:
      self.assertIn(
          'Features disallowed for S3: Setting Recovery Point Objective',
          stderr)
    else:
      self.assertIn('command can only be used for GCS buckets', stderr)

  @SkipForGS('Testing S3 only behavior.')
  def test_s3_fails_for_get(self):
    bucket_uri = self.CreateBucket()
    expected_status = 0 if self._use_gcloud_storage else 1
    stdout, stderr = self.RunGsUtil(
        ['rpo', 'get', suri(bucket_uri)],
        return_stderr=True,
        return_stdout=True,
        expected_status=expected_status)
    if self._use_gcloud_storage:
      # TODO(b/265304295)
      self.assertIn('gs://None: None', stdout)
    else:
      self.assertIn('command can only be used for GCS buckets', stderr)
