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
"""Calls cloud run service of a Google Cloud Function."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.functions.v2 import util as v2_api_util
from googlecloudsdk.command_lib.config import config_helper
from googlecloudsdk.command_lib.functions import call_util
from googlecloudsdk.core.credentials import store


def GenerateIdToken():
  """Generate an expiring Google-signed OAuth2 identity token.

  Returns:
    token: str, expiring Google-signed OAuth2 identity token
  """

  # str | None, account is either a user account or google service account.
  account = None

  # oauth2client.client.OAuth2Credentials |
  # core.credentials.google_auth_credentials.Credentials
  cred = store.Load(
      # if account is None, implicitly retrieves properties.VALUES.core.account
      account,
      allow_account_impersonation=True,
      use_google_auth=True)

  # sets token on property of either
  # credentials.token_response['id_token'] or
  # credentials.id_tokenb64
  store.Refresh(cred)

  credential = config_helper.Credential(cred)

  # str, Expiring Google-signed OAuth2 identity token
  token = credential.id_token

  return token


def Run(args, release_track):
  """Call a v2 Google Cloud Function."""
  v2_client = v2_api_util.GetClientInstance(release_track=release_track)
  v2_messages = v2_client.MESSAGES_MODULE

  function_ref = args.CONCEPTS.name.Parse()

  # cloudfunctions_v2alpha_messages.Function
  function = v2_client.projects_locations_functions.Get(
      v2_messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
          name=function_ref.RelativeName()))

  call_util.UpdateHttpTimeout(args, function, 'v2', release_track)

  cloud_run_uri = function.serviceConfig.uri
  token = GenerateIdToken()
  auth_header = {'Authorization': 'Bearer {}'.format(token)}

  return call_util.MakePostRequest(
      cloud_run_uri, args, extra_headers=auth_header)
