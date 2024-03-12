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

# import datetime
import json
import os
import subprocess

import mock
import pytest  # type: ignore

# from six.moves import http_client
# from six.moves import urllib

# from google.auth import _helpers
from google.auth import exceptions
from google.auth import pluggable
from tests.test__default import WORKFORCE_AUDIENCE

# from google.auth import transport


CLIENT_ID = "username"
CLIENT_SECRET = "password"
# Base64 encoding of "username:password".
BASIC_AUTH_ENCODING = "dXNlcm5hbWU6cGFzc3dvcmQ="
SERVICE_ACCOUNT_EMAIL = "service-1234@service-name.iam.gserviceaccount.com"
SERVICE_ACCOUNT_IMPERSONATION_URL_BASE = (
    "https://us-east1-iamcredentials.googleapis.com"
)
SERVICE_ACCOUNT_IMPERSONATION_URL_ROUTE = "/v1/projects/-/serviceAccounts/{}:generateAccessToken".format(
    SERVICE_ACCOUNT_EMAIL
)
SERVICE_ACCOUNT_IMPERSONATION_URL = (
    SERVICE_ACCOUNT_IMPERSONATION_URL_BASE + SERVICE_ACCOUNT_IMPERSONATION_URL_ROUTE
)
QUOTA_PROJECT_ID = "QUOTA_PROJECT_ID"
SCOPES = ["scope1", "scope2"]
SUBJECT_TOKEN_FIELD_NAME = "access_token"

TOKEN_URL = "https://sts.googleapis.com/v1/token"
TOKEN_INFO_URL = "https://sts.googleapis.com/v1/introspect"
SUBJECT_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:jwt"
AUDIENCE = "//iam.googleapis.com/projects/123456/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID"

VALID_TOKEN_URLS = [
    "https://sts.googleapis.com",
    "https://us-east-1.sts.googleapis.com",
    "https://US-EAST-1.sts.googleapis.com",
    "https://sts.us-east-1.googleapis.com",
    "https://sts.US-WEST-1.googleapis.com",
    "https://us-east-1-sts.googleapis.com",
    "https://US-WEST-1-sts.googleapis.com",
    "https://us-west-1-sts.googleapis.com/path?query",
    "https://sts-us-east-1.p.googleapis.com",
]
INVALID_TOKEN_URLS = [
    "https://iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "https://",
    "http://sts.googleapis.com",
    "https://st.s.googleapis.com",
    "https://us-eas\t-1.sts.googleapis.com",
    "https:/us-east-1.sts.googleapis.com",
    "https://US-WE/ST-1-sts.googleapis.com",
    "https://sts-us-east-1.googleapis.com",
    "https://sts-US-WEST-1.googleapis.com",
    "testhttps://us-east-1.sts.googleapis.com",
    "https://us-east-1.sts.googleapis.comevil.com",
    "https://us-east-1.us-east-1.sts.googleapis.com",
    "https://us-ea.s.t.sts.googleapis.com",
    "https://sts.googleapis.comevil.com",
    "hhttps://us-east-1.sts.googleapis.com",
    "https://us- -1.sts.googleapis.com",
    "https://-sts.googleapis.com",
    "https://us-east-1.sts.googleapis.com.evil.com",
    "https://sts.pgoogleapis.com",
    "https://p.googleapis.com",
    "https://sts.p.com",
    "http://sts.p.googleapis.com",
    "https://xyz-sts.p.googleapis.com",
    "https://sts-xyz.123.p.googleapis.com",
    "https://sts-xyz.p1.googleapis.com",
    "https://sts-xyz.p.foo.com",
    "https://sts-xyz.p.foo.googleapis.com",
]
VALID_SERVICE_ACCOUNT_IMPERSONATION_URLS = [
    "https://iamcredentials.googleapis.com",
    "https://us-east-1.iamcredentials.googleapis.com",
    "https://US-EAST-1.iamcredentials.googleapis.com",
    "https://iamcredentials.us-east-1.googleapis.com",
    "https://iamcredentials.US-WEST-1.googleapis.com",
    "https://us-east-1-iamcredentials.googleapis.com",
    "https://US-WEST-1-iamcredentials.googleapis.com",
    "https://us-west-1-iamcredentials.googleapis.com/path?query",
    "https://iamcredentials-us-east-1.p.googleapis.com",
]
INVALID_SERVICE_ACCOUNT_IMPERSONATION_URLS = [
    "https://sts.googleapis.com",
    "iamcredentials.googleapis.com",
    "https://",
    "http://iamcredentials.googleapis.com",
    "https://iamcre.dentials.googleapis.com",
    "https://us-eas\t-1.iamcredentials.googleapis.com",
    "https:/us-east-1.iamcredentials.googleapis.com",
    "https://US-WE/ST-1-iamcredentials.googleapis.com",
    "https://iamcredentials-us-east-1.googleapis.com",
    "https://iamcredentials-US-WEST-1.googleapis.com",
    "testhttps://us-east-1.iamcredentials.googleapis.com",
    "https://us-east-1.iamcredentials.googleapis.comevil.com",
    "https://us-east-1.us-east-1.iamcredentials.googleapis.com",
    "https://us-ea.s.t.iamcredentials.googleapis.com",
    "https://iamcredentials.googleapis.comevil.com",
    "hhttps://us-east-1.iamcredentials.googleapis.com",
    "https://us- -1.iamcredentials.googleapis.com",
    "https://-iamcredentials.googleapis.com",
    "https://us-east-1.iamcredentials.googleapis.com.evil.com",
    "https://iamcredentials.pgoogleapis.com",
    "https://p.googleapis.com",
    "https://iamcredentials.p.com",
    "http://iamcredentials.p.googleapis.com",
    "https://xyz-iamcredentials.p.googleapis.com",
    "https://iamcredentials-xyz.123.p.googleapis.com",
    "https://iamcredentials-xyz.p1.googleapis.com",
    "https://iamcredentials-xyz.p.foo.com",
    "https://iamcredentials-xyz.p.foo.googleapis.com",
]


