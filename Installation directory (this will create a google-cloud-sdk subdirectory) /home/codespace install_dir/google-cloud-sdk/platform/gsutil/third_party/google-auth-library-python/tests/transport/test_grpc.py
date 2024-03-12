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
import os
import time

import mock
import pytest  # type: ignore

from google.auth import _helpers
from google.auth import credentials
from google.auth import environment_vars
from google.auth import exceptions
from google.auth import transport
from google.oauth2 import service_account

try:
    # pylint: disable=ungrouped-imports
    import grpc  # type: ignore
    import google.auth.transport.grpc

    HAS_GRPC = True
except ImportError:  # pragma: NO COVER
    HAS_GRPC = False

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
METADATA_PATH = os.path.join(DATA_DIR, "context_aware_metadata.json")
with open(os.path.join(DATA_DIR, "privatekey.pem"), "rb") as fh:
    PRIVATE_KEY_BYTES = fh.read()
with open(os.path.join(DATA_DIR, "public_cert.pem"), "rb") as fh:
    PUBLIC_CERT_BYTES = fh.read()

pytestmark = pytest.mark.skipif(not HAS_GRPC, reason="gRPC is unavailable.")


class CredentialsStub(credentials.Credentials):
    def __init__(self, token="token"):
        super(CredentialsStub, self).__init__()
        self.token = token
        self.expiry = None

    def refresh(self, request):
        self.token += "1"

    def with_quota_project(self, quota_project_id):
        raise NotImplementedError()


class TestAuthMetadataPlugin(object):
    def test_call_no_refresh(self):
        credentials = CredentialsStub()
        request = mock.create_autospec(transport.Request)

        plugin = google.auth.transport.grpc.AuthMetadataPlugin(credentials, request)

        context = mock.create_autospec(grpc.AuthMetadataContext, instance=True)
        context.method_name = mock.sentinel.method_name
        context.service_url = mock.sentinel.service_url
        callback = mock.create_autospec(grpc.AuthMetadataPluginCallback)

        plugin(context, callback)

        time.sleep(2)

        callback.assert_called_once_with(
            [("authorization", "Bearer {}".format(credentials.token))], None
        )

    def test_call_refresh(self):
        credentials = CredentialsStub()
        credentials.expiry = datetime.datetime.min + _helpers.REFRESH_THRESHOLD
        request = mock.create_autospec(transport.Request)

        plugin = google.auth.transport.grpc.AuthMetadataPlugin(credentials, request)

        context = mock.create_autospec(grpc.AuthMetadataContext, instance=True)
        context.method_name = mock.sentinel.method_name
        context.service_url = mock.sentinel.service_url
        callback = mock.create_autospec(grpc.AuthMetadataPluginCallback)

        plugin(context, callback)

        time.sleep(2)

        assert credentials.token == "token1"
        callback.assert_called_once_with(
            [("authorization", "Bearer {}".format(credentials.token))], None
        )

    def test__get_authorization_headers_with_service_account(self):
        credentials = mock.create_autospec(service_account.Credentials)
        request = mock.create_autospec(transport.Request)

        plugin = google.auth.transport.grpc.AuthMetadataPlugin(credentials, request)

        context = mock.create_autospec(grpc.AuthMetadataContext, instance=True)
        context.method_name = "methodName"
        context.service_url = "https://pubsub.googleapis.com/methodName"

        plugin._get_authorization_headers(context)

        credentials._create_self_signed_jwt.assert_called_once_with(None)

    def test__get_authorization_headers_with_service_account_and_default_host(self):
        credentials = mock.create_autospec(service_account.Credentials)
        request = mock.create_autospec(transport.Request)

        default_host = "pubsub.googleapis.com"
        plugin = google.auth.transport.grpc.AuthMetadataPlugin(
            credentials, request, default_host=default_host
        )

        context = mock.create_autospec(grpc.AuthMetadataContext, instance=True)
        context.method_name = "methodName"
        context.service_url = "https://pubsub.googleapis.com/methodName"

        plugin._get_authorization_headers(context)

        credentials._create_self_signed_jwt.assert_called_once_with(
            "https://{}/".format(default_host)
        )


