# Copyright 2017 Google LLC
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

import mock
import pytest  # type: ignore
from six.moves import http_client

from google.auth import _helpers
from google.auth import exceptions
from google.auth import iam
from google.auth import transport
import google.auth.credentials


def make_request(status, data=None):
    response = mock.create_autospec(transport.Response, instance=True)
    response.status = status

    if data is not None:
        response.data = json.dumps(data).encode("utf-8")

    request = mock.create_autospec(transport.Request)
    request.return_value = response
    return request


def make_credentials():
    class CredentialsImpl(google.auth.credentials.Credentials):
        def __init__(self):
            super(CredentialsImpl, self).__init__()
            self.token = "token"
            # Force refresh
            self.expiry = datetime.datetime.min + _helpers.REFRESH_THRESHOLD

        def refresh(self, request):
            pass

        def with_quota_project(self, quota_project_id):
            raise NotImplementedError()

    return CredentialsImpl()


class TestSigner(object):
    def test_constructor(self):
        request = mock.sentinel.request
        credentials = mock.create_autospec(
            google.auth.credentials.Credentials, instance=True
        )

        signer = iam.Signer(request, credentials, mock.sentinel.service_account_email)

        assert signer._request == mock.sentinel.request
        assert signer._credentials == credentials
        assert signer._service_account_email == mock.sentinel.service_account_email

    def test_key_id(self):
        signer = iam.Signer(
            mock.sentinel.request,
            mock.sentinel.credentials,
            mock.sentinel.service_account_email,
        )

        assert signer.key_id is None

    def test_sign_bytes(self):
        signature = b"DEADBEEF"
        encoded_signature = base64.b64encode(signature).decode("utf-8")
        request = make_request(http_client.OK, data={"signedBlob": encoded_signature})
        credentials = make_credentials()

        signer = iam.Signer(request, credentials, mock.sentinel.service_account_email)

        returned_signature = signer.sign("123")

        assert returned_signature == signature
        kwargs = request.call_args[1]
        assert kwargs["headers"]["Content-Type"] == "application/json"

    def test_sign_bytes_failure(self):
        request = make_request(http_client.UNAUTHORIZED)
        credentials = make_credentials()

        signer = iam.Signer(request, credentials, mock.sentinel.service_account_email)

        with pytest.raises(exceptions.TransportError):
            signer.sign("123")
