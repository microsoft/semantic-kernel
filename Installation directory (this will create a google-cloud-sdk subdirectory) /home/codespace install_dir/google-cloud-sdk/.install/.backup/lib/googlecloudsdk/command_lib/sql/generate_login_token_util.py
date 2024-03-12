# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Common utility functions for sql generate-login-token commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from google.auth import credentials
from google.auth import exceptions as google_auth_exceptions
from google.oauth2 import credentials as google_auth_creds
from googlecloudsdk.api_lib.auth import exceptions as auth_exceptions
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import log
from googlecloudsdk.core import requests
from googlecloudsdk.core.credentials import creds as c_creds
from googlecloudsdk.core.credentials import google_auth_credentials as c_google_auth
from googlecloudsdk.core.credentials import store as c_store
import six


def generate_login_token_from_gcloud_auth(scopes):
  """Genearete a down-coped access token with given scopes for IAM DB authentication from gcloud credentials.

  Args:
    scopes: scopes to be included in the down-scoped token.

  Returns:
    Down-scoped access token.
  """
  cred = c_store.Load(
      allow_account_impersonation=True,
      use_google_auth=True,
      with_access_token_cache=False)

  cred = _downscope_credential(cred, scopes)

  c_store.Refresh(cred)
  if c_creds.IsOauth2ClientCredentials(cred):
    token = cred.access_token
  else:
    token = cred.token
  if not token:
    raise auth_exceptions.InvalidCredentialsError(
        'No access token could be obtained from the current credentials.')
  return token


def generate_login_token_from_adc(scopes):
  """Genearete a down-coped access token with given scopes for IAM DB authentication from application default credentials.

  Args:
    scopes: scopes to be included in the down-scoped token.

  Returns:
    Down-scoped access token.
  """
  try:
    creds, _ = c_creds.GetGoogleAuthDefault().default(
        scopes=scopes)
  except google_auth_exceptions.DefaultCredentialsError as e:
    log.debug(e, exc_info=True)
    raise c_exc.ToolException(six.text_type(e))

  creds = _downscope_credential(creds, scopes)

  # Converts the user credentials so that it can handle reauth during refresh.
  if isinstance(creds, google_auth_creds.Credentials):
    creds = c_google_auth.Credentials.FromGoogleAuthUserCredentials(
        creds)

  with c_store.HandleGoogleAuthCredentialsRefreshError(for_adc=True):
    creds.refresh(requests.GoogleAuthRequest())
  return creds


def _downscope_credential(creds, scopes):
  """Genearte a down-scoped credential.

  Args:
    creds: end user credential
    scopes: scopes to be included in the down-scoped credential

  Returns:
    Down-scoped credential.
  """
  cred_type = c_creds.CredentialTypeGoogleAuth.FromCredentials(creds)
  if cred_type not in [
      c_creds.CredentialTypeGoogleAuth.USER_ACCOUNT,
      c_creds.CredentialTypeGoogleAuth.SERVICE_ACCOUNT,
      c_creds.CredentialTypeGoogleAuth.IMPERSONATED_ACCOUNT,
  ]:
    # TODO(b/223649175): Add support for other credential types(e.g GCE).
    log.warning(
        'This command may not working as expected '
        'for account type {}.'.format(cred_type.key)
    )

  # non user account credential types
  # pylint:disable=protected-access
  if isinstance(creds, credentials.Scoped):
    creds = creds.with_scopes(scopes)
  else:
    creds._scopes = scopes
  return creds
