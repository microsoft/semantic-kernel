# Copyright 2021 Google LLC
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
from google.auth import credentials
from google.auth import downscoped
from google.auth import exceptions
from google.auth import transport


EXPRESSION = (
    "resource.name.startsWith('projects/_/buckets/example-bucket/objects/customer-a')"
)
TITLE = "customer-a-objects"
DESCRIPTION = (
    "Condition to make permissions available for objects starting with customer-a"
)
AVAILABLE_RESOURCE = "//storage.googleapis.com/projects/_/buckets/example-bucket"
AVAILABLE_PERMISSIONS = ["inRole:roles/storage.objectViewer"]

OTHER_EXPRESSION = (
    "resource.name.startsWith('projects/_/buckets/example-bucket/objects/customer-b')"
)
OTHER_TITLE = "customer-b-objects"
OTHER_DESCRIPTION = (
    "Condition to make permissions available for objects starting with customer-b"
)
OTHER_AVAILABLE_RESOURCE = "//storage.googleapis.com/projects/_/buckets/other-bucket"
OTHER_AVAILABLE_PERMISSIONS = ["inRole:roles/storage.objectCreator"]
QUOTA_PROJECT_ID = "QUOTA_PROJECT_ID"
GRANT_TYPE = "urn:ietf:params:oauth:grant-type:token-exchange"
REQUESTED_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:access_token"
TOKEN_EXCHANGE_ENDPOINT = "https://sts.googleapis.com/v1/token"
SUBJECT_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:access_token"
SUCCESS_RESPONSE = {
    "access_token": "ACCESS_TOKEN",
    "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
    "token_type": "Bearer",
    "expires_in": 3600,
}
ERROR_RESPONSE = {
    "error": "invalid_grant",
    "error_description": "Subject token is invalid.",
    "error_uri": "https://tools.ietf.org/html/rfc6749",
}
CREDENTIAL_ACCESS_BOUNDARY_JSON = {
    "accessBoundary": {
        "accessBoundaryRules": [
            {
                "availablePermissions": AVAILABLE_PERMISSIONS,
                "availableResource": AVAILABLE_RESOURCE,
                "availabilityCondition": {
                    "expression": EXPRESSION,
                    "title": TITLE,
                    "description": DESCRIPTION,
                },
            }
        ]
    }
}


class SourceCredentials(credentials.Credentials):
    def __init__(self, raise_error=False, expires_in=3600):
        super(SourceCredentials, self).__init__()
        self._counter = 0
        self._raise_error = raise_error
        self._expires_in = expires_in

    def refresh(self, request):
        if self._raise_error:
            raise exceptions.RefreshError(
                "Failed to refresh access token in source credentials."
            )
        now = _helpers.utcnow()
        self._counter += 1
        self.token = "ACCESS_TOKEN_{}".format(self._counter)
        self.expiry = now + datetime.timedelta(seconds=self._expires_in)


def make_availability_condition(expression, title=None, description=None):
    return downscoped.AvailabilityCondition(expression, title, description)


def make_access_boundary_rule(
    available_resource, available_permissions, availability_condition=None
):
    return downscoped.AccessBoundaryRule(
        available_resource, available_permissions, availability_condition
    )


def make_credential_access_boundary(rules):
    return downscoped.CredentialAccessBoundary(rules)


