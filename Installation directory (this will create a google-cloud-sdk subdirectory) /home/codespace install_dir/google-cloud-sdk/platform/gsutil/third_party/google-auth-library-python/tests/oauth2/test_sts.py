# Copyright 2020 Google LLC
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

import json

import mock
import pytest  # type: ignore
from six.moves import http_client
from six.moves import urllib

from google.auth import exceptions
from google.auth import transport
from google.oauth2 import sts
from google.oauth2 import utils

CLIENT_ID = "username"
CLIENT_SECRET = "password"
# Base64 encoding of "username:password"
BASIC_AUTH_ENCODING = "dXNlcm5hbWU6cGFzc3dvcmQ="


class TestStsClient(object):
    GRANT_TYPE = "urn:ietf:params:oauth:grant-type:token-exchange"
    RESOURCE = "https://api.example.com/"
    AUDIENCE = "urn:example:cooperation-context"
    SCOPES = ["scope1", "scope2"]
    REQUESTED_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:access_token"
    SUBJECT_TOKEN = "HEADER.SUBJECT_TOKEN_PAYLOAD.SIGNATURE"
    SUBJECT_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:jwt"
    ACTOR_TOKEN = "HEADER.ACTOR_TOKEN_PAYLOAD.SIGNATURE"
    ACTOR_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:jwt"
    TOKEN_EXCHANGE_ENDPOINT = "https://example.com/token.oauth2"
    ADDON_HEADERS = {"x-client-version": "0.1.2"}
    ADDON_OPTIONS = {"additional": {"non-standard": ["options"], "other": "some-value"}}
    SUCCESS_RESPONSE = {
        "access_token": "ACCESS_TOKEN",
        "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "scope1 scope2",
    }
    SUCCESS_RESPONSE_WITH_REFRESH = {
        "access_token": "abc",
        "refresh_token": "xyz",
        "expires_in": 3600,
    }
    ERROR_RESPONSE = {
        "error": "invalid_request",
        "error_description": "Invalid subject token",
        "error_uri": "https://tools.ietf.org/html/rfc6749",
    }
    CLIENT_AUTH_BASIC = utils.ClientAuthentication(
        utils.ClientAuthType.basic, CLIENT_ID, CLIENT_SECRET
    )
    CLIENT_AUTH_REQUEST_BODY = utils.ClientAuthentication(
        utils.ClientAuthType.request_body, CLIENT_ID, CLIENT_SECRET
    )

    @classmethod
    def make_client(cls, client_auth=None):
        return sts.Client(cls.TOKEN_EXCHANGE_ENDPOINT, client_auth)

    @classmethod
    def make_mock_request(cls, data, status=http_client.OK):
        response = mock.create_autospec(transport.Response, instance=True)
        response.status = status
        response.data = json.dumps(data).encode("utf-8")

        request = mock.create_autospec(transport.Request)
        request.return_value = response

        return request

    @classmethod
    def assert_request_kwargs(cls, request_kwargs, headers, request_data):
        """Asserts the request was called with the expected parameters.
        """
        assert request_kwargs["url"] == cls.TOKEN_EXCHANGE_ENDPOINT
        assert request_kwargs["method"] == "POST"
        assert request_kwargs["headers"] == headers
        assert request_kwargs["body"] is not None
        body_tuples = urllib.parse.parse_qsl(request_kwargs["body"])
        for (k, v) in body_tuples:
            assert v.decode("utf-8") == request_data[k.decode("utf-8")]
        assert len(body_tuples) == len(request_data.keys())

    def test_exchange_token_full_success_without_auth(self):
        """Test token exchange success without client authentication using full
        parameters.
        """
        client = self.make_client()
        headers = self.ADDON_HEADERS.copy()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        request_data = {
            "grant_type": self.GRANT_TYPE,
            "resource": self.RESOURCE,
            "audience": self.AUDIENCE,
            "scope": " ".join(self.SCOPES),
            "requested_token_type": self.REQUESTED_TOKEN_TYPE,
            "subject_token": self.SUBJECT_TOKEN,
            "subject_token_type": self.SUBJECT_TOKEN_TYPE,
            "actor_token": self.ACTOR_TOKEN,
            "actor_token_type": self.ACTOR_TOKEN_TYPE,
            "options": urllib.parse.quote(json.dumps(self.ADDON_OPTIONS)),
        }
        request = self.make_mock_request(
            status=http_client.OK, data=self.SUCCESS_RESPONSE
        )

        response = client.exchange_token(
            request,
            self.GRANT_TYPE,
            self.SUBJECT_TOKEN,
            self.SUBJECT_TOKEN_TYPE,
            self.RESOURCE,
            self.AUDIENCE,
            self.SCOPES,
            self.REQUESTED_TOKEN_TYPE,
            self.ACTOR_TOKEN,
            self.ACTOR_TOKEN_TYPE,
            self.ADDON_OPTIONS,
            self.ADDON_HEADERS,
        )

        self.assert_request_kwargs(request.call_args[1], headers, request_data)
        assert response == self.SUCCESS_RESPONSE

    def test_exchange_token_partial_success_without_auth(self):
        """Test token exchange success without client authentication using
        partial (required only) parameters.
        """
        client = self.make_client()
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        request_data = {
            "grant_type": self.GRANT_TYPE,
            "audience": self.AUDIENCE,
            "requested_token_type": self.REQUESTED_TOKEN_TYPE,
            "subject_token": self.SUBJECT_TOKEN,
            "subject_token_type": self.SUBJECT_TOKEN_TYPE,
        }
        request = self.make_mock_request(
            status=http_client.OK, data=self.SUCCESS_RESPONSE
        )

        response = client.exchange_token(
            request,
            grant_type=self.GRANT_TYPE,
            subject_token=self.SUBJECT_TOKEN,
            subject_token_type=self.SUBJECT_TOKEN_TYPE,
            audience=self.AUDIENCE,
            requested_token_type=self.REQUESTED_TOKEN_TYPE,
        )

        self.assert_request_kwargs(request.call_args[1], headers, request_data)
        assert response == self.SUCCESS_RESPONSE

    def test_exchange_token_non200_without_auth(self):
        """Test token exchange without client auth responding with non-200 status.
        """
        client = self.make_client()
        request = self.make_mock_request(
            status=http_client.BAD_REQUEST, data=self.ERROR_RESPONSE
        )

        with pytest.raises(exceptions.OAuthError) as excinfo:
            client.exchange_token(
                request,
                self.GRANT_TYPE,
                self.SUBJECT_TOKEN,
                self.SUBJECT_TOKEN_TYPE,
                self.RESOURCE,
                self.AUDIENCE,
                self.SCOPES,
                self.REQUESTED_TOKEN_TYPE,
                self.ACTOR_TOKEN,
                self.ACTOR_TOKEN_TYPE,
                self.ADDON_OPTIONS,
                self.ADDON_HEADERS,
            )

        assert excinfo.match(
            r"Error code invalid_request: Invalid subject token - https://tools.ietf.org/html/rfc6749"
        )

    def test_exchange_token_full_success_with_basic_auth(self):
        """Test token exchange success with basic client authentication using full
        parameters.
        """
        client = self.make_client(self.CLIENT_AUTH_BASIC)
        headers = self.ADDON_HEADERS.copy()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        headers["Authorization"] = "Basic {}".format(BASIC_AUTH_ENCODING)
        request_data = {
            "grant_type": self.GRANT_TYPE,
            "resource": self.RESOURCE,
            "audience": self.AUDIENCE,
            "scope": " ".join(self.SCOPES),
            "requested_token_type": self.REQUESTED_TOKEN_TYPE,
            "subject_token": self.SUBJECT_TOKEN,
            "subject_token_type": self.SUBJECT_TOKEN_TYPE,
            "actor_token": self.ACTOR_TOKEN,
            "actor_token_type": self.ACTOR_TOKEN_TYPE,
            "options": urllib.parse.quote(json.dumps(self.ADDON_OPTIONS)),
        }
        request = self.make_mock_request(
            status=http_client.OK, data=self.SUCCESS_RESPONSE
        )

        response = client.exchange_token(
            request,
            self.GRANT_TYPE,
            self.SUBJECT_TOKEN,
            self.SUBJECT_TOKEN_TYPE,
            self.RESOURCE,
            self.AUDIENCE,
            self.SCOPES,
            self.REQUESTED_TOKEN_TYPE,
            self.ACTOR_TOKEN,
            self.ACTOR_TOKEN_TYPE,
            self.ADDON_OPTIONS,
            self.ADDON_HEADERS,
        )

        self.assert_request_kwargs(request.call_args[1], headers, request_data)
        assert response == self.SUCCESS_RESPONSE

    def test_exchange_token_partial_success_with_basic_auth(self):
        """Test token exchange success with basic client authentication using
        partial (required only) parameters.
        """
        client = self.make_client(self.CLIENT_AUTH_BASIC)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic {}".format(BASIC_AUTH_ENCODING),
        }
        request_data = {
            "grant_type": self.GRANT_TYPE,
            "audience": self.AUDIENCE,
            "requested_token_type": self.REQUESTED_TOKEN_TYPE,
            "subject_token": self.SUBJECT_TOKEN,
            "subject_token_type": self.SUBJECT_TOKEN_TYPE,
        }
        request = self.make_mock_request(
            status=http_client.OK, data=self.SUCCESS_RESPONSE
        )

        response = client.exchange_token(
            request,
            grant_type=self.GRANT_TYPE,
            subject_token=self.SUBJECT_TOKEN,
            subject_token_type=self.SUBJECT_TOKEN_TYPE,
            audience=self.AUDIENCE,
            requested_token_type=self.REQUESTED_TOKEN_TYPE,
        )

        self.assert_request_kwargs(request.call_args[1], headers, request_data)
        assert response == self.SUCCESS_RESPONSE

    def test_exchange_token_non200_with_basic_auth(self):
        """Test token exchange with basic client auth responding with non-200
        status.
        """
        client = self.make_client(self.CLIENT_AUTH_BASIC)
        request = self.make_mock_request(
            status=http_client.BAD_REQUEST, data=self.ERROR_RESPONSE
        )

        with pytest.raises(exceptions.OAuthError) as excinfo:
            client.exchange_token(
                request,
                self.GRANT_TYPE,
                self.SUBJECT_TOKEN,
                self.SUBJECT_TOKEN_TYPE,
                self.RESOURCE,
                self.AUDIENCE,
                self.SCOPES,
                self.REQUESTED_TOKEN_TYPE,
                self.ACTOR_TOKEN,
                self.ACTOR_TOKEN_TYPE,
                self.ADDON_OPTIONS,
                self.ADDON_HEADERS,
            )

        assert excinfo.match(
            r"Error code invalid_request: Invalid subject token - https://tools.ietf.org/html/rfc6749"
        )

    def test_exchange_token_full_success_with_reqbody_auth(self):
        """Test token exchange success with request body client authenticaiton
        using full parameters.
        """
        client = self.make_client(self.CLIENT_AUTH_REQUEST_BODY)
        headers = self.ADDON_HEADERS.copy()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        request_data = {
            "grant_type": self.GRANT_TYPE,
            "resource": self.RESOURCE,
            "audience": self.AUDIENCE,
            "scope": " ".join(self.SCOPES),
            "requested_token_type": self.REQUESTED_TOKEN_TYPE,
            "subject_token": self.SUBJECT_TOKEN,
            "subject_token_type": self.SUBJECT_TOKEN_TYPE,
            "actor_token": self.ACTOR_TOKEN,
            "actor_token_type": self.ACTOR_TOKEN_TYPE,
            "options": urllib.parse.quote(json.dumps(self.ADDON_OPTIONS)),
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
        request = self.make_mock_request(
            status=http_client.OK, data=self.SUCCESS_RESPONSE
        )

        response = client.exchange_token(
            request,
            self.GRANT_TYPE,
            self.SUBJECT_TOKEN,
            self.SUBJECT_TOKEN_TYPE,
            self.RESOURCE,
            self.AUDIENCE,
            self.SCOPES,
            self.REQUESTED_TOKEN_TYPE,
            self.ACTOR_TOKEN,
            self.ACTOR_TOKEN_TYPE,
            self.ADDON_OPTIONS,
            self.ADDON_HEADERS,
        )

        self.assert_request_kwargs(request.call_args[1], headers, request_data)
        assert response == self.SUCCESS_RESPONSE

    def test_exchange_token_partial_success_with_reqbody_auth(self):
        """Test token exchange success with request body client authentication
        using partial (required only) parameters.
        """
        client = self.make_client(self.CLIENT_AUTH_REQUEST_BODY)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        request_data = {
            "grant_type": self.GRANT_TYPE,
            "audience": self.AUDIENCE,
            "requested_token_type": self.REQUESTED_TOKEN_TYPE,
            "subject_token": self.SUBJECT_TOKEN,
            "subject_token_type": self.SUBJECT_TOKEN_TYPE,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
        request = self.make_mock_request(
            status=http_client.OK, data=self.SUCCESS_RESPONSE
        )

        response = client.exchange_token(
            request,
            grant_type=self.GRANT_TYPE,
            subject_token=self.SUBJECT_TOKEN,
            subject_token_type=self.SUBJECT_TOKEN_TYPE,
            audience=self.AUDIENCE,
            requested_token_type=self.REQUESTED_TOKEN_TYPE,
        )

        self.assert_request_kwargs(request.call_args[1], headers, request_data)
        assert response == self.SUCCESS_RESPONSE

    def test_exchange_token_non200_with_reqbody_auth(self):
        """Test token exchange with POST request body client auth responding
        with non-200 status.
        """
        client = self.make_client(self.CLIENT_AUTH_REQUEST_BODY)
        request = self.make_mock_request(
            status=http_client.BAD_REQUEST, data=self.ERROR_RESPONSE
        )

        with pytest.raises(exceptions.OAuthError) as excinfo:
            client.exchange_token(
                request,
                self.GRANT_TYPE,
                self.SUBJECT_TOKEN,
                self.SUBJECT_TOKEN_TYPE,
                self.RESOURCE,
                self.AUDIENCE,
                self.SCOPES,
                self.REQUESTED_TOKEN_TYPE,
                self.ACTOR_TOKEN,
                self.ACTOR_TOKEN_TYPE,
                self.ADDON_OPTIONS,
                self.ADDON_HEADERS,
            )

        assert excinfo.match(
            r"Error code invalid_request: Invalid subject token - https://tools.ietf.org/html/rfc6749"
        )

    def test_refresh_token_success(self):
        """Test refresh token with successful response."""
        client = self.make_client(self.CLIENT_AUTH_BASIC)
        request = self.make_mock_request(
            status=http_client.OK, data=self.SUCCESS_RESPONSE
        )

        response = client.refresh_token(request, "refreshtoken")

        headers = {
            "Authorization": "Basic dXNlcm5hbWU6cGFzc3dvcmQ=",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        request_data = {"grant_type": "refresh_token", "refresh_token": "refreshtoken"}
        self.assert_request_kwargs(request.call_args[1], headers, request_data)
        assert response == self.SUCCESS_RESPONSE

    def test_refresh_token_success_with_refresh(self):
        """Test refresh token with successful response."""
        client = self.make_client(self.CLIENT_AUTH_BASIC)
        request = self.make_mock_request(
            status=http_client.OK, data=self.SUCCESS_RESPONSE_WITH_REFRESH
        )

        response = client.refresh_token(request, "refreshtoken")

        headers = {
            "Authorization": "Basic dXNlcm5hbWU6cGFzc3dvcmQ=",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        request_data = {"grant_type": "refresh_token", "refresh_token": "refreshtoken"}
        self.assert_request_kwargs(request.call_args[1], headers, request_data)
        assert response == self.SUCCESS_RESPONSE_WITH_REFRESH

    def test_refresh_token_failure(self):
        """Test refresh token with failure response."""
        client = self.make_client(self.CLIENT_AUTH_BASIC)
        request = self.make_mock_request(
            status=http_client.BAD_REQUEST, data=self.ERROR_RESPONSE
        )

        with pytest.raises(exceptions.OAuthError) as excinfo:
            client.refresh_token(request, "refreshtoken")

        assert excinfo.match(
            r"Error code invalid_request: Invalid subject token - https://tools.ietf.org/html/rfc6749"
        )

    def test__make_request_success(self):
        """Test base method with successful response."""
        client = self.make_client(self.CLIENT_AUTH_BASIC)
        request = self.make_mock_request(
            status=http_client.OK, data=self.SUCCESS_RESPONSE
        )

        response = client._make_request(request, {"a": "b"}, {"c": "d"})

        headers = {
            "Authorization": "Basic dXNlcm5hbWU6cGFzc3dvcmQ=",
            "Content-Type": "application/x-www-form-urlencoded",
            "a": "b",
        }
        request_data = {"c": "d"}
        self.assert_request_kwargs(request.call_args[1], headers, request_data)
        assert response == self.SUCCESS_RESPONSE

    def test_make_request_failure(self):
        """Test refresh token with failure response."""
        client = self.make_client(self.CLIENT_AUTH_BASIC)
        request = self.make_mock_request(
            status=http_client.BAD_REQUEST, data=self.ERROR_RESPONSE
        )

        with pytest.raises(exceptions.OAuthError) as excinfo:
            client._make_request(request, {"a": "b"}, {"c": "d"})

        assert excinfo.match(
            r"Error code invalid_request: Invalid subject token - https://tools.ietf.org/html/rfc6749"
        )
