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

import datetime
import json

import mock
import pytest  # type: ignore
import six
from six.moves import http_client
from six.moves import urllib

from google.auth import _helpers
from google.auth import _jwt_async as jwt
from google.auth import exceptions
from google.oauth2 import _client as sync_client
from google.oauth2 import _client_async as _client
from tests.oauth2 import test__client as test_client


def make_request(response_data, status=http_client.OK, text=False):
    response = mock.AsyncMock(spec=["transport.Response"])
    response.status = status
    data = response_data if text else json.dumps(response_data).encode("utf-8")
    response.data = mock.AsyncMock(spec=["__call__", "read"])
    response.data.read = mock.AsyncMock(spec=["__call__"], return_value=data)
    response.content = mock.AsyncMock(spec=["__call__"], return_value=data)
    request = mock.AsyncMock(spec=["transport.Request"])
    request.return_value = response
    return request


@pytest.mark.asyncio
async def test__token_endpoint_request():

    request = make_request({"test": "response"})

    result = await _client._token_endpoint_request(
        request, "http://example.com", {"test": "params"}
    )

    # Check request call
    request.assert_called_with(
        method="POST",
        url="http://example.com",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        body="test=params".encode("utf-8"),
    )

    # Check result
    assert result == {"test": "response"}


@pytest.mark.asyncio
async def test__token_endpoint_request_text():

    request = make_request("response", text=True)

    result = await _client._token_endpoint_request(
        request, "http://example.com", {"test": "params"}
    )

    # Check request call
    request.assert_called_with(
        method="POST",
        url="http://example.com",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        body="test=params".encode("utf-8"),
    )

    # Check result
    assert result == "response"


@pytest.mark.asyncio
async def test__token_endpoint_request_json():

    request = make_request({"test": "response"})
    access_token = "access_token"

    result = await _client._token_endpoint_request(
        request,
        "http://example.com",
        {"test": "params"},
        access_token=access_token,
        use_json=True,
    )

    # Check request call
    request.assert_called_with(
        method="POST",
        url="http://example.com",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer access_token",
        },
        body=b'{"test": "params"}',
    )

    # Check result
    assert result == {"test": "response"}


@pytest.mark.asyncio
async def test__token_endpoint_request_error():
    request = make_request({}, status=http_client.BAD_REQUEST)

    with pytest.raises(exceptions.RefreshError) as excinfo:
        await _client._token_endpoint_request(request, "http://example.com", {})
    assert not excinfo.value.retryable


@pytest.mark.asyncio
async def test__token_endpoint_request_internal_failure_error():
    request = make_request(
        {"error_description": "internal_failure"}, status=http_client.BAD_REQUEST
    )

    with pytest.raises(exceptions.RefreshError) as excinfo:
        await _client._token_endpoint_request(
            request, "http://example.com", {"error_description": "internal_failure"}
        )
    assert excinfo.value.retryable

    request = make_request(
        {"error": "internal_failure"}, status=http_client.BAD_REQUEST
    )

    with pytest.raises(exceptions.RefreshError):
        await _client._token_endpoint_request(
            request, "http://example.com", {"error": "internal_failure"}
        )
    assert excinfo.value.retryable


@pytest.mark.asyncio
async def test__token_endpoint_request_internal_failure_and_retry_failure_error():
    retryable_error = mock.AsyncMock(spec=["transport.Response"])
    retryable_error.status = http_client.BAD_REQUEST
    data = json.dumps({"error_description": "internal_failure"}).encode("utf-8")
    retryable_error.data = mock.AsyncMock(spec=["__call__", "read"])
    retryable_error.data.read = mock.AsyncMock(spec=["__call__"], return_value=data)
    retryable_error.content = mock.AsyncMock(spec=["__call__"], return_value=data)

    unretryable_error = mock.AsyncMock(spec=["transport.Response"])
    unretryable_error.status = http_client.BAD_REQUEST
    data = json.dumps({"error_description": "invalid_scope"}).encode("utf-8")
    unretryable_error.data = mock.AsyncMock(spec=["__call__", "read"])
    unretryable_error.data.read = mock.AsyncMock(spec=["__call__"], return_value=data)
    unretryable_error.content = mock.AsyncMock(spec=["__call__"], return_value=data)

    request = mock.AsyncMock(spec=["transport.Request"])
    request.side_effect = [retryable_error, retryable_error, unretryable_error]

    with pytest.raises(exceptions.RefreshError):
        await _client._token_endpoint_request(
            request, "http://example.com", {"error_description": "invalid_scope"}
        )
    # request should be called three times. Two retryable errors and one
    # unretryable error to break the retry loop.
    assert request.call_count == 3


