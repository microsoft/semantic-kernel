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
from six.moves import http_client
from six.moves import urllib

from google.auth import _helpers
from google.auth import exceptions
from google.auth import external_account
from google.auth import transport


CLIENT_ID = "username"
CLIENT_SECRET = "password"
# Base64 encoding of "username:password"
BASIC_AUTH_ENCODING = "dXNlcm5hbWU6cGFzc3dvcmQ="
SERVICE_ACCOUNT_EMAIL = "service-1234@service-name.iam.gserviceaccount.com"
# List of valid workforce pool audiences.
TEST_USER_AUDIENCES = [
    "//iam.googleapis.com/locations/global/workforcePools/pool-id/providers/provider-id",
    "//iam.googleapis.com/locations/eu/workforcePools/pool-id/providers/provider-id",
    "//iam.googleapis.com/locations/eu/workforcePools/workloadIdentityPools/providers/provider-id",
]
# Workload identity pool audiences or invalid workforce pool audiences.
TEST_NON_USER_AUDIENCES = [
    # Legacy K8s audience format.
    "identitynamespace:1f12345:my_provider",
    (
        "//iam.googleapis.com/projects/123456/locations/"
        "global/workloadIdentityPools/pool-id/providers/"
        "provider-id"
    ),
    (
        "//iam.googleapis.com/projects/123456/locations/"
        "eu/workloadIdentityPools/pool-id/providers/"
        "provider-id"
    ),
    # Pool ID with workforcePools string.
    (
        "//iam.googleapis.com/projects/123456/locations/"
        "global/workloadIdentityPools/workforcePools/providers/"
        "provider-id"
    ),
    # Unrealistic / incorrect workforce pool audiences.
    "//iamgoogleapis.com/locations/eu/workforcePools/pool-id/providers/provider-id",
    "//iam.googleapiscom/locations/eu/workforcePools/pool-id/providers/provider-id",
    "//iam.googleapis.com/locations/workforcePools/pool-id/providers/provider-id",
    "//iam.googleapis.com/locations/eu/workforcePool/pool-id/providers/provider-id",
    "//iam.googleapis.com/locations//workforcePool/pool-id/providers/provider-id",
]


class CredentialsImpl(external_account.Credentials):
    def __init__(self, **kwargs):
        super(CredentialsImpl, self).__init__(**kwargs)
        self._counter = 0

    def retrieve_subject_token(self, request):
        counter = self._counter
        self._counter += 1
        return "subject_token_{}".format(counter)


