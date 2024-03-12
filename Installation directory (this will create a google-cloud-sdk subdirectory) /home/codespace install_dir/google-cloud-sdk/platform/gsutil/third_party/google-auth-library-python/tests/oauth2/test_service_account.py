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

import mock

from google.auth import _helpers
from google.auth import crypt
from google.auth import jwt
from google.auth import transport
from google.oauth2 import service_account


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

with open(os.path.join(DATA_DIR, "privatekey.pem"), "rb") as fh:
    PRIVATE_KEY_BYTES = fh.read()

with open(os.path.join(DATA_DIR, "public_cert.pem"), "rb") as fh:
    PUBLIC_CERT_BYTES = fh.read()

with open(os.path.join(DATA_DIR, "other_cert.pem"), "rb") as fh:
    OTHER_CERT_BYTES = fh.read()

SERVICE_ACCOUNT_JSON_FILE = os.path.join(DATA_DIR, "service_account.json")

with open(SERVICE_ACCOUNT_JSON_FILE, "rb") as fh:
    SERVICE_ACCOUNT_INFO = json.load(fh)

SIGNER = crypt.RSASigner.from_string(PRIVATE_KEY_BYTES, "1")


class TestCredentials(object):
    SERVICE_ACCOUNT_EMAIL = "service-account@example.com"
    TOKEN_URI = "https://example.com/oauth2/token"

    @classmethod
    def make_credentials(cls):
        return service_account.Credentials(
            SIGNER, cls.SERVICE_ACCOUNT_EMAIL, cls.TOKEN_URI
        )

    def test_from_service_account_info(self):
        credentials = service_account.Credentials.from_service_account_info(
            SERVICE_ACCOUNT_INFO
        )

        assert credentials._signer.key_id == SERVICE_ACCOUNT_INFO["private_key_id"]
        assert credentials.service_account_email == SERVICE_ACCOUNT_INFO["client_email"]
        assert credentials._token_uri == SERVICE_ACCOUNT_INFO["token_uri"]

    def test_from_service_account_info_args(self):
        info = SERVICE_ACCOUNT_INFO.copy()
        scopes = ["email", "profile"]
        subject = "subject"
        additional_claims = {"meta": "data"}

        credentials = service_account.Credentials.from_service_account_info(
            info, scopes=scopes, subject=subject, additional_claims=additional_claims
        )

        assert credentials.service_account_email == info["client_email"]
        assert credentials.project_id == info["project_id"]
        assert credentials._signer.key_id == info["private_key_id"]
        assert credentials._token_uri == info["token_uri"]
        assert credentials._scopes == scopes
        assert credentials._subject == subject
        assert credentials._additional_claims == additional_claims

    def test_from_service_account_file(self):
        info = SERVICE_ACCOUNT_INFO.copy()

        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_JSON_FILE
        )

        assert credentials.service_account_email == info["client_email"]
        assert credentials.project_id == info["project_id"]
        assert credentials._signer.key_id == info["private_key_id"]
        assert credentials._token_uri == info["token_uri"]

    def test_from_service_account_file_args(self):
        info = SERVICE_ACCOUNT_INFO.copy()
        scopes = ["email", "profile"]
        subject = "subject"
        additional_claims = {"meta": "data"}

        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_JSON_FILE,
            subject=subject,
            scopes=scopes,
            additional_claims=additional_claims,
        )

        assert credentials.service_account_email == info["client_email"]
        assert credentials.project_id == info["project_id"]
        assert credentials._signer.key_id == info["private_key_id"]
        assert credentials._token_uri == info["token_uri"]
        assert credentials._scopes == scopes
        assert credentials._subject == subject
        assert credentials._additional_claims == additional_claims

    def test_default_state(self):
        credentials = self.make_credentials()
        assert not credentials.valid
        # Expiration hasn't been set yet
        assert not credentials.expired
        # Scopes haven't been specified yet
        assert credentials.requires_scopes

    def test_sign_bytes(self):
        credentials = self.make_credentials()
        to_sign = b"123"
        signature = credentials.sign_bytes(to_sign)
        assert crypt.verify_signature(to_sign, signature, PUBLIC_CERT_BYTES)

    def test_signer(self):
        credentials = self.make_credentials()
        assert isinstance(credentials.signer, crypt.Signer)

    def test_signer_email(self):
        credentials = self.make_credentials()
        assert credentials.signer_email == self.SERVICE_ACCOUNT_EMAIL

    def test_create_scoped(self):
        credentials = self.make_credentials()
        scopes = ["email", "profile"]
        credentials = credentials.with_scopes(scopes)
        assert credentials._scopes == scopes

    def test_with_claims(self):
        credentials = self.make_credentials()
        new_credentials = credentials.with_claims({"meep": "moop"})
        assert new_credentials._additional_claims == {"meep": "moop"}

    def test_with_quota_project(self):
        credentials = self.make_credentials()
        new_credentials = credentials.with_quota_project("new-project-456")
        assert new_credentials.quota_project_id == "new-project-456"
        hdrs = {}
        new_credentials.apply(hdrs, token="tok")
        assert "x-goog-user-project" in hdrs

    def test_with_token_uri(self):
        credentials = self.make_credentials()
        new_token_uri = "https://example2.com/oauth2/token"
        assert credentials._token_uri == self.TOKEN_URI
        creds_with_new_token_uri = credentials.with_token_uri(new_token_uri)
        assert creds_with_new_token_uri._token_uri == new_token_uri

    def test__with_always_use_jwt_access(self):
        credentials = self.make_credentials()
        assert not credentials._always_use_jwt_access

        new_credentials = credentials.with_always_use_jwt_access(True)
        assert new_credentials._always_use_jwt_access

    def test__make_authorization_grant_assertion(self):
        credentials = self.make_credentials()
        token = credentials._make_authorization_grant_assertion()
        payload = jwt.decode(token, PUBLIC_CERT_BYTES)
        assert payload["iss"] == self.SERVICE_ACCOUNT_EMAIL
        assert payload["aud"] == service_account._GOOGLE_OAUTH2_TOKEN_ENDPOINT

    def test__make_authorization_grant_assertion_scoped(self):
        credentials = self.make_credentials()
        scopes = ["email", "profile"]
        credentials = credentials.with_scopes(scopes)
        token = credentials._make_authorization_grant_assertion()
        payload = jwt.decode(token, PUBLIC_CERT_BYTES)
        assert payload["scope"] == "email profile"

    def test__make_authorization_grant_assertion_subject(self):
        credentials = self.make_credentials()
        subject = "user@example.com"
        credentials = credentials.with_subject(subject)
        token = credentials._make_authorization_grant_assertion()
        payload = jwt.decode(token, PUBLIC_CERT_BYTES)
        assert payload["sub"] == subject

    def test_apply_with_quota_project_id(self):
        credentials = service_account.Credentials(
            SIGNER,
            self.SERVICE_ACCOUNT_EMAIL,
            self.TOKEN_URI,
            quota_project_id="quota-project-123",
        )

        headers = {}
        credentials.apply(headers, token="token")

        assert headers["x-goog-user-project"] == "quota-project-123"
        assert "token" in headers["authorization"]

    def test_apply_with_no_quota_project_id(self):
        credentials = service_account.Credentials(
            SIGNER, self.SERVICE_ACCOUNT_EMAIL, self.TOKEN_URI
        )

        headers = {}
        credentials.apply(headers, token="token")

        assert "x-goog-user-project" not in headers
        assert "token" in headers["authorization"]

    @mock.patch("google.auth.jwt.Credentials", instance=True, autospec=True)
    def test__create_self_signed_jwt(self, jwt):
        credentials = service_account.Credentials(
            SIGNER, self.SERVICE_ACCOUNT_EMAIL, self.TOKEN_URI
        )

        audience = "https://pubsub.googleapis.com"
        credentials._create_self_signed_jwt(audience)
        jwt.from_signing_credentials.assert_called_once_with(credentials, audience)

    @mock.patch("google.auth.jwt.Credentials", instance=True, autospec=True)
    def test__create_self_signed_jwt_with_user_scopes(self, jwt):
        credentials = service_account.Credentials(
            SIGNER, self.SERVICE_ACCOUNT_EMAIL, self.TOKEN_URI, scopes=["foo"]
        )

        audience = "https://pubsub.googleapis.com"
        credentials._create_self_signed_jwt(audience)

        # JWT should not be created if there are user-defined scopes
        jwt.from_signing_credentials.assert_not_called()

    @mock.patch("google.auth.jwt.Credentials", instance=True, autospec=True)
    def test__create_self_signed_jwt_always_use_jwt_access_with_audience(self, jwt):
        credentials = service_account.Credentials(
            SIGNER,
            self.SERVICE_ACCOUNT_EMAIL,
            self.TOKEN_URI,
            default_scopes=["bar", "foo"],
            always_use_jwt_access=True,
        )

        audience = "https://pubsub.googleapis.com"
        credentials._create_self_signed_jwt(audience)
        jwt.from_signing_credentials.assert_called_once_with(credentials, audience)

    @mock.patch("google.auth.jwt.Credentials", instance=True, autospec=True)
    def test__create_self_signed_jwt_always_use_jwt_access_with_audience_similar_jwt_is_reused(
        self, jwt
    ):
        credentials = service_account.Credentials(
            SIGNER,
            self.SERVICE_ACCOUNT_EMAIL,
            self.TOKEN_URI,
            default_scopes=["bar", "foo"],
            always_use_jwt_access=True,
        )

        audience = "https://pubsub.googleapis.com"
        credentials._create_self_signed_jwt(audience)
        credentials._jwt_credentials._audience = audience
        credentials._create_self_signed_jwt(audience)
        jwt.from_signing_credentials.assert_called_once_with(credentials, audience)

    @mock.patch("google.auth.jwt.Credentials", instance=True, autospec=True)
    def test__create_self_signed_jwt_always_use_jwt_access_with_scopes(self, jwt):
        credentials = service_account.Credentials(
            SIGNER,
            self.SERVICE_ACCOUNT_EMAIL,
            self.TOKEN_URI,
            scopes=["bar", "foo"],
            always_use_jwt_access=True,
        )

        audience = "https://pubsub.googleapis.com"
        credentials._create_self_signed_jwt(audience)
        jwt.from_signing_credentials.assert_called_once_with(
            credentials, None, additional_claims={"scope": "bar foo"}
        )

    @mock.patch("google.auth.jwt.Credentials", instance=True, autospec=True)
    def test__create_self_signed_jwt_always_use_jwt_access_with_scopes_similar_jwt_is_reused(
        self, jwt
    ):
        credentials = service_account.Credentials(
            SIGNER,
            self.SERVICE_ACCOUNT_EMAIL,
            self.TOKEN_URI,
            scopes=["bar", "foo"],
            always_use_jwt_access=True,
        )

        audience = "https://pubsub.googleapis.com"
        credentials._create_self_signed_jwt(audience)
        credentials._jwt_credentials.additional_claims = {"scope": "bar foo"}
        credentials._create_self_signed_jwt(audience)
        jwt.from_signing_credentials.assert_called_once_with(
            credentials, None, additional_claims={"scope": "bar foo"}
        )

    @mock.patch("google.auth.jwt.Credentials", instance=True, autospec=True)
    def test__create_self_signed_jwt_always_use_jwt_access_with_default_scopes(
        self, jwt
    ):
        credentials = service_account.Credentials(
            SIGNER,
            self.SERVICE_ACCOUNT_EMAIL,
            self.TOKEN_URI,
            default_scopes=["bar", "foo"],
            always_use_jwt_access=True,
        )

        credentials._create_self_signed_jwt(None)
        jwt.from_signing_credentials.assert_called_once_with(
            credentials, None, additional_claims={"scope": "bar foo"}
        )

    @mock.patch("google.auth.jwt.Credentials", instance=True, autospec=True)
    def test__create_self_signed_jwt_always_use_jwt_access_with_default_scopes_similar_jwt_is_reused(
        self, jwt
    ):
        credentials = service_account.Credentials(
            SIGNER,
            self.SERVICE_ACCOUNT_EMAIL,
            self.TOKEN_URI,
            default_scopes=["bar", "foo"],
            always_use_jwt_access=True,
        )

        credentials._create_self_signed_jwt(None)
        credentials._jwt_credentials.additional_claims = {"scope": "bar foo"}
        credentials._create_self_signed_jwt(None)
        jwt.from_signing_credentials.assert_called_once_with(
            credentials, None, additional_claims={"scope": "bar foo"}
        )

    @mock.patch("google.auth.jwt.Credentials", instance=True, autospec=True)
    def test__create_self_signed_jwt_always_use_jwt_access(self, jwt):
        credentials = service_account.Credentials(
            SIGNER,
            self.SERVICE_ACCOUNT_EMAIL,
            self.TOKEN_URI,
            always_use_jwt_access=True,
        )

        credentials._create_self_signed_jwt(None)
        jwt.from_signing_credentials.assert_not_called()

    @mock.patch("google.oauth2._client.jwt_grant", autospec=True)
    def test_refresh_success(self, jwt_grant):
        credentials = self.make_credentials()
        token = "token"
        jwt_grant.return_value = (
            token,
            _helpers.utcnow() + datetime.timedelta(seconds=500),
            {},
        )
        request = mock.create_autospec(transport.Request, instance=True)

        # Refresh credentials
        credentials.refresh(request)

        # Check jwt grant call.
        assert jwt_grant.called

        called_request, token_uri, assertion = jwt_grant.call_args[0]
        assert called_request == request
        assert token_uri == credentials._token_uri
        assert jwt.decode(assertion, PUBLIC_CERT_BYTES)
        # No further assertion done on the token, as there are separate tests
        # for checking the authorization grant assertion.

        # Check that the credentials have the token.
        assert credentials.token == token

        # Check that the credentials are valid (have a token and are not
        # expired)
        assert credentials.valid

    @mock.patch("google.oauth2._client.jwt_grant", autospec=True)
    def test_before_request_refreshes(self, jwt_grant):
        credentials = self.make_credentials()
        token = "token"
        jwt_grant.return_value = (
            token,
            _helpers.utcnow() + datetime.timedelta(seconds=500),
            None,
        )
        request = mock.create_autospec(transport.Request, instance=True)

        # Credentials should start as invalid
        assert not credentials.valid

        # before_request should cause a refresh
        credentials.before_request(request, "GET", "http://example.com?a=1#3", {})

        # The refresh endpoint should've been called.
        assert jwt_grant.called

        # Credentials should now be valid.
        assert credentials.valid

    @mock.patch("google.auth.jwt.Credentials._make_jwt")
    def test_refresh_with_jwt_credentials(self, make_jwt):
        credentials = self.make_credentials()
        credentials._create_self_signed_jwt("https://pubsub.googleapis.com")

        request = mock.create_autospec(transport.Request, instance=True)

        token = "token"
        expiry = _helpers.utcnow() + datetime.timedelta(seconds=500)
        make_jwt.return_value = (token, expiry)

        # Credentials should start as invalid
        assert not credentials.valid

        # before_request should cause a refresh
        credentials.before_request(request, "GET", "http://example.com?a=1#3", {})

        # Credentials should now be valid.
        assert credentials.valid

        # Assert make_jwt was called
        assert make_jwt.call_count == 1

        assert credentials.token == token
        assert credentials.expiry == expiry

    @mock.patch("google.oauth2._client.jwt_grant", autospec=True)
    @mock.patch("google.auth.jwt.Credentials.refresh", autospec=True)
    def test_refresh_jwt_not_used_for_domain_wide_delegation(
        self, self_signed_jwt_refresh, jwt_grant
    ):
        # Create a domain wide delegation credentials by setting the subject.
        credentials = service_account.Credentials(
            SIGNER,
            self.SERVICE_ACCOUNT_EMAIL,
            self.TOKEN_URI,
            always_use_jwt_access=True,
            subject="subject",
        )
        credentials._create_self_signed_jwt("https://pubsub.googleapis.com")
        jwt_grant.return_value = (
            "token",
            _helpers.utcnow() + datetime.timedelta(seconds=500),
            {},
        )
        request = mock.create_autospec(transport.Request, instance=True)

        # Refresh credentials
        credentials.refresh(request)

        # Make sure we are using jwt_grant and not self signed JWT refresh
        # method to obtain the token.
        assert jwt_grant.called
        assert not self_signed_jwt_refresh.called


