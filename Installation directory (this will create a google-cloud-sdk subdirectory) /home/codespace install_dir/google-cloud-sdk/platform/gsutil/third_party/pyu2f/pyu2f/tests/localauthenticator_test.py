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

"""Tests for pyu2f.convenience.localauthenticator."""

import base64
import sys

import mock
from pyu2f import errors
from pyu2f import model
from pyu2f.convenience import localauthenticator


if sys.version_info[:2] < (2, 7):
  import unittest2 as unittest  # pylint: disable=g-import-not-at-top
else:
  import unittest  # pylint: disable=g-import-not-at-top


# Input/ouput values recorded from a successful signing flow
SIGN_SUCCESS = {
    'app_id': 'test_app_id',
    'app_id_hash_encoded': 'TnMguTdPn7OcIO9f-0CgfQdY254bvc6WR-DTPZnJ49w=',
    'challenge': b'asdfasdf',
    'challenge_hash_encoded': 'qhJtbTQvsU0BmLLpDWes-3zFGbegR2wp1mv5BJ2BwC0=',
    'key_handle_encoded': ('iBbl9-VYt-XSdWeHVNX-gfQcXGzlrAQ7BcngVNUxWijIQQlnZEI'
                           '4Vb0Bp2ydBCbIQu_5rNlKqPH6NK1TtnM7fA=='),
    'origin': 'test_origin',
    'signature_data_encoded': ('AQAAAI8wRQIhALlIPo6Hg8HwzELdYRIXnAnpsiHYCSXHex'
                               'CS34eiS2ixAiBt3TRmKE1A9WyMjc3JGrGI7gSPg-QzDSNL'
                               'aIj7JwcCTA=='),
    'client_data_encoded': ('eyJjaGFsbGVuZ2UiOiAiWVhOa1ptRnpaR1kiLCAib3JpZ2luI'
                            'jogInRlc3Rfb3JpZ2luIiwgInR5cCI6ICJuYXZpZ2F0b3IuaW'
                            'QuZ2V0QXNzZXJ0aW9uIn0='),
    'u2f_version': 'U2F_V2'
}
SIGN_SUCCESS['registered_key'] = model.RegisteredKey(
    base64.urlsafe_b64decode(SIGN_SUCCESS['key_handle_encoded']))
SIGN_SUCCESS['client_data'] = model.ClientData(
    model.ClientData.TYP_AUTHENTICATION,
    SIGN_SUCCESS['challenge'],
    SIGN_SUCCESS['origin'])