@mock.patch(
    "google.auth.transport._mtls_helper.get_client_ssl_credentials", autospec=True
)
@mock.patch("grpc.composite_channel_credentials", autospec=True)
@mock.patch("grpc.metadata_call_credentials", autospec=True)
@mock.patch("grpc.ssl_channel_credentials", autospec=True)
@mock.patch("grpc.secure_channel", autospec=True)
class TestSecureAuthorizedChannel(object):
    @mock.patch(
        "google.auth.transport._mtls_helper._read_dca_metadata_file", autospec=True
    )
    @mock.patch(
        "google.auth.transport._mtls_helper._check_dca_metadata_path", autospec=True
    )
    def test_secure_authorized_channel_adc(
        self,
        check_dca_metadata_path,
        read_dca_metadata_file,
        secure_channel,
        ssl_channel_credentials,
        metadata_call_credentials,
        composite_channel_credentials,
        get_client_ssl_credentials,
    ):
        credentials = CredentialsStub()
        request = mock.create_autospec(transport.Request)
        target = "example.com:80"

        # Mock the context aware metadata and client cert/key so mTLS SSL channel
        # will be used.
        check_dca_metadata_path.return_value = METADATA_PATH
        read_dca_metadata_file.return_value = {
            "cert_provider_command": ["some command"]
        }
        get_client_ssl_credentials.return_value = (
            True,
            PUBLIC_CERT_BYTES,
            PRIVATE_KEY_BYTES,
            None,
        )

        channel = None
        with mock.patch.dict(
            os.environ, {environment_vars.GOOGLE_API_USE_CLIENT_CERTIFICATE: "true"}
        ):
            channel = google.auth.transport.grpc.secure_authorized_channel(
                credentials, request, target, options=mock.sentinel.options
            )

        # Check the auth plugin construction.
        auth_plugin = metadata_call_credentials.call_args[0][0]
        assert isinstance(auth_plugin, google.auth.transport.grpc.AuthMetadataPlugin)
        assert auth_plugin._credentials == credentials
        assert auth_plugin._request == request

        # Check the ssl channel call.
        ssl_channel_credentials.assert_called_once_with(
            certificate_chain=PUBLIC_CERT_BYTES, private_key=PRIVATE_KEY_BYTES
        )

        # Check the composite credentials call.
        composite_channel_credentials.assert_called_once_with(
            ssl_channel_credentials.return_value, metadata_call_credentials.return_value
        )

        # Check the channel call.
        secure_channel.assert_called_once_with(
            target,
            composite_channel_credentials.return_value,
            options=mock.sentinel.options,
        )
        assert channel == secure_channel.return_value

    @mock.patch("google.auth.transport.grpc.SslCredentials", autospec=True)
    def test_secure_authorized_channel_adc_without_client_cert_env(
        self,
        ssl_credentials_adc_method,
        secure_channel,
        ssl_channel_credentials,
        metadata_call_credentials,
        composite_channel_credentials,
        get_client_ssl_credentials,
    ):
        # Test client cert won't be used if GOOGLE_API_USE_CLIENT_CERTIFICATE
        # environment variable is not set.
        credentials = CredentialsStub()
        request = mock.create_autospec(transport.Request)
        target = "example.com:80"

        channel = google.auth.transport.grpc.secure_authorized_channel(
            credentials, request, target, options=mock.sentinel.options
        )

        # Check the auth plugin construction.
        auth_plugin = metadata_call_credentials.call_args[0][0]
        assert isinstance(auth_plugin, google.auth.transport.grpc.AuthMetadataPlugin)
        assert auth_plugin._credentials == credentials
        assert auth_plugin._request == request

        # Check the ssl channel call.
        ssl_channel_credentials.assert_called_once()
        ssl_credentials_adc_method.assert_not_called()

        # Check the composite credentials call.
        composite_channel_credentials.assert_called_once_with(
            ssl_channel_credentials.return_value, metadata_call_credentials.return_value
        )

        # Check the channel call.
        secure_channel.assert_called_once_with(
            target,
            composite_channel_credentials.return_value,
            options=mock.sentinel.options,
        )
        assert channel == secure_channel.return_value

    def test_secure_authorized_channel_explicit_ssl(
        self,
        secure_channel,
        ssl_channel_credentials,
        metadata_call_credentials,
        composite_channel_credentials,
        get_client_ssl_credentials,
    ):
        credentials = mock.Mock()
        request = mock.Mock()
        target = "example.com:80"
        ssl_credentials = mock.Mock()

        google.auth.transport.grpc.secure_authorized_channel(
            credentials, request, target, ssl_credentials=ssl_credentials
        )

        # Since explicit SSL credentials are provided, get_client_ssl_credentials
        # shouldn't be called.
        assert not get_client_ssl_credentials.called

        # Check the ssl channel call.
        assert not ssl_channel_credentials.called

        # Check the composite credentials call.
        composite_channel_credentials.assert_called_once_with(
            ssl_credentials, metadata_call_credentials.return_value
        )

    def test_secure_authorized_channel_mutual_exclusive(
        self,
        secure_channel,
        ssl_channel_credentials,
        metadata_call_credentials,
        composite_channel_credentials,
        get_client_ssl_credentials,
    ):
        credentials = mock.Mock()
        request = mock.Mock()
        target = "example.com:80"
        ssl_credentials = mock.Mock()
        client_cert_callback = mock.Mock()

        with pytest.raises(ValueError):
            google.auth.transport.grpc.secure_authorized_channel(
                credentials,
                request,
                target,
                ssl_credentials=ssl_credentials,
                client_cert_callback=client_cert_callback,
            )

    def test_secure_authorized_channel_with_client_cert_callback_success(
        self,
        secure_channel,
        ssl_channel_credentials,
        metadata_call_credentials,
        composite_channel_credentials,
        get_client_ssl_credentials,
    ):
        credentials = mock.Mock()
        request = mock.Mock()
        target = "example.com:80"
        client_cert_callback = mock.Mock()
        client_cert_callback.return_value = (PUBLIC_CERT_BYTES, PRIVATE_KEY_BYTES)

        with mock.patch.dict(
            os.environ, {environment_vars.GOOGLE_API_USE_CLIENT_CERTIFICATE: "true"}
        ):
            google.auth.transport.grpc.secure_authorized_channel(
                credentials, request, target, client_cert_callback=client_cert_callback
            )

        client_cert_callback.assert_called_once()

        # Check we are using the cert and key provided by client_cert_callback.
        ssl_channel_credentials.assert_called_once_with(
            certificate_chain=PUBLIC_CERT_BYTES, private_key=PRIVATE_KEY_BYTES
        )

        # Check the composite credentials call.
        composite_channel_credentials.assert_called_once_with(
            ssl_channel_credentials.return_value, metadata_call_credentials.return_value
        )

    @mock.patch(
        "google.auth.transport._mtls_helper._read_dca_metadata_file", autospec=True
    )
    @mock.patch(
        "google.auth.transport._mtls_helper._check_dca_metadata_path", autospec=True
    )
    def test_secure_authorized_channel_with_client_cert_callback_failure(
        self,
        check_dca_metadata_path,
        read_dca_metadata_file,
        secure_channel,
        ssl_channel_credentials,
        metadata_call_credentials,
        composite_channel_credentials,
        get_client_ssl_credentials,
    ):
        credentials = mock.Mock()
        request = mock.Mock()
        target = "example.com:80"

        client_cert_callback = mock.Mock()
        client_cert_callback.side_effect = Exception("callback exception")

        with pytest.raises(Exception) as excinfo:
            with mock.patch.dict(
                os.environ, {environment_vars.GOOGLE_API_USE_CLIENT_CERTIFICATE: "true"}
            ):
                google.auth.transport.grpc.secure_authorized_channel(
                    credentials,
                    request,
                    target,
                    client_cert_callback=client_cert_callback,
                )

        assert str(excinfo.value) == "callback exception"

    def test_secure_authorized_channel_cert_callback_without_client_cert_env(
        self,
        secure_channel,
        ssl_channel_credentials,
        metadata_call_credentials,
        composite_channel_credentials,
        get_client_ssl_credentials,
    ):
        # Test client cert won't be used if GOOGLE_API_USE_CLIENT_CERTIFICATE
        # environment variable is not set.
        credentials = mock.Mock()
        request = mock.Mock()
        target = "example.com:80"
        client_cert_callback = mock.Mock()

        google.auth.transport.grpc.secure_authorized_channel(
            credentials, request, target, client_cert_callback=client_cert_callback
        )

        # Check client_cert_callback is not called because GOOGLE_API_USE_CLIENT_CERTIFICATE
        # is not set.
        client_cert_callback.assert_not_called()

        ssl_channel_credentials.assert_called_once()

        # Check the composite credentials call.
        composite_channel_credentials.assert_called_once_with(
            ssl_channel_credentials.return_value, metadata_call_credentials.return_value
        )


