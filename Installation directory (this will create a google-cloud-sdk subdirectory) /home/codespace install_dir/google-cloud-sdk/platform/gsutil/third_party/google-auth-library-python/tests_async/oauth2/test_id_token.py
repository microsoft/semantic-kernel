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

import json
import os

import mock
import pytest  # type: ignore

from google.auth import environment_vars
from google.auth import exceptions
import google.auth.compute_engine._metadata
from google.oauth2 import _id_token_async as id_token
from google.oauth2 import _service_account_async
from google.oauth2 import id_token as sync_id_token
from tests.oauth2 import test_id_token


def make_request(status, data=None):
    response = mock.AsyncMock(spec=["transport.Response"])
    response.status = status

    if data is not None:
        response.data = mock.AsyncMock(spec=["__call__", "read"])
        response.content = mock.AsyncMock(
            spec=["__call__"], return_value=json.dumps(data).encode("utf-8")
        )

    request = mock.AsyncMock(spec=["transport.Request"])
    request.return_value = response
    return request


@pytest.mark.asyncio
async def test__fetch_certs_success():
    certs = {"1": "cert"}
    request = make_request(200, certs)

    returned_certs = await id_token._fetch_certs(request, mock.sentinel.cert_url)

    request.assert_called_once_with(mock.sentinel.cert_url, method="GET")
    assert returned_certs == certs


@pytest.mark.asyncio
async def test__fetch_certs_failure():
    request = make_request(404)

    with pytest.raises(exceptions.TransportError):
        await id_token._fetch_certs(request, mock.sentinel.cert_url)

    request.assert_called_once_with(mock.sentinel.cert_url, method="GET")


@mock.patch("google.auth.jwt.decode", autospec=True)
@mock.patch("google.oauth2._id_token_async._fetch_certs", autospec=True)
@pytest.mark.asyncio
async def test_verify_token(_fetch_certs, decode):
    result = await id_token.verify_token(mock.sentinel.token, mock.sentinel.request)

    assert result == decode.return_value
    _fetch_certs.assert_called_once_with(
        mock.sentinel.request, sync_id_token._GOOGLE_OAUTH2_CERTS_URL
    )
    decode.assert_called_once_with(
        mock.sentinel.token,
        certs=_fetch_certs.return_value,
        audience=None,
        clock_skew_in_seconds=0,
    )


@mock.patch("google.auth.jwt.decode", autospec=True)
@mock.patch("google.oauth2._id_token_async._fetch_certs", autospec=True)
@pytest.mark.asyncio
async def test_verify_token_clock_skew(_fetch_certs, decode):
    result = await id_token.verify_token(
        mock.sentinel.token, mock.sentinel.request, clock_skew_in_seconds=10
    )

    assert result == decode.return_value
    _fetch_certs.assert_called_once_with(
        mock.sentinel.request, sync_id_token._GOOGLE_OAUTH2_CERTS_URL
    )
    decode.assert_called_once_with(
        mock.sentinel.token,
        certs=_fetch_certs.return_value,
        audience=None,
        clock_skew_in_seconds=10,
    )


@mock.patch("google.auth.jwt.decode", autospec=True)
@mock.patch("google.oauth2._id_token_async._fetch_certs", autospec=True)
@pytest.mark.asyncio
async def test_verify_token_args(_fetch_certs, decode):
    result = await id_token.verify_token(
        mock.sentinel.token,
        mock.sentinel.request,
        audience=mock.sentinel.audience,
        certs_url=mock.sentinel.certs_url,
    )

    assert result == decode.return_value
    _fetch_certs.assert_called_once_with(mock.sentinel.request, mock.sentinel.certs_url)
    decode.assert_called_once_with(
        mock.sentinel.token,
        certs=_fetch_certs.return_value,
        audience=mock.sentinel.audience,
        clock_skew_in_seconds=0,
    )


@mock.patch("google.oauth2._id_token_async.verify_token", autospec=True)
@pytest.mark.asyncio
async def test_verify_oauth2_token(verify_token):
    verify_token.return_value = {"iss": "accounts.google.com"}
    result = await id_token.verify_oauth2_token(
        mock.sentinel.token, mock.sentinel.request, audience=mock.sentinel.audience
    )

    assert result == verify_token.return_value
    verify_token.assert_called_once_with(
        mock.sentinel.token,
        mock.sentinel.request,
        audience=mock.sentinel.audience,
        certs_url=sync_id_token._GOOGLE_OAUTH2_CERTS_URL,
        clock_skew_in_seconds=0,
    )


@mock.patch("google.oauth2._id_token_async.verify_token", autospec=True)
@pytest.mark.asyncio
async def test_verify_oauth2_token_clock_skew(verify_token):
    verify_token.return_value = {"iss": "accounts.google.com"}
    result = await id_token.verify_oauth2_token(
        mock.sentinel.token,
        mock.sentinel.request,
        audience=mock.sentinel.audience,
        clock_skew_in_seconds=10,
    )

    assert result == verify_token.return_value
    verify_token.assert_called_once_with(
        mock.sentinel.token,
        mock.sentinel.request,
        audience=mock.sentinel.audience,
        certs_url=sync_id_token._GOOGLE_OAUTH2_CERTS_URL,
        clock_skew_in_seconds=10,
    )


@mock.patch("google.oauth2._id_token_async.verify_token", autospec=True)
@pytest.mark.asyncio
async def test_verify_oauth2_token_invalid_iss(verify_token):
    verify_token.return_value = {"iss": "invalid_issuer"}

    with pytest.raises(exceptions.GoogleAuthError):
        await id_token.verify_oauth2_token(
            mock.sentinel.token, mock.sentinel.request, audience=mock.sentinel.audience
        )


