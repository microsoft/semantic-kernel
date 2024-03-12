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

import os
import re

import mock
from OpenSSL import crypto
import pytest  # type: ignore

from google.auth import exceptions
from google.auth.transport import _mtls_helper

CONTEXT_AWARE_METADATA = {"cert_provider_command": ["some command"]}

ENCRYPTED_EC_PRIVATE_KEY = b"""-----BEGIN ENCRYPTED PRIVATE KEY-----
MIHkME8GCSqGSIb3DQEFDTBCMCkGCSqGSIb3DQEFDDAcBAgl2/yVgs1h3QICCAAw
DAYIKoZIhvcNAgkFADAVBgkrBgEEAZdVAQIECJk2GRrvxOaJBIGQXIBnMU4wmciT
uA6yD8q0FxuIzjG7E2S6tc5VRgSbhRB00eBO3jWmO2pBybeQW+zVioDcn50zp2ts
wYErWC+LCm1Zg3r+EGnT1E1GgNoODbVQ3AEHlKh1CGCYhEovxtn3G+Fjh7xOBrNB
saVVeDb4tHD4tMkiVVUBrUcTZPndP73CtgyGHYEphasYPzEz3+AU
-----END ENCRYPTED PRIVATE KEY-----"""

EC_PUBLIC_KEY = b"""-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEvCNi1NoDY1oMqPHIgXI8RBbTYGi/
brEjbre1nSiQW11xRTJbVeETdsuP0EAu2tG3PcRhhwDfeJ8zXREgTBurNw==
-----END PUBLIC KEY-----"""

PASSPHRASE = b"""-----BEGIN PASSPHRASE-----
password
-----END PASSPHRASE-----"""
PASSPHRASE_VALUE = b"password"


def check_cert_and_key(content, expected_cert, expected_key):
    success = True

    cert_match = re.findall(_mtls_helper._CERT_REGEX, content)
    success = success and len(cert_match) == 1 and cert_match[0] == expected_cert

    key_match = re.findall(_mtls_helper._KEY_REGEX, content)
    success = success and len(key_match) == 1 and key_match[0] == expected_key

    return success


class TestCertAndKeyRegex(object):
    def test_cert_and_key(self):
        # Test single cert and single key
        check_cert_and_key(
            pytest.public_cert_bytes + pytest.private_key_bytes,
            pytest.public_cert_bytes,
            pytest.private_key_bytes,
        )
        check_cert_and_key(
            pytest.private_key_bytes + pytest.public_cert_bytes,
            pytest.public_cert_bytes,
            pytest.private_key_bytes,
        )

        # Test cert chain and single key
        check_cert_and_key(
            pytest.public_cert_bytes
            + pytest.public_cert_bytes
            + pytest.private_key_bytes,
            pytest.public_cert_bytes + pytest.public_cert_bytes,
            pytest.private_key_bytes,
        )
        check_cert_and_key(
            pytest.private_key_bytes
            + pytest.public_cert_bytes
            + pytest.public_cert_bytes,
            pytest.public_cert_bytes + pytest.public_cert_bytes,
            pytest.private_key_bytes,
        )

    def test_key(self):
        # Create some fake keys for regex check.
        KEY = b"""-----BEGIN PRIVATE KEY-----
        MIIBCgKCAQEA4ej0p7bQ7L/r4rVGUz9RN4VQWoej1Bg1mYWIDYslvKrk1gpj7wZg
        /fy3ZpsL7WqgsZS7Q+0VRK8gKfqkxg5OYQIDAQAB
        -----END PRIVATE KEY-----"""
        RSA_KEY = b"""-----BEGIN RSA PRIVATE KEY-----
        MIIBCgKCAQEA4ej0p7bQ7L/r4rVGUz9RN4VQWoej1Bg1mYWIDYslvKrk1gpj7wZg
        /fy3ZpsL7WqgsZS7Q+0VRK8gKfqkxg5OYQIDAQAB
        -----END RSA PRIVATE KEY-----"""
        EC_KEY = b"""-----BEGIN EC PRIVATE KEY-----
        MIIBCgKCAQEA4ej0p7bQ7L/r4rVGUz9RN4VQWoej1Bg1mYWIDYslvKrk1gpj7wZg
        /fy3ZpsL7WqgsZS7Q+0VRK8gKfqkxg5OYQIDAQAB
        -----END EC PRIVATE KEY-----"""

        check_cert_and_key(
            pytest.public_cert_bytes + KEY, pytest.public_cert_bytes, KEY
        )
        check_cert_and_key(
            pytest.public_cert_bytes + RSA_KEY, pytest.public_cert_bytes, RSA_KEY
        )
        check_cert_and_key(
            pytest.public_cert_bytes + EC_KEY, pytest.public_cert_bytes, EC_KEY
        )