class TestAvailabilityCondition(object):
    def test_constructor(self):
        availability_condition = make_availability_condition(
            EXPRESSION, TITLE, DESCRIPTION
        )

        assert availability_condition.expression == EXPRESSION
        assert availability_condition.title == TITLE
        assert availability_condition.description == DESCRIPTION

    def test_constructor_required_params_only(self):
        availability_condition = make_availability_condition(EXPRESSION)

        assert availability_condition.expression == EXPRESSION
        assert availability_condition.title is None
        assert availability_condition.description is None

    def test_setters(self):
        availability_condition = make_availability_condition(
            EXPRESSION, TITLE, DESCRIPTION
        )
        availability_condition.expression = OTHER_EXPRESSION
        availability_condition.title = OTHER_TITLE
        availability_condition.description = OTHER_DESCRIPTION

        assert availability_condition.expression == OTHER_EXPRESSION
        assert availability_condition.title == OTHER_TITLE
        assert availability_condition.description == OTHER_DESCRIPTION

    def test_invalid_expression_type(self):
        with pytest.raises(TypeError) as excinfo:
            make_availability_condition([EXPRESSION], TITLE, DESCRIPTION)

        assert excinfo.match("The provided expression is not a string.")

    def test_invalid_title_type(self):
        with pytest.raises(TypeError) as excinfo:
            make_availability_condition(EXPRESSION, False, DESCRIPTION)

        assert excinfo.match("The provided title is not a string or None.")

    def test_invalid_description_type(self):
        with pytest.raises(TypeError) as excinfo:
            make_availability_condition(EXPRESSION, TITLE, False)

        assert excinfo.match("The provided description is not a string or None.")

    def test_to_json_required_params_only(self):
        availability_condition = make_availability_condition(EXPRESSION)

        assert availability_condition.to_json() == {"expression": EXPRESSION}

    def test_to_json_(self):
        availability_condition = make_availability_condition(
            EXPRESSION, TITLE, DESCRIPTION
        )

        assert availability_condition.to_json() == {
            "expression": EXPRESSION,
            "title": TITLE,
            "description": DESCRIPTION,
        }


class TestAccessBoundaryRule(object):
    def test_constructor(self):
        availability_condition = make_availability_condition(
            EXPRESSION, TITLE, DESCRIPTION
        )
        access_boundary_rule = make_access_boundary_rule(
            AVAILABLE_RESOURCE, AVAILABLE_PERMISSIONS, availability_condition
        )

        assert access_boundary_rule.available_resource == AVAILABLE_RESOURCE
        assert access_boundary_rule.available_permissions == tuple(
            AVAILABLE_PERMISSIONS
        )
        assert access_boundary_rule.availability_condition == availability_condition

    def test_constructor_required_params_only(self):
        access_boundary_rule = make_access_boundary_rule(
            AVAILABLE_RESOURCE, AVAILABLE_PERMISSIONS
        )

        assert access_boundary_rule.available_resource == AVAILABLE_RESOURCE
        assert access_boundary_rule.available_permissions == tuple(
            AVAILABLE_PERMISSIONS
        )
        assert access_boundary_rule.availability_condition is None

    def test_setters(self):
        availability_condition = make_availability_condition(
            EXPRESSION, TITLE, DESCRIPTION
        )
        other_availability_condition = make_availability_condition(
            OTHER_EXPRESSION, OTHER_TITLE, OTHER_DESCRIPTION
        )
        access_boundary_rule = make_access_boundary_rule(
            AVAILABLE_RESOURCE, AVAILABLE_PERMISSIONS, availability_condition
        )
        access_boundary_rule.available_resource = OTHER_AVAILABLE_RESOURCE
        access_boundary_rule.available_permissions = OTHER_AVAILABLE_PERMISSIONS
        access_boundary_rule.availability_condition = other_availability_condition

        assert access_boundary_rule.available_resource == OTHER_AVAILABLE_RESOURCE
        assert access_boundary_rule.available_permissions == tuple(
            OTHER_AVAILABLE_PERMISSIONS
        )
        assert (
            access_boundary_rule.availability_condition == other_availability_condition
        )

    def test_invalid_available_resource_type(self):
        availability_condition = make_availability_condition(
            EXPRESSION, TITLE, DESCRIPTION
        )
        with pytest.raises(TypeError) as excinfo:
            make_access_boundary_rule(
                None, AVAILABLE_PERMISSIONS, availability_condition
            )

        assert excinfo.match("The provided available_resource is not a string.")

    def test_invalid_available_permissions_type(self):
        availability_condition = make_availability_condition(
            EXPRESSION, TITLE, DESCRIPTION
        )
        with pytest.raises(TypeError) as excinfo:
            make_access_boundary_rule(
                AVAILABLE_RESOURCE, [0, 1, 2], availability_condition
            )

        assert excinfo.match(
            "Provided available_permissions are not a list of strings."
        )

    def test_invalid_available_permissions_value(self):
        availability_condition = make_availability_condition(
            EXPRESSION, TITLE, DESCRIPTION
        )
        with pytest.raises(ValueError) as excinfo:
            make_access_boundary_rule(
                AVAILABLE_RESOURCE,
                ["roles/storage.objectViewer"],
                availability_condition,
            )

        assert excinfo.match("available_permissions must be prefixed with 'inRole:'.")

    def test_invalid_availability_condition_type(self):
        with pytest.raises(TypeError) as excinfo:
            make_access_boundary_rule(
                AVAILABLE_RESOURCE, AVAILABLE_PERMISSIONS, {"foo": "bar"}
            )

        assert excinfo.match(
            "The provided availability_condition is not a 'google.auth.downscoped.AvailabilityCondition' or None."
        )

    def test_to_json(self):
        availability_condition = make_availability_condition(
            EXPRESSION, TITLE, DESCRIPTION
        )
        access_boundary_rule = make_access_boundary_rule(
            AVAILABLE_RESOURCE, AVAILABLE_PERMISSIONS, availability_condition
        )

        assert access_boundary_rule.to_json() == {
            "availablePermissions": AVAILABLE_PERMISSIONS,
            "availableResource": AVAILABLE_RESOURCE,
            "availabilityCondition": {
                "expression": EXPRESSION,
                "title": TITLE,
                "description": DESCRIPTION,
            },
        }

    def test_to_json_required_params_only(self):
        access_boundary_rule = make_access_boundary_rule(
            AVAILABLE_RESOURCE, AVAILABLE_PERMISSIONS
        )

        assert access_boundary_rule.to_json() == {
            "availablePermissions": AVAILABLE_PERMISSIONS,
            "availableResource": AVAILABLE_RESOURCE,
        }


