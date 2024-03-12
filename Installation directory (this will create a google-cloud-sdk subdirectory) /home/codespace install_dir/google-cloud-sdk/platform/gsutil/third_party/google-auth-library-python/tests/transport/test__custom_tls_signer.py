# Copyright 2022 Google LLC
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
import ctypes
import os

import mock
import pytest  # type: ignore
from requests.packages.urllib3.util.ssl_ import create_urllib3_context  # type: ignore
import urllib3.contrib.pyopenssl  # type: ignore

from google.auth import exceptions
from google.auth.transport import _custom_tls_signer

urllib3.contrib.pyopenssl.inject_into_urllib3()

FAKE_ENTERPRISE_CERT_FILE_PATH = "/path/to/enterprise/cert/file"
ENTERPRISE_CERT_FILE = os.path.join(
    os.path.dirname(__file__), "../data/enterprise_cert_valid.json"
)
INVALID_ENTERPRISE_CERT_FILE = os.path.join(
    os.path.dirname(__file__), "../data/enterprise_cert_invalid.json"
)


def test_load_offload_lib():
    with mock.patch("ctypes.CDLL", return_value=mock.MagicMock()):
        lib = _custom_tls_signer.load_offload_lib("/path/to/offload/lib")

    assert lib.ConfigureSslContext.argtypes == [
        _custom_tls_signer.SIGN_CALLBACK_CTYPE,
        ctypes.c_char_p,
        ctypes.c_void_p,
    ]
    assert lib.ConfigureSslContext.restype == ctypes.c_int


def test_load_signer_lib():
    with mock.patch("ctypes.CDLL", return_value=mock.MagicMock()):
        lib = _custom_tls_signer.load_signer_lib("/path/to/signer/lib")

    assert lib.SignForPython.restype == ctypes.c_int
    assert lib.SignForPython.argtypes == [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
    ]

    assert lib.GetCertPemForPython.restype == ctypes.c_int
    assert lib.GetCertPemForPython.argtypes == [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_int,
    ]


def test__compute_sha256_digest():
    to_be_signed = ctypes.create_string_buffer(b"foo")
    sig = _custom_tls_signer._compute_sha256_digest(to_be_signed, 4)

    assert (
        base64.b64encode(sig).decode() == "RG5gyEH8CAAh3lxgbt2PLPAHPO8p6i9+cn5dqHfUUYM="
    )


def test_get_sign_callback():
    # mock signer lib's SignForPython function
    mock_sig_len = 10
    mock_signer_lib = mock.MagicMock()
    mock_signer_lib.SignForPython.return_value = mock_sig_len

    # create a sign callback. The callback calls signer lib's SignForPython method
    sign_callback = _custom_tls_signer.get_sign_callback(
        mock_signer_lib, FAKE_ENTERPRISE_CERT_FILE_PATH
    )

    # mock the parameters used to call the sign callback
    to_be_signed = ctypes.POINTER(ctypes.c_ubyte)()
    to_be_signed_len = 4
    returned_sig_array = ctypes.c_ubyte()
    mock_sig_array = ctypes.byref(returned_sig_array)
    returned_sign_len = ctypes.c_ulong()
    mock_sig_len_array = ctypes.byref(returned_sign_len)

    # call the callback, make sure the signature len is returned via mock_sig_len_array[0]
    assert sign_callback(
        mock_sig_array, mock_sig_len_array, to_be_signed, to_be_signed_len
    )
    assert returned_sign_len.value == mock_sig_len


def test_get_sign_callback_failed_to_sign():
    # mock signer lib's SignForPython function. Set the sig len to be 0 to
    # indicate the signing failed.
    mock_sig_len = 0
    mock_signer_lib = mock.MagicMock()
    mock_signer_lib.SignForPython.return_value = mock_sig_len

    # create a sign callback. The callback calls signer lib's SignForPython method
    sign_callback = _custom_tls_signer.get_sign_callback(
        mock_signer_lib, FAKE_ENTERPRISE_CERT_FILE_PATH
    )

    # mock the parameters used to call the sign callback
    to_be_signed = ctypes.POINTER(ctypes.c_ubyte)()
    to_be_signed_len = 4
    returned_sig_array = ctypes.c_ubyte()
    mock_sig_array = ctypes.byref(returned_sig_array)
    returned_sign_len = ctypes.c_ulong()
    mock_sig_len_array = ctypes.byref(returned_sign_len)
    sign_callback(mock_sig_array, mock_sig_len_array, to_be_signed, to_be_signed_len)

    # sign callback should return 0
    assert not sign_callback(
        mock_sig_array, mock_sig_len_array, to_be_signed, to_be_signed_len
    )


