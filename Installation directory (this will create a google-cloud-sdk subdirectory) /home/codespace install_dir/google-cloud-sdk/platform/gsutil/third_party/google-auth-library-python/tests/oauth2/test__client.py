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
import pytest  # type: ignore
import six
from six.moves import http_client
from six.moves import urllib

from google.auth import _helpers
from google.auth import crypt
from google.auth import exceptions
from google.auth import jwt
from google.auth import transport
from google.oauth2 import _client


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

with open(os.path.join(DATA_DIR, "privatekey.pem"), "rb") as fh:
    PRIVATE_KEY_BYTES = fh.read()

SIGNER = crypt.RSASigner.from_string(PRIVATE_KEY_BYTES, "1")

SCOPES_AS_LIST = [
    "https://www.googleapis.com/auth/pubsub",
    "https://www.googleapis.com/auth/logging.write",
]
SCOPES_AS_STRING = (
    "https://www.googleapis.com/auth/pubsub"
    " https://www.googleapis.com/auth/logging.write"
)


@pytest.mark.parametrize("retryable", [True, False])
def test__handle_error_response(retryable):
    response_data = {"error": "help", "error_description": "I'm alive"}

    with pytest.raises(exceptions.RefreshError) as excinfo:
        _client._handle_error_response(response_data, retryable)

    assert excinfo.value.retryable == retryable
    assert excinfo.match(r"help: I\'m alive")


def test__handle_error_response_no_error():
    response_data = {"foo": "bar"}

    with pytest.raises(exceptions.RefreshError) as excinfo:
        _client._handle_error_response(response_data, False)

    assert not excinfo.value.retryable
    assert excinfo.match(r"{\"foo\": \"bar\"}")


def test__handle_error_response_not_json():
    response_data = "this is an error message"

    with pytest.raises(exceptions.RefreshError) as excinfo:
        _client._handle_error_response(response_data, False)

    assert not excinfo.value.retryable
    assert excinfo.match(response_data)


def test__can_retry_retryable():
    retryable_codes = transport.DEFAULT_RETRYABLE_STATUS_CODES
    for status_code in range(100, 600):
        if status_code in retryable_codes:
            assert _client._can_retry(status_code, {"error": "invalid_scope"})
        else:
            assert not _client._can_retry(status_code, {"error": "invalid_scope"})


@pytest.mark.parametrize(
    "response_data", [{"error": "internal_failure"}, {"error": "server_error"}]
)
def test__can_retry_message(response_data):
    assert _client._can_retry(http_client.OK, response_data)


@pytest.mark.parametrize(
    "response_data",
    [
        {"error": "invalid_scope"},
        {"error": {"foo": "bar"}},
        {"error_description": {"foo", "bar"}},
    ],
)
def test__can_retry_no_retry_message(response_data):
    assert not _client._can_retry(http_client.OK, response_data)


@pytest.mark.parametrize("mock_expires_in", [500, "500"])
@mock.patch("google.auth._helpers.utcnow", return_value=datetime.datetime.min)
def test__parse_expiry(unused_utcnow, mock_expires_in):
    result = _client._parse_expiry({"expires_in": mock_expires_in})
    assert result == datetime.datetime.min + datetime.timedelta(seconds=500)


def test__parse_expiry_none():
    assert _client._parse_expiry({}) is None


def make_request(response_data, status=http_client.OK):
    response = mock.create_autospec(transport.Response, instance=True)
    response.status = status
    response.data = json.dumps(response_data).encode("utf-8")
    request = mock.create_autospec(transport.Request)
    request.return_value = response
    return request


