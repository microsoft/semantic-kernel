# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for pyu2f.convenience.customauthenticator."""

import base64
import json
import struct
import sys

import mock
from pyu2f import errors
from pyu2f import model
from pyu2f.convenience import customauthenticator


if sys.version_info[:2] < (2, 7):
  import unittest2 as unittest  # pylint: disable=g-import-not-at-top
else:
  import unittest  # pylint: disable=g-import-not-at-top


# Input/ouput values recorded from a successful signing flow
SIGN_SUCCESS = {
    'app_id': 'test_app_id',
    'app_id_hash_encoded': 'TnMguTdPn7OcIO9f-0CgfQdY254bvc6WR-DTPZnJ49w',
    'challenge': b'asdfasdf',
    'challenge_hash_encoded': 'qhJtbTQvsU0BmLLpDWes-3zFGbegR2wp1mv5BJ2BwC0',
    'key_handle_encoded': ('iBbl9-VYt-XSdWeHVNX-gfQcXGzlrAQ7BcngVNUxWijIQQlnZEI'
                           '4Vb0Bp2ydBCbIQu_5rNlKqPH6NK1TtnM7fA'),
    'origin': 'test_origin',
    'signature_data_encoded': ('AQAAAI8wRQIhALlIPo6Hg8HwzELdYRIXnAnpsiHYCSXHex'
                               'CS34eiS2ixAiBt3TRmKE1A9WyMjc3JGrGI7gSPg-QzDSNL'
                               'aIj7JwcCTA'),
    'client_data_encoded': ('eyJjaGFsbGVuZ2UiOiAiWVhOa1ptRnpaR1kiLCAib3JpZ2luI'
                            'jogInRlc3Rfb3JpZ2luIiwgInR5cCI6ICJuYXZpZ2F0b3IuaW'
                            'QuZ2V0QXNzZXJ0aW9uIn0'),
    'u2f_version': 'U2F_V2',
    'registered_key': model.RegisteredKey(base64.urlsafe_b64decode(
        'iBbl9-VYt-XSdWeHVNX-gfQcXGzlrAQ7BcngVNUxWijIQQlnZEI4Vb0Bp2ydBCbIQu'
        '_5rNlKqPH6NK1TtnM7fA=='
    ))
}