class TestCheckaMetadataPath(object):
    def test_success(self):
        metadata_path = os.path.join(pytest.data_dir, "context_aware_metadata.json")
        returned_path = _mtls_helper._check_dca_metadata_path(metadata_path)
        assert returned_path is not None

    def test_failure(self):
        metadata_path = os.path.join(pytest.data_dir, "not_exists.json")
        returned_path = _mtls_helper._check_dca_metadata_path(metadata_path)
        assert returned_path is None


class TestReadMetadataFile(object):
    def test_success(self):
        metadata_path = os.path.join(pytest.data_dir, "context_aware_metadata.json")
        metadata = _mtls_helper._read_dca_metadata_file(metadata_path)

        assert "cert_provider_command" in metadata

    def test_file_not_json(self):
        # read a file which is not json format.
        metadata_path = os.path.join(pytest.data_dir, "privatekey.pem")
        with pytest.raises(exceptions.ClientCertError):
            _mtls_helper._read_dca_metadata_file(metadata_path)


class TestRunCertProviderCommand(object):
    def create_mock_process(self, output, error):
        # There are two steps to execute a script with subprocess.Popen.
        # (1) process = subprocess.Popen([comannds])
        # (2) stdout, stderr = process.communicate()
        # This function creates a mock process which can be returned by a mock
        # subprocess.Popen. The mock process returns the given output and error
        # when mock_process.communicate() is called.
        mock_process = mock.Mock()
        attrs = {"communicate.return_value": (output, error), "returncode": 0}
        mock_process.configure_mock(**attrs)
        return mock_process

    @mock.patch("subprocess.Popen", autospec=True)
    def test_success(self, mock_popen):
        mock_popen.return_value = self.create_mock_process(
            pytest.public_cert_bytes + pytest.private_key_bytes, b""
        )
        cert, key, passphrase = _mtls_helper._run_cert_provider_command(["command"])
        assert cert == pytest.public_cert_bytes
        assert key == pytest.private_key_bytes
        assert passphrase is None

        mock_popen.return_value = self.create_mock_process(
            pytest.public_cert_bytes + ENCRYPTED_EC_PRIVATE_KEY + PASSPHRASE, b""
        )
        cert, key, passphrase = _mtls_helper._run_cert_provider_command(
            ["command"], expect_encrypted_key=True
        )
        assert cert == pytest.public_cert_bytes
        assert key == ENCRYPTED_EC_PRIVATE_KEY
        assert passphrase == PASSPHRASE_VALUE

    @mock.patch("subprocess.Popen", autospec=True)
    def test_success_with_cert_chain(self, mock_popen):
        PUBLIC_CERT_CHAIN_BYTES = pytest.public_cert_bytes + pytest.public_cert_bytes
        mock_popen.return_value = self.create_mock_process(
            PUBLIC_CERT_CHAIN_BYTES + pytest.private_key_bytes, b""
        )
        cert, key, passphrase = _mtls_helper._run_cert_provider_command(["command"])
        assert cert == PUBLIC_CERT_CHAIN_BYTES
        assert key == pytest.private_key_bytes
        assert passphrase is None

        mock_popen.return_value = self.create_mock_process(
            PUBLIC_CERT_CHAIN_BYTES + ENCRYPTED_EC_PRIVATE_KEY + PASSPHRASE, b""
        )
        cert, key, passphrase = _mtls_helper._run_cert_provider_command(
            ["command"], expect_encrypted_key=True
        )
        assert cert == PUBLIC_CERT_CHAIN_BYTES
        assert key == ENCRYPTED_EC_PRIVATE_KEY
        assert passphrase == PASSPHRASE_VALUE

    @mock.patch("subprocess.Popen", autospec=True)
    def test_missing_cert(self, mock_popen):
        mock_popen.return_value = self.create_mock_process(
            pytest.private_key_bytes, b""
        )
        with pytest.raises(exceptions.ClientCertError):
            _mtls_helper._run_cert_provider_command(["command"])

        mock_popen.return_value = self.create_mock_process(
            ENCRYPTED_EC_PRIVATE_KEY + PASSPHRASE, b""
        )
        with pytest.raises(exceptions.ClientCertError):
            _mtls_helper._run_cert_provider_command(
                ["command"], expect_encrypted_key=True
            )

    @mock.patch("subprocess.Popen", autospec=True)
    def test_missing_key(self, mock_popen):
        mock_popen.return_value = self.create_mock_process(
            pytest.public_cert_bytes, b""
        )
        with pytest.raises(exceptions.ClientCertError):
            _mtls_helper._run_cert_provider_command(["command"])

        mock_popen.return_value = self.create_mock_process(
            pytest.public_cert_bytes + PASSPHRASE, b""
        )
        with pytest.raises(exceptions.ClientCertError):
            _mtls_helper._run_cert_provider_command(
                ["command"], expect_encrypted_key=True
            )

    @mock.patch("subprocess.Popen", autospec=True)
    def test_missing_passphrase(self, mock_popen):
        mock_popen.return_value = self.create_mock_process(
            pytest.public_cert_bytes + ENCRYPTED_EC_PRIVATE_KEY, b""
        )
        with pytest.raises(exceptions.ClientCertError):
            _mtls_helper._run_cert_provider_command(
                ["command"], expect_encrypted_key=True
            )

    @mock.patch("subprocess.Popen", autospec=True)
    def test_passphrase_not_expected(self, mock_popen):
        mock_popen.return_value = self.create_mock_process(
            pytest.public_cert_bytes + pytest.private_key_bytes + PASSPHRASE, b""
        )
        with pytest.raises(exceptions.ClientCertError):
            _mtls_helper._run_cert_provider_command(["command"])

    @mock.patch("subprocess.Popen", autospec=True)
    def test_encrypted_key_expected(self, mock_popen):
        mock_popen.return_value = self.create_mock_process(
            pytest.public_cert_bytes + pytest.private_key_bytes + PASSPHRASE, b""
        )
        with pytest.raises(exceptions.ClientCertError):
            _mtls_helper._run_cert_provider_command(
                ["command"], expect_encrypted_key=True
            )

    @mock.patch("subprocess.Popen", autospec=True)
    def test_unencrypted_key_expected(self, mock_popen):
        mock_popen.return_value = self.create_mock_process(
            pytest.public_cert_bytes + ENCRYPTED_EC_PRIVATE_KEY, b""
        )
        with pytest.raises(exceptions.ClientCertError):
            _mtls_helper._run_cert_provider_command(["command"])

    @mock.patch("subprocess.Popen", autospec=True)
    def test_cert_provider_returns_error(self, mock_popen):
        mock_popen.return_value = self.create_mock_process(b"", b"some error")
        mock_popen.return_value.returncode = 1
        with pytest.raises(exceptions.ClientCertError):
            _mtls_helper._run_cert_provider_command(["command"])

    @mock.patch("subprocess.Popen", autospec=True)
    def test_popen_raise_exception(self, mock_popen):
        mock_popen.side_effect = OSError()
        with pytest.raises(exceptions.ClientCertError):
            _mtls_helper._run_cert_provider_command(["command"])