def test__token_endpoint_request():
    request = make_request({"test": "response"})

    result = _client._token_endpoint_request(
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


def test__token_endpoint_request_use_json():
    request = make_request({"test": "response"})

    result = _client._token_endpoint_request(
        request,
        "http://example.com",
        {"test": "params"},
        access_token="access_token",
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


def test__token_endpoint_request_error():
    request = make_request({}, status=http_client.BAD_REQUEST)

    with pytest.raises(exceptions.RefreshError):
        _client._token_endpoint_request(request, "http://example.com", {})


def test__token_endpoint_request_internal_failure_error():
    request = make_request(
        {"error_description": "internal_failure"}, status=http_client.BAD_REQUEST
    )

    with pytest.raises(exceptions.RefreshError):
        _client._token_endpoint_request(
            request, "http://example.com", {"error_description": "internal_failure"}
        )
    # request should be called once and then with 3 retries
    assert request.call_count == 4

    request = make_request(
        {"error": "internal_failure"}, status=http_client.BAD_REQUEST
    )

    with pytest.raises(exceptions.RefreshError):
        _client._token_endpoint_request(
            request, "http://example.com", {"error": "internal_failure"}
        )
    # request should be called once and then with 3 retries
    assert request.call_count == 4


def test__token_endpoint_request_internal_failure_and_retry_failure_error():
    retryable_error = mock.create_autospec(transport.Response, instance=True)
    retryable_error.status = http_client.BAD_REQUEST
    retryable_error.data = json.dumps({"error_description": "internal_failure"}).encode(
        "utf-8"
    )

    unretryable_error = mock.create_autospec(transport.Response, instance=True)
    unretryable_error.status = http_client.BAD_REQUEST
    unretryable_error.data = json.dumps({"error_description": "invalid_scope"}).encode(
        "utf-8"
    )

    request = mock.create_autospec(transport.Request)

    request.side_effect = [retryable_error, retryable_error, unretryable_error]

    with pytest.raises(exceptions.RefreshError):
        _client._token_endpoint_request(
            request, "http://example.com", {"error_description": "invalid_scope"}
        )
    # request should be called three times. Two retryable errors and one
    # unretryable error to break the retry loop.
    assert request.call_count == 3


def test__token_endpoint_request_internal_failure_and_retry_succeeds():
    retryable_error = mock.create_autospec(transport.Response, instance=True)
    retryable_error.status = http_client.BAD_REQUEST
    retryable_error.data = json.dumps({"error_description": "internal_failure"}).encode(
        "utf-8"
    )

    response = mock.create_autospec(transport.Response, instance=True)
    response.status = http_client.OK
    response.data = json.dumps({"hello": "world"}).encode("utf-8")

    request = mock.create_autospec(transport.Request)

    request.side_effect = [retryable_error, response]

    _ = _client._token_endpoint_request(
        request, "http://example.com", {"test": "params"}
    )

    assert request.call_count == 2


def test__token_endpoint_request_string_error():
    response = mock.create_autospec(transport.Response, instance=True)
    response.status = http_client.BAD_REQUEST
    response.data = "this is an error message"
    request = mock.create_autospec(transport.Request)
    request.return_value = response

    with pytest.raises(exceptions.RefreshError) as excinfo:
        _client._token_endpoint_request(request, "http://example.com", {})
    assert excinfo.match("this is an error message")


def verify_request_params(request, params):
    request_body = request.call_args[1]["body"].decode("utf-8")
    request_params = urllib.parse.parse_qs(request_body)

    for key, value in six.iteritems(params):
        assert request_params[key][0] == value


@mock.patch("google.auth._helpers.utcnow", return_value=datetime.datetime.min)
def test_jwt_grant(utcnow):
    request = make_request(
        {"access_token": "token", "expires_in": 500, "extra": "data"}
    )

    token, expiry, extra_data = _client.jwt_grant(
        request, "http://example.com", "assertion_value"
    )

    # Check request call
    verify_request_params(
        request, {"grant_type": _client._JWT_GRANT_TYPE, "assertion": "assertion_value"}
    )

    # Check result
    assert token == "token"
    assert expiry == utcnow() + datetime.timedelta(seconds=500)
    assert extra_data["extra"] == "data"


def test_jwt_grant_no_access_token():
    request = make_request(
        {
            # No access token.
            "expires_in": 500,
            "extra": "data",
        }
    )

    with pytest.raises(exceptions.RefreshError) as excinfo:
        _client.jwt_grant(request, "http://example.com", "assertion_value")
    assert not excinfo.value.retryable


def test_call_iam_generate_id_token_endpoint():
    now = _helpers.utcnow()
    id_token_expiry = _helpers.datetime_to_secs(now)
    id_token = jwt.encode(SIGNER, {"exp": id_token_expiry}).decode("utf-8")
    request = make_request({"token": id_token})

    token, expiry = _client.call_iam_generate_id_token_endpoint(
        request, "fake_email", "fake_audience", "fake_access_token"
    )

    assert (
        request.call_args[1]["url"]
        == "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/fake_email:generateIdToken"
    )
    assert request.call_args[1]["headers"]["Content-Type"] == "application/json"
    assert (
        request.call_args[1]["headers"]["Authorization"] == "Bearer fake_access_token"
    )
    response_body = json.loads(request.call_args[1]["body"])
    assert response_body["audience"] == "fake_audience"
    assert response_body["includeEmail"] == "true"
    assert response_body["useEmailAzp"] == "true"

    # Check result
    assert token == id_token
    # JWT does not store microseconds
    now = now.replace(microsecond=0)
    assert expiry == now


def test_call_iam_generate_id_token_endpoint_no_id_token():
    request = make_request(
        {
            # No access token.
            "error": "no token"
        }
    )

    with pytest.raises(exceptions.RefreshError) as excinfo:
        _client.call_iam_generate_id_token_endpoint(
            request, "fake_email", "fake_audience", "fake_access_token"
        )
    assert excinfo.match("No ID token in response")


def test_id_token_jwt_grant():
    now = _helpers.utcnow()
    id_token_expiry = _helpers.datetime_to_secs(now)
    id_token = jwt.encode(SIGNER, {"exp": id_token_expiry}).decode("utf-8")
    request = make_request({"id_token": id_token, "extra": "data"})

    token, expiry, extra_data = _client.id_token_jwt_grant(
        request, "http://example.com", "assertion_value"
    )

    # Check request call
    verify_request_params(
        request, {"grant_type": _client._JWT_GRANT_TYPE, "assertion": "assertion_value"}
    )

    # Check result
    assert token == id_token
    # JWT does not store microseconds
    now = now.replace(microsecond=0)
    assert expiry == now
    assert extra_data["extra"] == "data"


def test_id_token_jwt_grant_no_access_token():
    request = make_request(
        {
            # No access token.
            "expires_in": 500,
            "extra": "data",
        }
    )

    with pytest.raises(exceptions.RefreshError) as excinfo:
        _client.id_token_jwt_grant(request, "http://example.com", "assertion_value")
    assert not excinfo.value.retryable


@mock.patch("google.auth._helpers.utcnow", return_value=datetime.datetime.min)
def test_refresh_grant(unused_utcnow):
    request = make_request(
        {
            "access_token": "token",
            "refresh_token": "new_refresh_token",
            "expires_in": 500,
            "extra": "data",
        }
    )

    token, refresh_token, expiry, extra_data = _client.refresh_grant(
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
            "grant_type": _client._REFRESH_GRANT_TYPE,
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


@mock.patch("google.auth._helpers.utcnow", return_value=datetime.datetime.min)
def test_refresh_grant_with_scopes(unused_utcnow):
    request = make_request(
        {
            "access_token": "token",
            "refresh_token": "new_refresh_token",
            "expires_in": 500,
            "extra": "data",
            "scope": SCOPES_AS_STRING,
        }
    )

    token, refresh_token, expiry, extra_data = _client.refresh_grant(
        request,
        "http://example.com",
        "refresh_token",
        "client_id",
        "client_secret",
        SCOPES_AS_LIST,
    )

    # Check request call.
    verify_request_params(
        request,
        {
            "grant_type": _client._REFRESH_GRANT_TYPE,
            "refresh_token": "refresh_token",
            "client_id": "client_id",
            "client_secret": "client_secret",
            "scope": SCOPES_AS_STRING,
        },
    )

    # Check result.
    assert token == "token"
    assert refresh_token == "new_refresh_token"
    assert expiry == datetime.datetime.min + datetime.timedelta(seconds=500)
    assert extra_data["extra"] == "data"


def test_refresh_grant_no_access_token():
    request = make_request(
        {
            # No access token.
            "refresh_token": "new_refresh_token",
            "expires_in": 500,
            "extra": "data",
        }
    )

    with pytest.raises(exceptions.RefreshError) as excinfo:
        _client.refresh_grant(
            request, "http://example.com", "refresh_token", "client_id", "client_secret"
        )
    assert not excinfo.value.retryable


@mock.patch("google.oauth2._client._parse_expiry", return_value=None)
@mock.patch.object(_client, "_token_endpoint_request", autospec=True)
def test_jwt_grant_retry_default(mock_token_endpoint_request, mock_expiry):
    _client.jwt_grant(mock.Mock(), mock.Mock(), mock.Mock())
    mock_token_endpoint_request.assert_called_with(
        mock.ANY, mock.ANY, mock.ANY, can_retry=True
    )


@pytest.mark.parametrize("can_retry", [True, False])
@mock.patch("google.oauth2._client._parse_expiry", return_value=None)
@mock.patch.object(_client, "_token_endpoint_request", autospec=True)
def test_jwt_grant_retry_with_retry(
    mock_token_endpoint_request, mock_expiry, can_retry
):
    _client.jwt_grant(mock.Mock(), mock.Mock(), mock.Mock(), can_retry=can_retry)
    mock_token_endpoint_request.assert_called_with(
        mock.ANY, mock.ANY, mock.ANY, can_retry=can_retry
    )


@mock.patch("google.auth.jwt.decode", return_value={"exp": 0})
@mock.patch.object(_client, "_token_endpoint_request", autospec=True)
def test_id_token_jwt_grant_retry_default(mock_token_endpoint_request, mock_jwt_decode):
    _client.id_token_jwt_grant(mock.Mock(), mock.Mock(), mock.Mock())
    mock_token_endpoint_request.assert_called_with(
        mock.ANY, mock.ANY, mock.ANY, can_retry=True
    )


@pytest.mark.parametrize("can_retry", [True, False])
@mock.patch("google.auth.jwt.decode", return_value={"exp": 0})
@mock.patch.object(_client, "_token_endpoint_request", autospec=True)
def test_id_token_jwt_grant_retry_with_retry(
    mock_token_endpoint_request, mock_jwt_decode, can_retry
):
    _client.id_token_jwt_grant(
        mock.Mock(), mock.Mock(), mock.Mock(), can_retry=can_retry
    )
    mock_token_endpoint_request.assert_called_with(
        mock.ANY, mock.ANY, mock.ANY, can_retry=can_retry
    )


@mock.patch("google.oauth2._client._parse_expiry", return_value=None)
@mock.patch.object(_client, "_token_endpoint_request", autospec=True)
def test_refresh_grant_retry_default(mock_token_endpoint_request, mock_parse_expiry):
    _client.refresh_grant(
        mock.Mock(), mock.Mock(), mock.Mock(), mock.Mock(), mock.Mock()
    )
    mock_token_endpoint_request.assert_called_with(
        mock.ANY, mock.ANY, mock.ANY, can_retry=True
    )


@pytest.mark.parametrize("can_retry", [True, False])
@mock.patch("google.oauth2._client._parse_expiry", return_value=None)
@mock.patch.object(_client, "_token_endpoint_request", autospec=True)
def test_refresh_grant_retry_with_retry(
    mock_token_endpoint_request, mock_parse_expiry, can_retry
):
    _client.refresh_grant(
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
        can_retry=can_retry,
    )
    mock_token_endpoint_request.assert_called_with(
        mock.ANY, mock.ANY, mock.ANY, can_retry=can_retry
    )


@pytest.mark.parametrize("can_retry", [True, False])
def test__token_endpoint_request_no_throw_with_retry(can_retry):
    response_data = {"error": "help", "error_description": "I'm alive"}
    body = "dummy body"

    mock_response = mock.create_autospec(transport.Response, instance=True)
    mock_response.status = http_client.INTERNAL_SERVER_ERROR
    mock_response.data = json.dumps(response_data).encode("utf-8")

    mock_request = mock.create_autospec(transport.Request)
    mock_request.return_value = mock_response

    _client._token_endpoint_request_no_throw(
        mock_request, mock.Mock(), body, mock.Mock(), mock.Mock(), can_retry=can_retry
    )

    if can_retry:
        assert mock_request.call_count == 4
    else:
        assert mock_request.call_count == 1