@pytest.mark.asyncio
async def test__token_endpoint_request_internal_failure_and_retry_succeeds():
    retryable_error = mock.AsyncMock(spec=["transport.Response"])
    retryable_error.status = http_client.BAD_REQUEST
    data = json.dumps({"error_description": "internal_failure"}).encode("utf-8")
    retryable_error.data = mock.AsyncMock(spec=["__call__", "read"])
    retryable_error.data.read = mock.AsyncMock(spec=["__call__"], return_value=data)
    retryable_error.content = mock.AsyncMock(spec=["__call__"], return_value=data)

    response = mock.AsyncMock(spec=["transport.Response"])
    response.status = http_client.OK
    data = json.dumps({"hello": "world"}).encode("utf-8")
    response.data = mock.AsyncMock(spec=["__call__", "read"])
    response.data.read = mock.AsyncMock(spec=["__call__"], return_value=data)
    response.content = mock.AsyncMock(spec=["__call__"], return_value=data)

    request = mock.AsyncMock(spec=["transport.Request"])
    request.side_effect = [retryable_error, response]

    _ = await _client._token_endpoint_request(
        request, "http://example.com", {"test": "params"}
    )

    assert request.call_count == 2


def verify_request_params(request, params):
    request_body = request.call_args[1]["body"].decode("utf-8")
    request_params = urllib.parse.parse_qs(request_body)

    for key, value in six.iteritems(params):
        assert request_params[key][0] == value


@pytest.mark.asyncio
@mock.patch("google.auth._helpers.utcnow", return_value=datetime.datetime.min)
async def test_jwt_grant(utcnow):
    request = make_request(
        {"access_token": "token", "expires_in": 500, "extra": "data"}
    )

    token, expiry, extra_data = await _client.jwt_grant(
        request, "http://example.com", "assertion_value"
    )

    # Check request call
    verify_request_params(
        request,
        {"grant_type": sync_client._JWT_GRANT_TYPE, "assertion": "assertion_value"},
    )

    # Check result
    assert token == "token"
    assert expiry == utcnow() + datetime.timedelta(seconds=500)
    assert extra_data["extra"] == "data"


@pytest.mark.asyncio
async def test_jwt_grant_no_access_token():
    request = make_request(
        {
            # No access token.
            "expires_in": 500,
            "extra": "data",
        }
    )

    with pytest.raises(exceptions.RefreshError) as excinfo:
        await _client.jwt_grant(request, "http://example.com", "assertion_value")
    assert not excinfo.value.retryable


@pytest.mark.asyncio
async def test_id_token_jwt_grant():
    now = _helpers.utcnow()
    id_token_expiry = _helpers.datetime_to_secs(now)
    id_token = jwt.encode(test_client.SIGNER, {"exp": id_token_expiry}).decode("utf-8")
    request = make_request({"id_token": id_token, "extra": "data"})

    token, expiry, extra_data = await _client.id_token_jwt_grant(
        request, "http://example.com", "assertion_value"
    )

    # Check request call
    verify_request_params(
        request,
        {"grant_type": sync_client._JWT_GRANT_TYPE, "assertion": "assertion_value"},
    )

    # Check result
    assert token == id_token
    # JWT does not store microseconds
    now = now.replace(microsecond=0)
    assert expiry == now
    assert extra_data["extra"] == "data"


@pytest.mark.asyncio
async def test_id_token_jwt_grant_no_access_token():
    request = make_request(
        {
            # No access token.
            "expires_in": 500,
            "extra": "data",
        }
    )

    with pytest.raises(exceptions.RefreshError) as excinfo:
        await _client.id_token_jwt_grant(
            request, "http://example.com", "assertion_value"
        )
    assert not excinfo.value.retryable


@pytest.mark.asyncio
@mock.patch("google.auth._helpers.utcnow", return_value=datetime.datetime.min)
async def test_refresh_grant(unused_utcnow):
    request = make_request(
        {
            "access_token": "token",
            "refresh_token": "new_refresh_token",
            "expires_in": 500,
            "extra": "data",
        }
    )

    token, refresh_token, expiry, extra_data = await _client.refresh_grant(
        request,
        "http://example.com",
        "refresh_token",
        "client_id",
        "client_secret",
        rapt_token="rapt_token",
    )

    # Check request call
    verify_request_params(
        request,
        {
            "grant_type": sync_client._REFRESH_GRANT_TYPE,
            "refresh_token": "refresh_token",
            "client_id": "client_id",
            "client_secret": "client_secret",
            "rapt": "rapt_token",
        },
    )

    # Check result
    assert token == "token"
    assert refresh_token == "new_refresh_token"
    assert expiry == datetime.datetime.min + datetime.timedelta(seconds=500)
    assert extra_data["extra"] == "data"


@pytest.mark.asyncio
@mock.patch("google.auth._helpers.utcnow", return_value=datetime.datetime.min)
async def test_refresh_grant_with_scopes(unused_utcnow):
    request = make_request(
        {
            "access_token": "token",
            "refresh_token": "new_refresh_token",
            "expires_in": 500,
            "extra": "data",
            "scope": test_client.SCOPES_AS_STRING,
        }
    )

    token, refresh_token, expiry, extra_data = await _client.refresh_grant(
        request,
        "http://example.com",
        "refresh_token",
        "client_id",
        "client_secret",
        test_client.SCOPES_AS_LIST,
    )

    # Check request call.
    verify_request_params(
        request,
        {
            "grant_type": sync_client._REFRESH_GRANT_TYPE,
            "refresh_token": "refresh_token",
            "client_id": "client_id",
            "client_secret": "client_secret",
            "scope": test_client.SCOPES_AS_STRING,
        },
    )

    # Check result.
    assert token == "token"
    assert refresh_token == "new_refresh_token"
    assert expiry == datetime.datetime.min + datetime.timedelta(seconds=500)
    assert extra_data["extra"] == "data"


