# Copyright 2014 Google Inc.
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

import base64
import datetime
import json
import os

import mock
import pytest  # type: ignore

from google.auth import _helpers
from google.auth import crypt
from google.auth import exceptions
from google.auth import jwt


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

with open(os.path.join(DATA_DIR, "privatekey.pem"), "rb") as fh:
    PRIVATE_KEY_BYTES = fh.read()

with open(os.path.join(DATA_DIR, "public_cert.pem"), "rb") as fh:
    PUBLIC_CERT_BYTES = fh.read()

with open(os.path.join(DATA_DIR, "other_cert.pem"), "rb") as fh:
    OTHER_CERT_BYTES = fh.read()

with open(os.path.join(DATA_DIR, "es256_privatekey.pem"), "rb") as fh:
    EC_PRIVATE_KEY_BYTES = fh.read()

with open(os.path.join(DATA_DIR, "es256_public_cert.pem"), "rb") as fh:
    EC_PUBLIC_CERT_BYTES = fh.read()

SERVICE_ACCOUNT_JSON_FILE = os.path.join(DATA_DIR, "service_account.json")

with open(SERVICE_ACCOUNT_JSON_FILE, "rb") as fh:
    SERVICE_ACCOUNT_INFO = json.load(fh)


@pytest.fixture
def signer():
    return crypt.RSASigner.from_string(PRIVATE_KEY_BYTES, "1")


def test_encode_basic(signer):
    test_payload = {"test": "value"}
    encoded = jwt.encode(signer, test_payload)
    header, payload, _, _ = jwt._unverified_decode(encoded)
    assert payload == test_payload
    assert header == {"typ": "JWT", "alg": "RS256", "kid": signer.key_id}


def test_encode_extra_headers(signer):
    encoded = jwt.encode(signer, {}, header={"extra": "value"})
    header = jwt.decode_header(encoded)
    assert header == {
        "typ": "JWT",
        "alg": "RS256",
        "kid": signer.key_id,
        "extra": "value",
    }


def test_encode_custom_alg_in_headers(signer):
    encoded = jwt.encode(signer, {}, header={"alg": "foo"})
    header = jwt.decode_header(encoded)
    assert header == {"typ": "JWT", "alg": "foo", "kid": signer.key_id}


@pytest.fixture
def es256_signer():
    return crypt.ES256Signer.from_string(EC_PRIVATE_KEY_BYTES, "1")


def test_encode_basic_es256(es256_signer):
    test_payload = {"test": "value"}
    encoded = jwt.encode(es256_signer, test_payload)
    header, payload, _, _ = jwt._unverified_decode(encoded)
    assert payload == test_payload
    assert header == {"typ": "JWT", "alg": "ES256", "kid": es256_signer.key_id}


@pytest.fixture
def token_factory(signer, es256_signer):
    def factory(claims=None, key_id=None, use_es256_signer=False):
        now = _helpers.datetime_to_secs(_helpers.utcnow())
        payload = {
            "aud": "audience@example.com",
            "iat": now,
            "exp": now + 300,
            "user": "billy bob",
            "metadata": {"meta": "data"},
        }
        payload.update(claims or {})

        # False is specified to remove the signer's key id for testing
        # headers without key ids.
        if key_id is False:
            signer._key_id = None
            key_id = None

        if use_es256_signer:
            return jwt.encode(es256_signer, payload, key_id=key_id)
        else:
            return jwt.encode(signer, payload, key_id=key_id)

    return factory


def test_decode_valid(token_factory):
    payload = jwt.decode(token_factory(), certs=PUBLIC_CERT_BYTES)
    assert payload["aud"] == "audience@example.com"
    assert payload["user"] == "billy bob"
    assert payload["metadata"]["meta"] == "data"


def test_decode_header_object(token_factory):
    payload = token_factory()
    # Create a malformed JWT token with a number as a header instead of a
    # dictionary (3 == base64d(M7==))
    payload = b"M7." + b".".join(payload.split(b".")[1:])

    with pytest.raises(ValueError) as excinfo:
        jwt.decode(payload, certs=PUBLIC_CERT_BYTES)
    assert excinfo.match(r"Header segment should be a JSON object: " + str(b"M7"))


def test_decode_payload_object(signer):
    # Create a malformed JWT token with a payload containing both "iat" and
    # "exp" strings, although not as fields of a dictionary
    payload = jwt.encode(signer, "iatexp")

    with pytest.raises(ValueError) as excinfo:
        jwt.decode(payload, certs=PUBLIC_CERT_BYTES)
    assert excinfo.match(
        r"Payload segment should be a JSON object: " + str(b"ImlhdGV4cCI")
    )


