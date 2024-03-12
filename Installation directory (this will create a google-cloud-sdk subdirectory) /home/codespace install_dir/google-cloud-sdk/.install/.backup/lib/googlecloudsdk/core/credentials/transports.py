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

"""A module to get a credentialed transport object for making API calls."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import requests as core_requests
from googlecloudsdk.core.credentials import http
from googlecloudsdk.core.credentials import requests


def GetApitoolsTransport(timeout='unset',
                         enable_resource_quota=True,
                         response_encoding=None,
                         ca_certs=None,
                         allow_account_impersonation=True,
                         use_google_auth=None,
                         response_handler=None,
                         redact_request_body_reason=None):
  """Get an transport client for use with apitools.

  Args:
    timeout: double, The timeout in seconds to pass to httplib2.  This is the
        socket level timeout.  If timeout is None, timeout is infinite.  If
        default argument 'unset' is given, a sensible default is selected.
    enable_resource_quota: bool, By default, we are going to tell APIs to use
        the quota of the project being operated on. For some APIs we want to use
        gcloud's quota, so you can explicitly disable that behavior by passing
        False here.
    response_encoding: str, the encoding to use to decode the response.
    ca_certs: str, absolute filename of a ca_certs file that overrides the
        default
    allow_account_impersonation: bool, True to allow use of impersonated service
        account credentials for calls made with this client. If False, the
        active user credentials will always be used.
    use_google_auth: bool, True if the calling command indicates to use
        google-auth library for authentication. If False, authentication will
        fallback to using the oauth2client library.
    response_handler: requests.ResponseHandler, handler that gets executed
        before any other response handling.
    redact_request_body_reason: str, the reason why the request body must be
        redacted if --log-http is used. If None, the body is not redacted.

  Returns:
    1. A httplib2.Http-like object backed by httplib2 or requests.
  """
  if base.UseRequests():
    if response_handler:
      if not isinstance(response_handler, core_requests.ResponseHandler):
        raise ValueError('response_handler should be of type ResponseHandler.')
      if (properties.VALUES.core.log_http.GetBool() and
          properties.VALUES.core.log_http_streaming_body.GetBool()):
        # We want to print the actual body instead of printing the placeholder.
        # To achieve this, we need to set streaming_response_body as False.
        # Not that the body will be empty if the response_handler has already
        # consumed the stream.
        streaming_response_body = False
      else:
        streaming_response_body = response_handler.use_stream
    else:
      streaming_response_body = False
    session = requests.GetSession(
        timeout=timeout,
        enable_resource_quota=enable_resource_quota,
        ca_certs=ca_certs,
        allow_account_impersonation=allow_account_impersonation,
        streaming_response_body=streaming_response_body,
        redact_request_body_reason=redact_request_body_reason)

    return core_requests.GetApitoolsRequests(session, response_handler,
                                             response_encoding)

  return http.Http(timeout=timeout,
                   enable_resource_quota=enable_resource_quota,
                   response_encoding=response_encoding,
                   ca_certs=ca_certs,
                   allow_account_impersonation=allow_account_impersonation,
                   use_google_auth=use_google_auth)
