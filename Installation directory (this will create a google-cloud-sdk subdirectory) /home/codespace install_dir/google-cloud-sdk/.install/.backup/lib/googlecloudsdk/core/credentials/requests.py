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

"""A module to get a credentialed http object for making API calls."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from google.auth import external_account as google_auth_external_account
from google.auth.transport import requests as google_auth_requests
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import requests
from googlecloudsdk.core import transport as core_transport
from googlecloudsdk.core.credentials import transport

REFRESH_STATUS_CODES = [401]
MAX_REFRESH_ATTEMPTS = 1


class Error(exceptions.Error):
  """Exceptions for this module."""


def GetSession(timeout='unset',
               ca_certs=None,
               enable_resource_quota=True,
               allow_account_impersonation=True,
               session=None,
               streaming_response_body=False,
               redact_request_body_reason=None):
  """Get requests.Session object for working with the Google API.

  Args:
    timeout: double, The timeout in seconds to pass to httplib2.  This is the
        socket level timeout.  If timeout is None, timeout is infinite.  If
        default argument 'unset' is given, a sensible default is selected.
    ca_certs: str, absolute filename of a ca_certs file that overrides the
        default
    enable_resource_quota: bool, By default, we are going to tell APIs to use
        the quota of the project being operated on. For some APIs we want to use
        gcloud's quota, so you can explicitly disable that behavior by passing
        False here.
    allow_account_impersonation: bool, True to allow use of impersonated service
        account credentials for calls made with this client. If False, the
        active user credentials will always be used.
    session: requests.Session instance. Otherwise, a new requests.Session will
        be initialized.
    streaming_response_body: bool, True indicates that the response body will
        be a streaming body.
    redact_request_body_reason: str, the reason why the request body must be
        redacted if --log-http is used. If None, the body is not redacted.

  Returns:
    1. A regular requests.Session object if no credentials are available;
    2. Or an authorized requests.Session object authorized by google-auth
       credentials.

  Raises:
    creds_exceptions.Error: If an error loading the credentials occurs.
  """
  session = requests.GetSession(
      timeout=timeout,
      ca_certs=ca_certs,
      session=session,
      streaming_response_body=streaming_response_body,
      redact_request_body_reason=redact_request_body_reason)
  request_wrapper = RequestWrapper()
  session = request_wrapper.WrapQuota(session, enable_resource_quota,
                                      allow_account_impersonation, True)
  session = request_wrapper.WrapCredentials(session,
                                            allow_account_impersonation)

  return session


class RequestWrapper(transport.CredentialWrappingMixin,
                     transport.QuotaHandlerMixin, requests.RequestWrapper):
  """Class for wrapping requests.Session requests."""

  def AuthorizeClient(self, http_client, creds):
    """Returns an http_client authorized with the given credentials."""
    orig_request = http_client.request
    credential_refresh_state = {'attempt': 0}

    def WrappedRequest(method, url, data=None, headers=None, **kwargs):
      wrapped_request = http_client.request
      http_client.request = orig_request

      auth_request = google_auth_requests.Request(http_client)
      creds.before_request(auth_request, method, url, headers)

      http_client.request = wrapped_request
      response = orig_request(
          method, url, data=data, headers=headers or {}, **kwargs)

      if (response.status_code in REFRESH_STATUS_CODES and
          not (isinstance(creds, google_auth_external_account.Credentials) and
               creds.valid) and
          credential_refresh_state['attempt'] < MAX_REFRESH_ATTEMPTS):
        credential_refresh_state['attempt'] += 1
        creds.refresh(requests.GoogleAuthRequest())
        response = orig_request(
            method, url, data=data, headers=headers or {}, **kwargs)

      return response

    http_client.request = WrappedRequest
    return http_client

  def WrapQuota(self, http_client, enable_resource_quota,
                allow_account_impersonation, use_google_auth):
    """Returns an http_client with quota project handling."""
    quota_project = self.QuotaProject(enable_resource_quota,
                                      allow_account_impersonation,
                                      use_google_auth)
    if not quota_project:
      return http_client
    orig_request = http_client.request
    wrapped_request = self.QuotaWrappedRequest(http_client, quota_project)

    def RequestWithRetry(*args, **kwargs):
      """Retries the request after removing the quota project header.

      Try the request with the X-Goog-User-Project header. If the account does
      not have the permission to expense the quota of the user project in the
      header, remove the header and retry.

      Args:
        *args: *args to send to requests.Session.request method.
        **kwargs: **kwargs to send to requests.Session.request method.

      Returns:
        Response from requests.Session.request.
      """
      response = wrapped_request(*args, **kwargs)
      if response.status_code != 403:
        return response
      old_encoding = response.encoding
      response.encoding = response.encoding or core_transport.ENCODING
      try:
        err_details = response.json()['error']['details']
      except (KeyError, ValueError):
        return response
      finally:
        response.encoding = old_encoding
      for err_detail in err_details:
        if (err_detail.get('@type')
            == 'type.googleapis.com/google.rpc.ErrorInfo' and
            err_detail.get('reason') == transport.USER_PROJECT_ERROR_REASON and
            err_detail.get('domain') == transport.USER_PROJECT_ERROR_DOMAIN):
          return orig_request(*args, **kwargs)
      return response

    if base.UserProjectQuotaWithFallbackEnabled():
      http_client.request = RequestWithRetry
    else:
      http_client.request = wrapped_request
    return http_client
