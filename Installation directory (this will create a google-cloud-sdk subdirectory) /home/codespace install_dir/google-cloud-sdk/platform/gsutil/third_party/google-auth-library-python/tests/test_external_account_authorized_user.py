# Copyright 2022 Google LLC
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

import mock
import pytest  # type: ignore
from six.moves import http_client

from google.auth import exceptions
from google.auth import external_account_authorized_user
from google.auth import transport

TOKEN_URL = "https://sts.googleapis.com/v1/token"
TOKEN_INFO_URL = "https://sts.googleapis.com/v1/introspect"
REVOKE_URL = "https://sts.googleapis.com/v1/revoke"
PROJECT_NUMBER = "123456"
QUOTA_PROJECT_ID = "654321"
POOL_ID = "POOL_ID"
PROVIDER_ID = "PROVIDER_ID"
AUDIENCE = (
    "//iam.googleapis.com/projects/{}"
    "/locations/global/workloadIdentityPools/{}"
    "/providers/{}"
).format(PROJECT_NUMBER, POOL_ID, PROVIDER_ID)
REFRESH_TOKEN = "REFRESH_TOKEN"
NEW_REFRESH_TOKEN = "NEW_REFRESH_TOKEN"
ACCESS_TOKEN = "ACCESS_TOKEN"
CLIENT_ID = "username"
CLIENT_SECRET = "password"
# Base64 encoding of "username:password".
BASIC_AUTH_ENCODING = "dXNlcm5hbWU6cGFzc3dvcmQ="
SCOPES = ["email", "profile"]
NOW = datetime.datetime(1990, 8, 27, 6, 54, 30)