@mock.patch.object(sys, 'stderr', new=mock.MagicMock())
class LocalAuthenticatorTest(unittest.TestCase):

  @mock.patch.object(localauthenticator.u2f, 'GetLocalU2FInterface')
  def testSignSuccess(self, mock_get_u2f_method):
    """Test successful signing with a valid key."""
    # Prepare u2f mocks
    mock_u2f = mock.MagicMock()
    mock_get_u2f_method.return_value = mock_u2f

    mock_authenticate = mock.MagicMock()
    mock_u2f.Authenticate = mock_authenticate

    mock_authenticate.return_value = model.SignResponse(
        base64.urlsafe_b64decode(SIGN_SUCCESS['key_handle_encoded']),
        base64.urlsafe_b64decode(SIGN_SUCCESS['signature_data_encoded']),
        SIGN_SUCCESS['client_data']
    )

    # Call LocalAuthenticator
    challenge_data = [{'key': SIGN_SUCCESS['registered_key'],
                       'challenge': SIGN_SUCCESS['challenge']}]
    authenticator = localauthenticator.LocalAuthenticator('testorigin')
    self.assertTrue(authenticator.IsAvailable())
    response = authenticator.Authenticate(SIGN_SUCCESS['app_id'],
                                          challenge_data)

    # Validate that u2f authenticate was called with the correct values
    self.assertTrue(mock_authenticate.called)
    authenticate_args = mock_authenticate.call_args[0]
    self.assertEqual(len(authenticate_args), 3)
    self.assertEqual(authenticate_args[0], SIGN_SUCCESS['app_id'])
    self.assertEqual(authenticate_args[1], SIGN_SUCCESS['challenge'])
    registered_keys = authenticate_args[2]
    self.assertEqual(len(registered_keys), 1)
    self.assertEqual(registered_keys[0], SIGN_SUCCESS['registered_key'])

    # Validate authenticator response
    self.assertEquals(response.get('clientData'),
                      SIGN_SUCCESS['client_data_encoded'])
    self.assertEquals(response.get('signatureData'),
                      SIGN_SUCCESS['signature_data_encoded'])
    self.assertEquals(response.get('applicationId'),
                      SIGN_SUCCESS['app_id'])
    self.assertEquals(response.get('keyHandle'),
                      SIGN_SUCCESS['key_handle_encoded'])

  @mock.patch.object(localauthenticator.u2f, 'GetLocalU2FInterface')
  def testSignMultipleIneligible(self, mock_get_u2f_method):
    """Test signing with multiple keys registered, but none eligible."""
    # Prepare u2f mocks
    mock_u2f = mock.MagicMock()
    mock_get_u2f_method.return_value = mock_u2f

    mock_authenticate = mock.MagicMock()
    mock_u2f.Authenticate = mock_authenticate

    mock_authenticate.side_effect = errors.U2FError(
        errors.U2FError.DEVICE_INELIGIBLE)

    # Call LocalAuthenticator
    challenge_item = {'key': SIGN_SUCCESS['registered_key'],
                      'challenge': SIGN_SUCCESS['challenge']}
    challenge_data = [challenge_item, challenge_item]

    authenticator = localauthenticator.LocalAuthenticator('testorigin')

    with self.assertRaises(errors.U2FError) as cm:
      authenticator.Authenticate(SIGN_SUCCESS['app_id'],
                                 challenge_data)

    self.assertEquals(cm.exception.code, errors.U2FError.DEVICE_INELIGIBLE)

  @mock.patch.object(localauthenticator.u2f, 'GetLocalU2FInterface')
  def testSignMultipleSuccess(self, mock_get_u2f_method):
    """Test signing with multiple keys registered and one is eligible."""
    # Prepare u2f mocks
    mock_u2f = mock.MagicMock()
    mock_get_u2f_method.return_value = mock_u2f

    mock_authenticate = mock.MagicMock()
    mock_u2f.Authenticate = mock_authenticate

    return_value = model.SignResponse(
        base64.urlsafe_b64decode(SIGN_SUCCESS['key_handle_encoded']),
        base64.urlsafe_b64decode(SIGN_SUCCESS['signature_data_encoded']),
        SIGN_SUCCESS['client_data']
    )

    mock_authenticate.side_effect = [
        errors.U2FError(errors.U2FError.DEVICE_INELIGIBLE),
        return_value
    ]

    # Call LocalAuthenticator
    challenge_item = {'key': SIGN_SUCCESS['registered_key'],
                      'challenge': SIGN_SUCCESS['challenge']}
    challenge_data = [challenge_item, challenge_item]

    authenticator = localauthenticator.LocalAuthenticator('testorigin')
    response = authenticator.Authenticate(SIGN_SUCCESS['app_id'],
                                          challenge_data)

    # Validate that u2f authenticate was called with the correct values
    self.assertTrue(mock_authenticate.called)
    authenticate_args = mock_authenticate.call_args[0]
    self.assertEqual(len(authenticate_args), 3)
    self.assertEqual(authenticate_args[0], SIGN_SUCCESS['app_id'])
    self.assertEqual(authenticate_args[1], SIGN_SUCCESS['challenge'])
    registered_keys = authenticate_args[2]
    self.assertEqual(len(registered_keys), 1)
    self.assertEqual(registered_keys[0], SIGN_SUCCESS['registered_key'])

    # Validate authenticator response
    self.assertEquals(response.get('clientData'),
                      SIGN_SUCCESS['client_data_encoded'])
    self.assertEquals(response.get('signatureData'),
                      SIGN_SUCCESS['signature_data_encoded'])
    self.assertEquals(response.get('applicationId'),
                      SIGN_SUCCESS['app_id'])
    self.assertEquals(response.get('keyHandle'),
                      SIGN_SUCCESS['key_handle_encoded'])


if __name__ == '__main__':
  unittest.main()
