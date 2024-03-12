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

from google_reauth import challenges, errors

import pyu2f


class _U2FInterfaceMock(object):
    def Authenticate(self, unused_app_id, challenge, unused_registered_keys):
        raise self.error


_u2f_interface_mock = _U2FInterfaceMock()


class ChallengesTest(unittest.TestCase):
    """This class contains tests for reauth challanges. """

    @mock.patch('pyu2f.u2f.GetLocalU2FInterface', return_value = _u2f_interface_mock)
    def testSecurityKeyError(self, u2f_mock):
        metadata = {
            'status': 'READY',
            'challengeId': 2,
            'challengeType': 'SECURITY_KEY',
            'securityKey': {
                'applicationId': 'security_key_application_id',
                'challenges': [{
                    'keyHandle': 'some_key',
                    'challenge': base64.urlsafe_b64encode(
                        'some_challenge'.encode('ascii')).decode('ascii'),
                }]
            }}

        challenge = challenges.SecurityKeyChallenge()

        _u2f_interface_mock.error = pyu2f.errors.U2FError(
            pyu2f.errors.U2FError.DEVICE_INELIGIBLE)
        self.assertEqual(None, challenge.obtain_challenge_input(metadata))

        _u2f_interface_mock.error = pyu2f.errors.U2FError(
            pyu2f.errors.U2FError.TIMEOUT)
        self.assertEqual(None, challenge.obtain_challenge_input(metadata))

        _u2f_interface_mock.error = pyu2f.errors.NoDeviceFoundError()
        self.assertEqual(None, challenge.obtain_challenge_input(metadata))

        _u2f_interface_mock.error = pyu2f.errors.U2FError(
            pyu2f.errors.U2FError.BAD_REQUEST)
        with self.assertRaises(pyu2f.errors.U2FError):
            challenge.obtain_challenge_input(metadata)

        _u2f_interface_mock.error = pyu2f.errors.UnsupportedVersionException()
        with self.assertRaises(pyu2f.errors.UnsupportedVersionException):
            challenge.obtain_challenge_input(metadata)

    @mock.patch('getpass.getpass', return_value = None)
    def testNoPassword(self, getpass_mock):
        self.assertEqual(challenges.PasswordChallenge().obtain_challenge_input({}),
            {'credential': ' '})

    def testSaml(self):
        metadata = {
            'status': 'READY',
            'challengeId': 1,
            'challengeType': 'SAML',
            'securityKey': {}
            }
        challenge = challenges.SamlChallenge()
        self.assertEqual(True, challenge.is_locally_eligible)
        with self.assertRaises(errors.ReauthSamlLoginRequiredError):
            challenge.obtain_challenge_input(metadata)
