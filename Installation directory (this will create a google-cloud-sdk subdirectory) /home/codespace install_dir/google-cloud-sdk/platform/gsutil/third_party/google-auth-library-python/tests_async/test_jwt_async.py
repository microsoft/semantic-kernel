# Copyright 2020 Google Inc.
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

from google.auth import _jwt_async as jwt_async
from google.auth import crypt
from google.auth import exceptions
from tests import test_jwt


@pytest.fixture
def signer():
    return crypt.RSASigner.from_string(test_jwt.PRIVATE_KEY_BYTES, "1")


class TestCredentials(object):
    SERVICE_ACCOUNT_EMAIL = "service-account@example.com"
    SUBJECT = "subject"
    AUDIENCE = "audience"
    ADDITIONAL_CLAIMS = {"meta": "data"}
    credentials = None

    @pytest.fixture(autouse=True)
    def credentials_fixture(self, signer):
        self.credentials = jwt_async.Credentials(
            signer,
            self.SERVICE_ACCOUNT_EMAIL,
            self.SERVICE_ACCOUNT_EMAIL,
            self.AUDIENCE,
        )

    def test_from_service_account_info(self):
        with open(test_jwt.SERVICE_ACCOUNT_JSON_FILE, "r") as fh:
            info = json.load(fh)

        credentials = jwt_async.Credentials.from_service_account_info(
            info, audience=self.AUDIENCE
        )

        assert credentials._signer.key_id == info["private_key_id"]
        assert credentials._issuer == info["client_email"]
        assert credentials._subject == info["client_email"]
        assert credentials._audience == self.AUDIENCE

    def test_from_service_account_info_args(self):
        info = test_jwt.SERVICE_ACCOUNT_INFO.copy()

        credentials = jwt_async.Credentials.from_service_account_info(
            info,
            subject=self.SUBJECT,
            audience=self.AUDIENCE,
            additional_claims=self.ADDITIONAL_CLAIMS,
        )

        assert credentials._signer.key_id == info["private_key_id"]
        assert credentials._issuer == info["client_email"]
        assert credentials._subject == self.SUBJECT
        assert credentials._audience == self.AUDIENCE
        assert credentials._additional_claims == self.ADDITIONAL_CLAIMS

    def test_from_service_account_file(self):
        info = test_jwt.SERVICE_ACCOUNT_INFO.copy()

        credentials = jwt_async.Credentials.from_service_account_file(
            test_jwt.SERVICE_ACCOUNT_JSON_FILE, audience=self.AUDIENCE
        )

        assert credentials._signer.key_id == info["private_key_id"]
        assert credentials._issuer == info["client_email"]
        assert credentials._subject == info["client_email"]
        assert credentials._audience == self.AUDIENCE

    def test_from_service_account_file_args(self):
        info = test_jwt.SERVICE_ACCOUNT_INFO.copy()

        credentials = jwt_async.Credentials.from_service_account_file(
            test_jwt.SERVICE_ACCOUNT_JSON_FILE,
            subject=self.SUBJECT,
            audience=self.AUDIENCE,
            additional_claims=self.ADDITIONAL_CLAIMS,
        )

        assert credentials._signer.key_id == info["private_key_id"]
        assert credentials._issuer == info["client_email"]
        assert credentials._subject == self.SUBJECT
        assert credentials._audience == self.AUDIENCE
        assert credentials._additional_claims == self.ADDITIONAL_CLAIMS

    def test_from_signing_credentials(self):
        jwt_from_signing = self.credentials.from_signing_credentials(
            self.credentials, audience=mock.sentinel.new_audience
        )
        jwt_from_info = jwt_async.Credentials.from_service_account_info(
            test_jwt.SERVICE_ACCOUNT_INFO, audience=mock.sentinel.new_audience
        )

        assert isinstance(jwt_from_signing, jwt_async.Credentials)
        assert jwt_from_signing._signer.key_id == jwt_from_info._signer.key_id
        assert jwt_from_signing._issuer == jwt_from_info._issuer
        assert jwt_from_signing._subject == jwt_from_info._subject
        assert jwt_from_signing._audience == jwt_from_info._audience

    def test_default_state(self):
        assert not self.credentials.valid
        # Expiration hasn't been set yet
        assert not self.credentials.expired

    def test_with_claims(self):
        new_audience = "new_audience"
        new_credentials = self.credentials.with_claims(audience=new_audience)

        assert new_credentials._signer == self.credentials._signer
        assert new_credentials._issuer == self.credentials._issuer
        assert new_credentials._subject == self.credentials._subject
        assert new_credentials._audience == new_audience
        assert new_credentials._additional_claims == self.credentials._additional_claims
        assert new_credentials._quota_project_id == self.credentials._quota_project_id

    def test_with_quota_project(self):
        quota_project_id = "project-foo"

        new_credentials = self.credentials.with_quota_project(quota_project_id)
        assert new_credentials._signer == self.credentials._signer
        assert new_credentials._issuer == self.credentials._issuer
        assert new_credentials._subject == self.credentials._subject
        assert new_credentials._audience == self.credentials._audience
        assert new_credentials._additional_claims == self.credentials._additional_claims
        assert new_credentials._quota_project_id == quota_project_id

    def test_sign_bytes(self):
        to_sign = b"123"
        signature = self.credentials.sign_bytes(to_sign)
        assert crypt.verify_signature(to_sign, signature, test_jwt.PUBLIC_CERT_BYTES)

    def test_signer(self):
        assert isinstance(self.credentials.signer, crypt.RSASigner)

    def test_signer_email(self):
        assert (
            self.credentials.signer_email
            == test_jwt.SERVICE_ACCOUNT_INFO["client_email"]
        )

    def _verify_token(self, token):
        payload = jwt_async.decode(token, test_jwt.PUBLIC_CERT_BYTES)
        assert payload["iss"] == self.SERVICE_ACCOUNT_EMAIL
        return payload

    def test_refresh(self):
        self.credentials.refresh(None)
        assert self.credentials.valid
        assert not self.credentials.expired

    def test_expired(self):
        assert not self.credentials.expired

        self.credentials.refresh(None)
        assert not self.credentials.expired

        with mock.patch("google.auth._helpers.utcnow") as now:
            one_day = datetime.timedelta(days=1)
            now.return_value = self.credentials.expiry + one_day
            assert self.credentials.expired

    @pytest.mark.asyncio
    async def test_before_request(self):
        headers = {}

        self.credentials.refresh(None)
        await self.credentials.before_request(
            None, "GET", "http://example.com?a=1#3", headers
        )

        header_value = headers["authorization"]
        _, token = header_value.split(" ")

        # Since the audience is set, it should use the existing token.
        assert token.encode("utf-8") == self.credentials.token

        payload = self._verify_token(token)
        assert payload["aud"] == self.AUDIENCE

    @pytest.mark.asyncio
    async def test_before_request_refreshes(self):
        assert not self.credentials.valid
        await self.credentials.before_request(
            None, "GET", "http://example.com?a=1#3", {}
        )
        assert self.credentials.valid


