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

import copy
import datetime
import json
import os

import mock
import pytest  # type: ignore
import requests
import six

from google.auth import exceptions
from google.auth import jwt
import google.auth.transport.requests
from google.oauth2 import gdch_credentials
from google.oauth2.gdch_credentials import ServiceAccountCredentials


class TestServiceAccountCredentials(object):
    AUDIENCE = "https://service-identity.<Domain>/authenticate"
    PROJECT = "project_foo"
    PRIVATE_KEY_ID = "key_foo"
    NAME = "service_identity_name"
    CA_CERT_PATH = "/path/to/ca/cert"
    TOKEN_URI = "https://service-identity.<Domain>/authenticate"

    JSON_PATH = os.path.join(
        os.path.dirname(__file__), "..", "data", "gdch_service_account.json"
    )
    with open(JSON_PATH, "rb") as fh:
        INFO = json.load(fh)

    def test_with_gdch_audience(self):
        mock_signer = mock.Mock()
        creds = ServiceAccountCredentials._from_signer_and_info(mock_signer, self.INFO)
        assert creds._signer == mock_signer
        assert creds._service_identity_name == self.NAME
        assert creds._audience is None
        assert creds._token_uri == self.TOKEN_URI
        assert creds._ca_cert_path == self.CA_CERT_PATH

        new_creds = creds.with_gdch_audience(self.AUDIENCE)
        assert new_creds._signer == mock_signer
        assert new_creds._service_identity_name == self.NAME
        assert new_creds._audience == self.AUDIENCE
        assert new_creds._token_uri == self.TOKEN_URI
        assert new_creds._ca_cert_path == self.CA_CERT_PATH

    def test__create_jwt(self):
        creds = ServiceAccountCredentials.from_service_account_file(self.JSON_PATH)
        with mock.patch("google.auth._helpers.utcnow") as utcnow:
            utcnow.return_value = datetime.datetime.now()
            jwt_token = creds._create_jwt()
            header, payload, _, _ = jwt._unverified_decode(jwt_token)

        expected_iss_sub_value = (
            "system:serviceaccount:project_foo:service_identity_name"
        )
        assert isinstance(jwt_token, six.text_type)
        assert header["alg"] == "ES256"
        assert header["kid"] == self.PRIVATE_KEY_ID
        assert payload["iss"] == expected_iss_sub_value
        assert payload["sub"] == expected_iss_sub_value
        assert payload["aud"] == self.AUDIENCE
        assert payload["exp"] == (payload["iat"] + 3600)

    @mock.patch(
        "google.oauth2.gdch_credentials.ServiceAccountCredentials._create_jwt",
        autospec=True,
    )
    @mock.patch("google.oauth2._client._token_endpoint_request", autospec=True)
    def test_refresh(self, token_endpoint_request, create_jwt):
        creds = ServiceAccountCredentials.from_service_account_info(self.INFO)
        creds = creds.with_gdch_audience(self.AUDIENCE)
        req = google.auth.transport.requests.Request()

        mock_jwt_token = "jwt token"
        create_jwt.return_value = mock_jwt_token
        sts_token = "STS token"
        token_endpoint_request.return_value = {
            "access_token": sts_token,
            "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        creds.refresh(req)

        token_endpoint_request.assert_called_with(
            req,
            self.TOKEN_URI,
            {
                "grant_type": gdch_credentials.TOKEN_EXCHANGE_TYPE,
                "audience": self.AUDIENCE,
                "requested_token_type": gdch_credentials.ACCESS_TOKEN_TOKEN_TYPE,
                "subject_token": mock_jwt_token,
                "subject_token_type": gdch_credentials.SERVICE_ACCOUNT_TOKEN_TYPE,
            },
            access_token=None,
            use_json=True,
            verify=self.CA_CERT_PATH,
        )
        assert creds.token == sts_token

    def test_refresh_wrong_requests_object(self):
        creds = ServiceAccountCredentials.from_service_account_info(self.INFO)
        creds = creds.with_gdch_audience(self.AUDIENCE)
        req = requests.Request()

        with pytest.raises(exceptions.RefreshError) as excinfo:
            creds.refresh(req)
        assert excinfo.match(
            "request must be a google.auth.transport.requests.Request object"
        )

    def test__from_signer_and_info_wrong_format_version(self):
        with pytest.raises(ValueError) as excinfo:
            ServiceAccountCredentials._from_signer_and_info(
                mock.Mock(), {"format_version": "2"}
            )
        assert excinfo.match("Only format version 1 is supported")

    def test_from_service_account_info_miss_field(self):
        for field in [
            "format_version",
            "private_key_id",
            "private_key",
            "name",
            "project",
            "token_uri",
        ]:
            info_with_missing_field = copy.deepcopy(self.INFO)
            del info_with_missing_field[field]
            with pytest.raises(ValueError) as excinfo:
                ServiceAccountCredentials.from_service_account_info(
                    info_with_missing_field
                )
            assert excinfo.match("missing fields")

    @mock.patch("google.auth._service_account_info.from_filename")
    def test_from_service_account_file(self, from_filename):
        mock_signer = mock.Mock()
        from_filename.return_value = (self.INFO, mock_signer)
        creds = ServiceAccountCredentials.from_service_account_file(self.JSON_PATH)
        from_filename.assert_called_with(
            self.JSON_PATH,
            require=[
                "format_version",
                "private_key_id",
                "private_key",
                "name",
                "project",
                "token_uri",
            ],
            use_rsa_signer=False,
        )
        assert creds._signer == mock_signer
        assert creds._service_identity_name == self.NAME
        assert creds._audience is None
        assert creds._token_uri == self.TOKEN_URI
        assert creds._ca_cert_path == self.CA_CERT_PATH
