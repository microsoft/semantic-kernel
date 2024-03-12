# Copyright 2015 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the reauth module."""

import base64
import datetime
import json
import os
import unittest

import mock
from mock import patch

from six.moves import http_client
from six.moves import urllib

from oauth2client import client
from oauth2client import client

from google_reauth import reauth
from google_reauth import errors
from google_reauth import reauth_creds
from google_reauth import _reauth_client
from google_reauth.reauth_creds import Oauth2WithReauthCredentials


_ok_response = lambda: None
setattr(_ok_response, 'status', http_client.OK)

_error_response = lambda: None
setattr(_error_response, 'status', None)

_token_response = (
    _ok_response,
    json.dumps(
        {'access_token': 'new_access_token', 'refresh_token': 'new_refresh_token',
         'expires_in': 60 * 60}))


class MockStore(client.Storage):
    def __init__(self):
        self.credentials = None

    def locked_put(self, credentials):
        self.credentials = credentials

    def locked_get(self):
        return self.credentials


class ReauthCredsTest(unittest.TestCase):
    """This class contains tests for Oauth2WithReauthCredentials. """

    def StartPatch(self, *args, **kwargs):
        patcher = mock.patch(*args, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    @patch('google_reauth.reauth.get_rapt_token')
    def get_rapt_token(self, *args, **kwargs):
        return 'rapt_token'

    def _http_mock(self, request_side_effect):
        request_mock = self.StartPatch('httplib2.Http.request')
        request_mock.side_effect = request_side_effect
        http_mock = self.StartPatch('httplib2.Http')
        http_mock.request = request_mock
        return http_mock

    def _run_refresh_test(self, http_mock, access_token, refresh_token,
                          token_expiry, invalid):
        creds = self._get_creds()
        store = MockStore()
        creds.set_store(store)

        creds._do_refresh_request(http_mock)
        self._check_credentials(creds, store, access_token, refresh_token,
                                token_expiry, invalid)

    def _get_creds(self):
        return Oauth2WithReauthCredentials(
            access_token='old_token', client_id='id', client_secret='secret',
            refresh_token='old_refresh_token',
            token_expiry=datetime.datetime(2018, 3, 2, 21, 26, 13),
            token_uri='token_uri',
            user_agent='user_agent')

    def _check_credentials(self, creds, store, access_token, refresh_token,
                           token_expiry, invalid):
        stored_creds = store.locked_get() if store else creds

        self.assertEqual(access_token, creds.access_token)
        self.assertEqual(access_token, stored_creds.access_token)

        self.assertEqual(refresh_token, creds.refresh_token)
        self.assertEqual(refresh_token, stored_creds.refresh_token)

        self.assertEqual(token_expiry, creds.token_expiry)
        self.assertEqual(token_expiry, stored_creds.token_expiry)

        self.assertEqual(invalid, creds.invalid)
        self.assertEqual(invalid, stored_creds.invalid)

  #######
  # Helper functions and classes above.
  # Actual tests below.
  #######

    def setUp(self):
        get_rapt = self.StartPatch('google_reauth.reauth.get_rapt_token')
        get_rapt.return_value='rapt_token'

        current_datetime = self.StartPatch('oauth2client.client._UTCNOW')
        current_datetime.return_value = datetime.datetime(2018, 3, 2, 21, 26, 13)

    def testFromOAuth2Credentials(self):
        orig = client.OAuth2Credentials(
            access_token='at', client_id='ci', client_secret='cs',
            refresh_token='rt', token_expiry='te', token_uri='tu',
            user_agent='ua')
        cred = Oauth2WithReauthCredentials.from_OAuth2Credentials(orig)
        self.assertEqual('Oauth2WithReauthCredentials', cred.__class__.__name__)
        self.assertEqual('ci', cred.client_id)
        self.assertEqual('cs', cred.client_secret)

    def testTokenExpiryFromJson(self):
        cred = Oauth2WithReauthCredentials.from_json(json.dumps({
            'access_token': 'access_token',
            'client_id': 'client_id',
            'client_secret': 'client_secret',
            'refresh_token': 'refresh_token',
            'token_expiry': 'foo',
            'token_uri': 'token_uri',
            'user_agent': 'user_agent',
            'invalid': False}))
        self.assertEqual(None, cred.token_expiry)
        cred = Oauth2WithReauthCredentials.from_json(json.dumps({
            'access_token': 'access_token',
            'client_id': 'client_id',
            'client_secret': 'client_secret',
            'refresh_token': 'refresh_token',
            'token_expiry': '2018-03-02T21:26:13Z',
            'token_uri': 'token_uri',
            'user_agent': 'user_agent',
            'invalid': False}))
        self.assertEqual(datetime.datetime(2018, 3, 2, 21, 26, 13),
                         cred.token_expiry)

    def testRefreshNoReauthRequired(self):
        def request_side_effect(self, *args, **kwargs):
            return _token_response

        self._run_refresh_test(
            self._http_mock(request_side_effect),
            'new_access_token',
            'new_refresh_token',
            datetime.datetime(2018, 3, 2, 22, 26, 13),
            False)

    def testRefreshReauthRequired(self):
        responses = [
            _token_response,
            (_error_response, json.dumps({
                'error': 'invalid_grant',
                'error_subtype': 'rapt_required'}))]
        def request_side_effect(self, *args, **kwargs):
            return responses.pop()

        self._run_refresh_test(
            self._http_mock(request_side_effect),
            'new_access_token',
            'new_refresh_token',
            datetime.datetime(2018, 3, 2, 22, 26, 13),
            False)

    def testInvalidRapt(self):
        responses = [
            (_error_response, json.dumps({
                'error': 'invalid_grant',
                'error_subtype': 'rapt_required'})),
            (_error_response, json.dumps({
                'error': 'invalid_grant',
                'error_subtype': 'rapt_required'}))]
        def request_side_effect(self, *args, **kwargs):
            return responses.pop()

        creds = self._get_creds()
        store = MockStore()
        creds.set_store(store)

        with self.assertRaises(client.HttpAccessTokenRefreshError):
            creds._do_refresh_request(self._http_mock(request_side_effect))

        self._check_credentials(
            creds, store,
            'old_token',
            'old_refresh_token',
            datetime.datetime(2018, 3, 2, 21, 26, 13),
            True)

    def testRefreshWithStore(self):
        def request_side_effect(self, *args, **kwargs):
            return _token_response

        creds = self._get_creds()
        store = MockStore()
        creds.set_store(store)

        creds._do_refresh_request(self._http_mock(request_side_effect))

        self._check_credentials(
          creds, store,
          'new_access_token',
          'new_refresh_token',
          datetime.datetime(2018, 3, 2, 22, 26, 13),
          False)

    def testRefreshNoStore(self):
        def request_side_effect(self, *args, **kwargs):
            return _token_response

        creds = self._get_creds()
        creds._do_refresh_request(self._http_mock(request_side_effect))
        self._check_credentials(
            creds, None,
            'new_access_token',
            'new_refresh_token',
            datetime.datetime(2018, 3, 2, 22, 26, 13),
            False)

    def testRefreshNoExpiry(self):
        def request_side_effect(self, *args, **kwargs):
            return (
                _ok_response,
                json.dumps(
                    {'access_token': 'new_access_token',
                     'refresh_token': 'new_refresh_token'}))

        self._run_refresh_test(
            self._http_mock(request_side_effect),
            'new_access_token',
            'new_refresh_token',
            None,
            False)
