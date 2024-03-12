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

"""Unit tests for oauth2_client and related classes."""

from __future__ import absolute_import

import datetime
import logging
import os
import stat
import sys
import unittest

from freezegun import freeze_time
from gcs_oauth2_boto_plugin import oauth2_client
import httplib2

try:
  from unittest import mock
except ImportError:
  import mock

LOG = logging.getLogger('test_oauth2_client')

ACCESS_TOKEN = 'abc123'
RAPT_TOKEN = 'rapt123'
TOKEN_URI = 'https://provider.example.com/oauth/provider?mode=token'
AUTH_URI = 'https://provider.example.com/oauth/provider?mode=authorize'
DEFAULT_CA_CERTS_FILE = os.path.abspath(
    os.path.join('gslib', 'data', 'cacerts.txt'))

IS_WINDOWS = 'win32' in str(sys.platform).lower()


class MockDateTime(object):

  def __init__(self):
    self.mock_now = None

  def utcnow(self):  # pylint: disable=invalid-name
    return self.mock_now


class MockOAuth2ServiceAccountClient(oauth2_client.OAuth2ServiceAccountClient):
  """Mock service account client for testing OAuth2 with service accounts."""

  def __init__(self, client_id, private_key, password, auth_uri, token_uri,
               datetime_strategy):
    super(MockOAuth2ServiceAccountClient, self).__init__(
        client_id, private_key, password, auth_uri=auth_uri,
        token_uri=token_uri, datetime_strategy=datetime_strategy,
        ca_certs_file=DEFAULT_CA_CERTS_FILE)
    self.Reset()

  def Reset(self):
    self.fetched_token = False

  def FetchAccessToken(self, rapt_token=None):
    self.fetched_token = True
    return oauth2_client.AccessToken(
        ACCESS_TOKEN,
        GetExpiry(self.datetime_strategy, 3600),
        datetime_strategy=self.datetime_strategy,
        rapt_token=None)


class MockOAuth2UserAccountClient(oauth2_client.OAuth2UserAccountClient):
  """Mock user account client for testing OAuth2 with user accounts."""

  def __init__(self, token_uri, client_id, client_secret, refresh_token,
               auth_uri, datetime_strategy):
    super(MockOAuth2UserAccountClient, self).__init__(
        token_uri, client_id, client_secret, refresh_token, auth_uri=auth_uri,
        datetime_strategy=datetime_strategy,
        ca_certs_file=DEFAULT_CA_CERTS_FILE)
    self.Reset()

  def Reset(self):
    self.fetched_token = False

  def FetchAccessToken(self, rapt_token=None):
    self.fetched_token = True
    return oauth2_client.AccessToken(
        ACCESS_TOKEN,
        GetExpiry(self.datetime_strategy, 3600),
        datetime_strategy=self.datetime_strategy,
        rapt_token=RAPT_TOKEN if rapt_token is None else rapt_token)


def GetExpiry(datetime_strategy, length_in_seconds):
  token_expiry = (datetime_strategy.utcnow()
                  + datetime.timedelta(seconds=length_in_seconds))
  return token_expiry


def CreateMockUserAccountClient(mock_datetime):
  return MockOAuth2UserAccountClient(
      TOKEN_URI, 'clid', 'clsecret', 'ref_token_abc123', AUTH_URI,
      mock_datetime)


def CreateMockServiceAccountClient(mock_datetime):
  return MockOAuth2ServiceAccountClient(
      'clid', 'private_key', 'password', AUTH_URI, TOKEN_URI, mock_datetime)