def test_get_cert_no_cert():
    # mock signer lib's GetCertPemForPython function to return 0 to indicts
    # the cert doesn't exit (cert len = 0)
    mock_signer_lib = mock.MagicMock()
    mock_signer_lib.GetCertPemForPython.return_value = 0

    # call the get cert method
    with pytest.raises(exceptions.MutualTLSChannelError) as excinfo:
        _custom_tls_signer.get_cert(mock_signer_lib, FAKE_ENTERPRISE_CERT_FILE_PATH)

    assert excinfo.match("failed to get certificate")


def test_get_cert():
    # mock signer lib's GetCertPemForPython function
    mock_cert_len = 10
    mock_signer_lib = mock.MagicMock()
    mock_signer_lib.GetCertPemForPython.return_value = mock_cert_len

    # call the get cert method
    mock_cert = _custom_tls_signer.get_cert(
        mock_signer_lib, FAKE_ENTERPRISE_CERT_FILE_PATH
    )

    # make sure the signer lib's GetCertPemForPython is called twice, and the
    # mock_cert has length mock_cert_len
    assert mock_signer_lib.GetCertPemForPython.call_count == 2
    assert len(mock_cert) == mock_cert_len


def test_custom_tls_signer():
    offload_lib = mock.MagicMock()
    signer_lib = mock.MagicMock()

    # Test load_libraries method
    with mock.patch(
        "google.auth.transport._custom_tls_signer.load_signer_lib"
    ) as load_signer_lib:
        with mock.patch(
            "google.auth.transport._custom_tls_signer.load_offload_lib"
        ) as load_offload_lib:
            load_offload_lib.return_value = offload_lib
            load_signer_lib.return_value = signer_lib
            signer_object = _custom_tls_signer.CustomTlsSigner(ENTERPRISE_CERT_FILE)
            signer_object.load_libraries()
    assert signer_object._cert is None
    assert signer_object._enterprise_cert_file_path == ENTERPRISE_CERT_FILE
    assert signer_object._offload_lib == offload_lib
    assert signer_object._signer_lib == signer_lib
    load_signer_lib.assert_called_with("/path/to/signer/lib")
    load_offload_lib.assert_called_with("/path/to/offload/lib")

    # Test set_up_custom_key and set_up_ssl_context methods
    with mock.patch("google.auth.transport._custom_tls_signer.get_cert") as get_cert:
        with mock.patch(
            "google.auth.transport._custom_tls_signer.get_sign_callback"
        ) as get_sign_callback:
            get_cert.return_value = b"mock_cert"
            signer_object.set_up_custom_key()
            signer_object.attach_to_ssl_context(create_urllib3_context())
    get_cert.assert_called_once()
    get_sign_callback.assert_called_once()
    offload_lib.ConfigureSslContext.assert_called_once()


def test_custom_tls_signer_failed_to_load_libraries():
    # Test load_libraries method
    with pytest.raises(exceptions.MutualTLSChannelError) as excinfo:
        signer_object = _custom_tls_signer.CustomTlsSigner(INVALID_ENTERPRISE_CERT_FILE)
        signer_object.load_libraries()
    assert excinfo.match("enterprise cert file is invalid")


def test_custom_tls_signer_fail_to_offload():
    offload_lib = mock.MagicMock()
    signer_lib = mock.MagicMock()

    with mock.patch(
        "google.auth.transport._custom_tls_signer.load_signer_lib"
    ) as load_signer_lib:
        with mock.patch(
            "google.auth.transport._custom_tls_signer.load_offload_lib"
        ) as load_offload_lib:
            load_offload_lib.return_value = offload_lib
            load_signer_lib.return_value = signer_lib
            signer_object = _custom_tls_signer.CustomTlsSigner(ENTERPRISE_CERT_FILE)
            signer_object.load_libraries()

    # set the return value to be 0 which indicts offload fails
    offload_lib.ConfigureSslContext.return_value = 0

    with pytest.raises(exceptions.MutualTLSChannelError) as excinfo:
        with mock.patch(
            "google.auth.transport._custom_tls_signer.get_cert"
        ) as get_cert:
            with mock.patch(
                "google.auth.transport._custom_tls_signer.get_sign_callback"
            ):
                get_cert.return_value = b"mock_cert"
                signer_object.set_up_custom_key()
                signer_object.attach_to_ssl_context(create_urllib3_context())
    assert excinfo.match("failed to configure SSL context")
