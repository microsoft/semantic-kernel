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

"""A module to get a credentialed http object for making API calls."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from google.auth import external_account as google_auth_external_account
import google_auth_httplib2
from googlecloudsdk.calliope import base
from googlecloudsdk.core import http
from googlecloudsdk.core.credentials import creds as core_creds
from googlecloudsdk.core.credentials import transport
import six


def Http(timeout='unset',
         response_encoding=None,
         ca_certs=None,
         enable_resource_quota=True,
         allow_account_impersonation=True,
         use_google_auth=None):
  """Get an httplib2.Http client for working with the Google API.

  Args:
    timeout: double, The timeout in seconds to pass to httplib2.  This is the
        socket level timeout.  If timeout is None, timeout is infinite.  If
        default argument 'unset' is given, a sensible default is selected.
    response_encoding: str, the encoding to use to decode the response.
    ca_certs: str, absolute filename of a ca_certs file that overrides the
        default
    enable_resource_quota: bool, By default, we are going to tell APIs to use
        the quota of the project being operated on. For some APIs we want to use
        gcloud's quota, so you can explicitly disable that behavior by passing
        False here.
    allow_account_impersonation: bool, True to allow use of impersonated service
      account credentials for calls made with this client. If False, the active
      user credentials will always be used.
    use_google_auth: bool, True if the calling command indicates to use
      google-auth library for authentication. If False, authentication will
      fallback to using the oauth2client library. If None, set the value based
      on the configuration.

  Returns:
    1. A regular httplib2.Http object if no credentials are available;
    2. Or a httplib2.Http client object authorized by oauth2client
       credentials if use_google_auth==False;
    3. Or a google_auth_httplib2.AuthorizedHttp client object authorized by
       google-auth credentials.

  Raises:
    core.credentials.exceptions.Error: If an error loading the credentials
      occurs.
  """
  http_client = http.Http(timeout=timeout, response_encoding=response_encoding,
                          ca_certs=ca_certs)

  if use_google_auth is None:
    use_google_auth = base.UseGoogleAuth()
  request_wrapper = RequestWrapper()
  http_client = request_wrapper.WrapQuota(
      http_client,
      enable_resource_quota,
      allow_account_impersonation,
      use_google_auth)
  http_client = request_wrapper.WrapCredentials(http_client,
                                                allow_account_impersonation,
                                                use_google_auth)

  if hasattr(http_client, '_googlecloudsdk_credentials'):
    creds = http_client._googlecloudsdk_credentials  # pylint: disable=protected-access
    if core_creds.IsGoogleAuthCredentials(creds):
      apitools_creds = _GoogleAuthApitoolsCredentials(creds)
    else:
      apitools_creds = creds
    # apitools needs this attribute to do credential refreshes during batch API
    # requests.
    setattr(http_client.request, 'credentials', apitools_creds)

  return http_client


class _GoogleAuthApitoolsCredentials():
  """Class of wrapping credentials."""

  def __init__(self, credentials):
    self.credentials = credentials

  def refresh(self, http_client):  # pylint: disable=invalid-name
    del http_client  # unused
    if isinstance(
        self.credentials,
        google_auth_external_account.Credentials) and self.credentials.valid:
      return
    self.credentials.refresh(http.GoogleAuthRequest())


class RequestWrapper(transport.CredentialWrappingMixin,
                     transport.QuotaHandlerMixin, http.RequestWrapper):
  """Class for wrapping httplib.Httplib2 requests."""

  def AuthorizeClient(self, http_client, creds):
    """Returns an http_client authorized with the given credentials."""
    if core_creds.IsGoogleAuthCredentials(creds):
      http_client = google_auth_httplib2.AuthorizedHttp(creds, http_client)
    else:
      http_client = creds.authorize(http_client)
    return http_client

  def WrapQuota(self,
                http_client,
                enable_resource_quota,
                allow_account_impersonation,
                use_google_auth):
    """Returns an http_client with quota project handling."""
    quota_project = self.QuotaProject(enable_resource_quota,
                                      allow_account_impersonation,
                                      use_google_auth)
    if not quota_project:
      return http_client
    orig_request = http_client.request
    wrapped_request = self.QuotaWrappedRequest(
        http_client, quota_project)

    def RequestWithRetry(*args, **kwargs):
      """Retries the request after removing the quota project header.

      Try the request with the X-Goog-User-Project header. If the account does
      not have the permission to expense the quota of the user project in the
      header, remove the header and retry.

      Args:
        *args: *args to send to httplib2.Http.request method.
        **kwargs: **kwargs to send to httplib2.Http.request method.

      Returns:
        Response from httplib2.Http.request.
      """
      response, content = wrapped_request(*args, **kwargs)
      if response.status != 403:
        return response, content
      content_text = six.ensure_text(content)
      try:
        err_details = json.loads(content_text)['error']['details']
      except (KeyError, json.JSONDecodeError):
        return response, content

      for err_detail in err_details:
        if (err_detail.get('@type')
            == 'type.googleapis.com/google.rpc.ErrorInfo' and
            err_detail.get('reason') == transport.USER_PROJECT_ERROR_REASON and
            err_detail.get('domain') == transport.USER_PROJECT_ERROR_DOMAIN):
          return orig_request(*args, **kwargs)
      return response, content

    if base.UserProjectQuotaWithFallbackEnabled():
      http_client.request = RequestWithRetry
    else:
      http_client.request = wrapped_request
    return http_client