@pytest.mark.asyncio
async def test_refresh_grant_no_access_token():
    request = make_request(
        {
            # No access token.
            "refresh_token": "new_refresh_token",
            "expires_in": 500,
            "extra": "data",
        }
    )

    with pytest.raises(exceptions.RefreshError) as excinfo:
        await _client.refresh_grant(
            request, "http://example.com", "refresh_token", "client_id", "client_secret"
        )
    assert not excinfo.value.retryable


@pytest.mark.asyncio
@mock.patch("google.oauth2._client._parse_expiry", return_value=None)
@mock.patch.object(_client, "_token_endpoint_request", autospec=True)
async def test_jwt_grant_retry_default(mock_token_endpoint_request, mock_expiry):
    _ = await _client.jwt_grant(mock.Mock(), mock.Mock(), mock.Mock())
    mock_token_endpoint_request.assert_called_with(
        mock.ANY, mock.ANY, mock.ANY, can_retry=True
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("can_retry", [True, False])
@mock.patch("google.oauth2._client._parse_expiry", return_value=None)
@mock.patch.object(_client, "_token_endpoint_request", autospec=True)
async def test_jwt_grant_retry_with_retry(
    mock_token_endpoint_request, mock_expiry, can_retry
):
    _ = await _client.jwt_grant(
        mock.AsyncMock(), mock.Mock(), mock.Mock(), can_retry=can_retry
    )
    mock_token_endpoint_request.assert_called_with(
        mock.ANY, mock.ANY, mock.ANY, can_retry=can_retry
    )


@pytest.mark.asyncio
@mock.patch("google.auth.jwt.decode", return_value={"exp": 0})
@mock.patch.object(_client, "_token_endpoint_request", autospec=True)
async def test_id_token_jwt_grant_retry_default(
    mock_token_endpoint_request, mock_jwt_decode
):
    _ = await _client.id_token_jwt_grant(mock.Mock(), mock.Mock(), mock.Mock())
    mock_token_endpoint_request.assert_called_with(
        mock.ANY, mock.ANY, mock.ANY, can_retry=True
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("can_retry", [True, False])
@mock.patch("google.auth.jwt.decode", return_value={"exp": 0})
@mock.patch.object(_client, "_token_endpoint_request", autospec=True)
async def test_id_token_jwt_grant_retry_with_retry(
    mock_token_endpoint_request, mock_jwt_decode, can_retry
):
    _ = await _client.id_token_jwt_grant(
        mock.AsyncMock(), mock.AsyncMock(), mock.AsyncMock(), can_retry=can_retry
    )
    mock_token_endpoint_request.assert_called_with(
        mock.ANY, mock.ANY, mock.ANY, can_retry=can_retry
    )


@pytest.mark.asyncio
@mock.patch("google.oauth2._client._parse_expiry", return_value=None)
@mock.patch.object(_client, "_token_endpoint_request", autospec=True)
async def test_refresh_grant_retry_default(
    mock_token_endpoint_request, mock_parse_expiry
):
    _ = await _client.refresh_grant(
        mock.AsyncMock(),
        mock.AsyncMock(),
        mock.AsyncMock(),
        mock.AsyncMock(),
        mock.AsyncMock(),
    )
    mock_token_endpoint_request.assert_called_with(
        mock.ANY, mock.ANY, mock.ANY, can_retry=True
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("can_retry", [True, False])
@mock.patch("google.oauth2._client._parse_expiry", return_value=None)
@mock.patch.object(_client, "_token_endpoint_request", autospec=True)
async def test_refresh_grant_retry_with_retry(
    mock_token_endpoint_request, mock_parse_expiry, can_retry
):
    _ = await _client.refresh_grant(
        mock.AsyncMock(),
        mock.AsyncMock(),
        mock.AsyncMock(),
        mock.AsyncMock(),
        mock.AsyncMock(),
        can_retry=can_retry,
    )
    mock_token_endpoint_request.assert_called_with(
        mock.ANY, mock.ANY, mock.ANY, can_retry=can_retry
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("can_retry", [True, False])
async def test__token_endpoint_request_no_throw_with_retry(can_retry):
    mock_request = make_request(
        {"error": "help", "error_description": "I'm alive"},
        http_client.INTERNAL_SERVER_ERROR,
    )

    _ = await _client._token_endpoint_request_no_throw(
        mock_request,
        mock.AsyncMock(),
        "body",
        mock.AsyncMock(),
        mock.AsyncMock(),
        can_retry=can_retry,
    )

    if can_retry:
        assert mock_request.call_count == 4
    else:
        assert mock_request.call_count == 1
