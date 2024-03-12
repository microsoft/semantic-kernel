# -*- coding: utf-8 -*-
# Copyright 2022 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for wrapped_credentials.py."""

import datetime
import json
import httplib2

from google.auth import aws
from google.auth import external_account
from google.auth import external_account_authorized_user
from google.auth import identity_pool
from google.auth import pluggable
from gslib.tests import testcase
from gslib.utils.wrapped_credentials import WrappedCredentials
import oauth2client

from six import add_move, MovedModule

add_move(MovedModule("mock", "mock", "unittest.mock"))
from six.moves import mock

ACCESS_TOKEN = "foo"
CONTENT = "content"
RESPONSE = httplib2.Response({
    "content-type": "text/plain",
    "status": "200",
    "content-length": len(CONTENT),
})


class MockCredentials(external_account.Credentials):

  def __init__(self, token=None, expiry=None, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._audience = None
    self.expiry = expiry
    self.token = None

    def side_effect(*args, **kwargs):
      del args, kwargs  # Unused.
      self.token = token

    self.refresh = mock.Mock(side_effect=side_effect)

  def retrieve_subject_token():
    pass


class HeadersWithAuth(dict):
  """A utility class to use to make sure a set of headers includes specific authentication"""

  def __init__(self, token):
    self.token = token or ""

  def __eq__(self, headers):
    return headers[b"Authorization"] == bytes("Bearer " + self.token, "utf-8")


class TestWrappedCredentials(testcase.GsUtilUnitTestCase):
  """Test logic for interacting with Wrapped Credentials the way we intend to use them."""

  @mock.patch.object(httplib2, "Http", autospec=True)
  def testWrappedCredentialUsage(self, http):
    http.return_value.request.return_value = (RESPONSE, CONTENT)
    req = http.return_value.request

    creds = WrappedCredentials(
        MockCredentials(token=ACCESS_TOKEN,
                        audience="foo",
                        subject_token_type="bar",
                        token_url="https://sts.googleapis.com",
                        credential_source="qux"))

    http = oauth2client.transport.get_http_object()
    creds.authorize(http)
    _, content = http.request(uri="google.com")
    self.assertEqual(content, CONTENT)
    creds._base.refresh.assert_called_once_with(mock.ANY)

    # Make sure the default request gets called with the correct token.
    req.assert_called_once_with("google.com",
                                method="GET",
                                headers=HeadersWithAuth(ACCESS_TOKEN),
                                body=None,
                                connection_type=mock.ANY,
                                redirections=mock.ANY)

  def testWrappedCredentialSerialization(self):
    """Test logic for converting Wrapped Credentials to and from JSON for serialization."""
    creds = WrappedCredentials(
        identity_pool.Credentials(audience="foo",
                                  subject_token_type="bar",
                                  token_url="https://sts.googleapis.com",
                                  credential_source={"url": "google.com"}))
    creds.access_token = ACCESS_TOKEN
    creds.token_expiry = datetime.datetime(2001, 12, 5, 0, 0)
    creds_json = creds.to_json()
    json_values = json.loads(creds_json)
    self.assertEqual(json_values["client_id"], "foo")
    self.assertEqual(json_values['access_token'], ACCESS_TOKEN)
    self.assertEqual(json_values['token_expiry'], "2001-12-05T00:00:00Z")
    self.assertEqual(json_values["_base"]["audience"], "foo")
    self.assertEqual(json_values["_base"]["subject_token_type"], "bar")
    self.assertEqual(json_values["_base"]["token_url"],
                      "https://sts.googleapis.com")
    self.assertEqual(json_values["_base"]["credential_source"]["url"],
                      "google.com")

    creds2 = WrappedCredentials.from_json(creds_json)
    self.assertIsInstance(creds2, WrappedCredentials)
    self.assertIsInstance(creds2._base, identity_pool.Credentials)
    self.assertEqual(creds2.client_id, "foo")
    self.assertEqual(creds2.access_token, ACCESS_TOKEN)
    self.assertEqual(creds2.token_expiry, creds.token_expiry)

  def testWrappedCredentialSerializationMissingKeywords(self):
    """Test logic for creating a Wrapped Credentials using keywords that exist in IdentityPool but not AWS."""
    creds = WrappedCredentials.from_json(
        json.dumps({
            "client_id": "foo",
            "access_token": ACCESS_TOKEN,
            "token_expiry": "2001-12-05T00:00:00Z",
            "_base": {
                "type": "external_account",
                "audience": "foo",
                "subject_token_type": "bar",
                "token_url": "https://sts.googleapis.com",
                "credential_source": {
                    "url": "google.com",
                    "workforce_pool_user_project": "1234567890"
                }
            }
        }))

    self.assertIsInstance(creds, WrappedCredentials)
    self.assertIsInstance(creds._base, identity_pool.Credentials)

  @mock.patch.object(httplib2, "Http", autospec=True)
  def testWrappedCredentialUsageExternalAccountAuthorizedUser(self, http):
    http.return_value.request.return_value = (RESPONSE, CONTENT)
    req = http.return_value.request

    creds = WrappedCredentials(
        external_account_authorized_user.Credentials(
            audience=
            "//iam.googleapis.com/locations/global/workforcePools/$WORKFORCE_POOL_ID/providers/$PROVIDER_ID",
            refresh_token="refreshToken",
            token_url="https://sts.googleapis.com/v1/oauth/token",
            token_info_url="https://sts.googleapis.com/v1/instrospect",
            client_id="clientId",
            client_secret="clientSecret"))

    def _refresh_token_side_effect(*args, **kwargs):
      del args, kwargs  # Unused.
      creds._base.token = ACCESS_TOKEN

    creds._base.refresh = mock.Mock(side_effect=_refresh_token_side_effect)

    http = oauth2client.transport.get_http_object()
    creds.authorize(http)
    _, content = http.request(uri="google.com")
    self.assertEqual(content, CONTENT)
    creds._base.refresh.assert_called_once_with(mock.ANY)

    # Make sure the default request gets called with the correct token.
    req.assert_called_once_with("google.com",
                                method="GET",
                                headers=HeadersWithAuth(ACCESS_TOKEN),
                                body=None,
                                connection_type=mock.ANY,
                                redirections=mock.ANY)

  def testWrappedCredentialSerializationExternalAccountAuthorizedUser(self):
    """Test logic for converting Wrapped Credentials to and from JSON for serialization."""
    creds = WrappedCredentials(
        external_account_authorized_user.Credentials(
            audience=
            "//iam.googleapis.com/locations/global/workforcePools/$WORKFORCE_POOL_ID/providers/$PROVIDER_ID",
            refresh_token="refreshToken",
            token_url="https://sts.googleapis.com/v1/oauth/token",
            token_info_url="https://sts.googleapis.com/v1/instrospect",
            client_id="clientId",
            client_secret="clientSecret"))
    creds.access_token = ACCESS_TOKEN
    creds.token_expiry = datetime.datetime(2001, 12, 5, 0, 0)
    creds_json = creds.to_json()
    json_values = json.loads(creds_json)
    expected_json_values = {
        "_class": "WrappedCredentials",
        "_module": "gslib.utils.wrapped_credentials",
        "client_id": "clientId",
        "access_token": ACCESS_TOKEN,
        "token_expiry": "2001-12-05T00:00:00Z",
        "client_secret": "clientSecret",
        "refresh_token": "refreshToken",
        "id_token": None,
        "id_token_jwt": None,
        "invalid": False,
        "revoke_uri": None,
        "scopes": [],
        "token_info_uri": None,
        "token_response": None,
        "token_uri": None,
        "user_agent": None,
        "_base": {
            "type":
                "external_account_authorized_user",
            "audience":
                "//iam.googleapis.com/locations/global/workforcePools/$WORKFORCE_POOL_ID/providers/$PROVIDER_ID",
            "token":
                ACCESS_TOKEN,
            "expiry":
                "2001-12-05T00:00:00Z",
            "token_url":
                "https://sts.googleapis.com/v1/oauth/token",
            "token_info_url":
                "https://sts.googleapis.com/v1/instrospect",
            "refresh_token":
                "refreshToken",
            "client_id":
                "clientId",
            "client_secret":
                "clientSecret",
        }
    }
    self.assertEqual(json_values, expected_json_values)

    creds2 = WrappedCredentials.from_json(creds_json)
    self.assertIsInstance(creds2, WrappedCredentials)
    self.assertIsInstance(creds2._base,
                          external_account_authorized_user.Credentials)
    self.assertEqual(creds2.client_id, "clientId")

  def testFromJsonAWSCredentials(self):
    creds = WrappedCredentials.from_json(
        json.dumps({
            "_base": {
                "audience":
                    "//iam.googleapis.com/projects/123456/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID",
                "credential_source": {
                    "environment_id":
                        "aws1",
                    "region_url":
                        "http://169.254.169.254/latest/meta-data/placement/availability-zone",
                    "regional_cred_verification_url":
                        "https://sts.{region}.amazonaws.com?Action=GetCallerIdentity&Version=2011-06-15",
                    "url":
                        "http://169.254.169.254/latest/meta-data/iam/security-credentials"
                },
                "service_account_impersonation_url":
                    "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/service-1234@service-name.iam.gserviceaccount.com:generateAccessToken",
                "subject_token_type":
                    "urn:ietf:params:aws:token-type:aws4_request",
                "token_url":
                    "https://sts.googleapis.com/v1/token",
                "type":
                    "external_account"
            }
        }))

    self.assertIsInstance(creds, WrappedCredentials)
    self.assertIsInstance(creds._base, external_account.Credentials)
    self.assertIsInstance(creds._base, aws.Credentials)

  def testFromJsonFileBasedCredentials(self):
    creds = WrappedCredentials.from_json(
        json.dumps({
            "_base": {
                "audience":
                    "//iam.googleapis.com/projects/123456/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID",
                "credential_source": {
                    "file": "/var/run/secrets/goog.id/token"
                },
                "service_account_impersonation_url":
                    "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/service-1234@service-name.iam.gserviceaccount.com:generateAccessToken",
                "subject_token_type":
                    "urn:ietf:params:oauth:token-type:jwt",
                "token_url":
                    "https://sts.googleapis.com/v1/token",
                "type":
                    "external_account"
            }
        }))

    self.assertIsInstance(creds, WrappedCredentials)
    self.assertIsInstance(creds._base, external_account.Credentials)
    self.assertIsInstance(creds._base, identity_pool.Credentials)

  def testFromJsonPluggableCredentials(self):
    creds = WrappedCredentials.from_json(
        json.dumps({
            "_base": {
                "audience":
                    "//iam.googleapis.com/projects/123456/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID",
                "credential_source": {
                    "executable": {
                        "command": "/path/to/command.sh"
                    }
                },
                "service_account_impersonation_url":
                    "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/service-1234@service-name.iam.gserviceaccount.com:generateAccessToken",
                "subject_token_type":
                    "urn:ietf:params:oauth:token-type:jwt",
                "token_url":
                    "https://sts.googleapis.com/v1/token",
                "type":
                    "external_account"
            }
        }))

    self.assertIsInstance(creds, WrappedCredentials)
    self.assertIsInstance(creds._base, external_account.Credentials)
    self.assertIsInstance(creds._base, pluggable.Credentials)

  def testFromJsonExternalAccountAuthorizedUserCredentials(self):
    creds = WrappedCredentials.from_json(
        json.dumps({
            "_base": {
                "type":
                    "external_account_authorized_user",
                "audience":
                    "//iam.googleapis.com/locations/global/workforcePools/$WORKFORCE_POOL_ID/providers/$PROVIDER_ID",
                "refresh_token":
                    "refreshToken",
                "token_url":
                    "https://sts.googleapis.com/v1/oauth/token",
                "token_info_url":
                    "https://sts.googleapis.com/v1/instrospect",
                "client_id":
                    "clientId",
                "client_secret":
                    "clientSecret",
            }
        }))

    self.assertIsInstance(creds, WrappedCredentials)
    self.assertIsInstance(creds._base,
                          external_account_authorized_user.Credentials)
