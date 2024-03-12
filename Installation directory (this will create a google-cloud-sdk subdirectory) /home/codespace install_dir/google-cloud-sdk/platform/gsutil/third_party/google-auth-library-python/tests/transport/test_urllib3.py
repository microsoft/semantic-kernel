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

import os
import sys

import mock
import OpenSSL
import pytest  # type: ignore
from six.moves import http_client
import urllib3  # type: ignore

from google.auth import environment_vars
from google.auth import exceptions
import google.auth.credentials
import google.auth.transport._mtls_helper
import google.auth.transport.urllib3
from google.oauth2 import service_account
from tests.transport import compliance


class TestRequestResponse(compliance.RequestResponseTests):
    def make_request(self):
        http = urllib3.PoolManager()
        return google.auth.transport.urllib3.Request(http)

    def test_timeout(self):
        http = mock.create_autospec(urllib3.PoolManager)
        request = google.auth.transport.urllib3.Request(http)
        request(url="http://example.com", method="GET", timeout=5)

        assert http.request.call_args[1]["timeout"] == 5


def test__make_default_http_with_certifi():
    http = google.auth.transport.urllib3._make_default_http()
    assert "cert_reqs" in http.connection_pool_kw


@mock.patch.object(google.auth.transport.urllib3, "certifi", new=None)
def test__make_default_http_without_certifi():
    http = google.auth.transport.urllib3._make_default_http()
    assert "cert_reqs" not in http.connection_pool_kw


class CredentialsStub(google.auth.credentials.Credentials):
    def __init__(self, token="token"):
        super(CredentialsStub, self).__init__()
        self.token = token

    def apply(self, headers, token=None):
        headers["authorization"] = self.token

    def before_request(self, request, method, url, headers):
        self.apply(headers)

    def refresh(self, request):
        self.token += "1"

    def with_quota_project(self, quota_project_id):
        raise NotImplementedError()


class HttpStub(object):
    def __init__(self, responses, headers=None):
        self.responses = responses
        self.requests = []
        self.headers = headers or {}

    def urlopen(self, method, url, body=None, headers=None, **kwargs):
        self.requests.append((method, url, body, headers, kwargs))
        return self.responses.pop(0)

    def clear(self):
        pass


class ResponseStub(object):
    def __init__(self, status=http_client.OK, data=None):
        self.status = status
        self.data = data


class TestMakeMutualTlsHttp(object):
    def test_success(self):
        http = google.auth.transport.urllib3._make_mutual_tls_http(
            pytest.public_cert_bytes, pytest.private_key_bytes
        )
        assert isinstance(http, urllib3.PoolManager)

    def test_crypto_error(self):
        with pytest.raises(OpenSSL.crypto.Error):
            google.auth.transport.urllib3._make_mutual_tls_http(
                b"invalid cert", b"invalid key"
            )

    @mock.patch.dict("sys.modules", {"OpenSSL.crypto": None})
    def test_import_error(self):
        with pytest.raises(ImportError):
            google.auth.transport.urllib3._make_mutual_tls_http(
                pytest.public_cert_bytes, pytest.private_key_bytes
            )


