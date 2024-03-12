# -*- coding: utf-8 -*-
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Integration tests for pap command."""

from __future__ import absolute_import

import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForGS
from gslib.tests.testcase.integration_testcase import SkipForJSON
from gslib.tests.testcase.integration_testcase import SkipForXML
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import SetBotoConfigForTest


class TestPublicAccessPrevention(testcase.GsUtilIntegrationTestCase):
  """Integration tests for pap command."""

  _set_pap_cmd = ['pap', 'set']
  _get_pap_cmd = ['pap', 'get']

  @SkipForXML('Public access prevention only runs on GCS JSON API')
  def test_off_on_default_buckets(self):
    bucket_uri = self.CreateBucket()
    self.VerifyPublicAccessPreventionValue(bucket_uri, 'inherited')

  @SkipForXML('Public access prevention only runs on GCS JSON API')
  def test_turning_off_on_enabled_buckets(self):
    bucket_uri = self.CreateBucket(public_access_prevention='enforced',
                                   prefer_json_api=True)
    self.VerifyPublicAccessPreventionValue(bucket_uri, 'enforced')

    self.RunGsUtil(self._set_pap_cmd + ['inherited', suri(bucket_uri)])
    self.VerifyPublicAccessPreventionValue(bucket_uri, 'inherited')

  @SkipForXML('Public access prevention only runs on GCS JSON API')
  def test_turning_on(self):
    bucket_uri = self.CreateBucket()
    self.RunGsUtil(self._set_pap_cmd + ['enforced', suri(bucket_uri)])
    self.VerifyPublicAccessPreventionValue(bucket_uri, 'enforced')

  @SkipForXML('Public access prevention only runs on GCS JSON API')
  def test_turning_on_and_off(self):
    bucket_uri = self.CreateBucket()

    self.RunGsUtil(self._set_pap_cmd + ['enforced', suri(bucket_uri)])
    self.VerifyPublicAccessPreventionValue(bucket_uri, 'enforced')

    self.RunGsUtil(self._set_pap_cmd + ['inherited', suri(bucket_uri)])
    self.VerifyPublicAccessPreventionValue(bucket_uri, 'inherited')

  @SkipForXML('Public access prevention only runs on GCS JSON API')
  def test_multiple_buckets(self):
    bucket_uri1 = self.CreateBucket()
    bucket_uri2 = self.CreateBucket()
    stdout = self.RunGsUtil(
        self._get_pap_cmd +
        [suri(bucket_uri1), suri(bucket_uri2)],
        return_stdout=True)
    self.assertRegex(stdout, r'%s:\s+inherited' % suri(bucket_uri1))
    self.assertRegex(stdout, r'%s:\s+inherited' % suri(bucket_uri2))

  @SkipForJSON('Testing XML only behavior')
  def test_xml_fails(self):
    # use HMAC for force XML API
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
      stderr = self.RunGsUtil(self._set_pap_cmd + ['inherited', bucket_uri],
                              return_stderr=True,
                              expected_status=1)
      self.assertIn('command can only be with the Cloud Storage JSON API',
                    stderr)

      stderr = self.RunGsUtil(self._get_pap_cmd + [bucket_uri],
                              return_stderr=True,
                              expected_status=1)
      self.assertIn('command can only be with the Cloud Storage JSON API',
                    stderr)

  @SkipForGS('Testing S3 only behavior')
  def test_s3_fails(self):
    bucket_uri = self.CreateBucket()
    stderr = self.RunGsUtil(self._set_pap_cmd +
                            ['inherited', suri(bucket_uri)],
                            return_stderr=True,
                            expected_status=1)
    if self._use_gcloud_storage:
      self.assertIn('Flags disallowed for S3', stderr)
    else:
      self.assertIn('command can only be used for GCS Buckets', stderr)

    if not self._use_gcloud_storage:
      # gcloud storage uses a generic buckets describe command for this, and it
      # would not print a result instead of erroring.
      stderr = self.RunGsUtil(self._get_pap_cmd + [suri(bucket_uri)],
                              return_stderr=True,
                              expected_status=1)
      self.assertIn('command can only be used for GCS Buckets', stderr)

  def test_set_too_few_arguments_fails(self):
    stderr = self.RunGsUtil(self._set_pap_cmd,
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('command requires at least', stderr)

  def test_get_too_few_arguments_fails(self):
    stderr = self.RunGsUtil(self._get_pap_cmd,
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('command requires at least', stderr)

  def test_no_subcommand_fails(self):
    stderr = self.RunGsUtil(['pap'], return_stderr=True, expected_status=1)
    self.assertIn('command requires at least', stderr)

  def test_invalid_subcommand_fails(self):
    stderr = self.RunGsUtil(['pap', 'fakecommand', 'test'],
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('Invalid subcommand', stderr)
