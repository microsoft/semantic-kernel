# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Boto auth plugin for OAuth2.0 for Google Cloud Storage."""

from __future__ import absolute_import

import boto.auth_handler

from gcs_oauth2_boto_plugin import oauth2_client
from gcs_oauth2_boto_plugin import oauth2_helper

IS_SERVICE_ACCOUNT = False


class OAuth2Auth(boto.auth_handler.AuthHandler):
  """AuthHandler for working with OAuth2 user account credentials."""

  capability = ['google-oauth2', 's3']

  def __init__(self, path, config, provider):
    self.oauth2_client = None
    if provider.name == 'google':
      if config.has_option('Credentials', 'gs_oauth2_refresh_token'):
        self.oauth2_client = oauth2_helper.OAuth2ClientFromBotoConfig(config)
      elif config.has_option('GoogleCompute', 'service_account'):
        self.oauth2_client = oauth2_client.CreateOAuth2GCEClient()
    if not self.oauth2_client:
      raise boto.auth_handler.NotReadyToAuthenticate()

  def add_auth(self, http_request):
    http_request.headers['Authorization'] = (
        self.oauth2_client.GetAuthorizationHeader())


class OAuth2ServiceAccountAuth(boto.auth_handler.AuthHandler):
  """AuthHandler for working with OAuth2 service account credentials."""

  capability = ['google-oauth2', 's3']

  def __init__(self, path, config, provider):
    if (provider.name == 'google'
        and config.has_option('Credentials', 'gs_service_key_file')):
      self.oauth2_client = oauth2_helper.OAuth2ClientFromBotoConfig(
          config, cred_type=oauth2_client.CredTypes.OAUTH2_SERVICE_ACCOUNT)

      # If we make it to this point, then we will later attempt to authenticate
      # as a service account based on how the boto auth plugins work. This is
      # global so that command.py can access this value once it's set.
      # TODO: replace this approach with a way to get the current plugin
      # from boto so that we don't have to have global variables.
      global IS_SERVICE_ACCOUNT
      IS_SERVICE_ACCOUNT = True
    else:
      raise boto.auth_handler.NotReadyToAuthenticate()

  def add_auth(self, http_request):
    http_request.headers['Authorization'] = (
        self.oauth2_client.GetAuthorizationHeader())