def test_decode_valid_es256(token_factory):
    payload = jwt.decode(
        token_factory(use_es256_signer=True), certs=EC_PUBLIC_CERT_BYTES
    )
    assert payload["aud"] == "audience@example.com"
    assert payload["user"] == "billy bob"
    assert payload["metadata"]["meta"] == "data"


def test_decode_valid_with_audience(token_factory):
    payload = jwt.decode(
        token_factory(), certs=PUBLIC_CERT_BYTES, audience="audience@example.com"
    )
    assert payload["aud"] == "audience@example.com"
    assert payload["user"] == "billy bob"
    assert payload["metadata"]["meta"] == "data"


def test_decode_valid_with_audience_list(token_factory):
    payload = jwt.decode(
        token_factory(),
        certs=PUBLIC_CERT_BYTES,
        audience=["audience@example.com", "another_audience@example.com"],
    )
    assert payload["aud"] == "audience@example.com"
    assert payload["user"] == "billy bob"
    assert payload["metadata"]["meta"] == "data"


def test_decode_valid_unverified(token_factory):
    payload = jwt.decode(token_factory(), certs=OTHER_CERT_BYTES, verify=False)
    assert payload["aud"] == "audience@example.com"
    assert payload["user"] == "billy bob"
    assert payload["metadata"]["meta"] == "data"


def test_decode_bad_token_wrong_number_of_segments():
    with pytest.raises(ValueError) as excinfo:
        jwt.decode("1.2", PUBLIC_CERT_BYTES)
    assert excinfo.match(r"Wrong number of segments")


def test_decode_bad_token_not_base64():
    with pytest.raises((ValueError, TypeError)) as excinfo:
        jwt.decode("1.2.3", PUBLIC_CERT_BYTES)
    assert excinfo.match(r"Incorrect padding|more than a multiple of 4")


def test_decode_bad_token_not_json():
    token = b".".join([base64.urlsafe_b64encode(b"123!")] * 3)
    with pytest.raises(ValueError) as excinfo:
        jwt.decode(token, PUBLIC_CERT_BYTES)
    assert excinfo.match(r"Can\'t parse segment")


def test_decode_bad_token_no_iat_or_exp(signer):
    token = jwt.encode(signer, {"test": "value"})
    with pytest.raises(ValueError) as excinfo:
        jwt.decode(token, PUBLIC_CERT_BYTES)
    assert excinfo.match(r"Token does not contain required claim")


def test_decode_bad_token_too_early(token_factory):
    token = token_factory(
        claims={
            "iat": _helpers.datetime_to_secs(
                _helpers.utcnow() + datetime.timedelta(hours=1)
            )
        }
    )
    with pytest.raises(ValueError) as excinfo:
        jwt.decode(token, PUBLIC_CERT_BYTES, clock_skew_in_seconds=59)
    assert excinfo.match(r"Token used too early")


def test_decode_bad_token_expired(token_factory):
    token = token_factory(
        claims={
            "exp": _helpers.datetime_to_secs(
                _helpers.utcnow() - datetime.timedelta(hours=1)
            )
        }
    )
    with pytest.raises(ValueError) as excinfo:
        jwt.decode(token, PUBLIC_CERT_BYTES, clock_skew_in_seconds=59)
    assert excinfo.match(r"Token expired")


def test_decode_success_with_no_clock_skew(token_factory):
    token = token_factory(
        claims={
            "exp": _helpers.datetime_to_secs(
                _helpers.utcnow() + datetime.timedelta(seconds=1)
            ),
            "iat": _helpers.datetime_to_secs(
                _helpers.utcnow() - datetime.timedelta(seconds=1)
            ),
        }
    )

    jwt.decode(token, PUBLIC_CERT_BYTES)


def test_decode_success_with_custom_clock_skew(token_factory):
    token = token_factory(
        claims={
            "exp": _helpers.datetime_to_secs(
                _helpers.utcnow() + datetime.timedelta(seconds=2)
            ),
            "iat": _helpers.datetime_to_secs(
                _helpers.utcnow() - datetime.timedelta(seconds=2)
            ),
        }
    )

    jwt.decode(token, PUBLIC_CERT_BYTES, clock_skew_in_seconds=1)


def test_decode_bad_token_wrong_audience(token_factory):
    token = token_factory()
    audience = "audience2@example.com"
    with pytest.raises(ValueError) as excinfo:
        jwt.decode(token, PUBLIC_CERT_BYTES, audience=audience)
    assert excinfo.match(r"Token has wrong audience")


def test_decode_bad_token_wrong_audience_list(token_factory):
    token = token_factory()
    audience = ["audience2@example.com", "audience3@example.com"]
    with pytest.raises(ValueError) as excinfo:
        jwt.decode(token, PUBLIC_CERT_BYTES, audience=audience)
    assert excinfo.match(r"Token has wrong audience")