class TestIDTokenCredentials(object):
    SERVICE_ACCOUNT_EMAIL = "service-account@example.com"
    TOKEN_URI = "https://example.com/oauth2/token"
    TARGET_AUDIENCE = "https://example.com"

    @classmethod
    def make_credentials(cls):
        return service_account.IDTokenCredentials(
            SIGNER, cls.SERVICE_ACCOUNT_EMAIL, cls.TOKEN_URI, cls.TARGET_AUDIENCE
        )

    def test_from_service_account_info(self):
        credentials = service_account.IDTokenCredentials.from_service_account_info(
            SERVICE_ACCOUNT_INFO, target_audience=self.TARGET_AUDIENCE
        )

        assert credentials._signer.key_id == SERVICE_ACCOUNT_INFO["private_key_id"]
        assert credentials.service_account_email == SERVICE_ACCOUNT_INFO["client_email"]
        assert credentials._token_uri == SERVICE_ACCOUNT_INFO["token_uri"]
        assert credentials._target_audience == self.TARGET_AUDIENCE
        assert not credentials._use_iam_endpoint

    def test_from_service_account_file(self):
        info = SERVICE_ACCOUNT_INFO.copy()

        credentials = service_account.IDTokenCredentials.from_service_account_file(
            SERVICE_ACCOUNT_JSON_FILE, target_audience=self.TARGET_AUDIENCE
        )

        assert credentials.service_account_email == info["client_email"]
        assert credentials._signer.key_id == info["private_key_id"]
        assert credentials._token_uri == info["token_uri"]
        assert credentials._target_audience == self.TARGET_AUDIENCE
        assert not credentials._use_iam_endpoint

    def test_default_state(self):
        credentials = self.make_credentials()
        assert not credentials.valid
        # Expiration hasn't been set yet
        assert not credentials.expired

    def test_sign_bytes(self):
        credentials = self.make_credentials()
        to_sign = b"123"
        signature = credentials.sign_bytes(to_sign)
        assert crypt.verify_signature(to_sign, signature, PUBLIC_CERT_BYTES)

    def test_signer(self):
        credentials = self.make_credentials()
        assert isinstance(credentials.signer, crypt.Signer)

    def test_signer_email(self):
        credentials = self.make_credentials()
        assert credentials.signer_email == self.SERVICE_ACCOUNT_EMAIL

    def test_with_target_audience(self):
        credentials = self.make_credentials()
        new_credentials = credentials.with_target_audience("https://new.example.com")
        assert new_credentials._target_audience == "https://new.example.com"

    def test__with_use_iam_endpoint(self):
        credentials = self.make_credentials()
        new_credentials = credentials._with_use_iam_endpoint(True)
        assert new_credentials._use_iam_endpoint

    def test_with_quota_project(self):
        credentials = self.make_credentials()
        new_credentials = credentials.with_quota_project("project-foo")
        assert new_credentials._quota_project_id == "project-foo"

    def test_with_token_uri(self):
        credentials = self.make_credentials()
        new_token_uri = "https://example2.com/oauth2/token"
        assert credentials._token_uri == self.TOKEN_URI
        creds_with_new_token_uri = credentials.with_token_uri(new_token_uri)
        assert creds_with_new_token_uri._token_uri == new_token_uri

    def test__make_authorization_grant_assertion(self):
        credentials = self.make_credentials()
        token = credentials._make_authorization_grant_assertion()
        payload = jwt.decode(token, PUBLIC_CERT_BYTES)
        assert payload["iss"] == self.SERVICE_ACCOUNT_EMAIL
        assert payload["aud"] == service_account._GOOGLE_OAUTH2_TOKEN_ENDPOINT
        assert payload["target_audience"] == self.TARGET_AUDIENCE

    @mock.patch("google.oauth2._client.id_token_jwt_grant", autospec=True)
    def test_refresh_success(self, id_token_jwt_grant):
        credentials = self.make_credentials()
        token = "token"
        id_token_jwt_grant.return_value = (
            token,
            _helpers.utcnow() + datetime.timedelta(seconds=500),
            {},
        )
        request = mock.create_autospec(transport.Request, instance=True)

        # Refresh credentials
        credentials.refresh(request)

        # Check jwt grant call.
        assert id_token_jwt_grant.called

        called_request, token_uri, assertion = id_token_jwt_grant.call_args[0]
        assert called_request == request
        assert token_uri == credentials._token_uri
        assert jwt.decode(assertion, PUBLIC_CERT_BYTES)
        # No further assertion done on the token, as there are separate tests
        # for checking the authorization grant assertion.

        # Check that the credentials have the token.
        assert credentials.token == token

        # Check that the credentials are valid (have a token and are not
        # expired)
        assert credentials.valid

    @mock.patch(
        "google.oauth2._client.call_iam_generate_id_token_endpoint", autospec=True
    )
    def test_refresh_iam_flow(self, call_iam_generate_id_token_endpoint):
        credentials = self.make_credentials()
        credentials._use_iam_endpoint = True
        token = "id_token"
        call_iam_generate_id_token_endpoint.return_value = (
            token,
            _helpers.utcnow() + datetime.timedelta(seconds=500),
        )
        request = mock.Mock()
        credentials.refresh(request)
        req, signer_email, target_audience, access_token = call_iam_generate_id_token_endpoint.call_args[
            0
        ]
        assert req == request
        assert signer_email == "service-account@example.com"
        assert target_audience == "https://example.com"
        decoded_access_token = jwt.decode(access_token, verify=False)
        assert decoded_access_token["scope"] == "https://www.googleapis.com/auth/iam"

    @mock.patch("google.oauth2._client.id_token_jwt_grant", autospec=True)
    def test_before_request_refreshes(self, id_token_jwt_grant):
        credentials = self.make_credentials()
        token = "token"
        id_token_jwt_grant.return_value = (
            token,
            _helpers.utcnow() + datetime.timedelta(seconds=500),
            None,
        )
        request = mock.create_autospec(transport.Request, instance=True)

        # Credentials should start as invalid
        assert not credentials.valid

        # before_request should cause a refresh
        credentials.before_request(request, "GET", "http://example.com?a=1#3", {})

        # The refresh endpoint should've been called.
        assert id_token_jwt_grant.called

        # Credentials should now be valid.
        assert credentials.valid
