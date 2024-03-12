# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Module for wrapping transports with credentials."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc

from googlecloudsdk.calliope import base
from googlecloudsdk.core import context_aware
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import transport
from googlecloudsdk.core.credentials import creds as core_creds
from googlecloudsdk.core.credentials import exceptions as creds_exceptions
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.util import files

from oauth2client import client
import six
from google.auth import exceptions as google_auth_exceptions


class Error(exceptions.Error):
  """Exceptions for the credentials transport module."""


USER_PROJECT_ERROR_REASON = 'USER_PROJECT_DENIED'
USER_PROJECT_ERROR_DOMAIN = 'googleapis.com'


class QuotaHandlerMixin(object):
  """Mixin for handling quota project."""

  def QuotaProject(self, enable_resource_quota,
                   allow_account_impersonation, use_google_auth):
    if not enable_resource_quota:
      return None
    creds = store.LoadIfEnabled(allow_account_impersonation, use_google_auth)
    return core_creds.GetQuotaProject(creds)

  def QuotaWrappedRequest(self,
                          http_client,
                          quota_project):
    """Returns a request method which adds the quota project header."""
    handlers = [
        transport.Handler(
            transport.SetHeader('X-Goog-User-Project', quota_project))
    ]
    self.WrapRequest(http_client, handlers)
    return http_client.request

  @abc.abstractmethod
  def WrapQuota(self,
                http_client,
                enable_resource_quota,
                allow_account_impersonation,
                use_google_auth):
    """Returns a http_client with quota project handling.

    Args:
      http_client: The http client to be wrapped.
      enable_resource_quota: bool, By default, we are going to tell APIs to use
        the quota of the project being operated on. For some APIs we want to use
        gcloud's quota, so you can explicitly disable that behavior by passing
        False here.
      allow_account_impersonation: bool, True to allow use of impersonated
        service account credentials for calls made with this client. If False,
        the active user credentials will always be used.
      use_google_auth: bool, True if the calling command indicates to use
        google-auth library for authentication. If False, authentication will
        fallback to using the oauth2client library. If None, set the value based
        the configuration.
    """


class CredentialWrappingMixin(object):
  """Mixin for wrapping authorized http clients."""

  def WrapCredentials(self,
                      http_client,
                      allow_account_impersonation=True,
                      use_google_auth=None):
    """Get an http client for working with Google APIs.

    Args:
      http_client: The http client to be wrapped.
      allow_account_impersonation: bool, True to allow use of impersonated
        service account credentials for calls made with this client. If False,
        the active user credentials will always be used.
      use_google_auth: bool, True if the calling command indicates to use
        google-auth library for authentication. If False, authentication will
        fallback to using the oauth2client library. If None, set the value based
        the configuration.

    Returns:
      An authorized http client with exception handling.

    Raises:
      creds_exceptions.Error: If an error loading the credentials occurs.
    """

    # Wrappers for IAM header injection.
    authority_selector = properties.VALUES.auth.authority_selector.Get()
    authorization_token_file = (
        properties.VALUES.auth.authorization_token_file.Get())
    handlers = _GetIAMAuthHandlers(authority_selector, authorization_token_file)

    if use_google_auth is None:
      use_google_auth = base.UseGoogleAuth()
    creds = store.LoadIfEnabled(allow_account_impersonation, use_google_auth)
    if creds:
      http_client = self.AuthorizeClient(http_client, creds)
      # Set this attribute so we can access it later, even after the http_client
      # request method has been wrapped
      setattr(http_client, '_googlecloudsdk_credentials', creds)

    self.WrapRequest(
        http_client, handlers, _HandleAuthError,
        (client.AccessTokenRefreshError, google_auth_exceptions.RefreshError))

    return http_client

  @abc.abstractmethod
  def AuthorizeClient(self, http_client, credentials):
    """Returns an http_client authorized with the given credentials."""


def _GetIAMAuthHandlers(authority_selector, authorization_token_file):
  """Get the request handlers for IAM authority selctors and auth tokens..

  Args:
    authority_selector: str, The authority selector string we want to use for
      the request or None.
    authorization_token_file: str, The file that contains the authorization
      token we want to use for the request or None.

  Returns:
    [transport Modifiers]: A list of request modifier functions to use to wrap
    an http request.
  """
  authorization_token = None
  if authorization_token_file:
    try:
      authorization_token = files.ReadFileContents(authorization_token_file)
    except files.Error as e:
      raise Error(e)

  handlers = []
  if authority_selector:
    handlers.append(
        transport.Handler(
            transport.SetHeader('x-goog-iam-authority-selector',
                                authority_selector)))

  if authorization_token:
    handlers.append(
        transport.Handler(
            transport.SetHeader('x-goog-iam-authorization-token',
                                authorization_token.strip())))

  return handlers


def _HandleAuthError(e):
  """Handle a generic auth error and raise a nicer message.

  Args:
    e: The exception that was caught.

  Raises:
    creds_exceptions.TokenRefreshError: If an auth error occurs.
  """
  msg = six.text_type(e)
  log.debug('Exception caught during HTTP request: %s', msg,
            exc_info=True)
  if context_aware.IsContextAwareAccessDeniedError(e):
    raise creds_exceptions.TokenRefreshDeniedByCAAError(msg)
  raise creds_exceptions.TokenRefreshError(msg)