class TestCredentials(object):
    CREDENTIAL_SOURCE_EXECUTABLE_COMMAND = (
        "/fake/external/excutable --arg1=value1 --arg2=value2"
    )
    CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE = "fake_output_file"
    CREDENTIAL_SOURCE_EXECUTABLE = {
        "command": CREDENTIAL_SOURCE_EXECUTABLE_COMMAND,
        "timeout_millis": 30000,
        "interactive_timeout_millis": 300000,
        "output_file": CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE,
    }
    CREDENTIAL_SOURCE = {"executable": CREDENTIAL_SOURCE_EXECUTABLE}
    EXECUTABLE_OIDC_TOKEN = "FAKE_ID_TOKEN"
    EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE_ID_TOKEN = {
        "version": 1,
        "success": True,
        "token_type": "urn:ietf:params:oauth:token-type:id_token",
        "id_token": EXECUTABLE_OIDC_TOKEN,
        "expiration_time": 9999999999,
    }
    EXECUTABLE_SUCCESSFUL_OIDC_NO_EXPIRATION_TIME_RESPONSE_ID_TOKEN = {
        "version": 1,
        "success": True,
        "token_type": "urn:ietf:params:oauth:token-type:id_token",
        "id_token": EXECUTABLE_OIDC_TOKEN,
    }
    EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE_JWT = {
        "version": 1,
        "success": True,
        "token_type": "urn:ietf:params:oauth:token-type:jwt",
        "id_token": EXECUTABLE_OIDC_TOKEN,
        "expiration_time": 9999999999,
    }
    EXECUTABLE_SUCCESSFUL_OIDC_NO_EXPIRATION_TIME_RESPONSE_JWT = {
        "version": 1,
        "success": True,
        "token_type": "urn:ietf:params:oauth:token-type:jwt",
        "id_token": EXECUTABLE_OIDC_TOKEN,
    }
    EXECUTABLE_SAML_TOKEN = "FAKE_SAML_RESPONSE"
    EXECUTABLE_SUCCESSFUL_SAML_RESPONSE = {
        "version": 1,
        "success": True,
        "token_type": "urn:ietf:params:oauth:token-type:saml2",
        "saml_response": EXECUTABLE_SAML_TOKEN,
        "expiration_time": 9999999999,
    }
    EXECUTABLE_SUCCESSFUL_SAML_NO_EXPIRATION_TIME_RESPONSE = {
        "version": 1,
        "success": True,
        "token_type": "urn:ietf:params:oauth:token-type:saml2",
        "saml_response": EXECUTABLE_SAML_TOKEN,
    }
    EXECUTABLE_FAILED_RESPONSE = {
        "version": 1,
        "success": False,
        "code": "401",
        "message": "Permission denied. Caller not authorized",
    }
    CREDENTIAL_URL = "http://fakeurl.com"

    @classmethod
    def make_pluggable(
        cls,
        audience=AUDIENCE,
        subject_token_type=SUBJECT_TOKEN_TYPE,
        token_url=TOKEN_URL,
        token_info_url=TOKEN_INFO_URL,
        client_id=None,
        client_secret=None,
        quota_project_id=None,
        scopes=None,
        default_scopes=None,
        service_account_impersonation_url=None,
        credential_source=None,
        workforce_pool_user_project=None,
        interactive=None,
    ):
        return pluggable.Credentials(
            audience=audience,
            subject_token_type=subject_token_type,
            token_url=token_url,
            token_info_url=token_info_url,
            service_account_impersonation_url=service_account_impersonation_url,
            credential_source=credential_source,
            client_id=client_id,
            client_secret=client_secret,
            quota_project_id=quota_project_id,
            scopes=scopes,
            default_scopes=default_scopes,
            workforce_pool_user_project=workforce_pool_user_project,
            interactive=interactive,
        )

    def test_from_constructor_and_injection(self):
        credentials = pluggable.Credentials(
            audience=AUDIENCE,
            subject_token_type=SUBJECT_TOKEN_TYPE,
            token_url=TOKEN_URL,
            token_info_url=TOKEN_INFO_URL,
            credential_source=self.CREDENTIAL_SOURCE,
            interactive=True,
        )
        setattr(credentials, "_tokeninfo_username", "mock_external_account_id")

        assert isinstance(credentials, pluggable.Credentials)
        assert credentials.interactive
        assert credentials.external_account_id == "mock_external_account_id"

    @mock.patch.object(pluggable.Credentials, "__init__", return_value=None)
    def test_from_info_full_options(self, mock_init):
        credentials = pluggable.Credentials.from_info(
            {
                "audience": AUDIENCE,
                "subject_token_type": SUBJECT_TOKEN_TYPE,
                "token_url": TOKEN_URL,
                "token_info_url": TOKEN_INFO_URL,
                "service_account_impersonation_url": SERVICE_ACCOUNT_IMPERSONATION_URL,
                "service_account_impersonation": {"token_lifetime_seconds": 2800},
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "quota_project_id": QUOTA_PROJECT_ID,
                "credential_source": self.CREDENTIAL_SOURCE,
            }
        )

        # Confirm pluggable.Credentials instantiated with expected attributes.
        assert isinstance(credentials, pluggable.Credentials)
        mock_init.assert_called_once_with(
            audience=AUDIENCE,
            subject_token_type=SUBJECT_TOKEN_TYPE,
            token_url=TOKEN_URL,
            token_info_url=TOKEN_INFO_URL,
            service_account_impersonation_url=SERVICE_ACCOUNT_IMPERSONATION_URL,
            service_account_impersonation_options={"token_lifetime_seconds": 2800},
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            credential_source=self.CREDENTIAL_SOURCE,
            quota_project_id=QUOTA_PROJECT_ID,
            workforce_pool_user_project=None,
        )

    @mock.patch.object(pluggable.Credentials, "__init__", return_value=None)
    def test_from_info_required_options_only(self, mock_init):
        credentials = pluggable.Credentials.from_info(
            {
                "audience": AUDIENCE,
                "subject_token_type": SUBJECT_TOKEN_TYPE,
                "token_url": TOKEN_URL,
                "credential_source": self.CREDENTIAL_SOURCE,
            }
        )

        # Confirm pluggable.Credentials instantiated with expected attributes.
        assert isinstance(credentials, pluggable.Credentials)
        mock_init.assert_called_once_with(
            audience=AUDIENCE,
            subject_token_type=SUBJECT_TOKEN_TYPE,
            token_url=TOKEN_URL,
            token_info_url=None,
            service_account_impersonation_url=None,
            service_account_impersonation_options={},
            client_id=None,
            client_secret=None,
            credential_source=self.CREDENTIAL_SOURCE,
            quota_project_id=None,
            workforce_pool_user_project=None,
        )

    @mock.patch.object(pluggable.Credentials, "__init__", return_value=None)
    def test_from_file_full_options(self, mock_init, tmpdir):
        info = {
            "audience": AUDIENCE,
            "subject_token_type": SUBJECT_TOKEN_TYPE,
            "token_url": TOKEN_URL,
            "token_info_url": TOKEN_INFO_URL,
            "service_account_impersonation_url": SERVICE_ACCOUNT_IMPERSONATION_URL,
            "service_account_impersonation": {"token_lifetime_seconds": 2800},
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "quota_project_id": QUOTA_PROJECT_ID,
            "credential_source": self.CREDENTIAL_SOURCE,
        }
        config_file = tmpdir.join("config.json")
        config_file.write(json.dumps(info))
        credentials = pluggable.Credentials.from_file(str(config_file))

        # Confirm pluggable.Credentials instantiated with expected attributes.
        assert isinstance(credentials, pluggable.Credentials)
        mock_init.assert_called_once_with(
            audience=AUDIENCE,
            subject_token_type=SUBJECT_TOKEN_TYPE,
            token_url=TOKEN_URL,
            token_info_url=TOKEN_INFO_URL,
            service_account_impersonation_url=SERVICE_ACCOUNT_IMPERSONATION_URL,
            service_account_impersonation_options={"token_lifetime_seconds": 2800},
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            credential_source=self.CREDENTIAL_SOURCE,
            quota_project_id=QUOTA_PROJECT_ID,
            workforce_pool_user_project=None,
        )

    @mock.patch.object(pluggable.Credentials, "__init__", return_value=None)
    def test_from_file_required_options_only(self, mock_init, tmpdir):
        info = {
            "audience": AUDIENCE,
            "subject_token_type": SUBJECT_TOKEN_TYPE,
            "token_url": TOKEN_URL,
            "credential_source": self.CREDENTIAL_SOURCE,
        }
        config_file = tmpdir.join("config.json")
        config_file.write(json.dumps(info))
        credentials = pluggable.Credentials.from_file(str(config_file))

        # Confirm pluggable.Credentials instantiated with expected attributes.
        assert isinstance(credentials, pluggable.Credentials)
        mock_init.assert_called_once_with(
            audience=AUDIENCE,
            subject_token_type=SUBJECT_TOKEN_TYPE,
            token_url=TOKEN_URL,
            token_info_url=None,
            service_account_impersonation_url=None,
            service_account_impersonation_options={},
            client_id=None,
            client_secret=None,
            credential_source=self.CREDENTIAL_SOURCE,
            quota_project_id=None,
            workforce_pool_user_project=None,
        )

    def test_constructor_invalid_options(self):
        credential_source = {"unsupported": "value"}

        with pytest.raises(ValueError) as excinfo:
            self.make_pluggable(credential_source=credential_source)

        assert excinfo.match(r"Missing credential_source")

    def test_constructor_invalid_credential_source(self):
        with pytest.raises(ValueError) as excinfo:
            self.make_pluggable(credential_source="non-dict")

        assert excinfo.match(r"Missing credential_source")

    def test_info_with_credential_source(self):
        credentials = self.make_pluggable(
            credential_source=self.CREDENTIAL_SOURCE.copy()
        )

        assert credentials.info == {
            "type": "external_account",
            "audience": AUDIENCE,
            "subject_token_type": SUBJECT_TOKEN_TYPE,
            "token_url": TOKEN_URL,
            "token_info_url": TOKEN_INFO_URL,
            "credential_source": self.CREDENTIAL_SOURCE,
        }

    def test_token_info_url(self):
        credentials = self.make_pluggable(
            credential_source=self.CREDENTIAL_SOURCE.copy()
        )

        assert credentials.token_info_url == TOKEN_INFO_URL

    def test_token_info_url_custom(self):
        for url in VALID_TOKEN_URLS:
            credentials = self.make_pluggable(
                credential_source=self.CREDENTIAL_SOURCE.copy(),
                token_info_url=(url + "/introspect"),
            )

            assert credentials.token_info_url == url + "/introspect"

    def test_token_info_url_negative(self):
        credentials = self.make_pluggable(
            credential_source=self.CREDENTIAL_SOURCE.copy(), token_info_url=None
        )

        assert not credentials.token_info_url

    def test_token_url_custom(self):
        for url in VALID_TOKEN_URLS:
            credentials = self.make_pluggable(
                credential_source=self.CREDENTIAL_SOURCE.copy(),
                token_url=(url + "/token"),
            )

            assert credentials._token_url == (url + "/token")

    def test_service_account_impersonation_url_custom(self):
        for url in VALID_SERVICE_ACCOUNT_IMPERSONATION_URLS:
            credentials = self.make_pluggable(
                credential_source=self.CREDENTIAL_SOURCE.copy(),
                service_account_impersonation_url=(
                    url + SERVICE_ACCOUNT_IMPERSONATION_URL_ROUTE
                ),
            )

            assert credentials._service_account_impersonation_url == (
                url + SERVICE_ACCOUNT_IMPERSONATION_URL_ROUTE
            )

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_successfully(self, tmpdir):
        ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE = tmpdir.join(
            "actual_output_file"
        )
        ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE = {
            "command": "command",
            "interactive_timeout_millis": 300000,
            "output_file": ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE,
        }
        ACTUAL_CREDENTIAL_SOURCE = {"executable": ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE}

        testData = {
            "subject_token_oidc_id_token": {
                "stdout": json.dumps(
                    self.EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE_ID_TOKEN
                ).encode("UTF-8"),
                "impersonation_url": SERVICE_ACCOUNT_IMPERSONATION_URL,
                "file_content": self.EXECUTABLE_SUCCESSFUL_OIDC_NO_EXPIRATION_TIME_RESPONSE_ID_TOKEN,
                "expect_token": self.EXECUTABLE_OIDC_TOKEN,
            },
            "subject_token_oidc_id_token_interacitve_mode": {
                "audience": WORKFORCE_AUDIENCE,
                "file_content": self.EXECUTABLE_SUCCESSFUL_OIDC_NO_EXPIRATION_TIME_RESPONSE_ID_TOKEN,
                "interactive": True,
                "expect_token": self.EXECUTABLE_OIDC_TOKEN,
            },
            "subject_token_oidc_jwt": {
                "stdout": json.dumps(
                    self.EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE_JWT
                ).encode("UTF-8"),
                "impersonation_url": SERVICE_ACCOUNT_IMPERSONATION_URL,
                "file_content": self.EXECUTABLE_SUCCESSFUL_OIDC_NO_EXPIRATION_TIME_RESPONSE_JWT,
                "expect_token": self.EXECUTABLE_OIDC_TOKEN,
            },
            "subject_token_oidc_jwt_interactive_mode": {
                "audience": WORKFORCE_AUDIENCE,
                "file_content": self.EXECUTABLE_SUCCESSFUL_OIDC_NO_EXPIRATION_TIME_RESPONSE_JWT,
                "interactive": True,
                "expect_token": self.EXECUTABLE_OIDC_TOKEN,
            },
            "subject_token_saml": {
                "stdout": json.dumps(self.EXECUTABLE_SUCCESSFUL_SAML_RESPONSE).encode(
                    "UTF-8"
                ),
                "impersonation_url": SERVICE_ACCOUNT_IMPERSONATION_URL,
                "file_content": self.EXECUTABLE_SUCCESSFUL_SAML_NO_EXPIRATION_TIME_RESPONSE,
                "expect_token": self.EXECUTABLE_SAML_TOKEN,
            },
            "subject_token_saml_interactive_mode": {
                "audience": WORKFORCE_AUDIENCE,
                "file_content": self.EXECUTABLE_SUCCESSFUL_SAML_NO_EXPIRATION_TIME_RESPONSE,
                "interactive": True,
                "expect_token": self.EXECUTABLE_SAML_TOKEN,
            },
        }

        for data in testData.values():
            with open(
                ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE, "w"
            ) as output_file:
                json.dump(data.get("file_content"), output_file)

            with mock.patch(
                "subprocess.run",
                return_value=subprocess.CompletedProcess(
                    args=[], stdout=data.get("stdout"), returncode=0
                ),
            ):
                credentials = self.make_pluggable(
                    audience=data.get("audience", AUDIENCE),
                    service_account_impersonation_url=data.get("impersonation_url"),
                    credential_source=ACTUAL_CREDENTIAL_SOURCE,
                    interactive=data.get("interactive", False),
                )
                subject_token = credentials.retrieve_subject_token(None)
                assert subject_token == data.get("expect_token")
            os.remove(ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE)

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_saml(self):
        with mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[],
                stdout=json.dumps(self.EXECUTABLE_SUCCESSFUL_SAML_RESPONSE).encode(
                    "UTF-8"
                ),
                returncode=0,
            ),
        ):
            credentials = self.make_pluggable(credential_source=self.CREDENTIAL_SOURCE)

            subject_token = credentials.retrieve_subject_token(None)

            assert subject_token == self.EXECUTABLE_SAML_TOKEN

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_saml_interactive_mode(self, tmpdir):

        ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE = tmpdir.join(
            "actual_output_file"
        )
        ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE = {
            "command": "command",
            "interactive_timeout_millis": 300000,
            "output_file": ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE,
        }
        ACTUAL_CREDENTIAL_SOURCE = {"executable": ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE}
        with open(ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE, "w") as output_file:
            json.dump(
                self.EXECUTABLE_SUCCESSFUL_SAML_NO_EXPIRATION_TIME_RESPONSE, output_file
            )

        with mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=0),
        ):
            credentials = self.make_pluggable(
                audience=WORKFORCE_AUDIENCE,
                credential_source=ACTUAL_CREDENTIAL_SOURCE,
                interactive=True,
            )

            subject_token = credentials.retrieve_subject_token(None)

            assert subject_token == self.EXECUTABLE_SAML_TOKEN
            os.remove(ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE)

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_failed(self):
        with mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[],
                stdout=json.dumps(self.EXECUTABLE_FAILED_RESPONSE).encode("UTF-8"),
                returncode=0,
            ),
        ):
            credentials = self.make_pluggable(credential_source=self.CREDENTIAL_SOURCE)

            with pytest.raises(exceptions.RefreshError) as excinfo:
                _ = credentials.retrieve_subject_token(None)

            assert excinfo.match(
                r"Executable returned unsuccessful response: code: 401, message: Permission denied. Caller not authorized."
            )

    @mock.patch.dict(
        os.environ,
        {
            "GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1",
            "GOOGLE_EXTERNAL_ACCOUNT_INTERACTIVE": "1",
        },
    )
    def test_retrieve_subject_token_failed_interactive_mode(self, tmpdir):
        ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE = tmpdir.join(
            "actual_output_file"
        )
        ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE = {
            "command": "command",
            "interactive_timeout_millis": 300000,
            "output_file": ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE,
        }
        ACTUAL_CREDENTIAL_SOURCE = {"executable": ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE}
        with open(
            ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE, "w", encoding="utf-8"
        ) as output_file:
            json.dump(self.EXECUTABLE_FAILED_RESPONSE, output_file)

        with mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=0),
        ):
            credentials = self.make_pluggable(
                audience=WORKFORCE_AUDIENCE,
                credential_source=ACTUAL_CREDENTIAL_SOURCE,
                interactive=True,
            )

            with pytest.raises(exceptions.RefreshError) as excinfo:
                _ = credentials.retrieve_subject_token(None)

            assert excinfo.match(
                r"Executable returned unsuccessful response: code: 401, message: Permission denied. Caller not authorized."
            )
            os.remove(ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE)

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "0"})
    def test_retrieve_subject_token_not_allowd(self):
        with mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[],
                stdout=json.dumps(
                    self.EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE_ID_TOKEN
                ).encode("UTF-8"),
                returncode=0,
            ),
        ):
            credentials = self.make_pluggable(credential_source=self.CREDENTIAL_SOURCE)

            with pytest.raises(ValueError) as excinfo:
                _ = credentials.retrieve_subject_token(None)

            assert excinfo.match(r"Executables need to be explicitly allowed")

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_invalid_version(self):
        EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE_VERSION_2 = {
            "version": 2,
            "success": True,
            "token_type": "urn:ietf:params:oauth:token-type:id_token",
            "id_token": self.EXECUTABLE_OIDC_TOKEN,
            "expiration_time": 9999999999,
        }

        with mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[],
                stdout=json.dumps(EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE_VERSION_2).encode(
                    "UTF-8"
                ),
                returncode=0,
            ),
        ):
            credentials = self.make_pluggable(credential_source=self.CREDENTIAL_SOURCE)

            with pytest.raises(exceptions.RefreshError) as excinfo:
                _ = credentials.retrieve_subject_token(None)

            assert excinfo.match(r"Executable returned unsupported version.")

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_expired_token(self):
        EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE_EXPIRED = {
            "version": 1,
            "success": True,
            "token_type": "urn:ietf:params:oauth:token-type:id_token",
            "id_token": self.EXECUTABLE_OIDC_TOKEN,
            "expiration_time": 0,
        }

        with mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[],
                stdout=json.dumps(EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE_EXPIRED).encode(
                    "UTF-8"
                ),
                returncode=0,
            ),
        ):
            credentials = self.make_pluggable(credential_source=self.CREDENTIAL_SOURCE)

            with pytest.raises(exceptions.RefreshError) as excinfo:
                _ = credentials.retrieve_subject_token(None)

            assert excinfo.match(r"The token returned by the executable is expired.")

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_file_cache(self, tmpdir):
        ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE = tmpdir.join(
            "actual_output_file"
        )
        ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE = {
            "command": "command",
            "timeout_millis": 30000,
            "output_file": ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE,
        }
        ACTUAL_CREDENTIAL_SOURCE = {"executable": ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE}
        with open(ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE, "w") as output_file:
            json.dump(self.EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE_ID_TOKEN, output_file)

        credentials = self.make_pluggable(credential_source=ACTUAL_CREDENTIAL_SOURCE)

        subject_token = credentials.retrieve_subject_token(None)
        assert subject_token == self.EXECUTABLE_OIDC_TOKEN

        os.remove(ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE)

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_no_file_cache(self):
        ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE = {
            "command": "command",
            "timeout_millis": 30000,
        }
        ACTUAL_CREDENTIAL_SOURCE = {"executable": ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE}

        with mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[],
                stdout=json.dumps(
                    self.EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE_ID_TOKEN
                ).encode("UTF-8"),
                returncode=0,
            ),
        ):
            credentials = self.make_pluggable(
                credential_source=ACTUAL_CREDENTIAL_SOURCE
            )

            subject_token = credentials.retrieve_subject_token(None)

            assert subject_token == self.EXECUTABLE_OIDC_TOKEN

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_file_cache_value_error_report(self, tmpdir):
        ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE = tmpdir.join(
            "actual_output_file"
        )
        ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE = {
            "command": "command",
            "timeout_millis": 30000,
            "output_file": ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE,
        }
        ACTUAL_CREDENTIAL_SOURCE = {"executable": ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE}
        ACTUAL_EXECUTABLE_RESPONSE = {
            "success": True,
            "token_type": "urn:ietf:params:oauth:token-type:id_token",
            "id_token": self.EXECUTABLE_OIDC_TOKEN,
            "expiration_time": 9999999999,
        }
        with open(ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE, "w") as output_file:
            json.dump(ACTUAL_EXECUTABLE_RESPONSE, output_file)

        credentials = self.make_pluggable(credential_source=ACTUAL_CREDENTIAL_SOURCE)

        with pytest.raises(ValueError) as excinfo:
            _ = credentials.retrieve_subject_token(None)

        assert excinfo.match(r"The executable response is missing the version field.")

        os.remove(ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE)

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_file_cache_refresh_error_retry(self, tmpdir):
        ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE = tmpdir.join(
            "actual_output_file"
        )
        ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE = {
            "command": "command",
            "timeout_millis": 30000,
            "output_file": ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE,
        }
        ACTUAL_CREDENTIAL_SOURCE = {"executable": ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE}
        ACTUAL_EXECUTABLE_RESPONSE = {
            "version": 2,
            "success": True,
            "token_type": "urn:ietf:params:oauth:token-type:id_token",
            "id_token": self.EXECUTABLE_OIDC_TOKEN,
            "expiration_time": 9999999999,
        }
        with open(ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE, "w") as output_file:
            json.dump(ACTUAL_EXECUTABLE_RESPONSE, output_file)

        with mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[],
                stdout=json.dumps(
                    self.EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE_ID_TOKEN
                ).encode("UTF-8"),
                returncode=0,
            ),
        ):
            credentials = self.make_pluggable(
                credential_source=ACTUAL_CREDENTIAL_SOURCE
            )

            subject_token = credentials.retrieve_subject_token(None)

            assert subject_token == self.EXECUTABLE_OIDC_TOKEN

        os.remove(ACTUAL_CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE)

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_unsupported_token_type(self):
        EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE = {
            "version": 1,
            "success": True,
            "token_type": "unsupported_token_type",
            "id_token": self.EXECUTABLE_OIDC_TOKEN,
            "expiration_time": 9999999999,
        }

        with mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[],
                stdout=json.dumps(EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE).encode("UTF-8"),
                returncode=0,
            ),
        ):
            credentials = self.make_pluggable(credential_source=self.CREDENTIAL_SOURCE)

            with pytest.raises(exceptions.RefreshError) as excinfo:
                _ = credentials.retrieve_subject_token(None)

            assert excinfo.match(r"Executable returned unsupported token type.")

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_missing_version(self):
        EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE = {
            "success": True,
            "token_type": "urn:ietf:params:oauth:token-type:id_token",
            "id_token": self.EXECUTABLE_OIDC_TOKEN,
            "expiration_time": 9999999999,
        }

        with mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[],
                stdout=json.dumps(EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE).encode("UTF-8"),
                returncode=0,
            ),
        ):
            credentials = self.make_pluggable(credential_source=self.CREDENTIAL_SOURCE)

            with pytest.raises(ValueError) as excinfo:
                _ = credentials.retrieve_subject_token(None)

            assert excinfo.match(
                r"The executable response is missing the version field."
            )

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_missing_success(self):
        EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE = {
            "version": 1,
            "token_type": "urn:ietf:params:oauth:token-type:id_token",
            "id_token": self.EXECUTABLE_OIDC_TOKEN,
            "expiration_time": 9999999999,
        }

        with mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[],
                stdout=json.dumps(EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE).encode("UTF-8"),
                returncode=0,
            ),
        ):
            credentials = self.make_pluggable(credential_source=self.CREDENTIAL_SOURCE)

            with pytest.raises(ValueError) as excinfo:
                _ = credentials.retrieve_subject_token(None)

            assert excinfo.match(
                r"The executable response is missing the success field."
            )

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_missing_error_code_message(self):
        EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE = {"version": 1, "success": False}

        with mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[],
                stdout=json.dumps(EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE).encode("UTF-8"),
                returncode=0,
            ),
        ):
            credentials = self.make_pluggable(credential_source=self.CREDENTIAL_SOURCE)

            with pytest.raises(ValueError) as excinfo:
                _ = credentials.retrieve_subject_token(None)

            assert excinfo.match(
                r"Error code and message fields are required in the response."
            )

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_without_expiration_time_should_pass_when_output_file_not_specified(
        self,
    ):
        EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE = {
            "version": 1,
            "success": True,
            "token_type": "urn:ietf:params:oauth:token-type:id_token",
            "id_token": self.EXECUTABLE_OIDC_TOKEN,
        }

        CREDENTIAL_SOURCE = {
            "executable": {"command": "command", "timeout_millis": 30000}
        }

        with mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[],
                stdout=json.dumps(EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE).encode("UTF-8"),
                returncode=0,
            ),
        ):
            credentials = self.make_pluggable(credential_source=CREDENTIAL_SOURCE)
            subject_token = credentials.retrieve_subject_token(None)

            assert subject_token == self.EXECUTABLE_OIDC_TOKEN

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_missing_token_type(self):
        EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE = {
            "version": 1,
            "success": True,
            "id_token": self.EXECUTABLE_OIDC_TOKEN,
            "expiration_time": 9999999999,
        }

        with mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[],
                stdout=json.dumps(EXECUTABLE_SUCCESSFUL_OIDC_RESPONSE).encode("UTF-8"),
                returncode=0,
            ),
        ):
            credentials = self.make_pluggable(credential_source=self.CREDENTIAL_SOURCE)

            with pytest.raises(ValueError) as excinfo:
                _ = credentials.retrieve_subject_token(None)

            assert excinfo.match(
                r"The executable response is missing the token_type field."
            )

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_credential_source_missing_command(self):
        with pytest.raises(ValueError) as excinfo:
            CREDENTIAL_SOURCE = {
                "executable": {
                    "timeout_millis": 30000,
                    "output_file": self.CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE,
                }
            }
            _ = self.make_pluggable(credential_source=CREDENTIAL_SOURCE)

        assert excinfo.match(
            r"Missing command field. Executable command must be provided."
        )

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_credential_source_missing_output_interactive_mode(self):
        CREDENTIAL_SOURCE = {
            "executable": {"command": self.CREDENTIAL_SOURCE_EXECUTABLE_COMMAND}
        }
        credentials = self.make_pluggable(
            credential_source=CREDENTIAL_SOURCE, interactive=True
        )
        with pytest.raises(ValueError) as excinfo:
            _ = credentials.retrieve_subject_token(None)

        assert excinfo.match(
            r"An output_file must be specified in the credential configuration for interactive mode."
        )

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_credential_source_timeout_missing_will_use_default_timeout_value(self):
        CREDENTIAL_SOURCE = {
            "executable": {
                "command": self.CREDENTIAL_SOURCE_EXECUTABLE_COMMAND,
                "output_file": self.CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE,
            }
        }
        credentials = self.make_pluggable(credential_source=CREDENTIAL_SOURCE)

        assert (
            credentials._credential_source_executable_timeout_millis
            == pluggable.EXECUTABLE_TIMEOUT_MILLIS_DEFAULT
        )

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_credential_source_timeout_small(self):
        with pytest.raises(ValueError) as excinfo:
            CREDENTIAL_SOURCE = {
                "executable": {
                    "command": self.CREDENTIAL_SOURCE_EXECUTABLE_COMMAND,
                    "timeout_millis": 5000 - 1,
                    "output_file": self.CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE,
                }
            }
            _ = self.make_pluggable(credential_source=CREDENTIAL_SOURCE)

        assert excinfo.match(r"Timeout must be between 5 and 120 seconds.")

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_credential_source_timeout_large(self):
        with pytest.raises(ValueError) as excinfo:
            CREDENTIAL_SOURCE = {
                "executable": {
                    "command": self.CREDENTIAL_SOURCE_EXECUTABLE_COMMAND,
                    "timeout_millis": 120000 + 1,
                    "output_file": self.CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE,
                }
            }
            _ = self.make_pluggable(credential_source=CREDENTIAL_SOURCE)

        assert excinfo.match(r"Timeout must be between 5 and 120 seconds.")

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_credential_source_interactive_timeout_small(self):
        with pytest.raises(ValueError) as excinfo:
            CREDENTIAL_SOURCE = {
                "executable": {
                    "command": self.CREDENTIAL_SOURCE_EXECUTABLE_COMMAND,
                    "interactive_timeout_millis": 30000 - 1,
                    "output_file": self.CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE,
                }
            }
            _ = self.make_pluggable(credential_source=CREDENTIAL_SOURCE)

        assert excinfo.match(
            r"Interactive timeout must be between 30 seconds and 30 minutes."
        )

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_credential_source_interactive_timeout_large(self):
        with pytest.raises(ValueError) as excinfo:
            CREDENTIAL_SOURCE = {
                "executable": {
                    "command": self.CREDENTIAL_SOURCE_EXECUTABLE_COMMAND,
                    "interactive_timeout_millis": 1800000 + 1,
                    "output_file": self.CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE,
                }
            }
            _ = self.make_pluggable(credential_source=CREDENTIAL_SOURCE)

        assert excinfo.match(
            r"Interactive timeout must be between 30 seconds and 30 minutes."
        )

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_executable_fail(self):
        with mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[], stdout=None, returncode=1
            ),
        ):
            credentials = self.make_pluggable(credential_source=self.CREDENTIAL_SOURCE)

            with pytest.raises(exceptions.RefreshError) as excinfo:
                _ = credentials.retrieve_subject_token(None)

            assert excinfo.match(
                r"Executable exited with non-zero return code 1. Error: None"
            )

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_non_workforce_fail_interactive_mode(self):
        credentials = self.make_pluggable(
            credential_source=self.CREDENTIAL_SOURCE, interactive=True
        )
        with pytest.raises(ValueError) as excinfo:
            _ = credentials.retrieve_subject_token(None)

        assert excinfo.match(r"Interactive mode is only enabled for workforce pool.")

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_fail_on_validation_missing_interactive_timeout(
        self
    ):
        CREDENTIAL_SOURCE_EXECUTABLE = {
            "command": self.CREDENTIAL_SOURCE_EXECUTABLE_COMMAND,
            "output_file": self.CREDENTIAL_SOURCE_EXECUTABLE_OUTPUT_FILE,
        }
        CREDENTIAL_SOURCE = {"executable": CREDENTIAL_SOURCE_EXECUTABLE}
        credentials = self.make_pluggable(
            credential_source=CREDENTIAL_SOURCE, interactive=True
        )
        with pytest.raises(ValueError) as excinfo:
            _ = credentials.retrieve_subject_token(None)

        assert excinfo.match(
            r"Interactive mode cannot run without an interactive timeout."
        )

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_executable_fail_interactive_mode(self):
        with mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[], stdout=None, returncode=1
            ),
        ):
            credentials = self.make_pluggable(
                audience=WORKFORCE_AUDIENCE,
                credential_source=self.CREDENTIAL_SOURCE,
                interactive=True,
            )

            with pytest.raises(exceptions.RefreshError) as excinfo:
                _ = credentials.retrieve_subject_token(None)

            assert excinfo.match(
                r"Executable exited with non-zero return code 1. Error: None"
            )

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "0"})
    def test_revoke_failed_executable_not_allowed(self):
        credentials = self.make_pluggable(
            credential_source=self.CREDENTIAL_SOURCE, interactive=True
        )
        with pytest.raises(ValueError) as excinfo:
            _ = credentials.revoke(None)

        assert excinfo.match(r"Executables need to be explicitly allowed")

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_revoke_failed(self):
        testData = {
            "non_interactive_mode": {
                "interactive": False,
                "expectErrType": ValueError,
                "expectErrPattern": r"Revoke is only enabled under interactive mode.",
            },
            "executable_failed": {
                "returncode": 1,
                "expectErrType": exceptions.RefreshError,
                "expectErrPattern": r"Auth revoke failed on executable.",
            },
            "response_validation_missing_version": {
                "response": {},
                "expectErrType": ValueError,
                "expectErrPattern": r"The executable response is missing the version field.",
            },
            "response_validation_invalid_version": {
                "response": {"version": 2},
                "expectErrType": exceptions.RefreshError,
                "expectErrPattern": r"Executable returned unsupported version.",
            },
            "response_validation_missing_success": {
                "response": {"version": 1},
                "expectErrType": ValueError,
                "expectErrPattern": r"The executable response is missing the success field.",
            },
            "response_validation_failed_with_success_field_is_false": {
                "response": {"version": 1, "success": False},
                "expectErrType": exceptions.RefreshError,
                "expectErrPattern": r"Revoke failed with unsuccessful response.",
            },
        }
        for data in testData.values():
            with mock.patch(
                "subprocess.run",
                return_value=subprocess.CompletedProcess(
                    args=[],
                    stdout=json.dumps(data.get("response")).encode("UTF-8"),
                    returncode=data.get("returncode", 0),
                ),
            ):
                credentials = self.make_pluggable(
                    audience=WORKFORCE_AUDIENCE,
                    service_account_impersonation_url=SERVICE_ACCOUNT_IMPERSONATION_URL,
                    credential_source=self.CREDENTIAL_SOURCE,
                    interactive=data.get("interactive", True),
                )

                with pytest.raises(data.get("expectErrType")) as excinfo:
                    _ = credentials.revoke(None)

                assert excinfo.match(data.get("expectErrPattern"))

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_revoke_successfully(self):
        ACTUAL_RESPONSE = {"version": 1, "success": True}
        with mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                args=[],
                stdout=json.dumps(ACTUAL_RESPONSE).encode("utf-8"),
                returncode=0,
            ),
        ):
            credentials = self.make_pluggable(
                audience=WORKFORCE_AUDIENCE,
                credential_source=self.CREDENTIAL_SOURCE,
                interactive=True,
            )
            _ = credentials.revoke(None)

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_retrieve_subject_token_python_2(self):
        with mock.patch("sys.version_info", (2, 7)):
            credentials = self.make_pluggable(credential_source=self.CREDENTIAL_SOURCE)

            with pytest.raises(exceptions.RefreshError) as excinfo:
                _ = credentials.retrieve_subject_token(None)

            assert excinfo.match(r"Pluggable auth is only supported for python 3.6+")

    @mock.patch.dict(os.environ, {"GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES": "1"})
    def test_revoke_subject_token_python_2(self):
        with mock.patch("sys.version_info", (2, 7)):
            credentials = self.make_pluggable(
                audience=WORKFORCE_AUDIENCE,
                credential_source=self.CREDENTIAL_SOURCE,
                interactive=True,
            )

            with pytest.raises(exceptions.RefreshError) as excinfo:
                _ = credentials.revoke(None)

            assert excinfo.match(r"Pluggable auth is only supported for python 3.6+")
