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

import pytest  # type: ignore

from google.auth import exceptions
from google.oauth2 import utils


CLIENT_ID = "username"
CLIENT_SECRET = "password"
# Base64 encoding of "username:password"
BASIC_AUTH_ENCODING = "dXNlcm5hbWU6cGFzc3dvcmQ="
# Base64 encoding of "username:"
BASIC_AUTH_ENCODING_SECRETLESS = "dXNlcm5hbWU6"


class AuthHandler(utils.OAuthClientAuthHandler):
    def __init__(self, client_auth=None):
        super(AuthHandler, self).__init__(client_auth)

    def apply_client_authentication_options(
        self, headers, request_body=None, bearer_token=None
    ):
        return super(AuthHandler, self).apply_client_authentication_options(
            headers, request_body, bearer_token
        )


class TestClientAuthentication(object):
    @classmethod
    def make_client_auth(cls, client_secret=None):
        return utils.ClientAuthentication(
            utils.ClientAuthType.basic, CLIENT_ID, client_secret
        )

    def test_initialization_with_client_secret(self):
        client_auth = self.make_client_auth(CLIENT_SECRET)

        assert client_auth.client_auth_type == utils.ClientAuthType.basic
        assert client_auth.client_id == CLIENT_ID
        assert client_auth.client_secret == CLIENT_SECRET

    def test_initialization_no_client_secret(self):
        client_auth = self.make_client_auth()

        assert client_auth.client_auth_type == utils.ClientAuthType.basic
        assert client_auth.client_id == CLIENT_ID
        assert client_auth.client_secret is None


