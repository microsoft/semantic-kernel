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
"""Tests for signurl command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from datetime import datetime
from datetime import timedelta
import os
import pkgutil

import boto

import gslib.commands.signurl
from gslib.commands.signurl import HAVE_OPENSSL
from gslib.exception import CommandException
from gslib.gcs_json_api import GcsJsonApi
from gslib.iamcredentials_api import IamcredentailsApi
from gslib.impersonation_credentials import ImpersonationCredentials
import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import (SkipForS3, SkipForXML)
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import SetEnvironmentForTest
from gslib.tests.util import unittest
import gslib.tests.signurl_signatures as sigs
from oauth2client import client
from oauth2client.service_account import ServiceAccountCredentials

from six import add_move, MovedModule

add_move(MovedModule('mock', 'mock', 'unittest.mock'))
from six.moves import mock

SERVICE_ACCOUNT = boto.config.get_value('GSUtil',
                                        'test_impersonate_service_account')
TEST_EMAIL = 'test%40developer.gserviceaccount.com'


# pylint: disable=protected-access
@unittest.skipUnless(HAVE_OPENSSL, 'signurl requires pyopenssl.')
@SkipForS3('Signed URLs are only supported for gs:// URLs.')
class TestSignUrl(testcase.GsUtilIntegrationTestCase):
  """Integration tests for signurl command."""

  def _GetJSONKsFile(self):
    if not hasattr(self, 'json_ks_file'):
      # Dummy json keystore constructed from test.p12.
      contents = pkgutil.get_data('gslib', 'tests/test_data/test.json')
      self.json_ks_file = self.CreateTempFile(contents=contents)
    return self.json_ks_file

  def _GetKsFile(self):
    if not hasattr(self, 'ks_file'):
      # Dummy pkcs12 keystore generated with the command

      # openssl req -new -passout pass:notasecret -batch \
      # -x509 -keyout signed_url_test.key -out signed_url_test.pem \
      # -subj '/CN=test.apps.googleusercontent.com'

      # &&

      # openssl pkcs12 -export -passin pass:notasecret \
      # -passout pass:notasecret -inkey signed_url_test.key \
      # -in signed_url_test.pem -out test.p12

      # &&

      # rm signed_url_test.key signed_url_test.pem
      contents = pkgutil.get_data('gslib', 'tests/test_data/test.p12')
      self.ks_file = self.CreateTempFile(contents=contents)
    return self.ks_file

  def testSignUrlInvalidDuration(self):
    """Tests signurl fails with out of bounds value for valid duration."""
    if self._use_gcloud_storage:
      expected_status = 2
    else:
      expected_status = 1
    stderr = self.RunGsUtil(['signurl', '-d', '123d', 'ks_file', 'gs://uri'],
                            return_stderr=True,
                            expected_status=expected_status)
    if self._use_gcloud_storage:
      self.assertIn('value must be less than or equal to 7d', stderr)
    else:
      self.assertIn('CommandException: Max valid duration allowed is 7 days',
                    stderr)

  def testSignUrlInvalidDurationWithUseServiceAccount(self):
    """Tests signurl with -u flag fails duration > 12 hours."""
    stderr = self.RunGsUtil(['signurl', '-d', '13h', '-u', 'gs://uri'],
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('CommandException: Max valid duration allowed is 12:00:00',
                  stderr)

  def testSignUrlOutputP12(self):
    """Tests signurl output of a sample object with pkcs12 keystore."""
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'z')
    cmd = [
        'signurl', '-p', 'notasecret', '-m', 'PUT',
        self._GetKsFile(),
        suri(object_uri)
    ]
    stdout = self.RunGsUtil(cmd, return_stdout=True)
    self.assertIn('x-goog-credential=test.apps.googleusercontent.com', stdout)
    self.assertIn('x-goog-expires=3600', stdout)
    self.assertIn('%2Fus-central1%2F', stdout)
    self.assertIn('\tPUT\t', stdout)

  def testSignUrlOutputJSON(self):
    """Tests signurl output of a sample object with JSON keystore."""
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'z')
    cmd = ['signurl', '-m', 'PUT', self._GetJSONKsFile(), suri(object_uri)]
    stdout = self.RunGsUtil(cmd, return_stdout=True)
    self.assertIn('x-goog-credential=' + TEST_EMAIL, stdout)
    self.assertIn('x-goog-expires=3600', stdout)
    self.assertIn('%2Fus-central1%2F', stdout)
    self.assertIn('\tPUT\t', stdout)

  def testSignUrlWithJSONKeyFileAndObjectGeneration(self):
    """Tests signurl output of a sample object version with JSON keystore."""
    bucket_uri = self.CreateBucket(versioning_enabled=True)
    object_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'z')
    cmd = ['signurl', self._GetJSONKsFile(), object_uri.version_specific_uri]
    stdout = self.RunGsUtil(cmd, return_stdout=True)
    self.assertIn('x-goog-credential=' + TEST_EMAIL, stdout)
    self.assertIn('generation=' + object_uri.generation, stdout)

  def testSignUrlWithURLEncodeRequiredChars(self):
    objs = [
        'gs://example.org/test 1', 'gs://example.org/test/test 2',
        'gs://example.org/Аудиоарi хив'
    ]
    expected_partial_urls = [
        'https://storage.googleapis.com/example.org/test%201?x-goog-signature=',
        ('https://storage.googleapis.com/example.org/test/test%202'
         '?x-goog-signature='),
        ('https://storage.googleapis.com/example.org/%D0%90%D1%83%D0%B4%D0%B8%D'
         '0%BE%D0%B0%D1%80i%20%D1%85%D0%B8%D0%B2?x-goog-signature=')
    ]

    self.assertEqual(len(objs), len(expected_partial_urls))

    cmd_args = [
        'signurl', '-m', 'PUT', '-p', 'notasecret', '-r', 'us',
        self._GetKsFile()
    ]
    cmd_args.extend(objs)

    stdout = self.RunGsUtil(cmd_args, return_stdout=True)

    lines = stdout.split('\n')
    # Header, signed urls, trailing newline.
    self.assertEqual(len(lines), len(objs) + 2)

    # Strip the header line to make the indices line up.
    lines = lines[1:]

    for obj, line, partial_url in zip(objs, lines, expected_partial_urls):
      self.assertIn(obj, line)
      self.assertIn(partial_url, line)
      self.assertIn('x-goog-credential=test.apps.googleusercontent.com', line)
    self.assertIn('%2Fus%2F', stdout)

  def testSignUrlWithWildcard(self):
    objs = ['test1', 'test2', 'test3']
    obj_urls = []
    bucket = self.CreateBucket()

    for obj_name in objs:
      obj_urls.append(
          self.CreateObject(bucket_uri=bucket,
                            object_name=obj_name,
                            contents=b''))

    stdout = self.RunGsUtil(
        ['signurl', '-p', 'notasecret',
         self._GetKsFile(),
         suri(bucket) + '/*'],
        return_stdout=True)

    # Header, 3 signed urls, trailing newline
    self.assertEqual(len(stdout.split('\n')), 5)

    for obj_url in obj_urls:
      self.assertIn(suri(obj_url), stdout)

  @unittest.skipUnless(SERVICE_ACCOUNT,
                       'Test requires test_impersonate_service_account.')
  @SkipForS3('Tests only uses gs credentials.')
  @SkipForXML('Tests only run on JSON API.')
  def testSignUrlWithServiceAccount(self):
    with SetBotoConfigForTest([('Credentials', 'gs_impersonate_service_account',
                                SERVICE_ACCOUNT)]):
      stdout, stderr = self.RunGsUtil(
          ['signurl', '-r', 'us-east1', '-u', 'gs://pub'],
          return_stdout=True,
          return_stderr=True)
    # The signed url returned in stdout relies on current time.
    # We are not able to mock the datetime here because RunGsUtil creates
    # a separate process and runs the command.
    self.assertIn('https://storage.googleapis.com/pub', stdout)
    self.assertIn('All API calls will be executed as [%s]' % SERVICE_ACCOUNT,
                  stderr)

  def testSignUrlOfNonObjectUrl(self):
    """Tests the signurl output of a non-existent file."""
    self.RunGsUtil(['signurl', self._GetKsFile(), 'gs://'],
                   expected_status=1,
                   stdin='notasecret')
    self.RunGsUtil(['signurl', 'file://tmp/abc', 'gs://bucket'],
                   expected_status=1)


@unittest.skipUnless(HAVE_OPENSSL, 'signurl requires pyopenssl.')
class UnitTestSignUrl(testcase.GsUtilUnitTestCase):
  """Unit tests for the signurl command."""

  # Helpful for comparing mismatched signed URLs that would be truncated.
  # https://stackoverflow.com/questions/14493670/how-to-set-self-maxdiff-in-nose-to-get-full-diff-output
  maxDiff = None

  def setUp(self):
    super(UnitTestSignUrl, self).setUp()
    ks_contents = pkgutil.get_data('gslib', 'tests/test_data/test.p12')
    self.key, self.client_email = gslib.commands.signurl._ReadKeystore(
        ks_contents, 'notasecret')

    def fake_now():
      return datetime(1900, 1, 1, 0, 5, 55)

    gslib.utils.signurl_helper._NowUTC = fake_now

  def _get_mock_api_delegator(self):
    mock_api_delegator = self.MakeGsUtilApi()

    # The MAkeGsUtilAPi maps apiclass.gs.JSON to BotoTranslation
    # instead of GcsJsonApi
    # Issue https://github.com/GoogleCloudPlatform/gsutil/issues/970
    # SignUrl relies on the GcsJsonApi so we are replacing the mapping here.
    mock_api_delegator.api_map['apiclass']['gs']['JSON'] = GcsJsonApi
    return mock_api_delegator

  def testDurationSpec(self):
    tests = [
        ('1h', timedelta(hours=1)),
        ('2d', timedelta(days=2)),
        ('5D', timedelta(days=5)),
        ('35s', timedelta(seconds=35)),
        ('1h', timedelta(hours=1)),
        ('33', timedelta(hours=33)),
        ('22m', timedelta(minutes=22)),
        ('3.7', None),
        ('27Z', None),
    ]

    for inp, expected in tests:
      try:
        td = gslib.commands.signurl._DurationToTimeDelta(inp)
        self.assertEqual(td, expected)
      except CommandException:
        if expected is not None:
          self.fail('{0} failed to parse')

  def testSignPutUsingKeyFile(self):
    """Tests the _GenSignedUrl function with a PUT method using Key file."""
    expected = sigs.TEST_SIGN_PUT_SIG

    duration = timedelta(seconds=3600)
    with SetBotoConfigForTest([('Credentials', 'gs_host',
                                'storage.googleapis.com')]):
      signed_url = gslib.commands.signurl._GenSignedUrl(
          self.key,
          api=None,
          use_service_account=False,
          provider='gs',
          client_id=self.client_email,
          method='RESUMABLE',
          gcs_path='test/test.txt',
          duration=duration,
          logger=self.logger,
          region='us-east',
          content_type='')
    self.assertEqual(expected, signed_url)

  @SkipForS3('Tests only uses gs credentials.')
  @SkipForXML('Tests only run on JSON API.')
  def testSignPutUsingServiceAccount(self):
    """Tests the _GenSignedUrl function PUT method with service account."""
    expected = sigs.TEST_SIGN_URL_PUT_WITH_SERVICE_ACCOUNT
    duration = timedelta(seconds=3600)

    mock_api_delegator = self._get_mock_api_delegator()
    json_api = mock_api_delegator._GetApi('gs')
    # patch a service account credentials
    mock_credentials = mock.Mock(spec=ServiceAccountCredentials)
    mock_credentials.service_account_email = 'fake_service_account_email'
    mock_credentials.sign_blob.return_value = ('fake_key', b'fake_signature')
    json_api.credentials = mock_credentials
    with SetBotoConfigForTest([('Credentials', 'gs_host',
                                'storage.googleapis.com')]):
      signed_url = gslib.commands.signurl._GenSignedUrl(
          None,
          api=mock_api_delegator,
          use_service_account=True,
          provider='gs',
          client_id=self.client_email,
          method='PUT',
          gcs_path='test/test.txt',
          duration=duration,
          logger=self.logger,
          region='us-east1',
          content_type='')
    self.assertEqual(expected, signed_url)
    mock_credentials.sign_blob.assert_called_once_with(
        b'GOOG4-RSA-SHA256\n19000101T000555Z\n19000101/us-east1/storage/'
        b'goog4_request\n7f110b30eeca7fdd8846e876bceee85384d8e4c7388b359'
        b'6544b1b503f9e2320')

  @SkipForS3('Tests only uses gs credentials.')
  @SkipForXML('Tests only run on JSON API.')
  def testSignUrlWithIncorrectAccountType(self):
    """Tests the _GenSignedUrl with incorrect account type.

    Test that GenSignedUrl function with 'use_service_account' set to True
    and a service account not used for credentials raises an error.
    """
    expected = sigs.TEST_SIGN_URL_PUT_WITH_SERVICE_ACCOUNT
    duration = timedelta(seconds=3600)

    mock_api_delegator = self._get_mock_api_delegator()
    json_api = mock_api_delegator._GetApi('gs')
    # patch a service account credentials
    mock_credentials = mock.Mock(spec=client.OAuth2Credentials)
    mock_credentials.service_account_email = 'fake_service_account_email'
    json_api.credentials = mock_credentials
    with SetBotoConfigForTest([('Credentials', 'gs_host',
                                'storage.googleapis.com')]):
      self.assertRaises(CommandException,
                        gslib.commands.signurl._GenSignedUrl,
                        None,
                        api=mock_api_delegator,
                        use_service_account=True,
                        provider='gs',
                        client_id=self.client_email,
                        method='PUT',
                        gcs_path='test/test.txt',
                        duration=duration,
                        logger=self.logger,
                        region='us-east1',
                        content_type='')

  @SkipForS3('Tests only uses gs credentials.')
  @SkipForXML('Tests only run on JSON API.')
  @mock.patch('gslib.iamcredentials_api.apitools_client')
  @mock.patch('gslib.iamcredentials_api.apitools_messages')
  def testSignPutUsingImersonatedServiceAccount(self, mock_api_messages,
                                                mock_apiclient):
    """Tests the _GenSignedUrl function PUT method with impersonation.

    Test _GenSignedUrl function using an impersonated service account.
    """
    expected = sigs.TEST_SIGN_URL_PUT_WITH_SERVICE_ACCOUNT
    duration = timedelta(seconds=3600)

    mock_api_delegator = self._get_mock_api_delegator()
    json_api = mock_api_delegator._GetApi('gs')

    # A mock object of type ImpersonationCredentials.
    mock_credentials = mock.Mock(spec=ImpersonationCredentials)

    api_client_obj = mock.Mock()
    mock_apiclient.IamcredentialsV1.return_value = api_client_obj

    # The api_client.IamcredntialsV1 get's in IamCredentialsApi's init
    mock_iam_cred_api = IamcredentailsApi(credentials=mock.Mock())
    mock_credentials.api = mock_iam_cred_api
    mock_credentials.service_account_id = 'fake_service_account_email'

    # Mock the response and assign it as a  return value for the SignBlob func.
    mock_resp = mock.Mock()
    mock_resp.signedBlob = b'fake_signature'
    api_client_obj.projects_serviceAccounts.SignBlob.return_value = mock_resp

    json_api.credentials = mock_credentials

    with SetBotoConfigForTest([('Credentials', 'gs_host',
                                'storage.googleapis.com')]):
      signed_url = gslib.commands.signurl._GenSignedUrl(
          None,
          api=mock_api_delegator,
          use_service_account=True,
          provider='gs',
          client_id=self.client_email,
          method='PUT',
          gcs_path='test/test.txt',
          duration=duration,
          logger=self.logger,
          region='us-east1',
          content_type='')
    self.assertEqual(expected, signed_url)
    mock_api_messages.SignBlobRequest.assert_called_once_with(
        payload=b'GOOG4-RSA-SHA256\n19000101T000555Z\n19000101/us-east1'
        b'/storage/goog4_request\n7f110b30eeca7fdd8846e876bceee'
        b'85384d8e4c7388b3596544b1b503f9e2320')

  def testSignResumableWithKeyFile(self):
    """Tests _GenSignedUrl using key file with a RESUMABLE method."""
    expected = sigs.TEST_SIGN_RESUMABLE

    class MockLogger(object):

      def __init__(self):
        self.warning_issued = False

      def warn(self, unused_msg):
        self.warning_issued = True

    mock_logger = MockLogger()
    duration = timedelta(seconds=3600)
    with SetBotoConfigForTest([('Credentials', 'gs_host',
                                'storage.googleapis.com')]):
      signed_url = gslib.commands.signurl._GenSignedUrl(
          self.key,
          api=None,
          use_service_account=False,
          provider='gs',
          client_id=self.client_email,
          method='RESUMABLE',
          gcs_path='test/test.txt',
          duration=duration,
          logger=mock_logger,
          region='us-east',
          content_type='')
    self.assertEqual(expected, signed_url)
    # Resumable uploads with no content-type should issue a warning.
    self.assertTrue(mock_logger.warning_issued)

    mock_logger2 = MockLogger()
    with SetBotoConfigForTest([('Credentials', 'gs_host',
                                'storage.googleapis.com')]):
      signed_url = gslib.commands.signurl._GenSignedUrl(
          self.key,
          api=None,
          use_service_account=False,
          provider='gs',
          client_id=self.client_email,
          method='RESUMABLE',
          gcs_path='test/test.txt',
          duration=duration,
          logger=mock_logger2,
          region='us-east',
          content_type='image/jpeg')
    # No warning, since content type was included.
    self.assertFalse(mock_logger2.warning_issued)

  def testSignurlPutContentypeUsingKeyFile(self):
    """Tests _GenSignedUrl using key file with a PUT method and content type."""
    expected = sigs.TEST_SIGN_URL_PUT_CONTENT

    duration = timedelta(seconds=3600)
    with SetBotoConfigForTest([('Credentials', 'gs_host',
                                'storage.googleapis.com')]):
      signed_url = gslib.commands.signurl._GenSignedUrl(
          self.key,
          api=None,
          use_service_account=False,
          provider='gs',
          client_id=self.client_email,
          method='PUT',
          gcs_path='test/test.txt',
          duration=duration,
          logger=self.logger,
          region='eu',
          content_type='text/plain')
    self.assertEqual(expected, signed_url)

  def testSignurlGetUsingKeyFile(self):
    """Tests the _GenSignedUrl function using key file with a GET method."""
    expected = sigs.TEST_SIGN_URL_GET

    duration = timedelta(seconds=0)
    with SetBotoConfigForTest([('Credentials', 'gs_host',
                                'storage.googleapis.com')]):
      signed_url = gslib.commands.signurl._GenSignedUrl(
          self.key,
          api=None,
          use_service_account=False,
          provider='gs',
          client_id=self.client_email,
          method='GET',
          gcs_path='test/test.txt',
          duration=duration,
          logger=self.logger,
          region='asia',
          content_type='')
    self.assertEqual(expected, signed_url)

  def testSignurlGetWithJSONKeyUsingKeyFile(self):
    """Tests _GenSignedUrl with a GET method and the test JSON private key."""
    expected = sigs.TEST_SIGN_URL_GET_WITH_JSON_KEY

    json_contents = pkgutil.get_data('gslib',
                                     'tests/test_data/test.json').decode()
    key, client_email = gslib.commands.signurl._ReadJSONKeystore(json_contents)

    duration = timedelta(seconds=0)
    with SetBotoConfigForTest([('Credentials', 'gs_host',
                                'storage.googleapis.com')]):
      signed_url = gslib.commands.signurl._GenSignedUrl(
          key,
          api=None,
          use_service_account=False,
          provider='gs',
          client_id=client_email,
          method='GET',
          gcs_path='test/test.txt',
          duration=duration,
          logger=self.logger,
          region='asia',
          content_type='')
    self.assertEqual(expected, signed_url)

  def testSignurlGetWithUserProject(self):
    """Tests the _GenSignedUrl function with a userproject."""
    expected = sigs.TEST_SIGN_URL_GET_USERPROJECT

    duration = timedelta(seconds=0)
    with SetBotoConfigForTest([('Credentials', 'gs_host',
                                'storage.googleapis.com')]):
      signed_url = gslib.commands.signurl._GenSignedUrl(
          self.key,
          api=None,
          use_service_account=False,
          provider='gs',
          client_id=self.client_email,
          method='GET',
          gcs_path='test/test.txt',
          duration=duration,
          logger=self.logger,
          region='asia',
          content_type='',
          billing_project='myproject')
    self.assertEqual(expected, signed_url)

  def testShimTranslatesFlags(self):
    key_contents = pkgutil.get_data('gslib', 'tests/test_data/test.json')
    key_path = self.CreateTempFile(contents=key_contents)

    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand('signurl', [
            '-d', '2m', '-m', 'RESUMABLE', '-r', 'US', '-b', 'project', '-c',
            'application/octet-stream', key_path, 'gs://bucket/object'
        ],
                                           return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            'storage sign-url'
            ' --format=csv[separator="\\t"](resource:label="URL", http_verb:label="HTTP Method", expiration:label="Expiration", signed_url:label="Signed URL")'
            ' --private-key-file={}'
            ' --headers=x-goog-resumable=start'
            ' --duration 120s'
            ' --http-verb POST'
            ' --region US'
            ' --query-params userProject=project'
            ' --headers content-type=application/octet-stream'
            ' gs://bucket/object'.format(key_path), info_lines)