class TestCredentials(object):
    TOKEN_URL = "https://sts.googleapis.com/v1/token"
    TOKEN_INFO_URL = "https://sts.googleapis.com/v1/introspect"
    PROJECT_NUMBER = "123456"
    POOL_ID = "POOL_ID"
    PROVIDER_ID = "PROVIDER_ID"
    AUDIENCE = (
        "//iam.googleapis.com/projects/{}"
        "/locations/global/workloadIdentityPools/{}"
        "/providers/{}"
    ).format(PROJECT_NUMBER, POOL_ID, PROVIDER_ID)
    WORKFORCE_AUDIENCE = (
        "//iam.googleapis.com/locations/global/workforcePools/{}/providers/{}"
    ).format(POOL_ID, PROVIDER_ID)
    WORKFORCE_POOL_USER_PROJECT = "WORKFORCE_POOL_USER_PROJECT_NUMBER"
    SUBJECT_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:jwt"
    WORKFORCE_SUBJECT_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:id_token"
    CREDENTIAL_SOURCE = {"file": "/var/run/secrets/goog.id/token"}
    SUCCESS_RESPONSE = {
        "access_token": "ACCESS_TOKEN",
        "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "scope1 scope2",
    }
    ERROR_RESPONSE = {
        "error": "invalid_request",
        "error_description": "Invalid subject token",
        "error_uri": "https://tools.ietf.org/html/rfc6749",
    }
    QUOTA_PROJECT_ID = "QUOTA_PROJECT_ID"
    SERVICE_ACCOUNT_IMPERSONATION_URL = (
        "https://us-east1-iamcredentials.googleapis.com/v1/projects/-"
        + "/serviceAccounts/{}:generateAccessToken".format(SERVICE_ACCOUNT_EMAIL)
    )
    SCOPES = ["scope1", "scope2"]
    IMPERSONATION_ERROR_RESPONSE = {
        "error": {
            "code": 400,
            "message": "Request contains an invalid argument",
            "status": "INVALID_ARGUMENT",
        }
    }
    PROJECT_ID = "my-proj-id"
    CLOUD_RESOURCE_MANAGER_URL = (
        "https://cloudresourcemanager.googleapis.com/v1/projects/"
    )
    CLOUD_RESOURCE_MANAGER_SUCCESS_RESPONSE = {
        "projectNumber": PROJECT_NUMBER,
        "projectId": PROJECT_ID,
        "lifecycleState": "ACTIVE",
        "name": "project-name",
        "createTime": "2018-11-06T04:42:54.109Z",
        "parent": {"type": "folder", "id": "12345678901"},
    }

    @classmethod
    def make_credentials(
        cls,
        client_id=None,
        client_secret=None,
        quota_project_id=None,
        token_info_url=None,
        scopes=None,
        default_scopes=None,
        service_account_impersonation_url=None,
        service_account_impersonation_options={},
    ):
        return CredentialsImpl(
            audience=cls.AUDIENCE,
            subject_token_type=cls.SUBJECT_TOKEN_TYPE,
            token_url=cls.TOKEN_URL,
            token_info_url=token_info_url,
            service_account_impersonation_url=service_account_impersonation_url,
            service_account_impersonation_options=service_account_impersonation_options,
            credential_source=cls.CREDENTIAL_SOURCE,
            client_id=client_id,
            client_secret=client_secret,
            quota_project_id=quota_project_id,
            scopes=scopes,
            default_scopes=default_scopes,
        )

    @classmethod
    def make_workforce_pool_credentials(
        cls,
        client_id=None,
        client_secret=None,
        quota_project_id=None,
        scopes=None,
        default_scopes=None,
        service_account_impersonation_url=None,
        workforce_pool_user_project=None,
    ):
        return CredentialsImpl(
            audience=cls.WORKFORCE_AUDIENCE,
            subject_token_type=cls.WORKFORCE_SUBJECT_TOKEN_TYPE,
            token_url=cls.TOKEN_URL,
            service_account_impersonation_url=service_account_impersonation_url,
            credential_source=cls.CREDENTIAL_SOURCE,
            client_id=client_id,
            client_secret=client_secret,
            quota_project_id=quota_project_id,
            scopes=scopes,
            default_scopes=default_scopes,
            workforce_pool_user_project=workforce_pool_user_project,
        )

    @classmethod
    def make_mock_request(
        cls,
        status=http_client.OK,
        data=None,
        impersonation_status=None,
        impersonation_data=None,
        cloud_resource_manager_status=None,
        cloud_resource_manager_data=None,
    ):
        # STS token exchange request.
        token_response = mock.create_autospec(transport.Response, instance=True)
        token_response.status = status
        token_response.data = json.dumps(data).encode("utf-8")
        responses = [token_response]

        # If service account impersonation is requested, mock the expected response.
        if impersonation_status:
            impersonation_response = mock.create_autospec(
                transport.Response, instance=True
            )
            impersonation_response.status = impersonation_status
            impersonation_response.data = json.dumps(impersonation_data).encode("utf-8")
            responses.append(impersonation_response)

        # If cloud resource manager is requested, mock the expected response.
        if cloud_resource_manager_status:
            cloud_resource_manager_response = mock.create_autospec(
                transport.Response, instance=True
            )
            cloud_resource_manager_response.status = cloud_resource_manager_status
            cloud_resource_manager_response.data = json.dumps(
                cloud_resource_manager_data
            ).encode("utf-8")
            responses.append(cloud_resource_manager_response)

        request = mock.create_autospec(transport.Request)
        request.side_effect = responses

        return request

    @classmethod
    def assert_token_request_kwargs(cls, request_kwargs, headers, request_data):
        assert request_kwargs["url"] == cls.TOKEN_URL
        assert request_kwargs["method"] == "POST"
        assert request_kwargs["headers"] == headers
        assert request_kwargs["body"] is not None
        body_tuples = urllib.parse.parse_qsl(request_kwargs["body"])
        for (k, v) in body_tuples:
            assert v.decode("utf-8") == request_data[k.decode("utf-8")]
        assert len(body_tuples) == len(request_data.keys())

    @classmethod
    def assert_impersonation_request_kwargs(cls, request_kwargs, headers, request_data):
        assert request_kwargs["url"] == cls.SERVICE_ACCOUNT_IMPERSONATION_URL
        assert request_kwargs["method"] == "POST"
        assert request_kwargs["headers"] == headers
        assert request_kwargs["body"] is not None
        body_json = json.loads(request_kwargs["body"].decode("utf-8"))
        assert body_json == request_data

    @classmethod
    def assert_resource_manager_request_kwargs(
        cls, request_kwargs, project_number, headers
    ):
        assert request_kwargs["url"] == cls.CLOUD_RESOURCE_MANAGER_URL + project_number
        assert request_kwargs["method"] == "GET"
        assert request_kwargs["headers"] == headers
        assert "body" not in request_kwargs

    def test_default_state(self):
        credentials = self.make_credentials(
            service_account_impersonation_url=self.SERVICE_ACCOUNT_IMPERSONATION_URL
        )

        # Token url and service account impersonation url should be set
        assert credentials._token_url
        assert credentials._service_account_impersonation_url
        # Not token acquired yet
        assert not credentials.token
        assert not credentials.valid
        # Expiration hasn't been set yet
        assert not credentials.expiry
        assert not credentials.expired
        # Scopes are required
        assert not credentials.scopes
        assert credentials.requires_scopes
        assert not credentials.quota_project_id
        # Token info url not set yet
        assert not credentials.token_info_url

    def test_nonworkforce_with_workforce_pool_user_project(self):
        with pytest.raises(ValueError) as excinfo:
            CredentialsImpl(
                audience=self.AUDIENCE,
                subject_token_type=self.SUBJECT_TOKEN_TYPE,
                token_url=self.TOKEN_URL,
                credential_source=self.CREDENTIAL_SOURCE,
                workforce_pool_user_project=self.WORKFORCE_POOL_USER_PROJECT,
            )

        assert excinfo.match(
            "workforce_pool_user_project should not be set for non-workforce "
            "pool credentials"
        )

    def test_with_scopes(self):
        credentials = self.make_credentials()

        assert not credentials.scopes
        assert credentials.requires_scopes

        scoped_credentials = credentials.with_scopes(["email"])

        assert scoped_credentials.has_scopes(["email"])
        assert not scoped_credentials.requires_scopes

    def test_with_scopes_workforce_pool(self):
        credentials = self.make_workforce_pool_credentials(
            workforce_pool_user_project=self.WORKFORCE_POOL_USER_PROJECT
        )

        assert not credentials.scopes
        assert credentials.requires_scopes

        scoped_credentials = credentials.with_scopes(["email"])

        assert scoped_credentials.has_scopes(["email"])
        assert not scoped_credentials.requires_scopes
        assert (
            scoped_credentials.info.get("workforce_pool_user_project")
            == self.WORKFORCE_POOL_USER_PROJECT
        )

    def test_with_scopes_using_user_and_default_scopes(self):
        credentials = self.make_credentials()

        assert not credentials.scopes
        assert credentials.requires_scopes

        scoped_credentials = credentials.with_scopes(
            ["email"], default_scopes=["profile"]
        )

        assert scoped_credentials.has_scopes(["email"])
        assert not scoped_credentials.has_scopes(["profile"])
        assert not scoped_credentials.requires_scopes
        assert scoped_credentials.scopes == ["email"]
        assert scoped_credentials.default_scopes == ["profile"]

    def test_with_scopes_using_default_scopes_only(self):
        credentials = self.make_credentials()

        assert not credentials.scopes
        assert credentials.requires_scopes

        scoped_credentials = credentials.with_scopes(None, default_scopes=["profile"])

        assert scoped_credentials.has_scopes(["profile"])
        assert not scoped_credentials.requires_scopes

    def test_with_scopes_full_options_propagated(self):
        credentials = self.make_credentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            quota_project_id=self.QUOTA_PROJECT_ID,
            scopes=self.SCOPES,
            token_info_url=self.TOKEN_INFO_URL,
            default_scopes=["default1"],
            service_account_impersonation_url=self.SERVICE_ACCOUNT_IMPERSONATION_URL,
            service_account_impersonation_options={"token_lifetime_seconds": 2800},
        )

        with mock.patch.object(
            external_account.Credentials, "__init__", return_value=None
        ) as mock_init:
            credentials.with_scopes(["email"], ["default2"])

        # Confirm with_scopes initialized the credential with the expected
        # parameters and scopes.
        mock_init.assert_called_once_with(
            audience=self.AUDIENCE,
            subject_token_type=self.SUBJECT_TOKEN_TYPE,
            token_url=self.TOKEN_URL,
            token_info_url=self.TOKEN_INFO_URL,
            credential_source=self.CREDENTIAL_SOURCE,
            service_account_impersonation_url=self.SERVICE_ACCOUNT_IMPERSONATION_URL,
            service_account_impersonation_options={"token_lifetime_seconds": 2800},
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            quota_project_id=self.QUOTA_PROJECT_ID,
            scopes=["email"],
            default_scopes=["default2"],
        )

    def test_with_token_uri(self):
        credentials = self.make_credentials()
        new_token_uri = "https://eu-sts.googleapis.com/v1/token"

        assert credentials._token_url == self.TOKEN_URL

        creds_with_new_token_uri = credentials.with_token_uri(new_token_uri)

        assert creds_with_new_token_uri._token_url == new_token_uri

    def test_with_token_uri_workforce_pool(self):
        credentials = self.make_workforce_pool_credentials(
            workforce_pool_user_project=self.WORKFORCE_POOL_USER_PROJECT
        )

        new_token_uri = "https://eu-sts.googleapis.com/v1/token"

        assert credentials._token_url == self.TOKEN_URL

        creds_with_new_token_uri = credentials.with_token_uri(new_token_uri)

        assert creds_with_new_token_uri._token_url == new_token_uri
        assert (
            creds_with_new_token_uri.info.get("workforce_pool_user_project")
            == self.WORKFORCE_POOL_USER_PROJECT
        )

    def test_with_quota_project(self):
        credentials = self.make_credentials()

        assert not credentials.scopes
        assert not credentials.quota_project_id

        quota_project_creds = credentials.with_quota_project("project-foo")

        assert quota_project_creds.quota_project_id == "project-foo"

    def test_with_quota_project_workforce_pool(self):
        credentials = self.make_workforce_pool_credentials(
            workforce_pool_user_project=self.WORKFORCE_POOL_USER_PROJECT
        )

        assert not credentials.scopes
        assert not credentials.quota_project_id

        quota_project_creds = credentials.with_quota_project("project-foo")

        assert quota_project_creds.quota_project_id == "project-foo"
        assert (
            quota_project_creds.info.get("workforce_pool_user_project")
            == self.WORKFORCE_POOL_USER_PROJECT
        )

    def test_with_quota_project_full_options_propagated(self):
        credentials = self.make_credentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_info_url=self.TOKEN_INFO_URL,
            quota_project_id=self.QUOTA_PROJECT_ID,
            scopes=self.SCOPES,
            default_scopes=["default1"],
            service_account_impersonation_url=self.SERVICE_ACCOUNT_IMPERSONATION_URL,
            service_account_impersonation_options={"token_lifetime_seconds": 2800},
        )

        with mock.patch.object(
            external_account.Credentials, "__init__", return_value=None
        ) as mock_init:
            credentials.with_quota_project("project-foo")

        # Confirm with_quota_project initialized the credential with the
        # expected parameters and quota project ID.
        mock_init.assert_called_once_with(
            audience=self.AUDIENCE,
            subject_token_type=self.SUBJECT_TOKEN_TYPE,
            token_url=self.TOKEN_URL,
            token_info_url=self.TOKEN_INFO_URL,
            credential_source=self.CREDENTIAL_SOURCE,
            service_account_impersonation_url=self.SERVICE_ACCOUNT_IMPERSONATION_URL,
            service_account_impersonation_options={"token_lifetime_seconds": 2800},
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            quota_project_id="project-foo",
            scopes=self.SCOPES,
            default_scopes=["default1"],
        )

    def test_with_invalid_impersonation_target_principal(self):
        invalid_url = "https://iamcredentials.googleapis.com/v1/invalid"

        with pytest.raises(exceptions.RefreshError) as excinfo:
            self.make_credentials(service_account_impersonation_url=invalid_url)

        assert excinfo.match(
            r"Unable to determine target principal from service account impersonation URL."
        )

    def test_info(self):
        credentials = self.make_credentials()

        assert credentials.info == {
            "type": "external_account",
            "audience": self.AUDIENCE,
            "subject_token_type": self.SUBJECT_TOKEN_TYPE,
            "token_url": self.TOKEN_URL,
            "credential_source": self.CREDENTIAL_SOURCE.copy(),
        }

    def test_info_workforce_pool(self):
        credentials = self.make_workforce_pool_credentials(
            workforce_pool_user_project=self.WORKFORCE_POOL_USER_PROJECT
        )

        assert credentials.info == {
            "type": "external_account",
            "audience": self.WORKFORCE_AUDIENCE,
            "subject_token_type": self.WORKFORCE_SUBJECT_TOKEN_TYPE,
            "token_url": self.TOKEN_URL,
            "credential_source": self.CREDENTIAL_SOURCE.copy(),
            "workforce_pool_user_project": self.WORKFORCE_POOL_USER_PROJECT,
        }

    def test_info_with_full_options(self):
        credentials = self.make_credentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            quota_project_id=self.QUOTA_PROJECT_ID,
            token_info_url=self.TOKEN_INFO_URL,
            service_account_impersonation_url=self.SERVICE_ACCOUNT_IMPERSONATION_URL,
            service_account_impersonation_options={"token_lifetime_seconds": 2800},
        )

        assert credentials.info == {
            "type": "external_account",
            "audience": self.AUDIENCE,
            "subject_token_type": self.SUBJECT_TOKEN_TYPE,
            "token_url": self.TOKEN_URL,
            "token_info_url": self.TOKEN_INFO_URL,
            "service_account_impersonation_url": self.SERVICE_ACCOUNT_IMPERSONATION_URL,
            "service_account_impersonation": {"token_lifetime_seconds": 2800},
            "credential_source": self.CREDENTIAL_SOURCE.copy(),
            "quota_project_id": self.QUOTA_PROJECT_ID,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }

    def test_service_account_email_without_impersonation(self):
        credentials = self.make_credentials()

        assert credentials.service_account_email is None

    def test_service_account_email_with_impersonation(self):
        credentials = self.make_credentials(
            service_account_impersonation_url=self.SERVICE_ACCOUNT_IMPERSONATION_URL
        )

        assert credentials.service_account_email == SERVICE_ACCOUNT_EMAIL

    @pytest.mark.parametrize("audience", TEST_NON_USER_AUDIENCES)
    def test_is_user_with_non_users(self, audience):
        credentials = CredentialsImpl(
            audience=audience,
            subject_token_type=self.SUBJECT_TOKEN_TYPE,
            token_url=self.TOKEN_URL,
            credential_source=self.CREDENTIAL_SOURCE,
        )

        assert credentials.is_user is False

    @pytest.mark.parametrize("audience", TEST_USER_AUDIENCES)
    def test_is_user_with_users(self, audience):
        credentials = CredentialsImpl(
            audience=audience,
            subject_token_type=self.SUBJECT_TOKEN_TYPE,
            token_url=self.TOKEN_URL,
            credential_source=self.CREDENTIAL_SOURCE,
        )

        assert credentials.is_user is True

    @pytest.mark.parametrize("audience", TEST_USER_AUDIENCES)
    def test_is_user_with_users_and_impersonation(self, audience):
        # Initialize the credentials with service account impersonation.
        credentials = CredentialsImpl(
            audience=audience,
            subject_token_type=self.SUBJECT_TOKEN_TYPE,
            token_url=self.TOKEN_URL,
            credential_source=self.CREDENTIAL_SOURCE,
            service_account_impersonation_url=self.SERVICE_ACCOUNT_IMPERSONATION_URL,
        )

        # Even though the audience is for a workforce pool, since service account
        # impersonation is used, the credentials will represent a service account and
        # not a user.
        assert credentials.is_user is False

    @pytest.mark.parametrize("audience", TEST_NON_USER_AUDIENCES)
    def test_is_workforce_pool_with_non_users(self, audience):
        credentials = CredentialsImpl(
            audience=audience,
            subject_token_type=self.SUBJECT_TOKEN_TYPE,
            token_url=self.TOKEN_URL,
            credential_source=self.CREDENTIAL_SOURCE,
        )

        assert credentials.is_workforce_pool is False

    @pytest.mark.parametrize("audience", TEST_USER_AUDIENCES)
    def test_is_workforce_pool_with_users(self, audience):
        credentials = CredentialsImpl(
            audience=audience,
            subject_token_type=self.SUBJECT_TOKEN_TYPE,
            token_url=self.TOKEN_URL,
            credential_source=self.CREDENTIAL_SOURCE,
        )

        assert credentials.is_workforce_pool is True

    @pytest.mark.parametrize("audience", TEST_USER_AUDIENCES)
    def test_is_workforce_pool_with_users_and_impersonation(self, audience):
        # Initialize the credentials with workforce audience and service account
        # impersonation.
        credentials = CredentialsImpl(
            audience=audience,
            subject_token_type=self.SUBJECT_TOKEN_TYPE,
            token_url=self.TOKEN_URL,
            credential_source=self.CREDENTIAL_SOURCE,
            service_account_impersonation_url=self.SERVICE_ACCOUNT_IMPERSONATION_URL,
        )

        # Even though impersonation is used, is_workforce_pool should still return True.
        assert credentials.is_workforce_pool is True

    @mock.patch("google.auth._helpers.utcnow", return_value=datetime.datetime.min)
    def test_refresh_without_client_auth_success(self, unused_utcnow):
        response = self.SUCCESS_RESPONSE.copy()
        # Test custom expiration to confirm expiry is set correctly.
        response["expires_in"] = 2800
        expected_expiry = datetime.datetime.min + datetime.timedelta(
            seconds=response["expires_in"]
        )
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        request_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "audience": self.AUDIENCE,
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "subject_token": "subject_token_0",
            "subject_token_type": self.SUBJECT_TOKEN_TYPE,
        }
        request = self.make_mock_request(status=http_client.OK, data=response)
        credentials = self.make_credentials()

        credentials.refresh(request)

        self.assert_token_request_kwargs(request.call_args[1], headers, request_data)
        assert credentials.valid
        assert credentials.expiry == expected_expiry
        assert not credentials.expired
        assert credentials.token == response["access_token"]

    @mock.patch("google.auth._helpers.utcnow", return_value=datetime.datetime.min)
    def test_refresh_workforce_without_client_auth_success(self, unused_utcnow):
        response = self.SUCCESS_RESPONSE.copy()
        # Test custom expiration to confirm expiry is set correctly.
        response["expires_in"] = 2800
        expected_expiry = datetime.datetime.min + datetime.timedelta(
            seconds=response["expires_in"]
        )
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        request_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "audience": self.WORKFORCE_AUDIENCE,
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "subject_token": "subject_token_0",
            "subject_token_type": self.WORKFORCE_SUBJECT_TOKEN_TYPE,
            "options": urllib.parse.quote(
                json.dumps({"userProject": self.WORKFORCE_POOL_USER_PROJECT})
            ),
        }
        request = self.make_mock_request(status=http_client.OK, data=response)
        credentials = self.make_workforce_pool_credentials(
            workforce_pool_user_project=self.WORKFORCE_POOL_USER_PROJECT
        )

        credentials.refresh(request)

        self.assert_token_request_kwargs(request.call_args[1], headers, request_data)
        assert credentials.valid
        assert credentials.expiry == expected_expiry
        assert not credentials.expired
        assert credentials.token == response["access_token"]

    @mock.patch("google.auth._helpers.utcnow", return_value=datetime.datetime.min)
    def test_refresh_workforce_with_client_auth_success(self, unused_utcnow):
        response = self.SUCCESS_RESPONSE.copy()
        # Test custom expiration to confirm expiry is set correctly.
        response["expires_in"] = 2800
        expected_expiry = datetime.datetime.min + datetime.timedelta(
            seconds=response["expires_in"]
        )
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic {}".format(BASIC_AUTH_ENCODING),
        }
        request_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "audience": self.WORKFORCE_AUDIENCE,
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "subject_token": "subject_token_0",
            "subject_token_type": self.WORKFORCE_SUBJECT_TOKEN_TYPE,
        }
        request = self.make_mock_request(status=http_client.OK, data=response)
        # Client Auth will have higher priority over workforce_pool_user_project.
        credentials = self.make_workforce_pool_credentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            workforce_pool_user_project=self.WORKFORCE_POOL_USER_PROJECT,
        )

        credentials.refresh(request)

        self.assert_token_request_kwargs(request.call_args[1], headers, request_data)
        assert credentials.valid
        assert credentials.expiry == expected_expiry
        assert not credentials.expired
        assert credentials.token == response["access_token"]

    @mock.patch("google.auth._helpers.utcnow", return_value=datetime.datetime.min)
    def test_refresh_workforce_with_client_auth_and_no_workforce_project_success(
        self, unused_utcnow
    ):
        response = self.SUCCESS_RESPONSE.copy()
        # Test custom expiration to confirm expiry is set correctly.
        response["expires_in"] = 2800
        expected_expiry = datetime.datetime.min + datetime.timedelta(
            seconds=response["expires_in"]
        )
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic {}".format(BASIC_AUTH_ENCODING),
        }
        request_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "audience": self.WORKFORCE_AUDIENCE,
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "subject_token": "subject_token_0",
            "subject_token_type": self.WORKFORCE_SUBJECT_TOKEN_TYPE,
        }
        request = self.make_mock_request(status=http_client.OK, data=response)
        # Client Auth will be sufficient for user project determination.
        credentials = self.make_workforce_pool_credentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            workforce_pool_user_project=None,
        )

        credentials.refresh(request)

        self.assert_token_request_kwargs(request.call_args[1], headers, request_data)
        assert credentials.valid
        assert credentials.expiry == expected_expiry
        assert not credentials.expired
        assert credentials.token == response["access_token"]

    def test_refresh_impersonation_without_client_auth_success(self):
        # Simulate service account access token expires in 2800 seconds.
        expire_time = (
            _helpers.utcnow().replace(microsecond=0) + datetime.timedelta(seconds=2800)
        ).isoformat("T") + "Z"
        expected_expiry = datetime.datetime.strptime(expire_time, "%Y-%m-%dT%H:%M:%SZ")
        # STS token exchange request/response.
        token_response = self.SUCCESS_RESPONSE.copy()
        token_headers = {"Content-Type": "application/x-www-form-urlencoded"}
        token_request_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "audience": self.AUDIENCE,
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "subject_token": "subject_token_0",
            "subject_token_type": self.SUBJECT_TOKEN_TYPE,
            "scope": "https://www.googleapis.com/auth/iam",
        }
        # Service account impersonation request/response.
        impersonation_response = {
            "accessToken": "SA_ACCESS_TOKEN",
            "expireTime": expire_time,
        }
        impersonation_headers = {
            "Content-Type": "application/json",
            "authorization": "Bearer {}".format(token_response["access_token"]),
        }
        impersonation_request_data = {
            "delegates": None,
            "scope": self.SCOPES,
            "lifetime": "3600s",
        }
        # Initialize mock request to handle token exchange and service account
        # impersonation request.
        request = self.make_mock_request(
            status=http_client.OK,
            data=token_response,
            impersonation_status=http_client.OK,
            impersonation_data=impersonation_response,
        )
        # Initialize credentials with service account impersonation.
        credentials = self.make_credentials(
            service_account_impersonation_url=self.SERVICE_ACCOUNT_IMPERSONATION_URL,
            scopes=self.SCOPES,
        )

        credentials.refresh(request)

        # Only 2 requests should be processed.
        assert len(request.call_args_list) == 2
        # Verify token exchange request parameters.
        self.assert_token_request_kwargs(
            request.call_args_list[0][1], token_headers, token_request_data
        )
        # Verify service account impersonation request parameters.
        self.assert_impersonation_request_kwargs(
            request.call_args_list[1][1],
            impersonation_headers,
            impersonation_request_data,
        )
        assert credentials.valid
        assert credentials.expiry == expected_expiry
        assert not credentials.expired
        assert credentials.token == impersonation_response["accessToken"]

    def test_refresh_workforce_impersonation_without_client_auth_success(self):
        # Simulate service account access token expires in 2800 seconds.
        expire_time = (
            _helpers.utcnow().replace(microsecond=0) + datetime.timedelta(seconds=2800)
        ).isoformat("T") + "Z"
        expected_expiry = datetime.datetime.strptime(expire_time, "%Y-%m-%dT%H:%M:%SZ")
        # STS token exchange request/response.
        token_response = self.SUCCESS_RESPONSE.copy()
        token_headers = {"Content-Type": "application/x-www-form-urlencoded"}
        token_request_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "audience": self.WORKFORCE_AUDIENCE,
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "subject_token": "subject_token_0",
            "subject_token_type": self.WORKFORCE_SUBJECT_TOKEN_TYPE,
            "scope": "https://www.googleapis.com/auth/iam",
            "options": urllib.parse.quote(
                json.dumps({"userProject": self.WORKFORCE_POOL_USER_PROJECT})
            ),
        }
        # Service account impersonation request/response.
        impersonation_response = {
            "accessToken": "SA_ACCESS_TOKEN",
            "expireTime": expire_time,
        }
        impersonation_headers = {
            "Content-Type": "application/json",
            "authorization": "Bearer {}".format(token_response["access_token"]),
        }
        impersonation_request_data = {
            "delegates": None,
            "scope": self.SCOPES,
            "lifetime": "3600s",
        }
        # Initialize mock request to handle token exchange and service account
        # impersonation request.
        request = self.make_mock_request(
            status=http_client.OK,
            data=token_response,
            impersonation_status=http_client.OK,
            impersonation_data=impersonation_response,
        )
        # Initialize credentials with service account impersonation.
        credentials = self.make_workforce_pool_credentials(
            service_account_impersonation_url=self.SERVICE_ACCOUNT_IMPERSONATION_URL,
            scopes=self.SCOPES,
            workforce_pool_user_project=self.WORKFORCE_POOL_USER_PROJECT,
        )

        credentials.refresh(request)

        # Only 2 requests should be processed.
        assert len(request.call_args_list) == 2
        # Verify token exchange request parameters.
        self.assert_token_request_kwargs(
            request.call_args_list[0][1], token_headers, token_request_data
        )
        # Verify service account impersonation request parameters.
        self.assert_impersonation_request_kwargs(
            request.call_args_list[1][1],
            impersonation_headers,
            impersonation_request_data,
        )
        assert credentials.valid
        assert credentials.expiry == expected_expiry
        assert not credentials.expired
        assert credentials.token == impersonation_response["accessToken"]

    def test_refresh_without_client_auth_success_explicit_user_scopes_ignore_default_scopes(
        self,
    ):
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        request_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "audience": self.AUDIENCE,
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "scope": "scope1 scope2",
            "subject_token": "subject_token_0",
            "subject_token_type": self.SUBJECT_TOKEN_TYPE,
        }
        request = self.make_mock_request(
            status=http_client.OK, data=self.SUCCESS_RESPONSE
        )
        credentials = self.make_credentials(
            scopes=["scope1", "scope2"],
            # Default scopes will be ignored in favor of user scopes.
            default_scopes=["ignored"],
        )

        credentials.refresh(request)

        self.assert_token_request_kwargs(request.call_args[1], headers, request_data)
        assert credentials.valid
        assert not credentials.expired
        assert credentials.token == self.SUCCESS_RESPONSE["access_token"]
        assert credentials.has_scopes(["scope1", "scope2"])
        assert not credentials.has_scopes(["ignored"])

    def test_refresh_without_client_auth_success_explicit_default_scopes_only(self):
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        request_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "audience": self.AUDIENCE,
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "scope": "scope1 scope2",
            "subject_token": "subject_token_0",
            "subject_token_type": self.SUBJECT_TOKEN_TYPE,
        }
        request = self.make_mock_request(
            status=http_client.OK, data=self.SUCCESS_RESPONSE
        )
        credentials = self.make_credentials(
            scopes=None,
            # Default scopes will be used since user scopes are none.
            default_scopes=["scope1", "scope2"],
        )

        credentials.refresh(request)

        self.assert_token_request_kwargs(request.call_args[1], headers, request_data)
        assert credentials.valid
        assert not credentials.expired
        assert credentials.token == self.SUCCESS_RESPONSE["access_token"]
        assert credentials.has_scopes(["scope1", "scope2"])

    def test_refresh_without_client_auth_error(self):
        request = self.make_mock_request(
            status=http_client.BAD_REQUEST, data=self.ERROR_RESPONSE
        )
        credentials = self.make_credentials()

        with pytest.raises(exceptions.OAuthError) as excinfo:
            credentials.refresh(request)

        assert excinfo.match(
            r"Error code invalid_request: Invalid subject token - https://tools.ietf.org/html/rfc6749"
        )
        assert not credentials.expired
        assert credentials.token is None

    def test_refresh_impersonation_without_client_auth_error(self):
        request = self.make_mock_request(
            status=http_client.OK,
            data=self.SUCCESS_RESPONSE,
            impersonation_status=http_client.BAD_REQUEST,
            impersonation_data=self.IMPERSONATION_ERROR_RESPONSE,
        )
        credentials = self.make_credentials(
            service_account_impersonation_url=self.SERVICE_ACCOUNT_IMPERSONATION_URL,
            scopes=self.SCOPES,
        )

        with pytest.raises(exceptions.RefreshError) as excinfo:
            credentials.refresh(request)

        assert excinfo.match(r"Unable to acquire impersonated credentials")
        assert not credentials.expired
        assert credentials.token is None

    def test_refresh_with_client_auth_success(self):
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic {}".format(BASIC_AUTH_ENCODING),
        }
        request_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "audience": self.AUDIENCE,
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "subject_token": "subject_token_0",
            "subject_token_type": self.SUBJECT_TOKEN_TYPE,
        }
        request = self.make_mock_request(
            status=http_client.OK, data=self.SUCCESS_RESPONSE
        )
        credentials = self.make_credentials(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET
        )

        credentials.refresh(request)

        self.assert_token_request_kwargs(request.call_args[1], headers, request_data)
        assert credentials.valid
        assert not credentials.expired
        assert credentials.token == self.SUCCESS_RESPONSE["access_token"]

    def test_refresh_impersonation_with_client_auth_success_ignore_default_scopes(self):
        # Simulate service account access token expires in 2800 seconds.
        expire_time = (
            _helpers.utcnow().replace(microsecond=0) + datetime.timedelta(seconds=2800)
        ).isoformat("T") + "Z"
        expected_expiry = datetime.datetime.strptime(expire_time, "%Y-%m-%dT%H:%M:%SZ")
        # STS token exchange request/response.
        token_response = self.SUCCESS_RESPONSE.copy()
        token_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic {}".format(BASIC_AUTH_ENCODING),
        }
        token_request_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "audience": self.AUDIENCE,
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "subject_token": "subject_token_0",
            "subject_token_type": self.SUBJECT_TOKEN_TYPE,
            "scope": "https://www.googleapis.com/auth/iam",
        }
        # Service account impersonation request/response.
        impersonation_response = {
            "accessToken": "SA_ACCESS_TOKEN",
            "expireTime": expire_time,
        }
        impersonation_headers = {
            "Content-Type": "application/json",
            "authorization": "Bearer {}".format(token_response["access_token"]),
        }
        impersonation_request_data = {
            "delegates": None,
            "scope": self.SCOPES,
            "lifetime": "3600s",
        }
        # Initialize mock request to handle token exchange and service account
        # impersonation request.
        request = self.make_mock_request(
            status=http_client.OK,
            data=token_response,
            impersonation_status=http_client.OK,
            impersonation_data=impersonation_response,
        )
        # Initialize credentials with service account impersonation and basic auth.
        credentials = self.make_credentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            service_account_impersonation_url=self.SERVICE_ACCOUNT_IMPERSONATION_URL,
            scopes=self.SCOPES,
            # Default scopes will be ignored since user scopes are specified.
            default_scopes=["ignored"],
        )

        credentials.refresh(request)

        # Only 2 requests should be processed.
        assert len(request.call_args_list) == 2
        # Verify token exchange request parameters.
        self.assert_token_request_kwargs(
            request.call_args_list[0][1], token_headers, token_request_data
        )
        # Verify service account impersonation request parameters.
        self.assert_impersonation_request_kwargs(
            request.call_args_list[1][1],
            impersonation_headers,
            impersonation_request_data,
        )
        assert credentials.valid
        assert credentials.expiry == expected_expiry
        assert not credentials.expired
        assert credentials.token == impersonation_response["accessToken"]

    def test_refresh_impersonation_with_client_auth_success_use_default_scopes(self):
        # Simulate service account access token expires in 2800 seconds.
        expire_time = (
            _helpers.utcnow().replace(microsecond=0) + datetime.timedelta(seconds=2800)
        ).isoformat("T") + "Z"
        expected_expiry = datetime.datetime.strptime(expire_time, "%Y-%m-%dT%H:%M:%SZ")
        # STS token exchange request/response.
        token_response = self.SUCCESS_RESPONSE.copy()
        token_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic {}".format(BASIC_AUTH_ENCODING),
        }
        token_request_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "audience": self.AUDIENCE,
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "subject_token": "subject_token_0",
            "subject_token_type": self.SUBJECT_TOKEN_TYPE,
            "scope": "https://www.googleapis.com/auth/iam",
        }
        # Service account impersonation request/response.
        impersonation_response = {
            "accessToken": "SA_ACCESS_TOKEN",
            "expireTime": expire_time,
        }
        impersonation_headers = {
            "Content-Type": "application/json",
            "authorization": "Bearer {}".format(token_response["access_token"]),
        }
        impersonation_request_data = {
            "delegates": None,
            "scope": self.SCOPES,
            "lifetime": "3600s",
        }
        # Initialize mock request to handle token exchange and service account
        # impersonation request.
        request = self.make_mock_request(
            status=http_client.OK,
            data=token_response,
            impersonation_status=http_client.OK,
            impersonation_data=impersonation_response,
        )
        # Initialize credentials with service account impersonation and basic auth.
        credentials = self.make_credentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            service_account_impersonation_url=self.SERVICE_ACCOUNT_IMPERSONATION_URL,
            scopes=None,
            # Default scopes will be used since user specified scopes are none.
            default_scopes=self.SCOPES,
        )

        credentials.refresh(request)

        # Only 2 requests should be processed.
        assert len(request.call_args_list) == 2
        # Verify token exchange request parameters.
        self.assert_token_request_kwargs(
            request.call_args_list[0][1], token_headers, token_request_data
        )
        # Verify service account impersonation request parameters.
        self.assert_impersonation_request_kwargs(
            request.call_args_list[1][1],
            impersonation_headers,
            impersonation_request_data,
        )
        assert credentials.valid
        assert credentials.expiry == expected_expiry
        assert not credentials.expired
        assert credentials.token == impersonation_response["accessToken"]

    def test_apply_without_quota_project_id(self):
        headers = {}
        request = self.make_mock_request(
            status=http_client.OK, data=self.SUCCESS_RESPONSE
        )
        credentials = self.make_credentials()

        credentials.refresh(request)
        credentials.apply(headers)

        assert headers == {
            "authorization": "Bearer {}".format(self.SUCCESS_RESPONSE["access_token"])
        }

    def test_apply_workforce_without_quota_project_id(self):
        headers = {}
        request = self.make_mock_request(
            status=http_client.OK, data=self.SUCCESS_RESPONSE
        )
        credentials = self.make_workforce_pool_credentials(
            workforce_pool_user_project=self.WORKFORCE_POOL_USER_PROJECT
        )

        credentials.refresh(request)
        credentials.apply(headers)

        assert headers == {
            "authorization": "Bearer {}".format(self.SUCCESS_RESPONSE["access_token"])
        }

    def test_apply_impersonation_without_quota_project_id(self):
        expire_time = (
            _helpers.utcnow().replace(microsecond=0) + datetime.timedelta(seconds=3600)
        ).isoformat("T") + "Z"
        # Service account impersonation response.
        impersonation_response = {
            "accessToken": "SA_ACCESS_TOKEN",
            "expireTime": expire_time,
        }
        # Initialize mock request to handle token exchange and service account
        # impersonation request.
        request = self.make_mock_request(
            status=http_client.OK,
            data=self.SUCCESS_RESPONSE.copy(),
            impersonation_status=http_client.OK,
            impersonation_data=impersonation_response,
        )
        # Initialize credentials with service account impersonation.
        credentials = self.make_credentials(
            service_account_impersonation_url=self.SERVICE_ACCOUNT_IMPERSONATION_URL,
            scopes=self.SCOPES,
        )
        headers = {}

        credentials.refresh(request)
        credentials.apply(headers)

        assert headers == {
            "authorization": "Bearer {}".format(impersonation_response["accessToken"])
        }

    def test_apply_with_quota_project_id(self):
        headers = {"other": "header-value"}
        request = self.make_mock_request(
            status=http_client.OK, data=self.SUCCESS_RESPONSE
        )
        credentials = self.make_credentials(quota_project_id=self.QUOTA_PROJECT_ID)

        credentials.refresh(request)
        credentials.apply(headers)

        assert headers == {
            "other": "header-value",
            "authorization": "Bearer {}".format(self.SUCCESS_RESPONSE["access_token"]),
            "x-goog-user-project": self.QUOTA_PROJECT_ID,
        }

    def test_apply_impersonation_with_quota_project_id(self):
        expire_time = (
            _helpers.utcnow().replace(microsecond=0) + datetime.timedelta(seconds=3600)
        ).isoformat("T") + "Z"
        # Service account impersonation response.
        impersonation_response = {
            "accessToken": "SA_ACCESS_TOKEN",
            "expireTime": expire_time,
        }
        # Initialize mock request to handle token exchange and service account
        # impersonation request.
        request = self.make_mock_request(
            status=http_client.OK,
            data=self.SUCCESS_RESPONSE.copy(),
            impersonation_status=http_client.OK,
            impersonation_data=impersonation_response,
        )
        # Initialize credentials with service account impersonation.
        credentials = self.make_credentials(
            service_account_impersonation_url=self.SERVICE_ACCOUNT_IMPERSONATION_URL,
            scopes=self.SCOPES,
            quota_project_id=self.QUOTA_PROJECT_ID,
        )
        headers = {"other": "header-value"}

        credentials.refresh(request)
        credentials.apply(headers)

        assert headers == {
            "other": "header-value",
            "authorization": "Bearer {}".format(impersonation_response["accessToken"]),
            "x-goog-user-project": self.QUOTA_PROJECT_ID,
        }

    def test_before_request(self):
        headers = {"other": "header-value"}
        request = self.make_mock_request(
            status=http_client.OK, data=self.SUCCESS_RESPONSE
        )
        credentials = self.make_credentials()

        # First call should call refresh, setting the token.
        credentials.before_request(request, "POST", "https://example.com/api", headers)

        assert headers == {
            "other": "header-value",
            "authorization": "Bearer {}".format(self.SUCCESS_RESPONSE["access_token"]),
        }

        # Second call shouldn't call refresh.
        credentials.before_request(request, "POST", "https://example.com/api", headers)

        assert headers == {
            "other": "header-value",
            "authorization": "Bearer {}".format(self.SUCCESS_RESPONSE["access_token"]),
        }

    def test_before_request_workforce(self):
        headers = {"other": "header-value"}
        request = self.make_mock_request(
            status=http_client.OK, data=self.SUCCESS_RESPONSE
        )
        credentials = self.make_workforce_pool_credentials(
            workforce_pool_user_project=self.WORKFORCE_POOL_USER_PROJECT
        )

        # First call should call refresh, setting the token.
        credentials.before_request(request, "POST", "https://example.com/api", headers)

        assert headers == {
            "other": "header-value",
            "authorization": "Bearer {}".format(self.SUCCESS_RESPONSE["access_token"]),
        }

        # Second call shouldn't call refresh.
        credentials.before_request(request, "POST", "https://example.com/api", headers)

        assert headers == {
            "other": "header-value",
            "authorization": "Bearer {}".format(self.SUCCESS_RESPONSE["access_token"]),
        }

    def test_before_request_impersonation(self):
        expire_time = (
            _helpers.utcnow().replace(microsecond=0) + datetime.timedelta(seconds=3600)
        ).isoformat("T") + "Z"
        # Service account impersonation response.
        impersonation_response = {
            "accessToken": "SA_ACCESS_TOKEN",
            "expireTime": expire_time,
        }
        # Initialize mock request to handle token exchange and service account
        # impersonation request.
        request = self.make_mock_request(
            status=http_client.OK,
            data=self.SUCCESS_RESPONSE.copy(),
            impersonation_status=http_client.OK,
            impersonation_data=impersonation_response,
        )
        headers = {"other": "header-value"}
        credentials = self.make_credentials(
            service_account_impersonation_url=self.SERVICE_ACCOUNT_IMPERSONATION_URL
        )

        # First call should call refresh, setting the token.
        credentials.before_request(request, "POST", "https://example.com/api", headers)

        assert headers == {
            "other": "header-value",
            "authorization": "Bearer {}".format(impersonation_response["accessToken"]),
        }

        # Second call shouldn't call refresh.
        credentials.before_request(request, "POST", "https://example.com/api", headers)

        assert headers == {
            "other": "header-value",
            "authorization": "Bearer {}".format(impersonation_response["accessToken"]),
        }

    @mock.patch("google.auth._helpers.utcnow")
    def test_before_request_expired(self, utcnow):
        headers = {}
        request = self.make_mock_request(
            status=http_client.OK, data=self.SUCCESS_RESPONSE
        )
        credentials = self.make_credentials()
        credentials.token = "token"
        utcnow.return_value = datetime.datetime.min
        # Set the expiration to one second more than now plus the clock skew
        # accomodation. These credentials should be valid.
        credentials.expiry = (
            datetime.datetime.min
            + _helpers.REFRESH_THRESHOLD
            + datetime.timedelta(seconds=1)
        )

        assert credentials.valid
        assert not credentials.expired

        credentials.before_request(request, "POST", "https://example.com/api", headers)

        # Cached token should be used.
        assert headers == {"authorization": "Bearer token"}

        # Next call should simulate 1 second passed.
        utcnow.return_value = datetime.datetime.min + datetime.timedelta(seconds=1)

        assert not credentials.valid
        assert credentials.expired

        credentials.before_request(request, "POST", "https://example.com/api", headers)

        # New token should be retrieved.
        assert headers == {
            "authorization": "Bearer {}".format(self.SUCCESS_RESPONSE["access_token"])
        }

    @mock.patch("google.auth._helpers.utcnow")
    def test_before_request_impersonation_expired(self, utcnow):
        headers = {}
        expire_time = (
            datetime.datetime.min + datetime.timedelta(seconds=3601)
        ).isoformat("T") + "Z"
        # Service account impersonation response.
        impersonation_response = {
            "accessToken": "SA_ACCESS_TOKEN",
            "expireTime": expire_time,
        }
        # Initialize mock request to handle token exchange and service account
        # impersonation request.
        request = self.make_mock_request(
            status=http_client.OK,
            data=self.SUCCESS_RESPONSE.copy(),
            impersonation_status=http_client.OK,
            impersonation_data=impersonation_response,
        )
        credentials = self.make_credentials(
            service_account_impersonation_url=self.SERVICE_ACCOUNT_IMPERSONATION_URL
        )
        credentials.token = "token"
        utcnow.return_value = datetime.datetime.min
        # Set the expiration to one second more than now plus the clock skew
        # accomodation. These credentials should be valid.
        credentials.expiry = (
            datetime.datetime.min
            + _helpers.REFRESH_THRESHOLD
            + datetime.timedelta(seconds=1)
        )

        assert credentials.valid
        assert not credentials.expired

        credentials.before_request(request, "POST", "https://example.com/api", headers)

        # Cached token should be used.
        assert headers == {"authorization": "Bearer token"}

        # Next call should simulate 1 second passed. This will trigger the expiration
        # threshold.
        utcnow.return_value = datetime.datetime.min + datetime.timedelta(seconds=1)

        assert not credentials.valid
        assert credentials.expired

        credentials.before_request(request, "POST", "https://example.com/api", headers)

        # New token should be retrieved.
        assert headers == {
            "authorization": "Bearer {}".format(impersonation_response["accessToken"])
        }

    @pytest.mark.parametrize(
        "audience",
        [
            # Legacy K8s audience format.
            "identitynamespace:1f12345:my_provider",
            # Unrealistic audiences.
            "//iam.googleapis.com/projects",
            "//iam.googleapis.com/projects/",
            "//iam.googleapis.com/project/123456",
            "//iam.googleapis.com/projects//123456",
            "//iam.googleapis.com/prefix_projects/123456",
            "//iam.googleapis.com/projects_suffix/123456",
        ],
    )
    def test_project_number_indeterminable(self, audience):
        credentials = CredentialsImpl(
            audience=audience,
            subject_token_type=self.SUBJECT_TOKEN_TYPE,
            token_url=self.TOKEN_URL,
            credential_source=self.CREDENTIAL_SOURCE,
        )

        assert credentials.project_number is None
        assert credentials.get_project_id(None) is None

    def test_project_number_determinable(self):
        credentials = CredentialsImpl(
            audience=self.AUDIENCE,
            subject_token_type=self.SUBJECT_TOKEN_TYPE,
            token_url=self.TOKEN_URL,
            credential_source=self.CREDENTIAL_SOURCE,
        )

        assert credentials.project_number == self.PROJECT_NUMBER

    def test_project_number_workforce(self):
        credentials = CredentialsImpl(
            audience=self.WORKFORCE_AUDIENCE,
            subject_token_type=self.WORKFORCE_SUBJECT_TOKEN_TYPE,
            token_url=self.TOKEN_URL,
            credential_source=self.CREDENTIAL_SOURCE,
            workforce_pool_user_project=self.WORKFORCE_POOL_USER_PROJECT,
        )

        assert credentials.project_number is None

    def test_project_id_without_scopes(self):
        # Initialize credentials with no scopes.
        credentials = CredentialsImpl(
            audience=self.AUDIENCE,
            subject_token_type=self.SUBJECT_TOKEN_TYPE,
            token_url=self.TOKEN_URL,
            credential_source=self.CREDENTIAL_SOURCE,
        )

        assert credentials.get_project_id(None) is None

    def test_get_project_id_cloud_resource_manager_success(self):
        # STS token exchange request/response.
        token_response = self.SUCCESS_RESPONSE.copy()
        token_headers = {"Content-Type": "application/x-www-form-urlencoded"}
        token_request_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "audience": self.AUDIENCE,
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "subject_token": "subject_token_0",
            "subject_token_type": self.SUBJECT_TOKEN_TYPE,
            "scope": "https://www.googleapis.com/auth/iam",
        }
        # Service account impersonation request/response.
        expire_time = (
            _helpers.utcnow().replace(microsecond=0) + datetime.timedelta(seconds=3600)
        ).isoformat("T") + "Z"
        expected_expiry = datetime.datetime.strptime(expire_time, "%Y-%m-%dT%H:%M:%SZ")
        impersonation_response = {
            "accessToken": "SA_ACCESS_TOKEN",
            "expireTime": expire_time,
        }
        impersonation_headers = {
            "Content-Type": "application/json",
            "x-goog-user-project": self.QUOTA_PROJECT_ID,
            "authorization": "Bearer {}".format(token_response["access_token"]),
        }
        impersonation_request_data = {
            "delegates": None,
            "scope": self.SCOPES,
            "lifetime": "3600s",
        }
        # Initialize mock request to handle token exchange, service account
        # impersonation and cloud resource manager request.
        request = self.make_mock_request(
            status=http_client.OK,
            data=self.SUCCESS_RESPONSE.copy(),
            impersonation_status=http_client.OK,
            impersonation_data=impersonation_response,
            cloud_resource_manager_status=http_client.OK,
            cloud_resource_manager_data=self.CLOUD_RESOURCE_MANAGER_SUCCESS_RESPONSE,
        )
        credentials = self.make_credentials(
            service_account_impersonation_url=self.SERVICE_ACCOUNT_IMPERSONATION_URL,
            scopes=self.SCOPES,
            quota_project_id=self.QUOTA_PROJECT_ID,
        )

        # Expected project ID from cloud resource manager response should be returned.
        project_id = credentials.get_project_id(request)

        assert project_id == self.PROJECT_ID
        # 3 requests should be processed.
        assert len(request.call_args_list) == 3
        # Verify token exchange request parameters.
        self.assert_token_request_kwargs(
            request.call_args_list[0][1], token_headers, token_request_data
        )
        # Verify service account impersonation request parameters.
        self.assert_impersonation_request_kwargs(
            request.call_args_list[1][1],
            impersonation_headers,
            impersonation_request_data,
        )
        # In the process of getting project ID, an access token should be
        # retrieved.
        assert credentials.valid
        assert credentials.expiry == expected_expiry
        assert not credentials.expired
        assert credentials.token == impersonation_response["accessToken"]
        # Verify cloud resource manager request parameters.
        self.assert_resource_manager_request_kwargs(
            request.call_args_list[2][1],
            self.PROJECT_NUMBER,
            {
                "x-goog-user-project": self.QUOTA_PROJECT_ID,
                "authorization": "Bearer {}".format(
                    impersonation_response["accessToken"]
                ),
            },
        )

        # Calling get_project_id again should return the cached project_id.
        project_id = credentials.get_project_id(request)

        assert project_id == self.PROJECT_ID
        # No additional requests.
        assert len(request.call_args_list) == 3

    def test_workforce_pool_get_project_id_cloud_resource_manager_success(self):
        # STS token exchange request/response.
        token_headers = {"Content-Type": "application/x-www-form-urlencoded"}
        token_request_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "audience": self.WORKFORCE_AUDIENCE,
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "subject_token": "subject_token_0",
            "subject_token_type": self.WORKFORCE_SUBJECT_TOKEN_TYPE,
            "scope": "scope1 scope2",
            "options": urllib.parse.quote(
                json.dumps({"userProject": self.WORKFORCE_POOL_USER_PROJECT})
            ),
        }
        # Initialize mock request to handle token exchange and cloud resource
        # manager request.
        request = self.make_mock_request(
            status=http_client.OK,
            data=self.SUCCESS_RESPONSE.copy(),
            cloud_resource_manager_status=http_client.OK,
            cloud_resource_manager_data=self.CLOUD_RESOURCE_MANAGER_SUCCESS_RESPONSE,
        )
        credentials = self.make_workforce_pool_credentials(
            scopes=self.SCOPES,
            quota_project_id=self.QUOTA_PROJECT_ID,
            workforce_pool_user_project=self.WORKFORCE_POOL_USER_PROJECT,
        )

        # Expected project ID from cloud resource manager response should be returned.
        project_id = credentials.get_project_id(request)

        assert project_id == self.PROJECT_ID
        # 2 requests should be processed.
        assert len(request.call_args_list) == 2
        # Verify token exchange request parameters.
        self.assert_token_request_kwargs(
            request.call_args_list[0][1], token_headers, token_request_data
        )
        # In the process of getting project ID, an access token should be
        # retrieved.
        assert credentials.valid
        assert not credentials.expired
        assert credentials.token == self.SUCCESS_RESPONSE["access_token"]
        # Verify cloud resource manager request parameters.
        self.assert_resource_manager_request_kwargs(
            request.call_args_list[1][1],
            self.WORKFORCE_POOL_USER_PROJECT,
            {
                "x-goog-user-project": self.QUOTA_PROJECT_ID,
                "authorization": "Bearer {}".format(
                    self.SUCCESS_RESPONSE["access_token"]
                ),
            },
        )

        # Calling get_project_id again should return the cached project_id.
        project_id = credentials.get_project_id(request)

        assert project_id == self.PROJECT_ID
        # No additional requests.
        assert len(request.call_args_list) == 2

    def test_refresh_impersonation_with_lifetime(self):
        # Simulate service account access token expires in 2800 seconds.
        expire_time = (
            _helpers.utcnow().replace(microsecond=0) + datetime.timedelta(seconds=2800)
        ).isoformat("T") + "Z"
        expected_expiry = datetime.datetime.strptime(expire_time, "%Y-%m-%dT%H:%M:%SZ")
        # STS token exchange request/response.
        token_response = self.SUCCESS_RESPONSE.copy()
        token_headers = {"Content-Type": "application/x-www-form-urlencoded"}
        token_request_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "audience": self.AUDIENCE,
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "subject_token": "subject_token_0",
            "subject_token_type": self.SUBJECT_TOKEN_TYPE,
            "scope": "https://www.googleapis.com/auth/iam",
        }
        # Service account impersonation request/response.
        impersonation_response = {
            "accessToken": "SA_ACCESS_TOKEN",
            "expireTime": expire_time,
        }
        impersonation_headers = {
            "Content-Type": "application/json",
            "authorization": "Bearer {}".format(token_response["access_token"]),
        }
        impersonation_request_data = {
            "delegates": None,
            "scope": self.SCOPES,
            "lifetime": "2800s",
        }
        # Initialize mock request to handle token exchange and service account
        # impersonation request.
        request = self.make_mock_request(
            status=http_client.OK,
            data=token_response,
            impersonation_status=http_client.OK,
            impersonation_data=impersonation_response,
        )
        # Initialize credentials with service account impersonation.
        credentials = self.make_credentials(
            service_account_impersonation_url=self.SERVICE_ACCOUNT_IMPERSONATION_URL,
            service_account_impersonation_options={"token_lifetime_seconds": 2800},
            scopes=self.SCOPES,
        )

        credentials.refresh(request)

        # Only 2 requests should be processed.
        assert len(request.call_args_list) == 2
        # Verify token exchange request parameters.
        self.assert_token_request_kwargs(
            request.call_args_list[0][1], token_headers, token_request_data
        )
        # Verify service account impersonation request parameters.
        self.assert_impersonation_request_kwargs(
            request.call_args_list[1][1],
            impersonation_headers,
            impersonation_request_data,
        )
        assert credentials.valid
        assert credentials.expiry == expected_expiry
        assert not credentials.expired
        assert credentials.token == impersonation_response["accessToken"]

    def test_get_project_id_cloud_resource_manager_error(self):
        # Simulate resource doesn't have sufficient permissions to access
        # cloud resource manager.
        request = self.make_mock_request(
            status=http_client.OK,
            data=self.SUCCESS_RESPONSE.copy(),
            cloud_resource_manager_status=http_client.UNAUTHORIZED,
        )
        credentials = self.make_credentials(scopes=self.SCOPES)

        project_id = credentials.get_project_id(request)

        assert project_id is None
        # Only 2 requests to STS and cloud resource manager should be sent.
        assert len(request.call_args_list) == 2