@mock.patch("grpc.ssl_channel_credentials", autospec=True)
@mock.patch(
    "google.auth.transport._mtls_helper.get_client_ssl_credentials", autospec=True
)
@mock.patch("google.auth.transport._mtls_helper._read_dca_metadata_file", autospec=True)
@mock.patch(
    "google.auth.transport._mtls_helper._check_dca_metadata_path", autospec=True
)
class TestSslCredentials(object):
    def test_no_context_aware_metadata(
        self,
        mock_check_dca_metadata_path,
        mock_read_dca_metadata_file,
        mock_get_client_ssl_credentials,
        mock_ssl_channel_credentials,
    ):
        # Mock that the metadata file doesn't exist.
        mock_check_dca_metadata_path.return_value = None

        with mock.patch.dict(
            os.environ, {environment_vars.GOOGLE_API_USE_CLIENT_CERTIFICATE: "true"}
        ):
            ssl_credentials = google.auth.transport.grpc.SslCredentials()

        # Since no context aware metadata is found, we wouldn't call
        # get_client_ssl_credentials, and the SSL channel credentials created is
        # non mTLS.
        assert ssl_credentials.ssl_credentials is not None
        assert not ssl_credentials.is_mtls
        mock_get_client_ssl_credentials.assert_not_called()
        mock_ssl_channel_credentials.assert_called_once_with()

    def test_get_client_ssl_credentials_failure(
        self,
        mock_check_dca_metadata_path,
        mock_read_dca_metadata_file,
        mock_get_client_ssl_credentials,
        mock_ssl_channel_credentials,
    ):
        mock_check_dca_metadata_path.return_value = METADATA_PATH
        mock_read_dca_metadata_file.return_value = {
            "cert_provider_command": ["some command"]
        }

        # Mock that client cert and key are not loaded and exception is raised.
        mock_get_client_ssl_credentials.side_effect = exceptions.ClientCertError()

        with pytest.raises(exceptions.MutualTLSChannelError):
            with mock.patch.dict(
                os.environ, {environment_vars.GOOGLE_API_USE_CLIENT_CERTIFICATE: "true"}
            ):
                assert google.auth.transport.grpc.SslCredentials().ssl_credentials

    def test_get_client_ssl_credentials_success(
        self,
        mock_check_dca_metadata_path,
        mock_read_dca_metadata_file,
        mock_get_client_ssl_credentials,
        mock_ssl_channel_credentials,
    ):
        mock_check_dca_metadata_path.return_value = METADATA_PATH
        mock_read_dca_metadata_file.return_value = {
            "cert_provider_command": ["some command"]
        }
        mock_get_client_ssl_credentials.return_value = (
            True,
            PUBLIC_CERT_BYTES,
            PRIVATE_KEY_BYTES,
            None,
        )

        with mock.patch.dict(
            os.environ, {environment_vars.GOOGLE_API_USE_CLIENT_CERTIFICATE: "true"}
        ):
            ssl_credentials = google.auth.transport.grpc.SslCredentials()

        assert ssl_credentials.ssl_credentials is not None
        assert ssl_credentials.is_mtls
        mock_get_client_ssl_credentials.assert_called_once()
        mock_ssl_channel_credentials.assert_called_once_with(
            certificate_chain=PUBLIC_CERT_BYTES, private_key=PRIVATE_KEY_BYTES
        )

    def test_get_client_ssl_credentials_without_client_cert_env(
        self,
        mock_check_dca_metadata_path,
        mock_read_dca_metadata_file,
        mock_get_client_ssl_credentials,
        mock_ssl_channel_credentials,
    ):
        # Test client cert won't be used if GOOGLE_API_USE_CLIENT_CERTIFICATE is not set.
        ssl_credentials = google.auth.transport.grpc.SslCredentials()

        assert ssl_credentials.ssl_credentials is not None
        assert not ssl_credentials.is_mtls
        mock_check_dca_metadata_path.assert_not_called()
        mock_read_dca_metadata_file.assert_not_called()
        mock_get_client_ssl_credentials.assert_not_called()
        mock_ssl_channel_credentials.assert_called_once()
