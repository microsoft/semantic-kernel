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

"""Support library for the login-config auth commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from google.auth import external_account_authorized_user
from googlecloudsdk.api_lib.auth import util as auth_util
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import config
from googlecloudsdk.core import properties

CLOUDSDK_AUTH_LOGIN_CONFIG_FILE = 'CLOUDSDK_AUTH_LOGIN_CONFIG_FILE'


def DoWorkforceHeadfulLogin(login_config_file, is_adc=False, **kwargs):
  """DoWorkforceHeadfulLogin attempts to log in with appropriate login configuration.

  It will return the account and credentials of the user if it succeeds

  Args:
    login_config_file (str): The path to the workforce headful login
      configuration file.
    is_adc (str): Whether the flow is initiated via application-default login.
    **kwargs (Mapping): Extra Arguments to pass to the method creating the flow.

  Returns:
    (google.auth.credentials.Credentials): The account and
    credentials of the user who logged in
  """
  login_config_data = auth_util.GetCredentialsConfigFromFile(login_config_file)
  if login_config_data.get(
      'type', None) != 'external_account_authorized_user_login_config':
    raise calliope_exceptions.BadFileException(
        'Only external account authorized user login config JSON credential '
        'file types are supported for Workforce Identity Federation login '
        'configurations.')

  client_config = _MakeThirdPartyClientConfig(login_config_data, is_adc)
  audience = login_config_data['audience']
  path_start = audience.find('/locations/')
  provider_name = None

  if path_start != -1:
    # If the audience is "//iam.googleapis.com/locations/global/workforcePools/
    # <workforce-pool-id>/providers/<provider-id>",
    # Then the provider_name is "locations/global/workforcePools/
    # <workforce-pool-id>/providers/<provider-id>".
    provider_name = audience[path_start + 1:]

  creds = auth_util.DoInstalledAppBrowserFlowGoogleAuth(
      config.CLOUDSDK_EXTERNAL_ACCOUNT_SCOPES,
      client_config=client_config,
      query_params={
          # For 3PI, we pass the provider_name
          # to be included in the query params.
          'provider_name': provider_name
      },
      **kwargs)
  if isinstance(creds, external_account_authorized_user.Credentials):
    universe_domain_from_config = login_config_data.get('universe_domain', None)
    # TODO: b/314826985 - Use the public with_universe_domain method instead of
    # _universe_domain once google-auth lib is updated in gcloud.
    creds._universe_domain = (  # pylint: disable=protected-access
        universe_domain_from_config
        or properties.VALUES.core.universe_domain.Get()
    )

  # TODO(b/260741921): Once google-oauthlib sets the audience, remove this.
  if not creds.audience:
    creds._audience = audience  # pylint: disable=protected-access
  return creds


def GetWorkforceLoginConfig():
  """_GetWorkforceLoginConfig gets the correct Credential Configuration.

  It will first check from the supplied argument if present, then from an
  environment variable if present, and finally from the project settings, if
  present.

  Returns:
    Optional[str]: The name of the Credential Configuration File to use.
  """

  # PropertyFile.Get() first checks any StoredProperty (which we do during
  # parsing), then the environment variable, then the project settings.
  return properties.VALUES.auth.login_config_file.Get()


def _MakeThirdPartyClientConfig(login_config_data, is_adc):
  client_id = config.CLOUDSDK_CLIENT_ID
  client_secret = config.CLOUDSDK_CLIENT_NOTSOSECRET
  return {
      'installed': {
          'client_id': client_id,
          'client_secret': client_secret,
          'auth_uri': login_config_data['auth_url'],
          'token_uri': login_config_data['token_url'],
          'token_info_url': login_config_data['token_info_url'],
          # TODO(b/260741921): Have google-oauthlib use this
          # audience field during credential creation.
          'audience': login_config_data['audience'],
          '3pi': True,
          'is_adc': is_adc,
      }
  }