class TestCredentialAccessBoundary(object):
    def test_constructor(self):
        availability_condition = make_availability_condition(
            EXPRESSION, TITLE, DESCRIPTION
        )
        access_boundary_rule = make_access_boundary_rule(
            AVAILABLE_RESOURCE, AVAILABLE_PERMISSIONS, availability_condition
        )
        rules = [access_boundary_rule]
        credential_access_boundary = make_credential_access_boundary(rules)

        assert credential_access_boundary.rules == tuple(rules)

    def test_setters(self):
        availability_condition = make_availability_condition(
            EXPRESSION, TITLE, DESCRIPTION
        )
        access_boundary_rule = make_access_boundary_rule(
            AVAILABLE_RESOURCE, AVAILABLE_PERMISSIONS, availability_condition
        )
        rules = [access_boundary_rule]
        other_availability_condition = make_availability_condition(
            OTHER_EXPRESSION, OTHER_TITLE, OTHER_DESCRIPTION
        )
        other_access_boundary_rule = make_access_boundary_rule(
            OTHER_AVAILABLE_RESOURCE,
            OTHER_AVAILABLE_PERMISSIONS,
            other_availability_condition,
        )
        other_rules = [other_access_boundary_rule]
        credential_access_boundary = make_credential_access_boundary(rules)
        credential_access_boundary.rules = other_rules

        assert credential_access_boundary.rules == tuple(other_rules)

    def test_add_rule(self):
        availability_condition = make_availability_condition(
            EXPRESSION, TITLE, DESCRIPTION
        )
        access_boundary_rule = make_access_boundary_rule(
            AVAILABLE_RESOURCE, AVAILABLE_PERMISSIONS, availability_condition
        )
        rules = [access_boundary_rule] * 9
        credential_access_boundary = make_credential_access_boundary(rules)

        # Add one more rule. This should not raise an error.
        additional_access_boundary_rule = make_access_boundary_rule(
            OTHER_AVAILABLE_RESOURCE, OTHER_AVAILABLE_PERMISSIONS
        )
        credential_access_boundary.add_rule(additional_access_boundary_rule)

        assert len(credential_access_boundary.rules) == 10
        assert credential_access_boundary.rules[9] == additional_access_boundary_rule

    def test_add_rule_invalid_value(self):
        availability_condition = make_availability_condition(
            EXPRESSION, TITLE, DESCRIPTION
        )
        access_boundary_rule = make_access_boundary_rule(
            AVAILABLE_RESOURCE, AVAILABLE_PERMISSIONS, availability_condition
        )
        rules = [access_boundary_rule] * 10
        credential_access_boundary = make_credential_access_boundary(rules)

        # Add one more rule to exceed maximum allowed rules.
        with pytest.raises(ValueError) as excinfo:
            credential_access_boundary.add_rule(access_boundary_rule)

        assert excinfo.match(
            "Credential access boundary rules can have a maximum of 10 rules."
        )
        assert len(credential_access_boundary.rules) == 10

    def test_add_rule_invalid_type(self):
        availability_condition = make_availability_condition(
            EXPRESSION, TITLE, DESCRIPTION
        )
        access_boundary_rule = make_access_boundary_rule(
            AVAILABLE_RESOURCE, AVAILABLE_PERMISSIONS, availability_condition
        )
        rules = [access_boundary_rule]
        credential_access_boundary = make_credential_access_boundary(rules)

        # Add an invalid rule to exceed maximum allowed rules.
        with pytest.raises(TypeError) as excinfo:
            credential_access_boundary.add_rule("invalid")

        assert excinfo.match(
            "The provided rule does not contain a valid 'google.auth.downscoped.AccessBoundaryRule'."
        )
        assert len(credential_access_boundary.rules) == 1
        assert credential_access_boundary.rules[0] == access_boundary_rule

    def test_invalid_rules_type(self):
        with pytest.raises(TypeError) as excinfo:
            make_credential_access_boundary(["invalid"])

        assert excinfo.match(
            "List of rules provided do not contain a valid 'google.auth.downscoped.AccessBoundaryRule'."
        )

    def test_invalid_rules_value(self):
        availability_condition = make_availability_condition(
            EXPRESSION, TITLE, DESCRIPTION
        )
        access_boundary_rule = make_access_boundary_rule(
            AVAILABLE_RESOURCE, AVAILABLE_PERMISSIONS, availability_condition
        )
        too_many_rules = [access_boundary_rule] * 11
        with pytest.raises(ValueError) as excinfo:
            make_credential_access_boundary(too_many_rules)

        assert excinfo.match(
            "Credential access boundary rules can have a maximum of 10 rules."
        )

    def test_to_json(self):
        availability_condition = make_availability_condition(
            EXPRESSION, TITLE, DESCRIPTION
        )
        access_boundary_rule = make_access_boundary_rule(
            AVAILABLE_RESOURCE, AVAILABLE_PERMISSIONS, availability_condition
        )
        rules = [access_boundary_rule]
        credential_access_boundary = make_credential_access_boundary(rules)

        assert credential_access_boundary.to_json() == {
            "accessBoundary": {
                "accessBoundaryRules": [
                    {
                        "availablePermissions": AVAILABLE_PERMISSIONS,
                        "availableResource": AVAILABLE_RESOURCE,
                        "availabilityCondition": {
                            "expression": EXPRESSION,
                            "title": TITLE,
                            "description": DESCRIPTION,
                        },
                    }
                ]
            }
        }