class OAuth2AccountClientTest(unittest.TestCase):
  """Unit tests for OAuth2UserAccountClient and OAuth2ServiceAccountClient."""

  def setUp(self):
    self.tempdirs = []
    self.mock_datetime = MockDateTime()
    self.start_time = datetime.datetime(2011, 3, 1, 11, 25, 13, 300826)
    self.mock_datetime.mock_now = self.start_time

  def testGetAccessTokenUserAccount(self):
    self.client = CreateMockUserAccountClient(self.mock_datetime)
    self._RunGetAccessTokenTest(expected_rapt=RAPT_TOKEN)

  def testGetAccessTokenServiceAccount(self):
    self.client = CreateMockServiceAccountClient(self.mock_datetime)
    self._RunGetAccessTokenTest()

  def _RunGetAccessTokenTest(self, expected_rapt=None):
    """Tests access token gets with self.client."""
    access_token_1 = 'abc123'

    self.assertFalse(self.client.fetched_token)
    token_1 = self.client.GetAccessToken()

    # There's no access token in the cache; verify that we fetched a fresh
    # token.
    self.assertTrue(self.client.fetched_token)
    self.assertEqual(access_token_1, token_1.token)
    self.assertEqual(self.start_time + datetime.timedelta(minutes=60),
                     token_1.expiry)
    self.assertEqual(token_1.rapt_token, expected_rapt)

    # Advance time by less than expiry time, and fetch another token.
    self.client.Reset()
    self.mock_datetime.mock_now = (
        self.start_time + datetime.timedelta(minutes=55))
    token_2 = self.client.GetAccessToken()

    # Since the access token wasn't expired, we get the cache token, and there
    # was no refresh request.
    self.assertEqual(token_1, token_2)
    self.assertEqual(access_token_1, token_2.token)
    self.assertFalse(self.client.fetched_token)

    # Advance time past expiry time, and fetch another token.
    self.client.Reset()
    self.mock_datetime.mock_now = (
        self.start_time + datetime.timedelta(minutes=55, seconds=1))
    self.client.datetime_strategy = self.mock_datetime
    token_3 = self.client.GetAccessToken()

    # This should have resulted in a refresh request and a fresh access token.
    self.assertTrue(self.client.fetched_token)
    self.assertEqual(
        self.mock_datetime.mock_now + datetime.timedelta(minutes=60),
        token_3.expiry)
    self.assertEqual(token_3.rapt_token, expected_rapt)


class AccessTokenTest(unittest.TestCase):
  """Unit tests for access token functions."""

  def testShouldRefresh(self):
    """Tests that token.ShouldRefresh returns the correct value."""
    mock_datetime = MockDateTime()
    start = datetime.datetime(2011, 3, 1, 11, 25, 13, 300826)
    expiry = start + datetime.timedelta(minutes=60)
    token = oauth2_client.AccessToken(
        'foo', expiry, datetime_strategy=mock_datetime)

    mock_datetime.mock_now = start
    self.assertFalse(token.ShouldRefresh())

    mock_datetime.mock_now = start + datetime.timedelta(minutes=54)
    self.assertFalse(token.ShouldRefresh())

    mock_datetime.mock_now = start + datetime.timedelta(minutes=55)
    self.assertFalse(token.ShouldRefresh())

    mock_datetime.mock_now = start + datetime.timedelta(
        minutes=55, seconds=1)
    self.assertTrue(token.ShouldRefresh())

    mock_datetime.mock_now = start + datetime.timedelta(
        minutes=61)
    self.assertTrue(token.ShouldRefresh())

    mock_datetime.mock_now = start + datetime.timedelta(minutes=58)
    self.assertFalse(token.ShouldRefresh(time_delta=120))

    mock_datetime.mock_now = start + datetime.timedelta(
        minutes=58, seconds=1)
    self.assertTrue(token.ShouldRefresh(time_delta=120))

  def testShouldRefreshNoExpiry(self):
    """Tests token.ShouldRefresh with no expiry time."""
    mock_datetime = MockDateTime()
    start = datetime.datetime(2011, 3, 1, 11, 25, 13, 300826)
    token = oauth2_client.AccessToken(
        'foo', None, datetime_strategy=mock_datetime)

    mock_datetime.mock_now = start
    self.assertFalse(token.ShouldRefresh())

    mock_datetime.mock_now = start + datetime.timedelta(
        minutes=472)
    self.assertFalse(token.ShouldRefresh())

  def testSerialization(self):
    """Tests token serialization."""
    expiry = datetime.datetime(2011, 3, 1, 11, 25, 13, 300826)
    token = oauth2_client.AccessToken('foo', expiry, rapt_token=RAPT_TOKEN)
    serialized_token = token.Serialize()
    LOG.debug('testSerialization: serialized_token=%s', serialized_token)

    token2 = oauth2_client.AccessToken.UnSerialize(serialized_token)
    self.assertEqual(token, token2)