@mock.patch("google.oauth2._id_token_async.verify_token", autospec=True)
@pytest.mark.asyncio
async def test_verify_firebase_token(verify_token):
    result = await id_token.verify_firebase_token(
        mock.sentinel.token, mock.sentinel.request, audience=mock.sentinel.audience
    )

    assert result == verify_token.return_value
    verify_token.assert_called_once_with(
        mock.sentinel.token,
        mock.sentinel.request,
        audience=mock.sentinel.audience,
        certs_url=sync_id_token._GOOGLE_APIS_CERTS_URL,
        clock_skew_in_seconds=0,
    )


@mock.patch("google.oauth2._id_token_async.verify_token", autospec=True)
@pytest.mark.asyncio
async def test_verify_firebase_token_clock_skew(verify_token):
    result = await id_token.verify_firebase_token(
        mock.sentinel.token,
        mock.sentinel.request,
        audience=mock.sentinel.audience,
        clock_skew_in_seconds=10,
    )

    assert result == verify_token.return_value
    verify_token.assert_called_once_with(
        mock.sentinel.token,
        mock.sentinel.request,
        audience=mock.sentinel.audience,
        certs_url=sync_id_token._GOOGLE_APIS_CERTS_URL,
        clock_skew_in_seconds=10,
    )


@pytest.mark.asyncio
async def test_fetch_id_token_from_metadata_server(monkeypatch):
    monkeypatch.delenv(environment_vars.CREDENTIALS, raising=False)

    def mock_init(self, request, audience, use_metadata_identity_endpoint):
        assert use_metadata_identity_endpoint
        self.token = "id_token"

    with mock.patch("google.auth.compute_engine._metadata.ping", return_value=True):
        with mock.patch.multiple(
            google.auth.compute_engine.IDTokenCredentials,
            __init__=mock_init,
            refresh=mock.Mock(),
        ):
            request = mock.AsyncMock()
            token = await id_token.fetch_id_token(
                request, "https://pubsub.googleapis.com"
            )
            assert token == "id_token"


@pytest.mark.asyncio
async def test_fetch_id_token_from_explicit_cred_json_file(monkeypatch):
    monkeypatch.setenv(environment_vars.CREDENTIALS, test_id_token.SERVICE_ACCOUNT_FILE)

    async def mock_refresh(self, request):
        self.token = "id_token"

    with mock.patch.object(
        _service_account_async.IDTokenCredentials, "refresh", mock_refresh
    ):
        request = mock.AsyncMock()
        token = await id_token.fetch_id_token(request, "https://pubsub.googleapis.com")
        assert token == "id_token"


@pytest.mark.asyncio
async def test_fetch_id_token_no_cred_exists(monkeypatch):
    monkeypatch.delenv(environment_vars.CREDENTIALS, raising=False)

    with mock.patch(
        "google.auth.compute_engine._metadata.ping",
        side_effect=exceptions.TransportError(),
    ):
        with pytest.raises(exceptions.DefaultCredentialsError) as excinfo:
            request = mock.AsyncMock()
            await id_token.fetch_id_token(request, "https://pubsub.googleapis.com")
        assert excinfo.match(
            r"Neither metadata server or valid service account credentials are found."
        )

    with mock.patch("google.auth.compute_engine._metadata.ping", return_value=False):
        with pytest.raises(exceptions.DefaultCredentialsError) as excinfo:
            request = mock.AsyncMock()
            await id_token.fetch_id_token(request, "https://pubsub.googleapis.com")
        assert excinfo.match(
            r"Neither metadata server or valid service account credentials are found."
        )


@pytest.mark.asyncio
async def test_fetch_id_token_invalid_cred_file(monkeypatch):
    not_json_file = os.path.join(
        os.path.dirname(__file__), "../../tests/data/public_cert.pem"
    )
    monkeypatch.setenv(environment_vars.CREDENTIALS, not_json_file)

    with pytest.raises(exceptions.DefaultCredentialsError) as excinfo:
        request = mock.AsyncMock()
        await id_token.fetch_id_token(request, "https://pubsub.googleapis.com")
    assert excinfo.match(
        r"GOOGLE_APPLICATION_CREDENTIALS is not valid service account credentials."
    )


@pytest.mark.asyncio
async def test_fetch_id_token_invalid_cred_type(monkeypatch):
    user_credentials_file = os.path.join(
        os.path.dirname(__file__), "../../tests/data/authorized_user.json"
    )
    monkeypatch.setenv(environment_vars.CREDENTIALS, user_credentials_file)

    with mock.patch("google.auth.compute_engine._metadata.ping", return_value=False):
        with pytest.raises(exceptions.DefaultCredentialsError) as excinfo:
            request = mock.AsyncMock()
            await id_token.fetch_id_token(request, "https://pubsub.googleapis.com")
        assert excinfo.match(
            r"Neither metadata server or valid service account credentials are found."
        )


@pytest.mark.asyncio
async def test_fetch_id_token_invalid_cred_path(monkeypatch):
    not_json_file = os.path.join(
        os.path.dirname(__file__), "../../tests/data/not_exists.json"
    )
    monkeypatch.setenv(environment_vars.CREDENTIALS, not_json_file)

    with pytest.raises(exceptions.DefaultCredentialsError) as excinfo:
        request = mock.AsyncMock()
        await id_token.fetch_id_token(request, "https://pubsub.googleapis.com")
    assert excinfo.match(
        r"GOOGLE_APPLICATION_CREDENTIALS path is either not found or invalid."
    )
