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
"""Helper Classes for using gapic clients in gcloud."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from google.auth import external_account as google_auth_external_account
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import requests
from googlecloudsdk.core.credentials import creds
from googlecloudsdk.core.credentials import store


class MissingStoredCredentialsError(exceptions.Error):
  """Indicates stored credentials do not exist or are not available."""


def GetGapicCredentials(enable_resource_quota=True,
                        allow_account_impersonation=True):
  """Returns a credential object for use by gapic client libraries.

  Currently, we set _quota_project on the credentials, unlike for http requests,
  which add quota project through request wrapping to implement
  go/gcloud-quota-model-v2.

  Additionally, we wrap the refresh method and plug in our own
  google.auth.transport.Request object that uses our transport.

  Args:
    enable_resource_quota: bool, By default, we are going to tell APIs to use
        the quota of the project being operated on. For some APIs we want to use
        gcloud's quota, so you can explicitly disable that behavior by passing
        False here.
    allow_account_impersonation: bool, True to allow use of impersonated service
        account credentials for calls made with this client. If False, the
        active user credentials will always be used.

  Returns:
    A google auth credentials.Credentials object.

  Raises:
    MissingStoredCredentialsError: If a google-auth credential cannot be loaded.
  """

  credentials = store.LoadIfEnabled(
      allow_account_impersonation=allow_account_impersonation,
      use_google_auth=True)
  if not creds.IsGoogleAuthCredentials(credentials):
    raise MissingStoredCredentialsError('Unable to load credentials')

  if enable_resource_quota:
    # pylint: disable=protected-access
    credentials._quota_project_id = creds.GetQuotaProject(credentials)

  # In order to ensure that credentials.Credentials:refresh is called with a
  # google.auth.transport.Request that uses our transport, we ignore the request
  # argument that is passed in and plug in our own.
  original_refresh = credentials.refresh
  def WrappedRefresh(request):
    del request  # unused
    # Currently we don't do any revokes on credentials. If a credential is still
    # valid, we don't refresh on 401 error
    if isinstance(
        credentials,
        google_auth_external_account.Credentials) and credentials.valid:
      return None
    return original_refresh(requests.GoogleAuthRequest())
  credentials.refresh = WrappedRefresh

  return credentials


def MakeBidiRpc(client, start_rpc, initial_request=None):
  """Initializes a BidiRpc instances.

  Args:
      client: GAPIC Wrapper client to use.
      start_rpc (grpc.StreamStreamMultiCallable): The gRPC method used to
          start the RPC.
      initial_request: The initial request to
          yield. This is useful if an initial request is needed to start the
          stream.
  Returns:
    A bidiRPC instance.
  """
  # pylint: disable=g-import-not-at-top
  from googlecloudsdk.core import gapic_util_internal
  return gapic_util_internal.BidiRpc(client, start_rpc,
                                     initial_request=initial_request)


def MakeRestClient(client_class,
                   credentials,
                   address_override_func=None,
                   mtls_enabled=False):
  """Instantiates a gapic REST client with gcloud defaults and configuration.

  Args:
    client_class: a gapic client class.
    credentials: google.auth.credentials.Credentials, the credentials to use.
    address_override_func: function, function to call to override the client
      host. It takes a single argument which is the original host.
    mtls_enabled: bool, True if mTLS is enabled for this client. _

  Returns:
    A gapic API client.
  """
  transport_class = client_class.get_transport_class('rest')
  address = client_class.DEFAULT_MTLS_ENDPOINT if mtls_enabled else client_class.DEFAULT_ENDPOINT
  if address_override_func:
    address = address_override_func(address)
  return client_class(
      transport=transport_class(host=address, credentials=credentials))


def MakeClient(client_class, credentials, address_override_func=None,
               mtls_enabled=False):
  """Instantiates a gapic API client with gcloud defaults and configuration.

  grpc cannot be packaged like our other Python dependencies, due to platform
  differences and must be installed by the user. googlecloudsdk.core.gapic
  depends on grpc and must be imported lazily here so that this module can be
  imported safely anywhere.

  Args:
    client_class: a gapic client class.
    credentials: google.auth.credentials.Credentials, the credentials to use.
    address_override_func: function, function to call to override the client
        host. It takes a single argument which is the original host.
    mtls_enabled: bool, True if mTLS is enabled for this client.

  Returns:
    A gapic API client.
  """
  # pylint: disable=g-import-not-at-top
  from googlecloudsdk.core import gapic_util_internal

  return client_class(
      transport=gapic_util_internal.MakeTransport(
          client_class, credentials, address_override_func, mtls_enabled))


def MakeAsyncClient(client_class, credentials, address_override_func=None,
                    mtls_enabled=False):
  """Instantiates a gapic API client with gcloud defaults and configuration.

  grpc cannot be packaged like our other Python dependencies, due to platform
  differences and must be installed by the user. googlecloudsdk.core.gapic
  depends on grpc and must be imported lazily here so that this module can be
  imported safely anywhere.

  Args:
    client_class: a gapic client class.
    credentials: google.auth.credentials.Credentials, the credentials to use.
    address_override_func: function, function to call to override the client
        host. It takes a single argument which is the original host.
    mtls_enabled: bool, True if mTLS is enabled for this client.

  Returns:
    A gapic API client.
  """
  # pylint: disable=g-import-not-at-top
  from googlecloudsdk.core import gapic_util_internal

  return client_class(
      transport=gapic_util_internal.MakeAsyncTransport(
          client_class, credentials, address_override_func, mtls_enabled))
