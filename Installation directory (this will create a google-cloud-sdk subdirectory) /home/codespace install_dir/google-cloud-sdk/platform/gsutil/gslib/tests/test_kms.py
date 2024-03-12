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
"""Integration tests for kms command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
from random import randint
from unittest import mock

from gslib.cloud_api import AccessDeniedException
from gslib.project_id import PopulateProjectId
import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForJSON
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.testcase.integration_testcase import SkipForXML
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import SetEnvironmentForTest
from gslib.utils.retry_util import Retry
from gslib.utils import shim_util


@SkipForS3('gsutil does not support KMS operations for S3 buckets.')
@SkipForXML('gsutil does not support KMS operations for S3 buckets.')
class TestKmsSuccessCases(testcase.GsUtilIntegrationTestCase):
  """Integration tests for the kms command."""

  def setUp(self):
    super(TestKmsSuccessCases, self).setUp()
    # Make sure our keyRing exists (only needs to be done once, but subsequent
    # attempts will receive a 409 and be treated as a success). Save the fully
    # qualified name for use with creating keys later.
    self.keyring_fqn = self.kms_api.CreateKeyRing(
        PopulateProjectId(None),
        testcase.KmsTestingResources.KEYRING_NAME,
        location=testcase.KmsTestingResources.KEYRING_LOCATION)

  @Retry(AssertionError, tries=3, timeout_secs=1)
  def DoTestAuthorize(self, specified_project=None):
    # Randomly pick 1 of 1000 key names.
    key_name = testcase.KmsTestingResources.MUTABLE_KEY_NAME_TEMPLATE % (
        randint(0, 9), randint(0, 9), randint(0, 9))
    # Make sure the key with that name has been created.
    key_fqn = self.kms_api.CreateCryptoKey(self.keyring_fqn, key_name)
    # They key may have already been created and used in a previous test
    # invocation; make sure it doesn't contain the IAM policy binding that
    # allows our project to encrypt/decrypt with it.
    key_policy = self.kms_api.GetKeyIamPolicy(key_fqn)
    while key_policy.bindings:
      key_policy.bindings.pop()
    self.kms_api.SetKeyIamPolicy(key_fqn, key_policy)
    # Set up the authorize command tokens.
    authorize_cmd = ['kms', 'authorize', '-k', key_fqn]
    if specified_project:
      authorize_cmd.extend(['-p', specified_project])

    stdout1 = self.RunGsUtil(authorize_cmd, return_stdout=True)
    stdout2 = self.RunGsUtil(authorize_cmd, return_stdout=True)

    self.assertIn(
        'Authorized project %s to encrypt and decrypt with key:\n%s' %
        (PopulateProjectId(None), key_fqn), stdout1)
    self.assertIn(
        ('Project %s was already authorized to encrypt and decrypt with '
         'key:\n%s.' % (PopulateProjectId(None), key_fqn)), stdout2)

  def DoTestServiceaccount(self, specified_project=None):
    serviceaccount_cmd = ['kms', 'serviceaccount']
    if specified_project:
      serviceaccount_cmd.extend(['-p', specified_project])

    stdout = self.RunGsUtil(serviceaccount_cmd, return_stdout=True)

    self.assertRegex(stdout,
                     r'[^@]+@gs-project-accounts\.iam\.gserviceaccount\.com')

  def testKmsAuthorizeWithoutProjectOption(self):
    self.DoTestAuthorize()

  def testKmsAuthorizeWithProjectOption(self):
    self.DoTestAuthorize(specified_project=PopulateProjectId(None))

  def testKmsServiceaccountWithoutProjectOption(self):
    self.DoTestServiceaccount()

  def testKmsServiceaccountWithProjectOption(self):
    self.DoTestServiceaccount(specified_project=PopulateProjectId(None))

  def testKmsEncryptionFlow(self):
    # Since we have to create a bucket and set a default KMS key to test most
    # of these behaviors, we just test them all in one flow to reduce the number
    # of API calls.

    bucket_uri = self.CreateBucket()
    # Make sure our key exists.
    key_fqn = self.kms_api.CreateCryptoKey(
        self.keyring_fqn, testcase.KmsTestingResources.CONSTANT_KEY_NAME)
    encryption_get_cmd = ['kms', 'encryption', suri(bucket_uri)]

    # Test output for bucket with no default KMS key set.
    stdout = self.RunGsUtil(encryption_get_cmd, return_stdout=True)
    self.assertIn('Bucket %s has no default encryption key' % suri(bucket_uri),
                  stdout)

    # Test that setting a bucket's default KMS key works and shows up correctly
    # via a follow-up call to display it.
    stdout = self.RunGsUtil(
        ['kms', 'encryption', '-k', key_fqn,
         suri(bucket_uri)],
        return_stdout=True)
    self.assertIn('Setting default KMS key for bucket %s...' % suri(bucket_uri),
                  stdout)

    stdout = self.RunGsUtil(encryption_get_cmd, return_stdout=True)
    self.assertIn(
        'Default encryption key for %s:\n%s' % (suri(bucket_uri), key_fqn),
        stdout)

    # Finally, remove the bucket's default KMS key and make sure a follow-up
    # call to display it shows that no default key is set.
    stdout = self.RunGsUtil(
        ['kms', 'encryption', '-d', suri(bucket_uri)], return_stdout=True)
    self.assertIn(
        'Clearing default encryption key for %s...' % suri(bucket_uri), stdout)

    stdout = self.RunGsUtil(encryption_get_cmd, return_stdout=True)
    self.assertIn('Bucket %s has no default encryption key' % suri(bucket_uri),
                  stdout)


@SkipForS3('gsutil does not support KMS operations for S3 buckets.')
@SkipForJSON('These tests only check for failures when the XML API is forced.')
class TestKmsSubcommandsFailWhenXmlForced(testcase.GsUtilIntegrationTestCase):
  """Tests that kms subcommands fail early when forced to use the XML API."""

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
  dummy_keyname = ('projects/my-project/locations/us-central1/'
                   'keyRings/my-keyring/cryptoKeys/my-key')

  def DoTestSubcommandFailsWhenXmlForcedFromHmacInBotoConfig(self, subcommand):
    with SetBotoConfigForTest(self.boto_config_hmac_auth_only):
      stderr = self.RunGsUtil(subcommand, expected_status=1, return_stderr=True)
      self.assertIn('The "kms" command can only be used with', stderr)

  def testEncryptionFailsWhenXmlForcedFromHmacInBotoConfig(self):
    self.DoTestSubcommandFailsWhenXmlForcedFromHmacInBotoConfig(
        ['kms', 'encryption', 'gs://dummybucket'])

  def testEncryptionDashKFailsWhenXmlForcedFromHmacInBotoConfig(self):
    self.DoTestSubcommandFailsWhenXmlForcedFromHmacInBotoConfig(
        ['kms', 'encryption', '-k', self.dummy_keyname, 'gs://dummybucket'])

  def testEncryptionDashDFailsWhenXmlForcedFromHmacInBotoConfig(self):
    self.DoTestSubcommandFailsWhenXmlForcedFromHmacInBotoConfig(
        ['kms', 'encryption', '-d', 'gs://dummybucket'])

  def testServiceaccountFailsWhenXmlForcedFromHmacInBotoConfig(self):
    self.DoTestSubcommandFailsWhenXmlForcedFromHmacInBotoConfig(
        ['kms', 'serviceaccount', 'gs://dummybucket'])

  def testAuthorizeFailsWhenXmlForcedFromHmacInBotoConfig(self):
    self.DoTestSubcommandFailsWhenXmlForcedFromHmacInBotoConfig(
        ['kms', 'authorize', '-k', self.dummy_keyname, 'gs://dummybucket'])


class TestKmsUnitTests(testcase.GsUtilUnitTestCase):
  """Unit tests for gsutil kms."""

  dummy_keyname = ('projects/my-project/locations/us-central1/'
                   'keyRings/my-keyring/cryptoKeys/my-key')

  @mock.patch(
      'gslib.cloud_api_delegator.CloudApiDelegator.GetProjectServiceAccount')
  @mock.patch('gslib.cloud_api_delegator.CloudApiDelegator.PatchBucket')
  @mock.patch('gslib.kms_api.KmsApi.GetKeyIamPolicy')
  @mock.patch('gslib.kms_api.KmsApi.SetKeyIamPolicy')
  def testEncryptionSetKeySucceedsWhenUpdateKeyPolicySucceeds(
      self, mock_set_key_iam_policy, mock_get_key_iam_policy, mock_patch_bucket,
      mock_get_project_service_account):
    bucket_uri = self.CreateBucket()
    mock_get_key_iam_policy.return_value.bindings = []
    mock_get_project_service_account.return_value.email_address = 'dummy@google.com'

    stdout = self.RunCommand(
        'kms', ['encryption', '-k', self.dummy_keyname,
                suri(bucket_uri)],
        return_stdout=True)
    self.assertIn('Setting default KMS key for bucket', stdout)
    self.assertTrue(mock_patch_bucket.called)

  @mock.patch(
      'gslib.cloud_api_delegator.CloudApiDelegator.GetProjectServiceAccount')
  @mock.patch('gslib.cloud_api_delegator.CloudApiDelegator.PatchBucket')
  @mock.patch('gslib.kms_api.KmsApi.GetKeyIamPolicy')
  @mock.patch('gslib.kms_api.KmsApi.SetKeyIamPolicy')
  def testEncryptionSetKeySucceedsWhenUpdateKeyPolicyFailsWithWarningFlag(
      self, mock_set_key_iam_policy, mock_get_key_iam_policy, mock_patch_bucket,
      mock_get_project_service_account):
    bucket_uri = self.CreateBucket()
    mock_get_key_iam_policy.side_effect = AccessDeniedException(
        'Permission denied')
    mock_get_project_service_account.return_value.email_address = 'dummy@google.com'

    stdout = self.RunCommand(
        'kms', ['encryption', '-k', self.dummy_keyname, '-w',
                suri(bucket_uri)],
        return_stdout=True)
    self.assertIn('Setting default KMS key for bucket', stdout)
    self.assertTrue(mock_patch_bucket.called)

  @mock.patch(
      'gslib.cloud_api_delegator.CloudApiDelegator.GetProjectServiceAccount')
  @mock.patch('gslib.cloud_api_delegator.CloudApiDelegator.PatchBucket')
  @mock.patch('gslib.kms_api.KmsApi.GetKeyIamPolicy')
  @mock.patch('gslib.kms_api.KmsApi.SetKeyIamPolicy')
  def testEncryptionSetKeyFailsWhenUpdateKeyPolicyFailsWithoutWarningFlag(
      self, mock_set_key_iam_policy, mock_get_key_iam_policy, mock_patch_bucket,
      mock_get_project_service_account):
    bucket_uri = self.CreateBucket()
    mock_get_key_iam_policy.side_effect = AccessDeniedException(
        'Permission denied')
    mock_get_project_service_account.return_value.email_address = 'dummy@google.com'

    try:
      stdout = self.RunCommand(
          'kms', ['encryption', '-k', self.dummy_keyname,
                  suri(bucket_uri)],
          return_stdout=True)
      self.fail('Did not get expected AccessDeniedException')
    except AccessDeniedException as e:
      self.assertIn('Permission denied', e.reason)

  @mock.patch(
      'gslib.cloud_api_delegator.CloudApiDelegator.GetProjectServiceAccount')
  @mock.patch('gslib.kms_api.KmsApi.GetKeyIamPolicy')
  @mock.patch('gslib.kms_api.KmsApi.SetKeyIamPolicy')
  def test_shim_translates_authorize_flags(self, mock_get_key_iam_policy,
                                           mock_set_key_iam_policy,
                                           mock_get_project_service_account):
    del mock_set_key_iam_policy
    mock_get_project_service_account.return_value.email_address = 'dummy@google.com'
    mock_get_key_iam_policy.return_value.bindings = []

    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand('kms', [
            'authorize',
            '-p',
            'foo',
            '-k',
            self.dummy_keyname,
        ],
                                           return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            'Gcloud Storage Command: {} storage service-agent'
            ' --project foo --authorize-cmek {}'.format(
                shim_util._get_gcloud_binary_path('fake_dir'),
                self.dummy_keyname), info_lines)

  def test_shim_translates_clear_encryption_key(self):
    bucket_uri = self.CreateBucket()

    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand(
            'kms', ['encryption', '-d', suri(bucket_uri)],
            return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            'Gcloud Storage Command: {} storage buckets update'
            ' --clear-default-encryption-key {}'.format(
                shim_util._get_gcloud_binary_path('fake_dir'),
                suri(bucket_uri)), info_lines)

  @mock.patch(
      'gslib.cloud_api_delegator.CloudApiDelegator.GetProjectServiceAccount')
  @mock.patch('gslib.kms_api.KmsApi.GetKeyIamPolicy')
  @mock.patch('gslib.kms_api.KmsApi.SetKeyIamPolicy')
  def test_shim_translates_update_encryption_key(
      self, mock_get_key_iam_policy, mock_set_key_iam_policy,
      mock_get_project_service_account):
    bucket_uri = self.CreateBucket()
    del mock_set_key_iam_policy
    mock_get_project_service_account.return_value.email_address = 'dummy@google.com'
    mock_get_key_iam_policy.return_value.bindings = []

    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand(
            'kms',
            ['encryption', '-w', '-k', self.dummy_keyname,
             suri(bucket_uri)],
            return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            'Gcloud Storage Command: {} storage buckets update'
            '  --default-encryption-key {} {}'.format(
                shim_util._get_gcloud_binary_path('fake_dir'),
                self.dummy_keyname, suri(bucket_uri)), info_lines)

  def test_shim_translates_displays_encryption_key(self):
    bucket_uri = self.CreateBucket()

    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand(
            'kms', ['encryption', suri(bucket_uri)], return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            'Gcloud Storage Command: {} storage buckets describe '
            '--format=value[separator=\": \"](name, encryption'
            '.defaultKmsKeyName.yesno(no="No default encryption key."))'
            ' --raw {}'.format(shim_util._get_gcloud_binary_path('fake_dir'),
                               suri(bucket_uri)), info_lines)

  @mock.patch(
      'gslib.cloud_api_delegator.CloudApiDelegator.GetProjectServiceAccount')
  def test_shim_translates_serviceaccount_command(
      self, mock_get_project_service_account):
    mock_get_project_service_account.return_value.email_address = 'dummy@google.com'

    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand('kms',
                                           ['serviceaccount', '-p', 'foo'],
                                           return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            'Gcloud Storage Command: {} storage service-agent'
            ' --project foo'.format(
                shim_util._get_gcloud_binary_path('fake_dir')), info_lines)