def test_decode_wrong_cert(token_factory):
    with pytest.raises(ValueError) as excinfo:
        jwt.decode(token_factory(), OTHER_CERT_BYTES)
    assert excinfo.match(r"Could not verify token signature")


def test_decode_multicert_bad_cert(token_factory):
    certs = {"1": OTHER_CERT_BYTES, "2": PUBLIC_CERT_BYTES}
    with pytest.raises(ValueError) as excinfo:
        jwt.decode(token_factory(), certs)
    assert excinfo.match(r"Could not verify token signature")


def test_decode_no_cert(token_factory):
    certs = {"2": PUBLIC_CERT_BYTES}
    with pytest.raises(ValueError) as excinfo:
        jwt.decode(token_factory(), certs)
    assert excinfo.match(r"Certificate for key id 1 not found")


def test_decode_no_key_id(token_factory):
    token = token_factory(key_id=False)
    certs = {"2": PUBLIC_CERT_BYTES}
    payload = jwt.decode(token, certs)
    assert payload["user"] == "billy bob"


def test_decode_unknown_alg():
    headers = json.dumps({u"kid": u"1", u"alg": u"fakealg"})
    token = b".".join(
        map(lambda seg: base64.b64encode(seg.encode("utf-8")), [headers, u"{}", u"sig"])
    )

    with pytest.raises(ValueError) as excinfo:
        jwt.decode(token)
    assert excinfo.match(r"fakealg")


def test_decode_missing_crytography_alg(monkeypatch):
    monkeypatch.delitem(jwt._ALGORITHM_TO_VERIFIER_CLASS, "ES256")
    headers = json.dumps({u"kid": u"1", u"alg": u"ES256"})
    token = b".".join(
        map(lambda seg: base64.b64encode(seg.encode("utf-8")), [headers, u"{}", u"sig"])
    )

    with pytest.raises(ValueError) as excinfo:
        jwt.decode(token)
    assert excinfo.match(r"cryptography")


def test_roundtrip_explicit_key_id(token_factory):
    token = token_factory(key_id="3")
    certs = {"2": OTHER_CERT_BYTES, "3": PUBLIC_CERT_BYTES}
    payload = jwt.decode(token, certs)
    assert payload["user"] == "billy bob"


class TestCredentials(object):
    SERVICE_ACCOUNT_EMAIL = "service-account@example.com"
    SUBJECT = "subject"
    AUDIENCE = "audience"
    ADDITIONAL_CLAIMS = {"meta": "data"}
    credentials = None

    @pytest.fixture(autouse=True)
    def credentials_fixture(self, signer):
        self.credentials = jwt.Credentials(
            signer,
            self.SERVICE_ACCOUNT_EMAIL,
            self.SERVICE_ACCOUNT_EMAIL,
            self.AUDIENCE,
        )

    def test_from_service_account_info(self):
        with open(SERVICE_ACCOUNT_JSON_FILE, "r") as fh:
            info = json.load(fh)

        credentials = jwt.Credentials.from_service_account_info(
            info, audience=self.AUDIENCE
        )

        assert credentials._signer.key_id == info["private_key_id"]
        assert credentials._issuer == info["client_email"]
        assert credentials._subject == info["client_email"]
        assert credentials._audience == self.AUDIENCE

    def test_from_service_account_info_args(self):
        info = SERVICE_ACCOUNT_INFO.copy()

        credentials = jwt.Credentials.from_service_account_info(
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
        info = SERVICE_ACCOUNT_INFO.copy()

        credentials = jwt.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_JSON_FILE, audience=self.AUDIENCE
        )

        assert credentials._signer.key_id == info["private_key_id"]
        assert credentials._issuer == info["client_email"]
        assert credentials._subject == info["client_email"]
        assert credentials._audience == self.AUDIENCE

    def test_from_service_account_file_args(self):
        info = SERVICE_ACCOUNT_INFO.copy()

        credentials = jwt.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_JSON_FILE,
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
        jwt_from_info = jwt.Credentials.from_service_account_info(
            SERVICE_ACCOUNT_INFO, audience=mock.sentinel.new_audience
        )

        assert isinstance(jwt_from_signing, jwt.Credentials)
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

    def test__make_jwt_without_audience(self):
        cred = jwt.Credentials.from_service_account_info(
            SERVICE_ACCOUNT_INFO.copy(),
            subject=self.SUBJECT,
            audience=None,
            additional_claims={"scope": "foo bar"},
        )
        token, _ = cred._make_jwt()
        payload = jwt.decode(token, PUBLIC_CERT_BYTES)
        assert payload["scope"] == "foo bar"
        assert "aud" not in payload

    def test_with_quota_project(self):
        quota_project_id = "project-foo"

        new_credentials = self.credentials.with_quota_project(quota_project_id)
        assert new_credentials._signer == self.credentials._signer
        assert new_credentials._issuer == self.credentials._issuer
        assert new_credentials._subject == self.credentials._subject
        assert new_credentials._audience == self.credentials._audience
        assert new_credentials._additional_claims == self.credentials._additional_claims
        assert new_credentials.additional_claims == self.credentials._additional_claims
        assert new_credentials._quota_project_id == quota_project_id

    def test_sign_bytes(self):
        to_sign = b"123"
        signature = self.credentials.sign_bytes(to_sign)
        assert crypt.verify_signature(to_sign, signature, PUBLIC_CERT_BYTES)

    def test_signer(self):
        assert isinstance(self.credentials.signer, crypt.RSASigner)

    def test_signer_email(self):
        assert self.credentials.signer_email == SERVICE_ACCOUNT_INFO["client_email"]

    def _verify_token(self, token):
        payload = jwt.decode(token, PUBLIC_CERT_BYTES)
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

    def test_before_request(self):
        headers = {}

        self.credentials.refresh(None)
        self.credentials.before_request(
            None, "GET", "http://example.com?a=1#3", headers
        )

        header_value = headers["authorization"]
        _, token = header_value.split(" ")

        # Since the audience is set, it should use the existing token.
        assert token.encode("utf-8") == self.credentials.token

        payload = self._verify_token(token)
        assert payload["aud"] == self.AUDIENCE

    def test_before_request_refreshes(self):
        assert not self.credentials.valid
        self.credentials.before_request(None, "GET", "http://example.com?a=1#3", {})
        assert self.credentials.valid


