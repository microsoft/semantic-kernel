# Copyright 2021 Google LLC
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
import sys

import mock
import pytest  # type: ignore
import pyu2f  # type: ignore

from google.auth import exceptions
from google.oauth2 import challenges


def test_get_user_password():
    with mock.patch("getpass.getpass", return_value="foo"):
        assert challenges.get_user_password("") == "foo"


def test_security_key():
    metadata = {
        "status": "READY",
        "challengeId": 2,
        "challengeType": "SECURITY_KEY",
        "securityKey": {
            "applicationId": "security_key_application_id",
            "challenges": [
                {
                    "keyHandle": "some_key",
                    "challenge": base64.urlsafe_b64encode(
                        "some_challenge".encode("ascii")
                    ).decode("ascii"),
                }
            ],
            "relyingPartyId": "security_key_application_id",
        },
    }
    mock_key = mock.Mock()

    challenge = challenges.SecurityKeyChallenge()

    # Test the case that security key challenge is passed with applicationId and
    # relyingPartyId the same.
    with mock.patch("pyu2f.model.RegisteredKey", return_value=mock_key):
        with mock.patch(
            "pyu2f.convenience.authenticator.CompositeAuthenticator.Authenticate"
        ) as mock_authenticate:
            mock_authenticate.return_value = "security key response"
            assert challenge.name == "SECURITY_KEY"
            assert challenge.is_locally_eligible
            assert challenge.obtain_challenge_input(metadata) == {
                "securityKey": "security key response"
            }
            mock_authenticate.assert_called_with(
                "security_key_application_id",
                [{"key": mock_key, "challenge": b"some_challenge"}],
                print_callback=sys.stderr.write,
            )

    # Test the case that security key challenge is passed with applicationId and
    # relyingPartyId different, first call works.
    metadata["securityKey"]["relyingPartyId"] = "security_key_relying_party_id"
    sys.stderr.write("metadata=" + str(metadata) + "\n")
    with mock.patch("pyu2f.model.RegisteredKey", return_value=mock_key):
        with mock.patch(
            "pyu2f.convenience.authenticator.CompositeAuthenticator.Authenticate"
        ) as mock_authenticate:
            mock_authenticate.return_value = "security key response"
            assert challenge.name == "SECURITY_KEY"
            assert challenge.is_locally_eligible
            assert challenge.obtain_challenge_input(metadata) == {
                "securityKey": "security key response"
            }
            mock_authenticate.assert_called_with(
                "security_key_relying_party_id",
                [{"key": mock_key, "challenge": b"some_challenge"}],
                print_callback=sys.stderr.write,
            )

    # Test the case that security key challenge is passed with applicationId and
    # relyingPartyId different, first call fails, requires retry.
    metadata["securityKey"]["relyingPartyId"] = "security_key_relying_party_id"
    with mock.patch("pyu2f.model.RegisteredKey", return_value=mock_key):
        with mock.patch(
            "pyu2f.convenience.authenticator.CompositeAuthenticator.Authenticate"
        ) as mock_authenticate:
            assert challenge.name == "SECURITY_KEY"
            assert challenge.is_locally_eligible
            mock_authenticate.side_effect = [
                pyu2f.errors.U2FError(pyu2f.errors.U2FError.DEVICE_INELIGIBLE),
                "security key response",
            ]
            assert challenge.obtain_challenge_input(metadata) == {
                "securityKey": "security key response"
            }
            calls = [
                mock.call(
                    "security_key_relying_party_id",
                    [{"key": mock_key, "challenge": b"some_challenge"}],
                    print_callback=sys.stderr.write,
                ),
                mock.call(
                    "security_key_application_id",
                    [{"key": mock_key, "challenge": b"some_challenge"}],
                    print_callback=sys.stderr.write,
                ),
            ]
            mock_authenticate.assert_has_calls(calls)

    # Test various types of exceptions.
    with mock.patch("pyu2f.model.RegisteredKey", return_value=mock_key):
        with mock.patch(
            "pyu2f.convenience.authenticator.CompositeAuthenticator.Authenticate"
        ) as mock_authenticate:
            mock_authenticate.side_effect = pyu2f.errors.U2FError(
                pyu2f.errors.U2FError.DEVICE_INELIGIBLE
            )
            assert challenge.obtain_challenge_input(metadata) is None

        with mock.patch(
            "pyu2f.convenience.authenticator.CompositeAuthenticator.Authenticate"
        ) as mock_authenticate:
            mock_authenticate.side_effect = pyu2f.errors.U2FError(
                pyu2f.errors.U2FError.TIMEOUT
            )
            assert challenge.obtain_challenge_input(metadata) is None

        with mock.patch(
            "pyu2f.convenience.authenticator.CompositeAuthenticator.Authenticate"
        ) as mock_authenticate:
            mock_authenticate.side_effect = pyu2f.errors.PluginError()
            assert challenge.obtain_challenge_input(metadata) is None

        with mock.patch(
            "pyu2f.convenience.authenticator.CompositeAuthenticator.Authenticate"
        ) as mock_authenticate:
            mock_authenticate.side_effect = pyu2f.errors.U2FError(
                pyu2f.errors.U2FError.BAD_REQUEST
            )
            with pytest.raises(pyu2f.errors.U2FError):
                challenge.obtain_challenge_input(metadata)

        with mock.patch(
            "pyu2f.convenience.authenticator.CompositeAuthenticator.Authenticate"
        ) as mock_authenticate:
            mock_authenticate.side_effect = pyu2f.errors.NoDeviceFoundError()
            assert challenge.obtain_challenge_input(metadata) is None

        with mock.patch(
            "pyu2f.convenience.authenticator.CompositeAuthenticator.Authenticate"
        ) as mock_authenticate:
            mock_authenticate.side_effect = pyu2f.errors.UnsupportedVersionException()
            with pytest.raises(pyu2f.errors.UnsupportedVersionException):
                challenge.obtain_challenge_input(metadata)

        with mock.patch.dict("sys.modules"):
            sys.modules["pyu2f"] = None
            with pytest.raises(exceptions.ReauthFailError) as excinfo:
                challenge.obtain_challenge_input(metadata)
            assert excinfo.match(r"pyu2f dependency is required")


@mock.patch("getpass.getpass", return_value="foo")
def test_password_challenge(getpass_mock):
    challenge = challenges.PasswordChallenge()

    with mock.patch("getpass.getpass", return_value="foo"):
        assert challenge.is_locally_eligible
        assert challenge.name == "PASSWORD"
        assert challenges.PasswordChallenge().obtain_challenge_input({}) == {
            "credential": "foo"
        }

    with mock.patch("getpass.getpass", return_value=None):
        assert challenges.PasswordChallenge().obtain_challenge_input({}) == {
            "credential": " "
        }


def test_saml_challenge():
    challenge = challenges.SamlChallenge()
    assert challenge.is_locally_eligible
    assert challenge.name == "SAML"
    with pytest.raises(exceptions.ReauthSamlChallengeFailError):
        challenge.obtain_challenge_input(None)