class TestOAuthClientAuthHandler(object):
    CLIENT_AUTH_BASIC = utils.ClientAuthentication(
        utils.ClientAuthType.basic, CLIENT_ID, CLIENT_SECRET
    )
    CLIENT_AUTH_BASIC_SECRETLESS = utils.ClientAuthentication(
        utils.ClientAuthType.basic, CLIENT_ID
    )
    CLIENT_AUTH_REQUEST_BODY = utils.ClientAuthentication(
        utils.ClientAuthType.request_body, CLIENT_ID, CLIENT_SECRET
    )
    CLIENT_AUTH_REQUEST_BODY_SECRETLESS = utils.ClientAuthentication(
        utils.ClientAuthType.request_body, CLIENT_ID
    )

    @classmethod
    def make_oauth_client_auth_handler(cls, client_auth=None):
        return AuthHandler(client_auth)

    def test_apply_client_authentication_options_none(self):
        headers = {"Content-Type": "application/json"}
        request_body = {"foo": "bar"}
        auth_handler = self.make_oauth_client_auth_handler()

        auth_handler.apply_client_authentication_options(headers, request_body)

        assert headers == {"Content-Type": "application/json"}
        assert request_body == {"foo": "bar"}

    def test_apply_client_authentication_options_basic(self):
        headers = {"Content-Type": "application/json"}
        request_body = {"foo": "bar"}
        auth_handler = self.make_oauth_client_auth_handler(self.CLIENT_AUTH_BASIC)

        auth_handler.apply_client_authentication_options(headers, request_body)

        assert headers == {
            "Content-Type": "application/json",
            "Authorization": "Basic {}".format(BASIC_AUTH_ENCODING),
        }
        assert request_body == {"foo": "bar"}

    def test_apply_client_authentication_options_basic_nosecret(self):
        headers = {"Content-Type": "application/json"}
        request_body = {"foo": "bar"}
        auth_handler = self.make_oauth_client_auth_handler(
            self.CLIENT_AUTH_BASIC_SECRETLESS
        )

        auth_handler.apply_client_authentication_options(headers, request_body)

        assert headers == {
            "Content-Type": "application/json",
            "Authorization": "Basic {}".format(BASIC_AUTH_ENCODING_SECRETLESS),
        }
        assert request_body == {"foo": "bar"}

    def test_apply_client_authentication_options_request_body(self):
        headers = {"Content-Type": "application/json"}
        request_body = {"foo": "bar"}
        auth_handler = self.make_oauth_client_auth_handler(
            self.CLIENT_AUTH_REQUEST_BODY
        )

        auth_handler.apply_client_authentication_options(headers, request_body)

        assert headers == {"Content-Type": "application/json"}
        assert request_body == {
            "foo": "bar",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }

    def test_apply_client_authentication_options_request_body_nosecret(self):
        headers = {"Content-Type": "application/json"}
        request_body = {"foo": "bar"}
        auth_handler = self.make_oauth_client_auth_handler(
            self.CLIENT_AUTH_REQUEST_BODY_SECRETLESS
        )

        auth_handler.apply_client_authentication_options(headers, request_body)

        assert headers == {"Content-Type": "application/json"}
        assert request_body == {
            "foo": "bar",
            "client_id": CLIENT_ID,
            "client_secret": "",
        }

    def test_apply_client_authentication_options_request_body_no_body(self):
        headers = {"Content-Type": "application/json"}
        auth_handler = self.make_oauth_client_auth_handler(
            self.CLIENT_AUTH_REQUEST_BODY
        )

        with pytest.raises(exceptions.OAuthError) as excinfo:
            auth_handler.apply_client_authentication_options(headers)

        assert excinfo.match(r"HTTP request does not support request-body")

    def test_apply_client_authentication_options_bearer_token(self):
        bearer_token = "ACCESS_TOKEN"
        headers = {"Content-Type": "application/json"}
        request_body = {"foo": "bar"}
        auth_handler = self.make_oauth_client_auth_handler()

        auth_handler.apply_client_authentication_options(
            headers, request_body, bearer_token
        )

        assert headers == {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(bearer_token),
        }
        assert request_body == {"foo": "bar"}

    def test_apply_client_authentication_options_bearer_and_basic(self):
        bearer_token = "ACCESS_TOKEN"
        headers = {"Content-Type": "application/json"}
        request_body = {"foo": "bar"}
        auth_handler = self.make_oauth_client_auth_handler(self.CLIENT_AUTH_BASIC)

        auth_handler.apply_client_authentication_options(
            headers, request_body, bearer_token
        )

        # Bearer token should have higher priority.
        assert headers == {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(bearer_token),
        }
        assert request_body == {"foo": "bar"}

    def test_apply_client_authentication_options_bearer_and_request_body(self):
        bearer_token = "ACCESS_TOKEN"
        headers = {"Content-Type": "application/json"}
        request_body = {"foo": "bar"}
        auth_handler = self.make_oauth_client_auth_handler(
            self.CLIENT_AUTH_REQUEST_BODY
        )

        auth_handler.apply_client_authentication_options(
            headers, request_body, bearer_token
        )

        # Bearer token should have higher priority.
        assert headers == {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(bearer_token),
        }
        assert request_body == {"foo": "bar"}


def test__handle_error_response_code_only():
    error_resp = {"error": "unsupported_grant_type"}
    response_data = json.dumps(error_resp)

    with pytest.raises(exceptions.OAuthError) as excinfo:
        utils.handle_error_response(response_data)

    assert excinfo.match(r"Error code unsupported_grant_type")


def test__handle_error_response_code_description():
    error_resp = {
        "error": "unsupported_grant_type",
        "error_description": "The provided grant_type is unsupported",
    }
    response_data = json.dumps(error_resp)

    with pytest.raises(exceptions.OAuthError) as excinfo:
        utils.handle_error_response(response_data)

    assert excinfo.match(
        r"Error code unsupported_grant_type: The provided grant_type is unsupported"
    )


def test__handle_error_response_code_description_uri():
    error_resp = {
        "error": "unsupported_grant_type",
        "error_description": "The provided grant_type is unsupported",
        "error_uri": "https://tools.ietf.org/html/rfc6749",
    }
    response_data = json.dumps(error_resp)

    with pytest.raises(exceptions.OAuthError) as excinfo:
        utils.handle_error_response(response_data)

    assert excinfo.match(
        r"Error code unsupported_grant_type: The provided grant_type is unsupported - https://tools.ietf.org/html/rfc6749"
    )


def test__handle_error_response_non_json():
    response_data = "Oops, something wrong happened"

    with pytest.raises(exceptions.OAuthError) as excinfo:
        utils.handle_error_response(response_data)

    assert excinfo.match(r"Oops, something wrong happened")
