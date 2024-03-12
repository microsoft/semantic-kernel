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
import json
import os
import unittest

import mock

from six.moves import http_client
from six.moves import urllib

from oauth2client import client

from google_reauth import challenges
from google_reauth import reauth
from google_reauth import errors
from google_reauth import reauth_creds
from google_reauth import _reauth_client
from google_reauth.reauth_creds import Oauth2WithReauthCredentials

from pyu2f import model
from pyu2f import u2f


_ok_response = mock.Mock(spec=['status'], status=http_client.OK)
_error_response = mock.Mock(spec=['status'], status=None)


class ReauthTest(unittest.TestCase):
    """This class contains tests for mocking reauth.

    The tests here are a bit more verbose since we are trying to mock out U2F, and
    present the reauth code some form of valid reply. This makes this test a bit
    of an integration test, as opposed to testing every individual method by
    itself.
    """

    rapt_token = 'encoded_proof_of_reauth_token'
    correct_password = 'correct_password'
    oauth_api_url = 'http://some_url.com'
    client_id = 'some_id'
    client_secret = 'some_secret'

    def _request_mock_side_effect(self, *args, **kwargs):
        """Helper function to respond with valid requests as if a real server.

        This is the helper function for mocking HTTP calls. The calls that should
        end up here are to the oauth2 API or to the reauth API. The order of ifs
        tries to mimic the real order that the requests are expected, but we do not
        enforce a particular order so it can be more general.

        Args:
          *args: Every arg passed to a request.
          **kwargs: Every keyed arg passed to a request.

        Returns:
          (str, str), Mocked (headers, content)

        Raises:
          Exception: In case this function doesn't know how to mock a request.
        """

        # Requests to oauth2 have the body urlencoded.
        # Requests to reauth have a JSON body.
        # Try to decode both and use as needed.
        qp = dict(urllib.parse.parse_qsl(kwargs['body']))
        try:
            qp_json = json.loads(kwargs['body'])
        except ValueError:
            qp_json = {}

        uri = kwargs['uri'] if 'uri' in kwargs else args[0]

        # First call to oauth2 has REAUTH_SCOPE and returns an access token.
        if ((uri == self.oauth_api_url and
             qp.get('scope') == reauth._REAUTH_SCOPE)):
            return _ok_response, json.dumps({'access_token': 'access_token_for_reauth'})

        # Initialization call for reauth, serve first challenge
        if uri == (_reauth_client._REAUTH_API + ':start'):
            return None, json.dumps({
                'status': 'CHALLENGE_REQUIRED',
                'sessionId': 'session_id_1',
                'challenges': [{
                    'status': 'READY',
                    'challengeId': 1,
                    'challengeType': 'PASSWORD',
                    'securityKey': {},
                }],
            })

        # Continuation call for reauth, check first challenge and serve the second
        if uri == (_reauth_client._REAUTH_API + '/session_id_1:continue'):
            self.assertEqual(1, qp_json.get('challengeId'))
            self.assertEqual('RESPOND', qp_json.get('action'))

            if (qp_json.get('proposalResponse', {}).get('credential')
                == self.correct_password):
                # We got a correct password, go to security key
                return None, json.dumps({
                    'status': 'CHALLENGE_REQUIRED',
                    'sessionId': 'session_id_2',
                    'challenges': [{
                        'status': 'READY',
                        'challengeId': 2,
                        'challengeType': 'SECURITY_KEY',
                        'securityKey': {
                            'applicationId': 'security_key_application_id',
                            'challenges': [{
                                'keyHandle': 'some_key',
                                'challenge': base64.urlsafe_b64encode(
                                    'some_challenge'.encode('ascii')).decode('ascii'),
                            }],
                        },
                    }],
                })
            else:
                # We got an incorrect password, ask again.
                # Normally, the sessionID should be different, but for keeping this
                # function simple, we are going to reuse session_id_1 to come back to
                # this if block.
                return None, json.dumps({
                    'status': 'CHALLENGE_PENDING',
                    'sessionId': 'session_id_1',
                    'challenges': [{
                        'status': 'READY',
                        'challengeId': 1,
                        'challengeType': 'PASSWORD',
                        'securityKey': {},
                    }],
                })

        # Continuation call for reauth, check second challenge and serve token
        if uri == (_reauth_client._REAUTH_API + '/session_id_2:continue'):
            self.assertEqual(2, qp_json.get('challengeId'))
            self.assertEqual('RESPOND', qp_json.get('action'))
            return None, json.dumps({
                'status': 'AUTHENTICATED',
                'sessionId': 'session_id_3',
                'encodedProofOfReauthToken': self.rapt_token,
            })

        raise Exception(
            'Unexpected call :/\nURL {0}\n{1}'.format(uri, kwargs['body']))

  # This U2F mock is made by looking into the implementation of the class and
  # making the minimum requirement to actually answer a challenge.
    class _U2FInterfaceMock(object):

        def Authenticate(self, unused_app_id, challenge, unused_registered_keys):
            client_data = model.ClientData(
                model.ClientData.TYP_AUTHENTICATION,
                challenge,
                'some_origin')
            return model.SignResponse('key_handle'.encode(), 'resp'.encode(), client_data)

    def _call_reauth(self, request_mock, scopes=None):
        if os.environ.get('SK_SIGNING_PLUGIN') is not None:
            raise unittest.SkipTest('unset SK_SIGNING_PLUGIN.')
        return reauth.get_rapt_token(
            request_mock,
            self.client_id,
            self.client_secret,
            'some_refresh_token',
            self.oauth_api_url,
            scopes=scopes)

    def StartPatch(self, *args, **kwargs):
        patcher = mock.patch(*args, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

  #######
  # Helper functions and classes above.
  # Actual tests below.
  #######

    def setUp(self):
        self.u2f_local_interface_mock = self.StartPatch(
            'pyu2f.u2f.GetLocalU2FInterface')
        self.u2f_local_interface_mock.return_value = self._U2FInterfaceMock()

        self.getpass_mock = self.StartPatch('getpass.getpass')
        self.getpass_mock.return_value = self.correct_password

        self.is_interactive_mock = self.StartPatch('sys.stdin')
        self.is_interactive_mock.isatty = lambda: True

    def testPassAndGnubbyReauth(self):
        with mock.patch('httplib2.Http.request',
                        side_effect = self._request_mock_side_effect) as request_mock:
            reauth_result = self._call_reauth(request_mock)
            self.assertEqual(self.rapt_token, reauth_result)
            self.assertEqual(4, request_mock.call_count)

    def testPassWithScopes(self):
        with mock.patch('httplib2.Http.request',
                        side_effect = self._request_mock_side_effect) as request_mock:
            reauth_result = self._call_reauth(request_mock, [
                'https://www.googleapis.com/auth/scope1',
                'https://www.googleapis.com/auth/scope2'])
            self.assertEqual(self.rapt_token, reauth_result)
            self.assertEqual(4, request_mock.call_count)

    def testIncorrectPassThenPassAndGnubbyReauth(self):
        with mock.patch('httplib2.Http.request',
                        side_effect = self._request_mock_side_effect) as request_mock:
            self.getpass_mock.return_value = None
            self.getpass_mock.side_effect = ['bad_pass', self.correct_password]
            reauth_result = self._call_reauth(request_mock)
            self.assertEqual(self.rapt_token, reauth_result)
            self.assertEqual(5, request_mock.call_count)

    def testNonInteractiveError(self):
        with mock.patch('httplib2.Http.request',
                        side_effect = self._request_mock_side_effect) as request_mock:
            self.is_interactive_mock.isatty = lambda: False
            with self.assertRaises(errors.ReauthUnattendedError):
                unused_reauth_result = self._call_reauth(request_mock)

    @mock.patch('google_reauth.challenges.AVAILABLE_CHALLENGES', {})
    def testChallengeNotSupported(self):
        with mock.patch('httplib2.Http.request',
                        side_effect = self._request_mock_side_effect) as request_mock:
            with self.assertRaises(errors.ReauthFailError):
                reauth_result = self._call_reauth(request_mock)
                self.assertEqual(self.rapt_token, reauth_result)
                self.assertEqual(4, request_mock.call_count)

    @mock.patch('google_reauth.challenges.PasswordChallenge.is_locally_eligible', False)
    def testChallengeNotEligible(self):
        with mock.patch('httplib2.Http.request',
                        side_effect = self._request_mock_side_effect) as request_mock:
            with self.assertRaises(errors.ReauthFailError):
                reauth_result = self._call_reauth(request_mock)
                self.assertEqual(self.rapt_token, reauth_result)
                self.assertEqual(4, request_mock.call_count)

    def accessTokenRefreshError(self, response, content):
        def side_effect(*args, **kwargs):
            uri = kwargs['uri'] if 'uri' in kwargs else args[0]
            if (uri == self.oauth_api_url):
                return response, content
            raise Exception(
                'Unexpected call :/\nURL {0}\n{1}'.format(uri, kwargs['body']))
        with mock.patch('httplib2.Http.request',
                        side_effect = side_effect) as request_mock:
            with self.assertRaises(errors.HttpAccessTokenRefreshError):
                reauth.refresh_access_token(
                    request_mock,
                    self.client_id,
                    self.client_secret,
                    'some_refresh_token',
                    self.oauth_api_url)
            self.assertEqual(1, request_mock.call_count)

    def testAccessTokenRefreshError(self):
        self.accessTokenRefreshError(_ok_response, "foo")
        self.accessTokenRefreshError(_error_response, "foo")
        self.accessTokenRefreshError(_error_response, json.dumps({
            'error': 'non_reauth_error'}))

    def reauthAccessTokenError(self, response, content):
        def side_effect(*args, **kwargs):
            qp = dict(urllib.parse.parse_qsl(kwargs['body']))
            try:
                qp_json = json.loads(kwargs['body'])
            except ValueError:
                qp_json = {}
            uri = kwargs['uri'] if 'uri' in kwargs else args[0]
            if ((uri == self.oauth_api_url and
                 qp.get('scope') == reauth._REAUTH_SCOPE)):
                return response, content
            raise Exception(
                'Unexpected call :/\nURL {0}\n{1}'.format(uri, kwargs['body']))
        with mock.patch('httplib2.Http.request',
                        side_effect = side_effect) as request_mock:
            with self.assertRaises(errors.ReauthAccessTokenRefreshError):
                reauth.get_rapt_token(
                    request_mock,
                    self.client_id,
                    self.client_secret,
                    'some_refresh_token',
                    self.oauth_api_url)
            self.assertEqual(1, request_mock.call_count)

    def testReauthAccessTokenError(self):
        self.reauthAccessTokenError(_ok_response, "foo")
        self.reauthAccessTokenError(_ok_response, json.dumps({}))
        self.reauthAccessTokenError(
            _error_response, json.dumps({'error': 'some error'}))

    def testResponseErrorMessage(self):
        self.assertEqual('Invalid response.',
            reauth._get_refresh_error_message({}))
        self.assertEqual('There was an error.',
            reauth._get_refresh_error_message({'error': 'There was an error.'}))
        self.assertEqual('There was an error: error description',
            reauth._get_refresh_error_message({
                'error': 'There was an error',
                'error_description': 'error description'}))

    def getChallengesError(self, content):
        def side_effect(*args, **kwargs):
            uri = kwargs['uri'] if 'uri' in kwargs else args[0]
            # First call to oauth2 has REAUTH_SCOPE and returns an access token.
            if ((uri == self.oauth_api_url)):
                return _ok_response, json.dumps({
                    'access_token': 'access_token_for_reauth'})

            # Initialization call for reauth, serve first challenge
            if uri == (_reauth_client._REAUTH_API + ':start'):
                return None, content

        with mock.patch('httplib2.Http.request',
                        side_effect = side_effect) as request_mock:
            with self.assertRaises(errors.ReauthAPIError) as e:
                reauth.get_rapt_token(
                    request_mock,
                    self.client_id,
                    self.client_secret,
                    'some_refresh_token',
                    self.oauth_api_url)
            self.assertEqual(2, request_mock.call_count)

    def testGetChallengesError(self):
        self.getChallengesError(json.dumps({'status': 'ERROR'}))
        self.getChallengesError(json.dumps({
            'error': {'message': 'Some error'}}))

    def testChallangeNotActivatedError(self):
        def side_effect(*args, **kwargs):
            uri = kwargs['uri'] if 'uri' in kwargs else args[0]
            # First call to oauth2 has REAUTH_SCOPE and returns an access token.
            if ((uri == self.oauth_api_url)):
                return _ok_response, json.dumps({
                    'access_token': 'access_token_for_reauth'})

            # Initialization call for reauth, serve first challenge
            if uri == (_reauth_client._REAUTH_API + ':start'):
                return None, json.dumps({
                    'status': 'CHALLENGE_REQUIRED',
                    'sessionId': 'session_id_1',
                    'challenges': [{
                        'status': 'NOT_READY',
                        'challengeId': 1,
                        'challengeType': 'PASSWORD'}]})

        request_mock = self.StartPatch('httplib2.Http.request')
        request_mock.side_effect = side_effect
        with self.assertRaises(errors.ReauthFailError) as e:
            reauth.get_rapt_token(
                request_mock,
                self.client_id,
                self.client_secret,
                'some_refresh_token',
                self.oauth_api_url,
                scopes=None)
        self.assertEqual(6, request_mock.call_count)

    @mock.patch('google_reauth.challenges.SecurityKeyChallenge.obtain_challenge_input', return_value = None)
    def testRetryOnNoUserInput(self, challenge_mock):
        with mock.patch('httplib2.Http.request',
                        side_effect = self._request_mock_side_effect) as request_mock:
            with self.assertRaises(errors.ReauthFailError):
                reauth_result = self._call_reauth(request_mock)
            self.assertEqual(7, request_mock.call_count)
