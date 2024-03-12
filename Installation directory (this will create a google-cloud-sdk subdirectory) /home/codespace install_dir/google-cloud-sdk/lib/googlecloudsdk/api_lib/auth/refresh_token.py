# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""Manages logic for refresh token."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.credentials import store as c_store

from oauth2client import client
from google.auth import exceptions as google_auth_exceptions


class LoadingCredentialsError(exceptions.Error):
  """Reraise on oauth2client and google-auth errors."""


class UnsupportedCredentialsType(exceptions.Error):
  """Raised when credentials do not have refresh token."""


def ActivateCredentials(account, refresh_token):
  """Activates credentials for given account with given refresh token."""

  creds = c_store.AcquireFromToken(
      refresh_token, use_google_auth=True)

  c_store.ActivateCredentials(account, creds)

  return creds


def GetForAccount(account=None):
  """Returns refresh token for given account.

  Args:
    account: str, usually email like string,
        if not provided current account is used.

  Returns:
    str: refresh token

  Raises:
    UnsupportedCredentialsType: if credentials are not user credentials.
  """
  try:
    creds = c_store.Load(account, use_google_auth=True)
  except (client.Error, google_auth_exceptions.GoogleAuthError):
    raise calliope_exceptions.NewErrorFromCurrentException(
        LoadingCredentialsError)

  refresh_token = getattr(creds, 'refresh_token', None)

  if refresh_token is None:
    raise UnsupportedCredentialsType(
        'Credentials for account {0} do not support refresh tokens.'
        .format(account))

  return refresh_token
