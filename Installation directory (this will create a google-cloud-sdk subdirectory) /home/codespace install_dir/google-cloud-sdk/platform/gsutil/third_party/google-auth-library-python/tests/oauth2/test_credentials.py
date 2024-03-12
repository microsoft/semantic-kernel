# Copyright 2016 Google LLC
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

import datetime
import json
import os
import pickle
import sys

import mock
import pytest  # type: ignore

from google.auth import _helpers
from google.auth import exceptions
from google.auth import transport
from google.oauth2 import credentials


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

AUTH_USER_JSON_FILE = os.path.join(DATA_DIR, "authorized_user.json")

with open(AUTH_USER_JSON_FILE, "r") as fh:
    AUTH_USER_INFO = json.load(fh)


class TestCredentials(object):
    TOKEN_URI = "https://example.com/oauth2/token"
    REFRESH_TOKEN = "refresh_token"
    RAPT_TOKEN = "rapt_token"
    CLIENT_ID = "client_id"
    CLIENT_SECRET = "client_secret"

    @classmethod
    def make_credentials(cls):
        return credentials.Credentials(
            token=None,
            refresh_token=cls.REFRESH_TOKEN,
            token_uri=cls.TOKEN_URI,
            client_id=cls.CLIENT_ID,
            client_secret=cls.CLIENT_SECRET,
            rapt_token=cls.RAPT_TOKEN,
            enable_reauth_refresh=True,
        )

    def test_default_state(self):
        credentials = self.make_credentials()
        assert not credentials.valid
        # Expiration hasn't been set yet
        assert not credentials.expired
        # Scopes aren't required for these credentials
        assert not credentials.requires_scopes
        # Test properties
        assert credentials.refresh_token == self.REFRESH_TOKEN
        assert credentials.token_uri == self.TOKEN_URI
        assert credentials.client_id == self.CLIENT_ID
        assert credentials.client_secret == self.CLIENT_SECRET
        assert credentials.rapt_token == self.RAPT_TOKEN
        assert credentials.refresh_handler is None

    def test_refresh_handler_setter_and_getter(self):
        scopes = ["email", "profile"]
        original_refresh_handler = mock.Mock(return_value=("ACCESS_TOKEN_1", None))
        updated_refresh_handler = mock.Mock(return_value=("ACCESS_TOKEN_2", None))
        creds = credentials.Credentials(
            token=None,
            refresh_token=None,
            token_uri=None,
            client_id=None,
            client_secret=None,
            rapt_token=None,
            scopes=scopes,
            default_scopes=None,
            refresh_handler=original_refresh_handler,
        )

        assert creds.refresh_handler is original_refresh_handler

        creds.refresh_handler = updated_refresh_handler

        assert creds.refresh_handler is updated_refresh_handler

        creds.refresh_handler = None

        assert creds.refresh_handler is None

    def test_invalid_refresh_handler(self):
        scopes = ["email", "profile"]
        with pytest.raises(TypeError) as excinfo:
            credentials.Credentials(
                token=None,
                refresh_token=None,
                token_uri=None,
                client_id=None,
                client_secret=None,
                rapt_token=None,
                scopes=scopes,
                default_scopes=None,
                refresh_handler=object(),
            )

        assert excinfo.match("The provided refresh_handler is not a callable or None.")

    @mock.patch("google.oauth2.reauth.refresh_grant", autospec=True)
    @mock.patch(
        "google.auth._helpers.utcnow",
        return_value=datetime.datetime.min + _helpers.REFRESH_THRESHOLD,
    )
    def test_refresh_success(self, unused_utcnow, refresh_grant):
        token = "token"
        new_rapt_token = "new_rapt_token"
        expiry = _helpers.utcnow() + datetime.timedelta(seconds=500)
        grant_response = {"id_token": mock.sentinel.id_token}
        refresh_grant.return_value = (
            # Access token
            token,
            # New refresh token
            None,
            # Expiry,
            expiry,
            # Extra data
            grant_response,
            # rapt_token
            new_rapt_token,
        )

        request = mock.create_autospec(transport.Request)
        credentials = self.make_credentials()

        # Refresh credentials
        credentials.refresh(request)

        # Check jwt grant call.
        refresh_grant.assert_called_with(
            request,
            self.TOKEN_URI,
            self.REFRESH_TOKEN,
            self.CLIENT_ID,
            self.CLIENT_SECRET,
            None,
            self.RAPT_TOKEN,
            True,
        )

        # Check that the credentials have the token and expiry
        assert credentials.token == token
        assert credentials.expiry == expiry
        assert credentials.id_token == mock.sentinel.id_token
        assert credentials.rapt_token == new_rapt_token

        # Check that the credentials are valid (have a token and are not
        # expired)
        assert credentials.valid

    def test_refresh_no_refresh_token(self):
        request = mock.create_autospec(transport.Request)
        credentials_ = credentials.Credentials(token=None, refresh_token=None)

        with pytest.raises(exceptions.RefreshError, match="necessary fields"):
            credentials_.refresh(request)

        request.assert_not_called()

    @mock.patch("google.oauth2.reauth.refresh_grant", autospec=True)
    @mock.patch(
        "google.auth._helpers.utcnow",
        return_value=datetime.datetime.min + _helpers.REFRESH_THRESHOLD,
    )
    def test_refresh_with_refresh_token_and_refresh_handler(
        self, unused_utcnow, refresh_grant
    ):
        token = "token"
        new_rapt_token = "new_rapt_token"
        expiry = _helpers.utcnow() + datetime.timedelta(seconds=500)
        grant_response = {"id_token": mock.sentinel.id_token}
        refresh_grant.return_value = (
            # Access token
            token,
            # New refresh token
            None,
            # Expiry,
            expiry,
            # Extra data
            grant_response,
            # rapt_token
            new_rapt_token,
        )

        refresh_handler = mock.Mock()
        request = mock.create_autospec(transport.Request)
        creds = credentials.Credentials(
            token=None,
            refresh_token=self.REFRESH_TOKEN,
            token_uri=self.TOKEN_URI,
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            rapt_token=self.RAPT_TOKEN,
            refresh_handler=refresh_handler,
        )

        # Refresh credentials
        creds.refresh(request)

        # Check jwt grant call.
        refresh_grant.assert_called_with(
            request,
            self.TOKEN_URI,
            self.REFRESH_TOKEN,
            self.CLIENT_ID,
            self.CLIENT_SECRET,
            None,
            self.RAPT_TOKEN,
            False,
        )

        # Check that the credentials have the token and expiry
        assert creds.token == token
        assert creds.expiry == expiry
        assert creds.id_token == mock.sentinel.id_token
        assert creds.rapt_token == new_rapt_token

        # Check that the credentials are valid (have a token and are not
        # expired)
        assert creds.valid

        # Assert refresh handler not called as the refresh token has
        # higher priority.
        refresh_handler.assert_not_called()

    @mock.patch("google.auth._helpers.utcnow", return_value=datetime.datetime.min)
    def test_refresh_with_refresh_handler_success_scopes(self, unused_utcnow):
        expected_expiry = datetime.datetime.min + datetime.timedelta(seconds=2800)
        refresh_handler = mock.Mock(return_value=("ACCESS_TOKEN", expected_expiry))
        scopes = ["email", "profile"]
        default_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        request = mock.create_autospec(transport.Request)
        creds = credentials.Credentials(
            token=None,
            refresh_token=None,
            token_uri=None,
            client_id=None,
            client_secret=None,
            rapt_token=None,
            scopes=scopes,
            default_scopes=default_scopes,
            refresh_handler=refresh_handler,
        )

        creds.refresh(request)

        assert creds.token == "ACCESS_TOKEN"
        assert creds.expiry == expected_expiry
        assert creds.valid
        assert not creds.expired
        # Confirm refresh handler called with the expected arguments.
        refresh_handler.assert_called_with(request, scopes=scopes)

    @mock.patch("google.auth._helpers.utcnow", return_value=datetime.datetime.min)
    def test_refresh_with_refresh_handler_success_default_scopes(self, unused_utcnow):
        expected_expiry = datetime.datetime.min + datetime.timedelta(seconds=2800)
        original_refresh_handler = mock.Mock(
            return_value=("UNUSED_TOKEN", expected_expiry)
        )
        refresh_handler = mock.Mock(return_value=("ACCESS_TOKEN", expected_expiry))
        default_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        request = mock.create_autospec(transport.Request)
        creds = credentials.Credentials(
            token=None,
            refresh_token=None,
            token_uri=None,
            client_id=None,
            client_secret=None,
            rapt_token=None,
            scopes=None,
            default_scopes=default_scopes,
            refresh_handler=original_refresh_handler,
        )

        # Test newly set refresh_handler is used instead of the original one.
        creds.refresh_handler = refresh_handler
        creds.refresh(request)

        assert creds.token == "ACCESS_TOKEN"
        assert creds.expiry == expected_expiry
        assert creds.valid
        assert not creds.expired
        # default_scopes should be used since no developer provided scopes
        # are provided.
        refresh_handler.assert_called_with(request, scopes=default_scopes)

    @mock.patch("google.auth._helpers.utcnow", return_value=datetime.datetime.min)
    def test_refresh_with_refresh_handler_invalid_token(self, unused_utcnow):
        expected_expiry = datetime.datetime.min + datetime.timedelta(seconds=2800)
        # Simulate refresh handler does not return a valid token.
        refresh_handler = mock.Mock(return_value=(None, expected_expiry))
        scopes = ["email", "profile"]
        default_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        request = mock.create_autospec(transport.Request)
        creds = credentials.Credentials(
            token=None,
            refresh_token=None,
            token_uri=None,
            client_id=None,
            client_secret=None,
            rapt_token=None,
            scopes=scopes,
            default_scopes=default_scopes,
            refresh_handler=refresh_handler,
        )

        with pytest.raises(
            exceptions.RefreshError, match="returned token is not a string"
        ):
            creds.refresh(request)

        assert creds.token is None
        assert creds.expiry is None
        assert not creds.valid
        # Confirm refresh handler called with the expected arguments.
        refresh_handler.assert_called_with(request, scopes=scopes)

    def test_refresh_with_refresh_handler_invalid_expiry(self):
        # Simulate refresh handler returns expiration time in an invalid unit.
        refresh_handler = mock.Mock(return_value=("TOKEN", 2800))
        scopes = ["email", "profile"]
        default_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        request = mock.create_autospec(transport.Request)
        creds = credentials.Credentials(
            token=None,
            refresh_token=None,
            token_uri=None,
            client_id=None,
            client_secret=None,
            rapt_token=None,
            scopes=scopes,
            default_scopes=default_scopes,
            refresh_handler=refresh_handler,
        )

        with pytest.raises(
            exceptions.RefreshError, match="returned expiry is not a datetime object"
        ):
            creds.refresh(request)

        assert creds.token is None
        assert creds.expiry is None
        assert not creds.valid
        # Confirm refresh handler called with the expected arguments.
        refresh_handler.assert_called_with(request, scopes=scopes)

    @mock.patch("google.auth._helpers.utcnow", return_value=datetime.datetime.min)
    def test_refresh_with_refresh_handler_expired_token(self, unused_utcnow):
        expected_expiry = datetime.datetime.min + _helpers.REFRESH_THRESHOLD
        # Simulate refresh handler returns an expired token.
        refresh_handler = mock.Mock(return_value=("TOKEN", expected_expiry))
        scopes = ["email", "profile"]
        default_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        request = mock.create_autospec(transport.Request)
        creds = credentials.Credentials(
            token=None,
            refresh_token=None,
            token_uri=None,
            client_id=None,
            client_secret=None,
            rapt_token=None,
            scopes=scopes,
            default_scopes=default_scopes,
            refresh_handler=refresh_handler,
        )

        with pytest.raises(exceptions.RefreshError, match="already expired"):
            creds.refresh(request)

        assert creds.token is None
        assert creds.expiry is None
        assert not creds.valid
        # Confirm refresh handler called with the expected arguments.
        refresh_handler.assert_called_with(request, scopes=scopes)

    @mock.patch("google.oauth2.reauth.refresh_grant", autospec=True)
    @mock.patch(
        "google.auth._helpers.utcnow",
        return_value=datetime.datetime.min + _helpers.REFRESH_THRESHOLD,
    )
    def test_credentials_with_scopes_requested_refresh_success(
        self, unused_utcnow, refresh_grant
    ):
        scopes = ["email", "profile"]
        default_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        token = "token"
        new_rapt_token = "new_rapt_token"
        expiry = _helpers.utcnow() + datetime.timedelta(seconds=500)
        grant_response = {"id_token": mock.sentinel.id_token, "scope": "email profile"}
        refresh_grant.return_value = (
            # Access token
            token,
            # New refresh token
            None,
            # Expiry,
            expiry,
            # Extra data
            grant_response,
            # rapt token
            new_rapt_token,
        )

        request = mock.create_autospec(transport.Request)
        creds = credentials.Credentials(
            token=None,
            refresh_token=self.REFRESH_TOKEN,
            token_uri=self.TOKEN_URI,
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            scopes=scopes,
            default_scopes=default_scopes,
            rapt_token=self.RAPT_TOKEN,
            enable_reauth_refresh=True,
        )

        # Refresh credentials
        creds.refresh(request)

        # Check jwt grant call.
        refresh_grant.assert_called_with(
            request,
            self.TOKEN_URI,
            self.REFRESH_TOKEN,
            self.CLIENT_ID,
            self.CLIENT_SECRET,
            scopes,
            self.RAPT_TOKEN,
            True,
        )

        # Check that the credentials have the token and expiry
        assert creds.token == token
        assert creds.expiry == expiry
        assert creds.id_token == mock.sentinel.id_token
        assert creds.has_scopes(scopes)
        assert creds.rapt_token == new_rapt_token
        assert creds.granted_scopes == scopes

        # Check that the credentials are valid (have a token and are not
        # expired.)
        assert creds.valid

    @mock.patch("google.oauth2.reauth.refresh_grant", autospec=True)
    @mock.patch(
        "google.auth._helpers.utcnow",
        return_value=datetime.datetime.min + _helpers.REFRESH_THRESHOLD,
    )
    def test_credentials_with_only_default_scopes_requested(
        self, unused_utcnow, refresh_grant
    ):
        default_scopes = ["email", "profile"]
        token = "token"
        new_rapt_token = "new_rapt_token"
        expiry = _helpers.utcnow() + datetime.timedelta(seconds=500)
        grant_response = {"id_token": mock.sentinel.id_token, "scope": "email profile"}
        refresh_grant.return_value = (
            # Access token
            token,
            # New refresh token
            None,
            # Expiry,
            expiry,
            # Extra data
            grant_response,
            # rapt token
            new_rapt_token,
        )

        request = mock.create_autospec(transport.Request)
        creds = credentials.Credentials(
            token=None,
            refresh_token=self.REFRESH_TOKEN,
            token_uri=self.TOKEN_URI,
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            default_scopes=default_scopes,
            rapt_token=self.RAPT_TOKEN,
            enable_reauth_refresh=True,
        )

        # Refresh credentials
        creds.refresh(request)

        # Check jwt grant call.
        refresh_grant.assert_called_with(
            request,
            self.TOKEN_URI,
            self.REFRESH_TOKEN,
            self.CLIENT_ID,
            self.CLIENT_SECRET,
            default_scopes,
            self.RAPT_TOKEN,
            True,
        )

        # Check that the credentials have the token and expiry
        assert creds.token == token
        assert creds.expiry == expiry
        assert creds.id_token == mock.sentinel.id_token
        assert creds.has_scopes(default_scopes)
        assert creds.rapt_token == new_rapt_token
        assert creds.granted_scopes == default_scopes

        # Check that the credentials are valid (have a token and are not
        # expired.)
        assert creds.valid

    @mock.patch("google.oauth2.reauth.refresh_grant", autospec=True)
    @mock.patch(
        "google.auth._helpers.utcnow",
        return_value=datetime.datetime.min + _helpers.REFRESH_THRESHOLD,
    )
    def test_credentials_with_scopes_returned_refresh_success(
        self, unused_utcnow, refresh_grant
    ):
        scopes = ["email", "profile"]
        token = "token"
        new_rapt_token = "new_rapt_token"
        expiry = _helpers.utcnow() + datetime.timedelta(seconds=500)
        grant_response = {"id_token": mock.sentinel.id_token, "scope": " ".join(scopes)}
        refresh_grant.return_value = (
            # Access token
            token,
            # New refresh token
            None,
            # Expiry,
            expiry,
            # Extra data
            grant_response,
            # rapt token
            new_rapt_token,
        )

        request = mock.create_autospec(transport.Request)
        creds = credentials.Credentials(
            token=None,
            refresh_token=self.REFRESH_TOKEN,
            token_uri=self.TOKEN_URI,
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            scopes=scopes,
            rapt_token=self.RAPT_TOKEN,
            enable_reauth_refresh=True,
        )

        # Refresh credentials
        creds.refresh(request)

        # Check jwt grant call.
        refresh_grant.assert_called_with(
            request,
            self.TOKEN_URI,
            self.REFRESH_TOKEN,
            self.CLIENT_ID,
            self.CLIENT_SECRET,
            scopes,
            self.RAPT_TOKEN,
            True,
        )

        # Check that the credentials have the token and expiry
        assert creds.token == token
        assert creds.expiry == expiry
        assert creds.id_token == mock.sentinel.id_token
        assert creds.has_scopes(scopes)
        assert creds.rapt_token == new_rapt_token
        assert creds.granted_scopes == scopes

        # Check that the credentials are valid (have a token and are not
        # expired.)
        assert creds.valid

    @mock.patch("google.oauth2.reauth.refresh_grant", autospec=True)
    @mock.patch(
        "google.auth._helpers.utcnow",
        return_value=datetime.datetime.min + _helpers.REFRESH_THRESHOLD,
    )
    def test_credentials_with_only_default_scopes_requested_different_granted_scopes(
        self, unused_utcnow, refresh_grant
    ):
        default_scopes = ["email", "profile"]
        token = "token"
        new_rapt_token = "new_rapt_token"
        expiry = _helpers.utcnow() + datetime.timedelta(seconds=500)
        grant_response = {"id_token": mock.sentinel.id_token, "scope": "email"}
        refresh_grant.return_value = (
            # Access token
            token,
            # New refresh token
            None,
            # Expiry,
            expiry,
            # Extra data
            grant_response,
            # rapt token
            new_rapt_token,
        )

        request = mock.create_autospec(transport.Request)
        creds = credentials.Credentials(
            token=None,
            refresh_token=self.REFRESH_TOKEN,
            token_uri=self.TOKEN_URI,
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            default_scopes=default_scopes,
            rapt_token=self.RAPT_TOKEN,
            enable_reauth_refresh=True,
        )

        # Refresh credentials
        creds.refresh(request)

        # Check jwt grant call.
        refresh_grant.assert_called_with(
            request,
            self.TOKEN_URI,
            self.REFRESH_TOKEN,
            self.CLIENT_ID,
            self.CLIENT_SECRET,
            default_scopes,
            self.RAPT_TOKEN,
            True,
        )

        # Check that the credentials have the token and expiry
        assert creds.token == token
        assert creds.expiry == expiry
        assert creds.id_token == mock.sentinel.id_token
        assert creds.has_scopes(default_scopes)
        assert creds.rapt_token == new_rapt_token
        assert creds.granted_scopes == ["email"]

        # Check that the credentials are valid (have a token and are not
        # expired.)
        assert creds.valid

    @mock.patch("google.oauth2.reauth.refresh_grant", autospec=True)
    @mock.patch(
        "google.auth._helpers.utcnow",
        return_value=datetime.datetime.min + _helpers.REFRESH_THRESHOLD,
    )
    def test_credentials_with_scopes_refresh_different_granted_scopes(
        self, unused_utcnow, refresh_grant
    ):
        scopes = ["email", "profile"]
        scopes_returned = ["email"]
        token = "token"
        new_rapt_token = "new_rapt_token"
        expiry = _helpers.utcnow() + datetime.timedelta(seconds=500)
        grant_response = {
            "id_token": mock.sentinel.id_token,
            "scope": " ".join(scopes_returned),
        }
        refresh_grant.return_value = (
            # Access token
            token,
            # New refresh token
            None,
            # Expiry,
            expiry,
            # Extra data
            grant_response,
            # rapt token
            new_rapt_token,
        )

        request = mock.create_autospec(transport.Request)
        creds = credentials.Credentials(
            token=None,
            refresh_token=self.REFRESH_TOKEN,
            token_uri=self.TOKEN_URI,
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            scopes=scopes,
            rapt_token=self.RAPT_TOKEN,
            enable_reauth_refresh=True,
        )

        # Refresh credentials
        creds.refresh(request)

        # Check jwt grant call.
        refresh_grant.assert_called_with(
            request,
            self.TOKEN_URI,
            self.REFRESH_TOKEN,
            self.CLIENT_ID,
            self.CLIENT_SECRET,
            scopes,
            self.RAPT_TOKEN,
            True,
        )

        # Check that the credentials have the token and expiry
        assert creds.token == token
        assert creds.expiry == expiry
        assert creds.id_token == mock.sentinel.id_token
        assert creds.has_scopes(scopes)
        assert creds.rapt_token == new_rapt_token
        assert creds.granted_scopes == scopes_returned

        # Check that the credentials are valid (have a token and are not
        # expired.)
        assert creds.valid

    def test_apply_with_quota_project_id(self):
        creds = credentials.Credentials(
            token="token",
            refresh_token=self.REFRESH_TOKEN,
            token_uri=self.TOKEN_URI,
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            quota_project_id="quota-project-123",
        )

        headers = {}
        creds.apply(headers)
        assert headers["x-goog-user-project"] == "quota-project-123"
        assert "token" in headers["authorization"]

    def test_apply_with_no_quota_project_id(self):
        creds = credentials.Credentials(
            token="token",
            refresh_token=self.REFRESH_TOKEN,
            token_uri=self.TOKEN_URI,
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
        )

        headers = {}
        creds.apply(headers)
        assert "x-goog-user-project" not in headers
        assert "token" in headers["authorization"]

    def test_with_quota_project(self):
        creds = credentials.Credentials(
            token="token",
            refresh_token=self.REFRESH_TOKEN,
            token_uri=self.TOKEN_URI,
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            quota_project_id="quota-project-123",
        )

        new_creds = creds.with_quota_project("new-project-456")
        assert new_creds.quota_project_id == "new-project-456"
        headers = {}
        creds.apply(headers)
        assert "x-goog-user-project" in headers

    def test_with_token_uri(self):
        info = AUTH_USER_INFO.copy()

        creds = credentials.Credentials.from_authorized_user_info(info)
        new_token_uri = "https://oauth2-eu.googleapis.com/token"

        assert creds._token_uri == credentials._GOOGLE_OAUTH2_TOKEN_ENDPOINT

        creds_with_new_token_uri = creds.with_token_uri(new_token_uri)

        assert creds_with_new_token_uri._token_uri == new_token_uri

    def test_from_authorized_user_info(self):
        info = AUTH_USER_INFO.copy()

        creds = credentials.Credentials.from_authorized_user_info(info)
        assert creds.client_secret == info["client_secret"]
        assert creds.client_id == info["client_id"]
        assert creds.refresh_token == info["refresh_token"]
        assert creds.token_uri == credentials._GOOGLE_OAUTH2_TOKEN_ENDPOINT
        assert creds.scopes is None

        scopes = ["email", "profile"]
        creds = credentials.Credentials.from_authorized_user_info(info, scopes)
        assert creds.client_secret == info["client_secret"]
        assert creds.client_id == info["client_id"]
        assert creds.refresh_token == info["refresh_token"]
        assert creds.token_uri == credentials._GOOGLE_OAUTH2_TOKEN_ENDPOINT
        assert creds.scopes == scopes

        info["scopes"] = "email"  # single non-array scope from file
        creds = credentials.Credentials.from_authorized_user_info(info)
        assert creds.scopes == [info["scopes"]]

        info["scopes"] = ["email", "profile"]  # array scope from file
        creds = credentials.Credentials.from_authorized_user_info(info)
        assert creds.scopes == info["scopes"]

        expiry = datetime.datetime(2020, 8, 14, 15, 54, 1)
        info["expiry"] = expiry.isoformat() + "Z"
        creds = credentials.Credentials.from_authorized_user_info(info)
        assert creds.expiry == expiry
        assert creds.expired

    def test_from_authorized_user_file(self):
        info = AUTH_USER_INFO.copy()

        creds = credentials.Credentials.from_authorized_user_file(AUTH_USER_JSON_FILE)
        assert creds.client_secret == info["client_secret"]
        assert creds.client_id == info["client_id"]
        assert creds.refresh_token == info["refresh_token"]
        assert creds.token_uri == credentials._GOOGLE_OAUTH2_TOKEN_ENDPOINT
        assert creds.scopes is None
        assert creds.rapt_token is None

        scopes = ["email", "profile"]
        creds = credentials.Credentials.from_authorized_user_file(
            AUTH_USER_JSON_FILE, scopes
        )
        assert creds.client_secret == info["client_secret"]
        assert creds.client_id == info["client_id"]
        assert creds.refresh_token == info["refresh_token"]
        assert creds.token_uri == credentials._GOOGLE_OAUTH2_TOKEN_ENDPOINT
        assert creds.scopes == scopes

    def test_from_authorized_user_file_with_rapt_token(self):
        info = AUTH_USER_INFO.copy()
        file_path = os.path.join(DATA_DIR, "authorized_user_with_rapt_token.json")

        creds = credentials.Credentials.from_authorized_user_file(file_path)
        assert creds.client_secret == info["client_secret"]
        assert creds.client_id == info["client_id"]
        assert creds.refresh_token == info["refresh_token"]
        assert creds.token_uri == credentials._GOOGLE_OAUTH2_TOKEN_ENDPOINT
        assert creds.scopes is None
        assert creds.rapt_token == "rapt"

    def test_to_json(self):
        info = AUTH_USER_INFO.copy()
        expiry = datetime.datetime(2020, 8, 14, 15, 54, 1)
        info["expiry"] = expiry.isoformat() + "Z"
        creds = credentials.Credentials.from_authorized_user_info(info)
        assert creds.expiry == expiry

        # Test with no `strip` arg
        json_output = creds.to_json()
        json_asdict = json.loads(json_output)
        assert json_asdict.get("token") == creds.token
        assert json_asdict.get("refresh_token") == creds.refresh_token
        assert json_asdict.get("token_uri") == creds.token_uri
        assert json_asdict.get("client_id") == creds.client_id
        assert json_asdict.get("scopes") == creds.scopes
        assert json_asdict.get("client_secret") == creds.client_secret
        assert json_asdict.get("expiry") == info["expiry"]

        # Test with a `strip` arg
        json_output = creds.to_json(strip=["client_secret"])
        json_asdict = json.loads(json_output)
        assert json_asdict.get("token") == creds.token
        assert json_asdict.get("refresh_token") == creds.refresh_token
        assert json_asdict.get("token_uri") == creds.token_uri
        assert json_asdict.get("client_id") == creds.client_id
        assert json_asdict.get("scopes") == creds.scopes
        assert json_asdict.get("client_secret") is None

        # Test with no expiry
        creds.expiry = None
        json_output = creds.to_json()
        json_asdict = json.loads(json_output)
        assert json_asdict.get("expiry") is None

    def test_pickle_and_unpickle(self):
        creds = self.make_credentials()
        unpickled = pickle.loads(pickle.dumps(creds))

        # make sure attributes aren't lost during pickling
        assert list(creds.__dict__).sort() == list(unpickled.__dict__).sort()

        for attr in list(creds.__dict__):
            assert getattr(creds, attr) == getattr(unpickled, attr)

    def test_pickle_and_unpickle_with_refresh_handler(self):
        expected_expiry = _helpers.utcnow() + datetime.timedelta(seconds=2800)
        refresh_handler = mock.Mock(return_value=("TOKEN", expected_expiry))

        creds = credentials.Credentials(
            token=None,
            refresh_token=None,
            token_uri=None,
            client_id=None,
            client_secret=None,
            rapt_token=None,
            refresh_handler=refresh_handler,
        )
        unpickled = pickle.loads(pickle.dumps(creds))

        # make sure attributes aren't lost during pickling
        assert list(creds.__dict__).sort() == list(unpickled.__dict__).sort()

        for attr in list(creds.__dict__):
            # For the _refresh_handler property, the unpickled creds should be
            # set to None.
            if attr == "_refresh_handler":
                assert getattr(unpickled, attr) is None
            else:
                assert getattr(creds, attr) == getattr(unpickled, attr)

    def test_pickle_with_missing_attribute(self):
        creds = self.make_credentials()

        # remove an optional attribute before pickling
        # this mimics a pickle created with a previous class definition with
        # fewer attributes
        del creds.__dict__["_quota_project_id"]

        unpickled = pickle.loads(pickle.dumps(creds))

        # Attribute should be initialized by `__setstate__`
        assert unpickled.quota_project_id is None

    # pickles are not compatible across versions
    @pytest.mark.skipif(
        sys.version_info < (3, 5),
        reason="pickle file can only be loaded with Python >= 3.5",
    )
    def test_unpickle_old_credentials_pickle(self):
        # make sure a credentials file pickled with an older
        # library version (google-auth==1.5.1) can be unpickled
        with open(
            os.path.join(DATA_DIR, "old_oauth_credentials_py3.pickle"), "rb"
        ) as f:
            credentials = pickle.load(f)
            assert credentials.quota_project_id is None


class TestUserAccessTokenCredentials(object):
    def test_instance(self):
        cred = credentials.UserAccessTokenCredentials()
        assert cred._account is None

        cred = cred.with_account("account")
        assert cred._account == "account"

    @mock.patch("google.auth._cloud_sdk.get_auth_access_token", autospec=True)
    def test_refresh(self, get_auth_access_token):
        get_auth_access_token.return_value = "access_token"
        cred = credentials.UserAccessTokenCredentials()
        cred.refresh(None)
        assert cred.token == "access_token"

    def test_with_quota_project(self):
        cred = credentials.UserAccessTokenCredentials()
        quota_project_cred = cred.with_quota_project("project-foo")

        assert quota_project_cred._quota_project_id == "project-foo"
        assert quota_project_cred._account == cred._account

    @mock.patch(
        "google.oauth2.credentials.UserAccessTokenCredentials.apply", autospec=True
    )
    @mock.patch(
        "google.oauth2.credentials.UserAccessTokenCredentials.refresh", autospec=True
    )
    def test_before_request(self, refresh, apply):
        cred = credentials.UserAccessTokenCredentials()
        cred.before_request(mock.Mock(), "GET", "https://example.com", {})
        refresh.assert_called()
        apply.assert_called()