class TestGetClientSslCredentials(object):
    @mock.patch(
        "google.auth.transport._mtls_helper._run_cert_provider_command", autospec=True
    )
    @mock.patch(
        "google.auth.transport._mtls_helper._read_dca_metadata_file", autospec=True
    )
    @mock.patch(
        "google.auth.transport._mtls_helper._check_dca_metadata_path", autospec=True
    )
    def test_success(
        self,
        mock_check_dca_metadata_path,
        mock_read_dca_metadata_file,
        mock_run_cert_provider_command,
    ):
        mock_check_dca_metadata_path.return_value = True
        mock_read_dca_metadata_file.return_value = {
            "cert_provider_command": ["command"]
        }
        mock_run_cert_provider_command.return_value = (b"cert", b"key", None)
        has_cert, cert, key, passphrase = _mtls_helper.get_client_ssl_credentials()
        assert has_cert
        assert cert == b"cert"
        assert key == b"key"
        assert passphrase is None

    @mock.patch(
        "google.auth.transport._mtls_helper._check_dca_metadata_path", autospec=True
    )
    def test_success_without_metadata(self, mock_check_dca_metadata_path):
        mock_check_dca_metadata_path.return_value = False
        has_cert, cert, key, passphrase = _mtls_helper.get_client_ssl_credentials()
        assert not has_cert
        assert cert is None
        assert key is None
        assert passphrase is None

    @mock.patch(
        "google.auth.transport._mtls_helper._run_cert_provider_command", autospec=True
    )
    @mock.patch(
        "google.auth.transport._mtls_helper._read_dca_metadata_file", autospec=True
    )
    @mock.patch(
        "google.auth.transport._mtls_helper._check_dca_metadata_path", autospec=True
    )
    def test_success_with_encrypted_key(
        self,
        mock_check_dca_metadata_path,
        mock_read_dca_metadata_file,
        mock_run_cert_provider_command,
    ):
        mock_check_dca_metadata_path.return_value = True
        mock_read_dca_metadata_file.return_value = {
            "cert_provider_command": ["command"]
        }
        mock_run_cert_provider_command.return_value = (b"cert", b"key", b"passphrase")
        has_cert, cert, key, passphrase = _mtls_helper.get_client_ssl_credentials(
            generate_encrypted_key=True
        )
        assert has_cert
        assert cert == b"cert"
        assert key == b"key"
        assert passphrase == b"passphrase"
        mock_run_cert_provider_command.assert_called_once_with(
            ["command", "--with_passphrase"], expect_encrypted_key=True
        )

    @mock.patch(
        "google.auth.transport._mtls_helper._read_dca_metadata_file", autospec=True
    )
    @mock.patch(
        "google.auth.transport._mtls_helper._check_dca_metadata_path", autospec=True
    )
    def test_missing_cert_command(
        self, mock_check_dca_metadata_path, mock_read_dca_metadata_file
    ):
        mock_check_dca_metadata_path.return_value = True
        mock_read_dca_metadata_file.return_value = {}
        with pytest.raises(exceptions.ClientCertError):
            _mtls_helper.get_client_ssl_credentials()

    @mock.patch(
        "google.auth.transport._mtls_helper._run_cert_provider_command", autospec=True
    )
    @mock.patch(
        "google.auth.transport._mtls_helper._read_dca_metadata_file", autospec=True
    )
    @mock.patch(
        "google.auth.transport._mtls_helper._check_dca_metadata_path", autospec=True
    )
    def test_customize_context_aware_metadata_path(
        self,
        mock_check_dca_metadata_path,
        mock_read_dca_metadata_file,
        mock_run_cert_provider_command,
    ):
        context_aware_metadata_path = "/path/to/metata/data"
        mock_check_dca_metadata_path.return_value = context_aware_metadata_path
        mock_read_dca_metadata_file.return_value = {
            "cert_provider_command": ["command"]
        }
        mock_run_cert_provider_command.return_value = (b"cert", b"key", None)

        has_cert, cert, key, passphrase = _mtls_helper.get_client_ssl_credentials(
            context_aware_metadata_path=context_aware_metadata_path
        )

        assert has_cert
        assert cert == b"cert"
        assert key == b"key"
        assert passphrase is None
        mock_check_dca_metadata_path.assert_called_with(context_aware_metadata_path)
        mock_read_dca_metadata_file.assert_called_with(context_aware_metadata_path)