class TestCredentials(object):
    @staticmethod
    def make_credentials(source_credentials=SourceCredentials(), quota_project_id=None):
        availability_condition = make_availability_condition(
            EXPRESSION, TITLE, DESCRIPTION
        )
        access_boundary_rule = make_access_boundary_rule(
            AVAILABLE_RESOURCE, AVAILABLE_PERMISSIONS, availability_condition
        )
        rules = [access_boundary_rule]
        credential_access_boundary = make_credential_access_boundary(rules)

        return downscoped.Credentials(
            source_credentials, credential_access_boundary, quota_project_id
        )

    @staticmethod
    def make_mock_request(data, status=http_client.OK):
        response = mock.create_autospec(transport.Response, instance=True)
        response.status = status
        response.data = json.dumps(data).encode("utf-8")

        request = mock.create_autospec(transport.Request)
        request.return_value = response

        return request

    @staticmethod
    def assert_request_kwargs(request_kwargs, headers, request_data):
        """Asserts the request was called with the expected parameters.
        """
        assert request_kwargs["url"] == TOKEN_EXCHANGE_ENDPOINT
        assert request_kwargs["method"] == "POST"
        assert request_kwargs["headers"] == headers
        assert request_kwargs["body"] is not None
        body_tuples = urllib.parse.parse_qsl(request_kwargs["body"])
        for (k, v) in body_tuples:
            assert v.decode("utf-8") == request_data[k.decode("utf-8")]
        assert len(body_tuples) == len(request_data.keys())

    def test_default_state(self):
        credentials = self.make_credentials()

        # No token acquired yet.
        assert not credentials.token
        assert not credentials.valid
        # Expiration hasn't been set yet.
        assert not credentials.expiry
        assert not credentials.expired
        # No quota project ID set.
        assert not credentials.quota_project_id

    def test_with_quota_project(self):
        credentials = self.make_credentials()

        assert not credentials.quota_project_id

        quota_project_creds = credentials.with_quota_project("project-foo")

        assert quota_project_creds.quota_project_id == "project-foo"

    @mock.patch("google.auth._helpers.utcnow", return_value=datetime.datetime.min)
    def test_refresh(self, unused_utcnow):
        response = SUCCESS_RESPONSE.copy()
        # Test custom expiration to confirm expiry is set correctly.
        response["expires_in"] = 2800
        expected_expiry = datetime.datetime.min + datetime.timedelta(
            seconds=response["expires_in"]
        )
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        request_data = {
            "grant_type": GRANT_TYPE,
            "subject_token": "ACCESS_TOKEN_1",
            "subject_token_type": SUBJECT_TOKEN_TYPE,
            "requested_token_type": REQUESTED_TOKEN_TYPE,
            "options": urllib.parse.quote(json.dumps(CREDENTIAL_ACCESS_BOUNDARY_JSON)),
        }
        request = self.make_mock_request(status=http_client.OK, data=response)
        source_credentials = SourceCredentials()
        credentials = self.make_credentials(source_credentials=source_credentials)

        # Spy on calls to source credentials refresh to confirm the expected request
        # instance is used.
        with mock.patch.object(
            source_credentials, "refresh", wraps=source_credentials.refresh
        ) as wrapped_souce_cred_refresh:
            credentials.refresh(request)

            self.assert_request_kwargs(request.call_args[1], headers, request_data)
            assert credentials.valid
            assert credentials.expiry == expected_expiry
            assert not credentials.expired
            assert credentials.token == response["access_token"]
            # Confirm source credentials called with the same request instance.
            wrapped_souce_cred_refresh.assert_called_with(request)

    @mock.patch("google.auth._helpers.utcnow", return_value=datetime.datetime.min)
    def test_refresh_without_response_expires_in(self, unused_utcnow):
        response = SUCCESS_RESPONSE.copy()
        # Simulate the response is missing the expires_in field.
        # The downscoped token expiration should match the source credentials
        # expiration.
        del response["expires_in"]
        expected_expires_in = 1800
        # Simulate the source credentials generates a token with 1800 second
        # expiration time. The generated downscoped token should have the same
        # expiration time.
        source_credentials = SourceCredentials(expires_in=expected_expires_in)
        expected_expiry = datetime.datetime.min + datetime.timedelta(
            seconds=expected_expires_in
        )
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        request_data = {
            "grant_type": GRANT_TYPE,
            "subject_token": "ACCESS_TOKEN_1",
            "subject_token_type": SUBJECT_TOKEN_TYPE,
            "requested_token_type": REQUESTED_TOKEN_TYPE,
            "options": urllib.parse.quote(json.dumps(CREDENTIAL_ACCESS_BOUNDARY_JSON)),
        }
        request = self.make_mock_request(status=http_client.OK, data=response)
        credentials = self.make_credentials(source_credentials=source_credentials)

        # Spy on calls to source credentials refresh to confirm the expected request
        # instance is used.
        with mock.patch.object(
            source_credentials, "refresh", wraps=source_credentials.refresh
        ) as wrapped_souce_cred_refresh:
            credentials.refresh(request)

            self.assert_request_kwargs(request.call_args[1], headers, request_data)
            assert credentials.valid
            assert credentials.expiry == expected_expiry
            assert not credentials.expired
            assert credentials.token == response["access_token"]
            # Confirm source credentials called with the same request instance.
            wrapped_souce_cred_refresh.assert_called_with(request)

    def test_refresh_token_exchange_error(self):
        request = self.make_mock_request(
            status=http_client.BAD_REQUEST, data=ERROR_RESPONSE
        )
        credentials = self.make_credentials()

        with pytest.raises(exceptions.OAuthError) as excinfo:
            credentials.refresh(request)

        assert excinfo.match(
            r"Error code invalid_grant: Subject token is invalid. - https://tools.ietf.org/html/rfc6749"
        )
        assert not credentials.expired
        assert credentials.token is None

    def test_refresh_source_credentials_refresh_error(self):
        # Initialize downscoped credentials with source credentials that raise
        # an error on refresh.
        credentials = self.make_credentials(
            source_credentials=SourceCredentials(raise_error=True)
        )

        with pytest.raises(exceptions.RefreshError) as excinfo:
            credentials.refresh(mock.sentinel.request)

        assert excinfo.match(r"Failed to refresh access token in source credentials.")
        assert not credentials.expired
        assert credentials.token is None

    def test_apply_without_quota_project_id(self):
        headers = {}
        request = self.make_mock_request(status=http_client.OK, data=SUCCESS_RESPONSE)
        credentials = self.make_credentials()

        credentials.refresh(request)
        credentials.apply(headers)

        assert headers == {
            "authorization": "Bearer {}".format(SUCCESS_RESPONSE["access_token"])
        }

    def test_apply_with_quota_project_id(self):
        headers = {"other": "header-value"}
        request = self.make_mock_request(status=http_client.OK, data=SUCCESS_RESPONSE)
        credentials = self.make_credentials(quota_project_id=QUOTA_PROJECT_ID)

        credentials.refresh(request)
        credentials.apply(headers)

        assert headers == {
            "other": "header-value",
            "authorization": "Bearer {}".format(SUCCESS_RESPONSE["access_token"]),
            "x-goog-user-project": QUOTA_PROJECT_ID,
        }

    def test_before_request(self):
        headers = {"other": "header-value"}
        request = self.make_mock_request(status=http_client.OK, data=SUCCESS_RESPONSE)
        credentials = self.make_credentials()

        # First call should call refresh, setting the token.
        credentials.before_request(request, "POST", "https://example.com/api", headers)

        assert headers == {
            "other": "header-value",
            "authorization": "Bearer {}".format(SUCCESS_RESPONSE["access_token"]),
        }

        # Second call shouldn't call refresh (request should be untouched).
        credentials.before_request(
            mock.sentinel.request, "POST", "https://example.com/api", headers
        )

        assert headers == {
            "other": "header-value",
            "authorization": "Bearer {}".format(SUCCESS_RESPONSE["access_token"]),
        }

    @mock.patch("google.auth._helpers.utcnow")
    def test_before_request_expired(self, utcnow):
        headers = {}
        request = self.make_mock_request(status=http_client.OK, data=SUCCESS_RESPONSE)
        credentials = self.make_credentials()
        credentials.token = "token"
        utcnow.return_value = datetime.datetime.min
        # Set the expiration to one second more than now plus the clock skew
        # accommodation. These credentials should be valid.
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
            "authorization": "Bearer {}".format(SUCCESS_RESPONSE["access_token"])
        }