class FileSystemTokenCacheTest(unittest.TestCase):
  """Unit tests for FileSystemTokenCache."""

  def setUp(self):
    self.cache = oauth2_client.FileSystemTokenCache()
    self.start_time = datetime.datetime(2011, 3, 1, 10, 25, 13, 300826)
    self.token_1 = oauth2_client.AccessToken(
        'token1', self.start_time, rapt_token=RAPT_TOKEN)
    self.token_2 = oauth2_client.AccessToken(
        'token2', self.start_time + datetime.timedelta(seconds=492),
        rapt_token=RAPT_TOKEN)
    self.key = 'token1key'

  def tearDown(self):
    try:
      os.unlink(self.cache.CacheFileName(self.key))
    except:  # pylint: disable=bare-except
      pass

  def testPut(self):
    self.cache.PutToken(self.key, self.token_1)
    # Assert that the cache file exists and has correct permissions.
    if not IS_WINDOWS:
      self.assertEqual(
          0o600,
          stat.S_IMODE(os.stat(self.cache.CacheFileName(self.key)).st_mode))

  def testPutGet(self):
    """Tests putting and getting various tokens."""
    # No cache file present.
    self.assertEqual(None, self.cache.GetToken(self.key))

    # Put a token
    self.cache.PutToken(self.key, self.token_1)
    cached_token = self.cache.GetToken(self.key)
    self.assertEqual(self.token_1, cached_token)

    # Put a different token
    self.cache.PutToken(self.key, self.token_2)
    cached_token = self.cache.GetToken(self.key)
    self.assertEqual(self.token_2, cached_token)

  def testGetBadFile(self):
    f = open(self.cache.CacheFileName(self.key), 'w')
    f.write('blah')
    f.close()
    self.assertEqual(None, self.cache.GetToken(self.key))

  def testCacheFileName(self):
    """Tests configuring the cache with a specific file name."""
    cache = oauth2_client.FileSystemTokenCache(
        path_pattern='/var/run/ccache/token.%(uid)s.%(key)s')
    if IS_WINDOWS:
      uid = '_'
    else:
      uid = os.getuid()
    self.assertEqual('/var/run/ccache/token.%s.abc123' % uid,
                     cache.CacheFileName('abc123'))

    cache = oauth2_client.FileSystemTokenCache(
        path_pattern='/var/run/ccache/token.%(key)s')
    self.assertEqual('/var/run/ccache/token.abc123',
                     cache.CacheFileName('abc123'))


class RefreshTokenTest(unittest.TestCase):
  """Unit tests for refresh tokens."""

  def setUp(self):
    self.mock_datetime = MockDateTime()
    self.start_time = datetime.datetime(2011, 3, 1, 10, 25, 13, 300826)
    self.mock_datetime.mock_now = self.start_time
    self.client = CreateMockUserAccountClient(self.mock_datetime)

  def testUniqeId(self):
    cred_id = self.client.CacheKey()
    self.assertEqual('0720afed6871f12761fbea3271f451e6ba184bf5', cred_id)

  def testGetAuthorizationHeader(self):
    self.assertEqual('Bearer %s' % ACCESS_TOKEN,
                     self.client.GetAuthorizationHeader())


class FakeResponse(object):

  def __init__(self, status):
    self._status = status

  @property
  def status(self):
    return self._status


class OAuth2GCEClientTest(unittest.TestCase):
  """Unit tests for OAuth2GCEClient."""

  def setUp(self):
    patcher = mock.patch(
        'gcs_oauth2_boto_plugin.oauth2_client.httplib2.Http', autospec=True)
    self.addCleanup(patcher.stop)
    self.mocked_http_class = patcher.start()
    self.mock_http = self.mocked_http_class.return_value

  @freeze_time('2014-03-26 01:01:01')
  def testFetchAccessToken(self):
    token = 'my_token'
    self.mock_http.request.return_value = (
        FakeResponse(200),
        '{"access_token":"%(TOKEN)s", "expires_in": %(EXPIRES_IN)d}' % {
            'TOKEN': token,
            'EXPIRES_IN': 42
        })

    client = oauth2_client.OAuth2GCEClient()

    self.assertEqual(
        str(client.FetchAccessToken()),
        'AccessToken(token=%s, expiry=2014-03-26 01:01:43Z)' % token)
    self.mock_http.request.assert_called_with(
        oauth2_client.META_TOKEN_URI,
        method='GET',
        body=None,
        headers=oauth2_client.META_HEADERS)

  def testIsGCENotFound(self):
    self.mock_http.request.return_value = (FakeResponse(404), '')

    self.assertFalse(oauth2_client._IsGCE())
    self.mock_http.request.assert_called_once_with(
        oauth2_client.METADATA_SERVER)

  def testIsGCEServerNotFound(self):
    self.mock_http.request.side_effect = httplib2.ServerNotFoundError()

    self.assertFalse(oauth2_client._IsGCE())
    self.mock_http.request.assert_called_once_with(
        oauth2_client.METADATA_SERVER)

  def testIsGCETrue(self):
    self.mock_http.request.return_value = (FakeResponse(200), '')

    self.assertTrue(oauth2_client._IsGCE())
    self.mock_http.request.assert_called_once_with(
        oauth2_client.METADATA_SERVER)


if __name__ == '__main__':
  unittest.main()