class TestAuthorizedHttp(object):
    TEST_URL = "http://example.com"

    def test_authed_http_defaults(self):
        authed_http = google.auth.transport.urllib3.AuthorizedHttp(
            mock.sentinel.credentials
        )

        assert authed_http.credentials == mock.sentinel.credentials
        assert isinstance(authed_http.http, urllib3.PoolManager)

    def test_urlopen_no_refresh(self):
        credentials = mock.Mock(wraps=CredentialsStub())
        response = ResponseStub()
        http = HttpStub([response])

        authed_http = google.auth.transport.urllib3.AuthorizedHttp(
            credentials, http=http
        )

        result = authed_http.urlopen("GET", self.TEST_URL)

        assert result == response
        assert credentials.before_request.called
        assert not credentials.refresh.called
        assert http.requests == [
            ("GET", self.TEST_URL, None, {"authorization": "token"}, {})
        ]

    def test_urlopen_refresh(self):
        credentials = mock.Mock(wraps=CredentialsStub())
        final_response = ResponseStub(status=http_client.OK)
        # First request will 401, second request will succeed.
        http = HttpStub([ResponseStub(status=http_client.UNAUTHORIZED), final_response])

        authed_http = google.auth.transport.urllib3.AuthorizedHttp(
            credentials, http=http
        )

        authed_http = authed_http.urlopen("GET", "http://example.com")

        assert authed_http == final_response
        assert credentials.before_request.call_count == 2
        assert credentials.refresh.called
        assert http.requests == [
            ("GET", self.TEST_URL, None, {"authorization": "token"}, {}),
            ("GET", self.TEST_URL, None, {"authorization": "token1"}, {}),
        ]

    def test_urlopen_no_default_host(self):
        credentials = mock.create_autospec(service_account.Credentials)

        authed_http = google.auth.transport.urllib3.AuthorizedHttp(credentials)

        authed_http.credentials._create_self_signed_jwt.assert_called_once_with(None)

    def test_urlopen_with_default_host(self):
        default_host = "pubsub.googleapis.com"
        credentials = mock.create_autospec(service_account.Credentials)

        authed_http = google.auth.transport.urllib3.AuthorizedHttp(
            credentials, default_host=default_host
        )

        authed_http.credentials._create_self_signed_jwt.assert_called_once_with(
            "https://{}/".format(default_host)
        )

    def test_proxies(self):
        http = mock.create_autospec(urllib3.PoolManager)
        authed_http = google.auth.transport.urllib3.AuthorizedHttp(None, http=http)

        with authed_http:
            pass

        assert http.__enter__.called
        assert http.__exit__.called

        authed_http.headers = mock.sentinel.headers
        assert authed_http.headers == http.headers

    @mock.patch("google.auth.transport.urllib3._make_mutual_tls_http", autospec=True)
    def test_configure_mtls_channel_with_callback(self, mock_make_mutual_tls_http):
        callback = mock.Mock()
        callback.return_value = (pytest.public_cert_bytes, pytest.private_key_bytes)

        authed_http = google.auth.transport.urllib3.AuthorizedHttp(
            credentials=mock.Mock(), http=mock.Mock()
        )

        with pytest.warns(UserWarning):
            with mock.patch.dict(
                os.environ, {environment_vars.GOOGLE_API_USE_CLIENT_CERTIFICATE: "true"}
            ):
                is_mtls = authed_http.configure_mtls_channel(callback)

        assert is_mtls
        mock_make_mutual_tls_http.assert_called_once_with(
            cert=pytest.public_cert_bytes, key=pytest.private_key_bytes
        )

    @mock.patch("google.auth.transport.urllib3._make_mutual_tls_http", autospec=True)
    @mock.patch(
        "google.auth.transport._mtls_helper.get_client_cert_and_key", autospec=True
    )
    def test_configure_mtls_channel_with_metadata(
        self, mock_get_client_cert_and_key, mock_make_mutual_tls_http
    ):
        authed_http = google.auth.transport.urllib3.AuthorizedHttp(
            credentials=mock.Mock()
        )

        mock_get_client_cert_and_key.return_value = (
            True,
            pytest.public_cert_bytes,
            pytest.private_key_bytes,
        )
        with mock.patch.dict(
            os.environ, {environment_vars.GOOGLE_API_USE_CLIENT_CERTIFICATE: "true"}
        ):
            is_mtls = authed_http.configure_mtls_channel()

        assert is_mtls
        mock_get_client_cert_and_key.assert_called_once()
        mock_make_mutual_tls_http.assert_called_once_with(
            cert=pytest.public_cert_bytes, key=pytest.private_key_bytes
        )

    @mock.patch("google.auth.transport.urllib3._make_mutual_tls_http", autospec=True)
    @mock.patch(
        "google.auth.transport._mtls_helper.get_client_cert_and_key", autospec=True
    )
    def test_configure_mtls_channel_non_mtls(
        self, mock_get_client_cert_and_key, mock_make_mutual_tls_http
    ):
        authed_http = google.auth.transport.urllib3.AuthorizedHttp(
            credentials=mock.Mock()
        )

        mock_get_client_cert_and_key.return_value = (False, None, None)
        with mock.patch.dict(
            os.environ, {environment_vars.GOOGLE_API_USE_CLIENT_CERTIFICATE: "true"}
        ):
            is_mtls = authed_http.configure_mtls_channel()

        assert not is_mtls
        mock_get_client_cert_and_key.assert_called_once()
        mock_make_mutual_tls_http.assert_not_called()

    @mock.patch(
        "google.auth.transport._mtls_helper.get_client_cert_and_key", autospec=True
    )
    def test_configure_mtls_channel_exceptions(self, mock_get_client_cert_and_key):
        authed_http = google.auth.transport.urllib3.AuthorizedHttp(
            credentials=mock.Mock()
        )

        mock_get_client_cert_and_key.side_effect = exceptions.ClientCertError()
        with pytest.raises(exceptions.MutualTLSChannelError):
            with mock.patch.dict(
                os.environ, {environment_vars.GOOGLE_API_USE_CLIENT_CERTIFICATE: "true"}
            ):
                authed_http.configure_mtls_channel()

        mock_get_client_cert_and_key.return_value = (False, None, None)
        with mock.patch.dict("sys.modules"):
            sys.modules["OpenSSL"] = None
            with pytest.raises(exceptions.MutualTLSChannelError):
                with mock.patch.dict(
                    os.environ,
                    {environment_vars.GOOGLE_API_USE_CLIENT_CERTIFICATE: "true"},
                ):
                    authed_http.configure_mtls_channel()

    @mock.patch(
        "google.auth.transport._mtls_helper.get_client_cert_and_key", autospec=True
    )
    def test_configure_mtls_channel_without_client_cert_env(
        self, get_client_cert_and_key
    ):
        callback = mock.Mock()

        authed_http = google.auth.transport.urllib3.AuthorizedHttp(
            credentials=mock.Mock(), http=mock.Mock()
        )

        # Test the callback is not called if GOOGLE_API_USE_CLIENT_CERTIFICATE is not set.
        is_mtls = authed_http.configure_mtls_channel(callback)
        assert not is_mtls
        callback.assert_not_called()

        # Test ADC client cert is not used if GOOGLE_API_USE_CLIENT_CERTIFICATE is not set.
        is_mtls = authed_http.configure_mtls_channel(callback)
        assert not is_mtls
        get_client_cert_and_key.assert_not_called()

    def test_clear_pool_on_del(self):
        http = mock.create_autospec(urllib3.PoolManager)
        authed_http = google.auth.transport.urllib3.AuthorizedHttp(
            mock.sentinel.credentials, http=http
        )
        authed_http.__del__()
        http.clear.assert_called_with()

        authed_http.http = None
        authed_http.__del__()
        # Expect it to not crash