class TestOnDemandCredentials(object):
    SERVICE_ACCOUNT_EMAIL = "service-account@example.com"
    SUBJECT = "subject"
    ADDITIONAL_CLAIMS = {"meta": "data"}
    credentials = None

    @pytest.fixture(autouse=True)
    def credentials_fixture(self, signer):
        self.credentials = jwt_async.OnDemandCredentials(
            signer,
            self.SERVICE_ACCOUNT_EMAIL,
            self.SERVICE_ACCOUNT_EMAIL,
            max_cache_size=2,
        )

    def test_from_service_account_info(self):
        with open(test_jwt.SERVICE_ACCOUNT_JSON_FILE, "r") as fh:
            info = json.load(fh)

        credentials = jwt_async.OnDemandCredentials.from_service_account_info(info)

        assert credentials._signer.key_id == info["private_key_id"]
        assert credentials._issuer == info["client_email"]
        assert credentials._subject == info["client_email"]

    def test_from_service_account_info_args(self):
        info = test_jwt.SERVICE_ACCOUNT_INFO.copy()

        credentials = jwt_async.OnDemandCredentials.from_service_account_info(
            info, subject=self.SUBJECT, additional_claims=self.ADDITIONAL_CLAIMS
        )

        assert credentials._signer.key_id == info["private_key_id"]
        assert credentials._issuer == info["client_email"]
        assert credentials._subject == self.SUBJECT
        assert credentials._additional_claims == self.ADDITIONAL_CLAIMS

    def test_from_service_account_file(self):
        info = test_jwt.SERVICE_ACCOUNT_INFO.copy()

        credentials = jwt_async.OnDemandCredentials.from_service_account_file(
            test_jwt.SERVICE_ACCOUNT_JSON_FILE
        )

        assert credentials._signer.key_id == info["private_key_id"]
        assert credentials._issuer == info["client_email"]
        assert credentials._subject == info["client_email"]

    def test_from_service_account_file_args(self):
        info = test_jwt.SERVICE_ACCOUNT_INFO.copy()

        credentials = jwt_async.OnDemandCredentials.from_service_account_file(
            test_jwt.SERVICE_ACCOUNT_JSON_FILE,
            subject=self.SUBJECT,
            additional_claims=self.ADDITIONAL_CLAIMS,
        )

        assert credentials._signer.key_id == info["private_key_id"]
        assert credentials._issuer == info["client_email"]
        assert credentials._subject == self.SUBJECT
        assert credentials._additional_claims == self.ADDITIONAL_CLAIMS

    def test_from_signing_credentials(self):
        jwt_from_signing = self.credentials.from_signing_credentials(self.credentials)
        jwt_from_info = jwt_async.OnDemandCredentials.from_service_account_info(
            test_jwt.SERVICE_ACCOUNT_INFO
        )

        assert isinstance(jwt_from_signing, jwt_async.OnDemandCredentials)
        assert jwt_from_signing._signer.key_id == jwt_from_info._signer.key_id
        assert jwt_from_signing._issuer == jwt_from_info._issuer
        assert jwt_from_signing._subject == jwt_from_info._subject

    def test_default_state(self):
        # Credentials are *always* valid.
        assert self.credentials.valid
        # Credentials *never* expire.
        assert not self.credentials.expired

    def test_with_claims(self):
        new_claims = {"meep": "moop"}
        new_credentials = self.credentials.with_claims(additional_claims=new_claims)

        assert new_credentials._signer == self.credentials._signer
        assert new_credentials._issuer == self.credentials._issuer
        assert new_credentials._subject == self.credentials._subject
        assert new_credentials._additional_claims == new_claims

    def test_with_quota_project(self):
        quota_project_id = "project-foo"
        new_credentials = self.credentials.with_quota_project(quota_project_id)

        assert new_credentials._signer == self.credentials._signer
        assert new_credentials._issuer == self.credentials._issuer
        assert new_credentials._subject == self.credentials._subject
        assert new_credentials._additional_claims == self.credentials._additional_claims
        assert new_credentials._quota_project_id == quota_project_id

    def test_sign_bytes(self):
        to_sign = b"123"
        signature = self.credentials.sign_bytes(to_sign)
        assert crypt.verify_signature(to_sign, signature, test_jwt.PUBLIC_CERT_BYTES)

    def test_signer(self):
        assert isinstance(self.credentials.signer, crypt.RSASigner)

    def test_signer_email(self):
        assert (
            self.credentials.signer_email
            == test_jwt.SERVICE_ACCOUNT_INFO["client_email"]
        )

    def _verify_token(self, token):
        payload = jwt_async.decode(token, test_jwt.PUBLIC_CERT_BYTES)
        assert payload["iss"] == self.SERVICE_ACCOUNT_EMAIL
        return payload

    def test_refresh(self):
        with pytest.raises(exceptions.RefreshError):
            self.credentials.refresh(None)

    def test_before_request(self):
        headers = {}

        self.credentials.before_request(
            None, "GET", "http://example.com?a=1#3", headers
        )

        _, token = headers["authorization"].split(" ")
        payload = self._verify_token(token)

        assert payload["aud"] == "http://example.com"

        # Making another request should re-use the same token.
        self.credentials.before_request(None, "GET", "http://example.com?b=2", headers)

        _, new_token = headers["authorization"].split(" ")

        assert new_token == token

    def test_expired_token(self):
        self.credentials._cache["audience"] = (
            mock.sentinel.token,
            datetime.datetime.min,
        )

        token = self.credentials._get_jwt_for_audience("audience")

        assert token != mock.sentinel.token