class TestGetClientCertAndKey(object):
    def test_callback_success(self):
        callback = mock.Mock()
        callback.return_value = (pytest.public_cert_bytes, pytest.private_key_bytes)

        found_cert_key, cert, key = _mtls_helper.get_client_cert_and_key(callback)
        assert found_cert_key
        assert cert == pytest.public_cert_bytes
        assert key == pytest.private_key_bytes

    @mock.patch(
        "google.auth.transport._mtls_helper.get_client_ssl_credentials", autospec=True
    )
    def test_use_metadata(self, mock_get_client_ssl_credentials):
        mock_get_client_ssl_credentials.return_value = (
            True,
            pytest.public_cert_bytes,
            pytest.private_key_bytes,
            None,
        )

        found_cert_key, cert, key = _mtls_helper.get_client_cert_and_key()
        assert found_cert_key
        assert cert == pytest.public_cert_bytes
        assert key == pytest.private_key_bytes


class TestDecryptPrivateKey(object):
    def test_success(self):
        decrypted_key = _mtls_helper.decrypt_private_key(
            ENCRYPTED_EC_PRIVATE_KEY, PASSPHRASE_VALUE
        )
        private_key = crypto.load_privatekey(crypto.FILETYPE_PEM, decrypted_key)
        public_key = crypto.load_publickey(crypto.FILETYPE_PEM, EC_PUBLIC_KEY)
        x509 = crypto.X509()
        x509.set_pubkey(public_key)

        # Test the decrypted key works by signing and verification.
        signature = crypto.sign(private_key, b"data", "sha256")
        crypto.verify(x509, signature, b"data", "sha256")

    def test_crypto_error(self):
        with pytest.raises(crypto.Error):
            _mtls_helper.decrypt_private_key(
                ENCRYPTED_EC_PRIVATE_KEY, b"wrong_password"
            )