class TestCredentials(object):
    @classmethod
    def make_credentials(
        cls,
        audience=AUDIENCE,
        refresh_token=REFRESH_TOKEN,
        token_url=TOKEN_URL,
        token_info_url=TOKEN_INFO_URL,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        **kwargs
    ):
        return external_account_authorized_user.Credentials(
            audience=audience,
            refresh_token=refresh_token,
            token_url=token_url,
            token_info_url=token_info_url,
            client_id=client_id,
            client_secret=client_secret,
            **kwargs
        )

    @classmethod
    def make_mock_request(cls, status=http_client.OK, data=None):
        # STS token exchange request.
        token_response = mock.create_autospec(transport.Response, instance=True)
        token_response.status = status
        token_response.data = json.dumps(data).encode("utf-8")
        responses = [token_response]

        request = mock.create_autospec(transport.Request)
        request.side_effect = responses

        return request

    def test_default_state(self):
        creds = self.make_credentials()

        assert not creds.expiry
        assert not creds.expired
        assert not creds.token
        assert not creds.valid
        assert not creds.requires_scopes
        assert not creds.scopes
        assert not creds.revoke_url
        assert creds.token_info_url
        assert creds.client_id
        assert creds.client_secret
        assert creds.is_user
        assert creds.refresh_token == REFRESH_TOKEN
        assert creds.audience == AUDIENCE
        assert creds.token_url == TOKEN_URL

    def test_basic_create(self):
        creds = external_account_authorized_user.Credentials(
            token=ACCESS_TOKEN,
            expiry=datetime.datetime.max,
            scopes=SCOPES,
            revoke_url=REVOKE_URL,
        )

        assert creds.expiry == datetime.datetime.max
        assert not creds.expired
        assert creds.token == ACCESS_TOKEN
        assert creds.valid
        assert not creds.requires_scopes
        assert creds.scopes == SCOPES
        assert creds.is_user
        assert creds.revoke_url == REVOKE_URL

    def test_stunted_create_no_refresh_token(self):
        with pytest.raises(ValueError) as excinfo:
            self.make_credentials(token=None, refresh_token=None)

        assert excinfo.match(
            r"Token should be created with fields to make it valid \(`token` and "
            r"`expiry`\), or fields to allow it to refresh \(`refresh_token`, "
            r"`token_url`, `client_id`, `client_secret`\)\."
        )

    def test_stunted_create_no_token_url(self):
        with pytest.raises(ValueError) as excinfo:
            self.make_credentials(token=None, token_url=None)

        assert excinfo.match(
            r"Token should be created with fields to make it valid \(`token` and "
            r"`expiry`\), or fields to allow it to refresh \(`refresh_token`, "
            r"`token_url`, `client_id`, `client_secret`\)\."
        )

    def test_stunted_create_no_client_id(self):
        with pytest.raises(ValueError) as excinfo:
            self.make_credentials(token=None, client_id=None)

        assert excinfo.match(
            r"Token should be created with fields to make it valid \(`token` and "
            r"`expiry`\), or fields to allow it to refresh \(`refresh_token`, "
            r"`token_url`, `client_id`, `client_secret`\)\."
        )

    def test_stunted_create_no_client_secret(self):
        with pytest.raises(ValueError) as excinfo:
            self.make_credentials(token=None, client_secret=None)

        assert excinfo.match(
            r"Token should be created with fields to make it valid \(`token` and "
            r"`expiry`\), or fields to allow it to refresh \(`refresh_token`, "
            r"`token_url`, `client_id`, `client_secret`\)\."
        )

    @mock.patch("google.auth._helpers.utcnow", return_value=NOW)
    def test_refresh_auth_success(self, utcnow):
        request = self.make_mock_request(
            status=http_client.OK,
            data={"access_token": ACCESS_TOKEN, "expires_in": 3600},
        )
        creds = self.make_credentials()

        creds.refresh(request)

        assert creds.expiry == utcnow() + datetime.timedelta(seconds=3600)
        assert not creds.expired
        assert creds.token == ACCESS_TOKEN
        assert creds.valid
        assert not creds.requires_scopes
        assert creds.is_user
        assert creds._refresh_token == REFRESH_TOKEN

        request.assert_called_once_with(
            url=TOKEN_URL,
            method="POST",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": "Basic " + BASIC_AUTH_ENCODING,
            },
            body=("grant_type=refresh_token&refresh_token=" + REFRESH_TOKEN).encode(
                "UTF-8"
            ),
        )

    @mock.patch("google.auth._helpers.utcnow", return_value=NOW)
    def test_refresh_auth_success_new_refresh_token(self, utcnow):
        request = self.make_mock_request(
            status=http_client.OK,
            data={
                "access_token": ACCESS_TOKEN,
                "expires_in": 3600,
                "refresh_token": NEW_REFRESH_TOKEN,
            },
        )
        creds = self.make_credentials()

        creds.refresh(request)

        assert creds.expiry == utcnow() + datetime.timedelta(seconds=3600)
        assert not creds.expired
        assert creds.token == ACCESS_TOKEN
        assert creds.valid
        assert not creds.requires_scopes
        assert creds.is_user
        assert creds._refresh_token == NEW_REFRESH_TOKEN

        request.assert_called_once_with(
            url=TOKEN_URL,
            method="POST",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": "Basic " + BASIC_AUTH_ENCODING,
            },
            body=("grant_type=refresh_token&refresh_token=" + REFRESH_TOKEN).encode(
                "UTF-8"
            ),
        )

    def test_refresh_auth_failure(self):
        request = self.make_mock_request(
            status=http_client.BAD_REQUEST,
            data={
                "error": "invalid_request",
                "error_description": "Invalid subject token",
                "error_uri": "https://tools.ietf.org/html/rfc6749",
            },
        )
        creds = self.make_credentials()

        with pytest.raises(exceptions.OAuthError) as excinfo:
            creds.refresh(request)

        assert excinfo.match(
            r"Error code invalid_request: Invalid subject token - https://tools.ietf.org/html/rfc6749"
        )

        assert not creds.expiry
        assert not creds.expired
        assert not creds.token
        assert not creds.valid
        assert not creds.requires_scopes
        assert creds.is_user

        request.assert_called_once_with(
            url=TOKEN_URL,
            method="POST",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": "Basic " + BASIC_AUTH_ENCODING,
            },
            body=("grant_type=refresh_token&refresh_token=" + REFRESH_TOKEN).encode(
                "UTF-8"
            ),
        )

    def test_refresh_without_refresh_token(self):
        request = self.make_mock_request()
        creds = self.make_credentials(refresh_token=None, token=ACCESS_TOKEN)

        with pytest.raises(exceptions.RefreshError) as excinfo:
            creds.refresh(request)

        assert excinfo.match(
            r"The credentials do not contain the necessary fields need to refresh the access token. You must specify refresh_token, token_url, client_id, and client_secret."
        )

        assert not creds.expiry
        assert not creds.expired
        assert not creds.requires_scopes
        assert creds.is_user

        request.assert_not_called()

    def test_refresh_without_token_url(self):
        request = self.make_mock_request()
        creds = self.make_credentials(token_url=None, token=ACCESS_TOKEN)

        with pytest.raises(exceptions.RefreshError) as excinfo:
            creds.refresh(request)

        assert excinfo.match(
            r"The credentials do not contain the necessary fields need to refresh the access token. You must specify refresh_token, token_url, client_id, and client_secret."
        )

        assert not creds.expiry
        assert not creds.expired
        assert not creds.requires_scopes
        assert creds.is_user

        request.assert_not_called()

    def test_refresh_without_client_id(self):
        request = self.make_mock_request()
        creds = self.make_credentials(client_id=None, token=ACCESS_TOKEN)

        with pytest.raises(exceptions.RefreshError) as excinfo:
            creds.refresh(request)

        assert excinfo.match(
            r"The credentials do not contain the necessary fields need to refresh the access token. You must specify refresh_token, token_url, client_id, and client_secret."
        )

        assert not creds.expiry
        assert not creds.expired
        assert not creds.requires_scopes
        assert creds.is_user

        request.assert_not_called()

    def test_refresh_without_client_secret(self):
        request = self.make_mock_request()
        creds = self.make_credentials(client_secret=None, token=ACCESS_TOKEN)

        with pytest.raises(exceptions.RefreshError) as excinfo:
            creds.refresh(request)

        assert excinfo.match(
            r"The credentials do not contain the necessary fields need to refresh the access token. You must specify refresh_token, token_url, client_id, and client_secret."
        )

        assert not creds.expiry
        assert not creds.expired
        assert not creds.requires_scopes
        assert creds.is_user

        request.assert_not_called()

    def test_info(self):
        creds = self.make_credentials()
        info = creds.info

        assert info["audience"] == AUDIENCE
        assert info["refresh_token"] == REFRESH_TOKEN
        assert info["token_url"] == TOKEN_URL
        assert info["token_info_url"] == TOKEN_INFO_URL
        assert info["client_id"] == CLIENT_ID
        assert info["client_secret"] == CLIENT_SECRET
        assert "token" not in info
        assert "expiry" not in info
        assert "revoke_url" not in info
        assert "quota_project_id" not in info

    def test_info_full(self):
        creds = self.make_credentials(
            token=ACCESS_TOKEN,
            expiry=NOW,
            revoke_url=REVOKE_URL,
            quota_project_id=QUOTA_PROJECT_ID,
        )
        info = creds.info

        assert info["audience"] == AUDIENCE
        assert info["refresh_token"] == REFRESH_TOKEN
        assert info["token_url"] == TOKEN_URL
        assert info["token_info_url"] == TOKEN_INFO_URL
        assert info["client_id"] == CLIENT_ID
        assert info["client_secret"] == CLIENT_SECRET
        assert info["token"] == ACCESS_TOKEN
        assert info["expiry"] == NOW.isoformat() + "Z"
        assert info["revoke_url"] == REVOKE_URL
        assert info["quota_project_id"] == QUOTA_PROJECT_ID

    def test_to_json(self):
        creds = self.make_credentials()
        json_info = creds.to_json()
        info = json.loads(json_info)

        assert info["audience"] == AUDIENCE
        assert info["refresh_token"] == REFRESH_TOKEN
        assert info["token_url"] == TOKEN_URL
        assert info["token_info_url"] == TOKEN_INFO_URL
        assert info["client_id"] == CLIENT_ID
        assert info["client_secret"] == CLIENT_SECRET
        assert "token" not in info
        assert "expiry" not in info
        assert "revoke_url" not in info
        assert "quota_project_id" not in info

    def test_to_json_full(self):
        creds = self.make_credentials(
            token=ACCESS_TOKEN,
            expiry=NOW,
            revoke_url=REVOKE_URL,
            quota_project_id=QUOTA_PROJECT_ID,
        )
        json_info = creds.to_json()
        info = json.loads(json_info)

        assert info["audience"] == AUDIENCE
        assert info["refresh_token"] == REFRESH_TOKEN
        assert info["token_url"] == TOKEN_URL
        assert info["token_info_url"] == TOKEN_INFO_URL
        assert info["client_id"] == CLIENT_ID
        assert info["client_secret"] == CLIENT_SECRET
        assert info["token"] == ACCESS_TOKEN
        assert info["expiry"] == NOW.isoformat() + "Z"
        assert info["revoke_url"] == REVOKE_URL
        assert info["quota_project_id"] == QUOTA_PROJECT_ID

    def test_to_json_full_with_strip(self):
        creds = self.make_credentials(
            token=ACCESS_TOKEN,
            expiry=NOW,
            revoke_url=REVOKE_URL,
            quota_project_id=QUOTA_PROJECT_ID,
        )
        json_info = creds.to_json(strip=["token", "expiry"])
        info = json.loads(json_info)

        assert info["audience"] == AUDIENCE
        assert info["refresh_token"] == REFRESH_TOKEN
        assert info["token_url"] == TOKEN_URL
        assert info["token_info_url"] == TOKEN_INFO_URL
        assert info["client_id"] == CLIENT_ID
        assert info["client_secret"] == CLIENT_SECRET
        assert "token" not in info
        assert "expiry" not in info
        assert info["revoke_url"] == REVOKE_URL
        assert info["quota_project_id"] == QUOTA_PROJECT_ID

    def test_get_project_id(self):
        creds = self.make_credentials()
        request = mock.create_autospec(transport.Request)

        assert creds.get_project_id(request) is None
        request.assert_not_called()

    def test_with_quota_project(self):
        creds = self.make_credentials(
            token=ACCESS_TOKEN,
            expiry=NOW,
            revoke_url=REVOKE_URL,
            quota_project_id=QUOTA_PROJECT_ID,
        )
        new_creds = creds.with_quota_project(QUOTA_PROJECT_ID)
        assert new_creds._audience == creds._audience
        assert new_creds._refresh_token == creds._refresh_token
        assert new_creds._token_url == creds._token_url
        assert new_creds._token_info_url == creds._token_info_url
        assert new_creds._client_id == creds._client_id
        assert new_creds._client_secret == creds._client_secret
        assert new_creds.token == creds.token
        assert new_creds.expiry == creds.expiry
        assert new_creds._revoke_url == creds._revoke_url
        assert new_creds._quota_project_id == QUOTA_PROJECT_ID

    def test_with_token_uri(self):
        creds = self.make_credentials(
            token=ACCESS_TOKEN,
            expiry=NOW,
            revoke_url=REVOKE_URL,
            quota_project_id=QUOTA_PROJECT_ID,
        )
        new_creds = creds.with_token_uri("https://google.com")
        assert new_creds._audience == creds._audience
        assert new_creds._refresh_token == creds._refresh_token
        assert new_creds._token_url == "https://google.com"
        assert new_creds._token_info_url == creds._token_info_url
        assert new_creds._client_id == creds._client_id
        assert new_creds._client_secret == creds._client_secret
        assert new_creds.token == creds.token
        assert new_creds.expiry == creds.expiry
        assert new_creds._revoke_url == creds._revoke_url
        assert new_creds._quota_project_id == creds._quota_project_id

    def test_from_file_required_options_only(self, tmpdir):
        from_creds = self.make_credentials()
        config_file = tmpdir.join("config.json")
        config_file.write(from_creds.to_json())
        creds = external_account_authorized_user.Credentials.from_file(str(config_file))

        assert isinstance(creds, external_account_authorized_user.Credentials)
        assert creds.audience == AUDIENCE
        assert creds.refresh_token == REFRESH_TOKEN
        assert creds.token_url == TOKEN_URL
        assert creds.token_info_url == TOKEN_INFO_URL
        assert creds.client_id == CLIENT_ID
        assert creds.client_secret == CLIENT_SECRET
        assert creds.token is None
        assert creds.expiry is None
        assert creds.scopes is None
        assert creds._revoke_url is None
        assert creds._quota_project_id is None

    def test_from_file_full_options(self, tmpdir):
        from_creds = self.make_credentials(
            token=ACCESS_TOKEN,
            expiry=NOW,
            revoke_url=REVOKE_URL,
            quota_project_id=QUOTA_PROJECT_ID,
            scopes=SCOPES,
        )
        config_file = tmpdir.join("config.json")
        config_file.write(from_creds.to_json())
        creds = external_account_authorized_user.Credentials.from_file(str(config_file))

        assert isinstance(creds, external_account_authorized_user.Credentials)
        assert creds.audience == AUDIENCE
        assert creds.refresh_token == REFRESH_TOKEN
        assert creds.token_url == TOKEN_URL
        assert creds.token_info_url == TOKEN_INFO_URL
        assert creds.client_id == CLIENT_ID
        assert creds.client_secret == CLIENT_SECRET
        assert creds.token == ACCESS_TOKEN
        assert creds.expiry == NOW
        assert creds.scopes == SCOPES
        assert creds._revoke_url == REVOKE_URL
        assert creds._quota_project_id == QUOTA_PROJECT_ID
