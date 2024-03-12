# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Provides utilities for token introspection."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from google.oauth2 import utils as oauth2_utils
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import requests as core_requests

from six.moves import http_client
from six.moves import urllib

_ACCESS_TOKEN_TYPE = 'urn:ietf:params:oauth:token-type:access_token'
_URLENCODED_HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}
_EXTERNAL_ACCT_TOKEN_INTROSPECT_ENDPOINT = (
    'https://sts.googleapis.com/v1/introspect')


class Error(exceptions.Error):
  """A base exception for this module."""


class InactiveCredentialsError(Error):
  """Raised when the provided credentials are invalid or expired."""


class TokenIntrospectionError(Error):
  """Raised when an error is encountered while calling token introspection."""


class IntrospectionClient(oauth2_utils.OAuthClientAuthHandler):
  """Implements the OAuth 2.0 token introspection spec.

  This is based on https://tools.ietf.org/html/rfc7662.
  The implementation supports 3 types of client authentication when calling
  the endpoints: no authentication, basic header authentication and POST body
  authentication.
  """

  def __init__(self, token_introspect_endpoint, client_authentication=None):
    """Initializes an OAuth introspection client instance.

    Args:
      token_introspect_endpoint (str): The token introspection endpoint.
      client_authentication (Optional[oauth2_utils.ClientAuthentication]): The
        optional OAuth client authentication credentials if available.
    """
    super(IntrospectionClient, self).__init__(client_authentication)
    self._token_introspect_endpoint = token_introspect_endpoint

  def introspect(self, request, token, token_type_hint=_ACCESS_TOKEN_TYPE):
    """Returns the meta-information associated with an OAuth token.

    Args:
      request (google.auth.transport.Request): A callable that makes HTTP
        requests.
      token (str): The OAuth token whose meta-information are to be returned.
      token_type_hint (Optional[str]): The optional token type. The default is
        access_token.

    Returns:
      Mapping: The active token meta-information returned by the introspection
        endpoint.

    Raises:
      InactiveCredentialsError: If the credentials are invalid or expired.
      TokenIntrospectionError: If an error is encountered while calling the
        token introspection endpoint.
    """
    headers = _URLENCODED_HEADERS.copy()
    request_body = {
        'token': token,
        'token_type_hint': token_type_hint,
    }
    # Apply OAuth client authentication.
    self.apply_client_authentication_options(headers, request_body)

    # Execute request.
    response = request(
        url=self._token_introspect_endpoint,
        method='POST',
        headers=headers,
        body=urllib.parse.urlencode(request_body).encode('utf-8'),
    )

    response_body = (
        response.data.decode('utf-8')
        if hasattr(response.data, 'decode') else response.data)

    # If non-200 response received, translate to TokenIntrospectionError.
    if response.status != http_client.OK:
      raise TokenIntrospectionError(response_body)

    response_data = json.loads(response_body)

    if response_data.get('active'):
      return response_data
    else:
      raise InactiveCredentialsError(response_body)


def GetExternalAccountId(creds):
  """Returns the external account credentials' identifier.

  This requires basic client authentication and only works with external
  account credentials that have not been impersonated. The returned username
  field is used for the account ID.

  Args:
    creds (google.auth.external_account.Credentials): The external account
      credentials whose account ID is to be determined.

  Returns:
    Optional(str): The account ID string if determinable.

  Raises:
    InactiveCredentialsError: If the credentials are invalid or expired.
    TokenIntrospectionError: If an error is encountered while calling the
      token introspection endpoint.
  """
  # Use basic client authentication.
  client_authentication = oauth2_utils.ClientAuthentication(
      oauth2_utils.ClientAuthType.basic, config.CLOUDSDK_CLIENT_ID,
      config.CLOUDSDK_CLIENT_NOTSOSECRET)

  # Check if the introspection endpoint has been overridden,
  # otherwise use default endpoint. Prioritize property override first then
  # credential config.
  token_introspection_endpoint = _EXTERNAL_ACCT_TOKEN_INTROSPECT_ENDPOINT

  endpoint_override = properties.VALUES.auth.token_introspection_endpoint.Get()
  property_override = creds.token_info_url

  if endpoint_override or property_override:
    token_introspection_endpoint = endpoint_override or property_override

  oauth_introspection = IntrospectionClient(
      token_introspect_endpoint=token_introspection_endpoint,
      client_authentication=client_authentication)
  request = core_requests.GoogleAuthRequest()
  if not creds.valid:
    creds.refresh(request)
  token_info = oauth_introspection.introspect(request, creds.token)
  # User friendly identifier is stored in username.
  return token_info.get('username')