class TestOnDemandCredentials(object):
    SERVICE_ACCOUNT_EMAIL = "service-account@example.com"
    SUBJECT = "subject"
    ADDITIONAL_CLAIMS = {"meta": "data"}
    credentials = None

    @pytest.fixture(autouse=True)
    def credentials_fixture(self, signer):
        self.credentials = jwt.OnDemandCredentials(
            signer,
            self.SERVICE_ACCOUNT_EMAIL,
            self.SERVICE_ACCOUNT_EMAIL,
            max_cache_size=2,
        )

    def test_from_service_account_info(self):
        with open(SERVICE_ACCOUNT_JSON_FILE, "r") as fh:
            info = json.load(fh)

        credentials = jwt.OnDemandCredentials.from_service_account_info(info)

        assert credentials._signer.key_id == info["private_key_id"]
        assert credentials._issuer == info["client_email"]
        assert credentials._subject == info["client_email"]

    def test_from_service_account_info_args(self):
        info = SERVICE_ACCOUNT_INFO.copy()

        credentials = jwt.OnDemandCredentials.from_service_account_info(
            info, subject=self.SUBJECT, additional_claims=self.ADDITIONAL_CLAIMS
        )

        assert credentials._signer.key_id == info["private_key_id"]
        assert credentials._issuer == info["client_email"]
        assert credentials._subject == self.SUBJECT
        assert credentials._additional_claims == self.ADDITIONAL_CLAIMS

    def test_from_service_account_file(self):
        info = SERVICE_ACCOUNT_INFO.copy()

        credentials = jwt.OnDemandCredentials.from_service_account_file(
            SERVICE_ACCOUNT_JSON_FILE
        )

        assert credentials._signer.key_id == info["private_key_id"]
        assert credentials._issuer == info["client_email"]
        assert credentials._subject == info["client_email"]

    def test_from_service_account_file_args(self):
        info = SERVICE_ACCOUNT_INFO.copy()

        credentials = jwt.OnDemandCredentials.from_service_account_file(
            SERVICE_ACCOUNT_JSON_FILE,
            subject=self.SUBJECT,
            additional_claims=self.ADDITIONAL_CLAIMS,
        )

        assert credentials._signer.key_id == info["private_key_id"]
        assert credentials._issuer == info["client_email"]
        assert credentials._subject == self.SUBJECT
        assert credentials._additional_claims == self.ADDITIONAL_CLAIMS

    def test_from_signing_credentials(self):
        jwt_from_signing = self.credentials.from_signing_credentials(self.credentials)
        jwt_from_info = jwt.OnDemandCredentials.from_service_account_info(
            SERVICE_ACCOUNT_INFO
        )

        assert isinstance(jwt_from_signing, jwt.OnDemandCredentials)
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
        assert crypt.verify_signature(to_sign, signature, PUBLIC_CERT_BYTES)

    def test_signer(self):
        assert isinstance(self.credentials.signer, crypt.RSASigner)

    def test_signer_email(self):
        assert self.credentials.signer_email == SERVICE_ACCOUNT_INFO["client_email"]

    def _verify_token(self, token):
        payload = jwt.decode(token, PUBLIC_CERT_BYTES)
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
