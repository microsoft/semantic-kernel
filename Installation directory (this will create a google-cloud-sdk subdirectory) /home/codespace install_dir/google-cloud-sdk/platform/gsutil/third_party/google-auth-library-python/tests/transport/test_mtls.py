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

import mock
import pytest  # type: ignore

from google.auth import exceptions
from google.auth.transport import mtls


@mock.patch(
    "google.auth.transport._mtls_helper._check_dca_metadata_path", autospec=True
)
def test_has_default_client_cert_source(check_dca_metadata_path):
    check_dca_metadata_path.return_value = mock.Mock()
    assert mtls.has_default_client_cert_source()

    check_dca_metadata_path.return_value = None
    assert not mtls.has_default_client_cert_source()


@mock.patch("google.auth.transport._mtls_helper.get_client_cert_and_key", autospec=True)
@mock.patch("google.auth.transport.mtls.has_default_client_cert_source", autospec=True)
def test_default_client_cert_source(
    has_default_client_cert_source, get_client_cert_and_key
):
    # Test default client cert source doesn't exist.
    has_default_client_cert_source.return_value = False
    with pytest.raises(exceptions.MutualTLSChannelError):
        mtls.default_client_cert_source()

    # The following tests will assume default client cert source exists.
    has_default_client_cert_source.return_value = True

    # Test good callback.
    get_client_cert_and_key.return_value = (True, b"cert", b"key")
    callback = mtls.default_client_cert_source()
    assert callback() == (b"cert", b"key")

    # Test bad callback which throws exception.
    get_client_cert_and_key.side_effect = ValueError()
    callback = mtls.default_client_cert_source()
    with pytest.raises(exceptions.MutualTLSChannelError):
        callback()


@mock.patch(
    "google.auth.transport._mtls_helper.get_client_ssl_credentials", autospec=True
)
@mock.patch("google.auth.transport.mtls.has_default_client_cert_source", autospec=True)
def test_default_client_encrypted_cert_source(
    has_default_client_cert_source, get_client_ssl_credentials
):
    # Test default client cert source doesn't exist.
    has_default_client_cert_source.return_value = False
    with pytest.raises(exceptions.MutualTLSChannelError):
        mtls.default_client_encrypted_cert_source("cert_path", "key_path")

    # The following tests will assume default client cert source exists.
    has_default_client_cert_source.return_value = True

    # Test good callback.
    get_client_ssl_credentials.return_value = (True, b"cert", b"key", b"passphrase")
    callback = mtls.default_client_encrypted_cert_source("cert_path", "key_path")
    with mock.patch("{}.open".format(__name__), return_value=mock.MagicMock()):
        assert callback() == ("cert_path", "key_path", b"passphrase")

    # Test bad callback which throws exception.
    get_client_ssl_credentials.side_effect = exceptions.ClientCertError()
    callback = mtls.default_client_encrypted_cert_source("cert_path", "key_path")
    with pytest.raises(exceptions.MutualTLSChannelError):
        callback()
