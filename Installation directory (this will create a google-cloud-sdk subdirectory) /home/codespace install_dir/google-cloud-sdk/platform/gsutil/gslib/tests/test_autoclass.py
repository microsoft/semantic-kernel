# -*- coding: utf-8 -*-
# Copyright 2021 Google LLC All Rights Reserved.
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
"""Tests for autoclass command."""

from __future__ import absolute_import

import re

import gslib.tests.testcase as testcase
from gslib import exception
from gslib.tests.testcase.integration_testcase import SkipForGS
from gslib.tests.testcase.integration_testcase import SkipForJSON
from gslib.tests.testcase.integration_testcase import SkipForXML
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import SetBotoConfigForTest


class TestAutoclassUnit(testcase.GsUtilUnitTestCase):

  def test_set_too_few_arguments_fails(self):
    with self.assertRaisesRegex(exception.CommandException,
                                 'command requires at least'):
      self.RunCommand('autoclass', ['set'])

  def test_get_too_few_arguments_fails(self):
    with self.assertRaisesRegex(exception.CommandException,
                                 'command requires at least'):
      self.RunCommand('autoclass', ['get'])

  def test_no_subcommand_fails(self):
    with self.assertRaisesRegex(exception.CommandException,
                                 'command requires at least'):
      self.RunCommand('autoclass', [])

  def test_invalid_subcommand_fails(self):
    with self.assertRaisesRegex(exception.CommandException,
                                 'Invalid subcommand'):
      self.RunCommand('autoclass', ['fakecommand', 'test'])

  def test_gets_multiple_buckets_with_wildcard(self):
    bucket_uri1 = self.CreateBucket(bucket_name='bucket1')
    bucket_uri2 = self.CreateBucket(bucket_name='bucket2')
    stdout = self.RunCommand('autoclass', ['get', 'gs://bucket*'],
                             return_stdout=True)
    self.assertIn(bucket_uri1.bucket_name, stdout)
    self.assertIn(bucket_uri2.bucket_name, stdout)


class TestAutoclassE2E(testcase.GsUtilIntegrationTestCase):
  """E2E tests for autoclass command."""

  _set_autoclass_cmd = ['autoclass', 'set']
  _get_autoclass_cmd = ['autoclass', 'get']

  @SkipForXML('Autoclass only runs on GCS JSON API.')
  def test_off_on_default_buckets(self):
    bucket_uri = self.CreateBucket()
    stdout = self.RunGsUtil(self._get_autoclass_cmd + [suri(bucket_uri)],
                            return_stdout=True)
    self.assertRegex(stdout, r'Enabled: False')
    self.assertRegex(stdout, r'Toggle Time: None')

  @SkipForXML('Autoclass only runs on GCS JSON API.')
  def test_turning_on_and_off(self):
    bucket_uri = self.CreateBucket()

    stdout, stderr = self.RunGsUtil(self._set_autoclass_cmd +
                                    ['on', suri(bucket_uri)],
                                    return_stdout=True,
                                    return_stderr=True)
    if self._use_gcloud_storage:
      self.assertRegex(stderr, re.escape('Updating {}'.format(str(bucket_uri))))
    else:
      self.assertRegex(
          stdout,
          re.escape('Setting Autoclass on for {}\n'.format(
              str(bucket_uri).rstrip('/'))))

    stdout = self.RunGsUtil(self._get_autoclass_cmd + [suri(bucket_uri)],
                            return_stdout=True)
    self.assertRegex(stdout, r'Enabled: True')
    self.assertRegex(stdout, r'Toggle Time: \d+')

    stdout, stderr = self.RunGsUtil(self._set_autoclass_cmd +
                                    ['off', suri(bucket_uri)],
                                    return_stdout=True,
                                    return_stderr=True)
    if self._use_gcloud_storage:
      self.assertRegex(stderr, re.escape('Updating {}'.format(str(bucket_uri))))
    else:
      self.assertRegex(
          stdout,
          re.escape('Setting Autoclass off for {}\n'.format(
              str(bucket_uri).rstrip('/'))))

    stdout = self.RunGsUtil(self._get_autoclass_cmd + [suri(bucket_uri)],
                            return_stdout=True)
    self.assertRegex(stdout, r'Enabled: False')
    self.assertRegex(stdout, r'Toggle Time: \d+')

  @SkipForXML('Autoclass only runs on GCS JSON API.')
  def test_multiple_buckets(self):
    bucket_uri1 = self.CreateBucket()
    bucket_uri2 = self.CreateBucket()
    stdout = self.RunGsUtil(
        self._get_autoclass_cmd +
        [suri(bucket_uri1), suri(bucket_uri2)],
        return_stdout=True)
    output_regex = (r'{}:\n'
                    r'  Enabled: False\n'
                    r'  Toggle Time: None\n'
                    r'{}:\n'
                    r'  Enabled: False\n'
                    r'  Toggle Time: None'.format(suri(bucket_uri1),
                                                  suri(bucket_uri2)))
    self.assertRegex(stdout, output_regex)

  @SkipForJSON('Testing XML only behavior.')
  def test_xml_fails(self):
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
      stderr = self.RunGsUtil(self._set_autoclass_cmd + ['on', bucket_uri],
                              return_stderr=True,
                              expected_status=1)
      self.assertIn('command can only be with the Cloud Storage JSON API',
                    stderr)

      stderr = self.RunGsUtil(self._get_autoclass_cmd + [bucket_uri],
                              return_stderr=True,
                              expected_status=1)
      self.assertIn('command can only be with the Cloud Storage JSON API',
                    stderr)

  @SkipForGS('Testing S3 only behavior')
  def test_s3_fails(self):
    bucket_uri = self.CreateBucket()
    stderr = self.RunGsUtil(self._set_autoclass_cmd +
                            ['on', suri(bucket_uri)],
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('command can only be used for GCS Buckets', stderr)

    stderr = self.RunGsUtil(self._get_autoclass_cmd + [suri(bucket_uri)],
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('command can only be used for GCS Buckets', stderr)