@mock.patch.object(sys, 'stderr', new=mock.MagicMock())
class CustomAuthenticatorTest(unittest.TestCase):

  @mock.patch.object(customauthenticator.os.environ, 'get', return_value=None)
  def testEnvVarNotSet(self, os_get_method):
    authenticator = customauthenticator.CustomAuthenticator('testorigin')

    self.assertFalse(authenticator.IsAvailable(),
                     'Should return false when no env var is present')

    # Assert exception if Authenticate is called when no env var is set
    with self.assertRaises(errors.PluginError):
      authenticator.Authenticate('appid', {})

  @mock.patch.object(customauthenticator.subprocess, 'Popen')
  @mock.patch.object(customauthenticator.os.environ, 'get',
                     return_value='gnubbyagent')
  def testSuccessAuthenticate(self, os_get_method, popen_method):
    """Test plugin Authenticate success."""
    valid_plugin_response = {
        'type': 'sign_helper_reply',
        'code': 0,
        'errorDetail': '',
        'responseData': {
            'appIdHash': SIGN_SUCCESS['app_id_hash_encoded'],
            'challengeHash': SIGN_SUCCESS['challenge_hash_encoded'],
            'keyHandle': SIGN_SUCCESS['key_handle_encoded'],
            'version': SIGN_SUCCESS['u2f_version'],
            'signatureData': SIGN_SUCCESS['signature_data_encoded']},
        'data': None
    }
    valid_plugin_response_json = json.dumps(valid_plugin_response).encode()
    valid_plugin_response_len = struct.pack('<I',
                                            len(valid_plugin_response_json))

    # process returns sign response in json
    mock_communicate_method = mock.MagicMock()
    mock_communicate_method.return_value = [valid_plugin_response_len +
                                            valid_plugin_response_json]

    # process returns with return code of 0
    mock_wait_method = mock.MagicMock()
    mock_wait_method.return_value = 0

    process_mock = mock.MagicMock()
    process_mock.communicate = mock_communicate_method
    process_mock.wait = mock_wait_method

    popen_method.return_value = process_mock

    # Call IsAvailable()
    authenticator = customauthenticator.CustomAuthenticator(
        SIGN_SUCCESS['origin'])

    self.assertTrue(authenticator.IsAvailable(),
                    'Should return true if env var is present')
    self.assertTrue(os_get_method.called)

    # Call Authenticate()
    challenge_data = [{'key': SIGN_SUCCESS['registered_key'],
                       'challenge': SIGN_SUCCESS['challenge']}]
    result = authenticator.Authenticate(SIGN_SUCCESS['app_id'], challenge_data)

    # Validate expected plugin request
    self.assertTrue(popen_method.called)

    self.assertTrue(mock_communicate_method.called)
    communicate_args = mock_communicate_method.call_args[0]
    self.assertEquals(len(communicate_args), 1,
                      'communicate() should have been called with two args')

    communicate_stdin = communicate_args[0]
    communicate_json_len_le = communicate_stdin[:4]
    communicate_json_len = struct.unpack('<I', communicate_json_len_le)[0]
    communicate_json = communicate_stdin[4:]
    self.assertEquals(len(communicate_json), communicate_json_len,
                      'communicate() should have been called with correct'
                      'length field')

    communicate_dict = json.loads(communicate_json)
    self.assertEquals(communicate_dict.get('type'), 'sign_helper_request')
    self.assertEquals(communicate_dict.get('timeoutSeconds'), 5)
    self.assertEquals(communicate_dict.get('localAlways'), True)
    challenges = communicate_dict.get('signData')

    # Validate Challenge portion of plugin request
    self.assertIsNotNone(challenges)
    self.assertEquals(len(challenges), 1)
    challenge = challenges[0]
    self.assertEquals(challenge.get('appIdHash'),
                      SIGN_SUCCESS['app_id_hash_encoded'])
    self.assertEquals(challenge.get('challengeHash'),
                      SIGN_SUCCESS['challenge_hash_encoded'])
    self.assertEquals(challenge.get('keyHandle'),
                      SIGN_SUCCESS['key_handle_encoded'])
    self.assertEquals(challenge.get('version'),
                      SIGN_SUCCESS['u2f_version'])

    mock_wait_method.assert_called_with()

    # Validate Authenticate() response
    self.assertEquals(result['applicationId'], SIGN_SUCCESS['app_id'])
    self.assertEquals(result['clientData'], SIGN_SUCCESS['client_data_encoded'])
    self.assertEquals(result['keyHandle'], SIGN_SUCCESS['key_handle_encoded'])
    self.assertEquals(result['signatureData'],
                      SIGN_SUCCESS['signature_data_encoded'])

  @mock.patch.object(customauthenticator.subprocess, 'Popen')
  @mock.patch.object(customauthenticator.os.environ, 'get',
                     return_value='gnubbyagent')
  def testPluginReturnsMalformedJson(self, os_get_method, popen_method):
    """Test when plugin returns non-json response."""
    plugin_response = b'abc'
    plugin_response_len = struct.pack('<I', len(plugin_response))

    # process returns sign response in json
    mock_communicate_method = mock.MagicMock()
    mock_communicate_method.return_value = [plugin_response_len +
                                            plugin_response]

    # process returns with return code of 0
    mock_wait_method = mock.MagicMock()
    mock_wait_method.return_value = 0

    process_mock = mock.MagicMock()
    process_mock.communicate = mock_communicate_method
    process_mock.wait = mock_wait_method

    popen_method.return_value = process_mock

    # Call Authenticate()
    challenge_data = [{'key': SIGN_SUCCESS['registered_key'],
                       'challenge': SIGN_SUCCESS['challenge']}]

    authenticator = customauthenticator.CustomAuthenticator(
        SIGN_SUCCESS['origin'])
    with self.assertRaises(errors.PluginError):
      authenticator.Authenticate(SIGN_SUCCESS['app_id'], challenge_data)

  @mock.patch.object(customauthenticator.subprocess, 'Popen')
  @mock.patch.object(customauthenticator.os.environ, 'get',
                     return_value='gnubbyagent')
  def testPluginResponseMissingType(self, os_get_method, popen_method):
    """Test when plugin response is missing sign_helper_reply type."""
    valid_plugin_response = {
        'errorDetail': '',
        'code': 0,
        'responseData': {
            'appIdHash': SIGN_SUCCESS['app_id_hash_encoded'],
            'challengeHash': SIGN_SUCCESS['challenge_hash_encoded'],
            'keyHandle': SIGN_SUCCESS['key_handle_encoded'],
            'version': SIGN_SUCCESS['u2f_version'],
            'signatureData': SIGN_SUCCESS['signature_data_encoded']},
        'data': None
    }
    plugin_response_json = json.dumps(valid_plugin_response).encode()
    plugin_response_len = struct.pack('<I', len(plugin_response_json))

    # process returns sign response in json
    mock_communicate_method = mock.MagicMock()
    mock_communicate_method.return_value = [plugin_response_len +
                                            plugin_response_json]

    # process returns with return code of 0
    mock_wait_method = mock.MagicMock()
    mock_wait_method.return_value = 0

    process_mock = mock.MagicMock()
    process_mock.communicate = mock_communicate_method
    process_mock.wait = mock_wait_method

    popen_method.return_value = process_mock

    # Call Authenticate()
    challenge_data = [{'key': SIGN_SUCCESS['registered_key'],
                       'challenge': SIGN_SUCCESS['challenge']}]

    authenticator = customauthenticator.CustomAuthenticator(
        SIGN_SUCCESS['origin'])
    with self.assertRaises(errors.PluginError):
      authenticator.Authenticate(SIGN_SUCCESS['app_id'], challenge_data)

  @mock.patch.object(customauthenticator.subprocess, 'Popen')
  @mock.patch.object(customauthenticator.os.environ, 'get',
                     return_value='gnubbyagent')
  def testPluginReturnsIncompleteResponse(self, os_get_method, popen_method):
    """Test when plugin response has missing fields."""
    valid_plugin_response = {
        'type': 'sign_helper_reply',
        'errorDetail': '',
        'responseData': {
            'appIdHash': SIGN_SUCCESS['app_id_hash_encoded'],
            'challengeHash': SIGN_SUCCESS['challenge_hash_encoded'],
            'keyHandle': SIGN_SUCCESS['key_handle_encoded'],
            'version': SIGN_SUCCESS['u2f_version'],
            'signatureData': SIGN_SUCCESS['signature_data_encoded']},
        'data': None
    }
    plugin_response_json = json.dumps(valid_plugin_response).encode()
    plugin_response_len = struct.pack('<I', len(plugin_response_json))

    # process returns sign response in json
    mock_communicate_method = mock.MagicMock()
    mock_communicate_method.return_value = [plugin_response_len +
                                            plugin_response_json]

    # process returns with return code of 0
    mock_wait_method = mock.MagicMock()
    mock_wait_method.return_value = 0

    process_mock = mock.MagicMock()
    process_mock.communicate = mock_communicate_method
    process_mock.wait = mock_wait_method

    popen_method.return_value = process_mock

    # Call Authenticate()
    challenge_data = [{'key': SIGN_SUCCESS['registered_key'],
                       'challenge': SIGN_SUCCESS['challenge']}]

    authenticator = customauthenticator.CustomAuthenticator(
        SIGN_SUCCESS['origin'])
    with self.assertRaises(errors.PluginError):
      authenticator.Authenticate(SIGN_SUCCESS['app_id'], challenge_data)

  @mock.patch.object(customauthenticator.subprocess, 'Popen')
  @mock.patch.object(customauthenticator.os.environ, 'get',
                     return_value='gnubbyagent')
  def testPluginReturnsTouchRequired(self, os_get_method, popen_method):
    """Test when plugin with error 'touch required'."""
    valid_plugin_response = {
        'type': 'sign_helper_reply',
        'errorDetail': '',
        'code': customauthenticator.SK_SIGNING_PLUGIN_TOUCH_REQUIRED,
        'responseData': {
            'appIdHash': SIGN_SUCCESS['app_id_hash_encoded'],
            'challengeHash': SIGN_SUCCESS['challenge_hash_encoded'],
            'keyHandle': SIGN_SUCCESS['key_handle_encoded'],
            'version': SIGN_SUCCESS['u2f_version'],
            'signatureData': SIGN_SUCCESS['signature_data_encoded']},
        'data': None
    }
    plugin_response_json = json.dumps(valid_plugin_response).encode()
    plugin_response_len = struct.pack('<I', len(plugin_response_json))

    # process returns sign response in json
    mock_communicate_method = mock.MagicMock()
    mock_communicate_method.return_value = [plugin_response_len +
                                            plugin_response_json]

    # process returns with return code of 0
    mock_wait_method = mock.MagicMock()
    mock_wait_method.return_value = 0

    process_mock = mock.MagicMock()
    process_mock.communicate = mock_communicate_method
    process_mock.wait = mock_wait_method

    popen_method.return_value = process_mock

    # Call Authenticate()
    challenge_data = [{'key': SIGN_SUCCESS['registered_key'],
                       'challenge': SIGN_SUCCESS['challenge']}]

    authenticator = customauthenticator.CustomAuthenticator(
        SIGN_SUCCESS['origin'])

    with self.assertRaises(errors.U2FError) as cm:
      authenticator.Authenticate(SIGN_SUCCESS['app_id'], challenge_data)
    self.assertEquals(cm.exception.code, errors.U2FError.TIMEOUT)

  @mock.patch.object(customauthenticator.subprocess, 'Popen')
  @mock.patch.object(customauthenticator.os.environ, 'get',
                     return_value='gnubbyagent')
  def testPluginReturnsWrongData(self, os_get_method, popen_method):
    """Test when plugin with error 'wrong data'."""
    valid_plugin_response = {
        'type': 'sign_helper_reply',
        'errorDetail': '',
        'code': customauthenticator.SK_SIGNING_PLUGIN_WRONG_DATA,
        'responseData': {
            'appIdHash': SIGN_SUCCESS['app_id_hash_encoded'],
            'challengeHash': SIGN_SUCCESS['challenge_hash_encoded'],
            'keyHandle': SIGN_SUCCESS['key_handle_encoded'],
            'version': SIGN_SUCCESS['u2f_version'],
            'signatureData': SIGN_SUCCESS['signature_data_encoded']},
        'data': None
    }
    plugin_response_json = json.dumps(valid_plugin_response).encode()
    plugin_response_len = struct.pack('<I', len(plugin_response_json))

    # process returns sign response in json
    mock_communicate_method = mock.MagicMock()
    mock_communicate_method.return_value = [plugin_response_len +
                                            plugin_response_json]

    # process returns with return code of 0
    mock_wait_method = mock.MagicMock()
    mock_wait_method.return_value = 0

    process_mock = mock.MagicMock()
    process_mock.communicate = mock_communicate_method
    process_mock.wait = mock_wait_method

    popen_method.return_value = process_mock

    # Call Authenticate()
    challenge_data = [{'key': SIGN_SUCCESS['registered_key'],
                       'challenge': SIGN_SUCCESS['challenge']}]

    authenticator = customauthenticator.CustomAuthenticator(
        SIGN_SUCCESS['origin'])

    with self.assertRaises(errors.U2FError) as cm:
      authenticator.Authenticate(SIGN_SUCCESS['app_id'], challenge_data)
    self.assertEquals(cm.exception.code, errors.U2FError.DEVICE_INELIGIBLE)


if __name__ == '__main__':
  unittest.main()
