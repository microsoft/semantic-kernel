# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Supporting libraries for the config-helper command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import config
from googlecloudsdk.core.credentials import creds as c_creds


class ConfigHelperResult(object):
  """The result of the gcloud config config-helper command that gets serialzied.

  Attributes:
    credential: Credential, The OAuth2 credential information.
    configuration: Configuration, Local Cloud SDK configuration information.
    sentinels: Sentinels, Paths to various sentinel files.
  """

  def __init__(self, credential, active_configuration, properties):
    self.credential = Credential(credential)
    self.configuration = Configuration(active_configuration, properties)
    self.sentinels = Sentinels(config.Paths().config_sentinel_file)


class Credential(object):
  """Holder for credential data.

  Attributes:
    access_token: str, The current OAuth2 access token.
    token_expiry: str, The expiry time in UTC as an RFC3339 formatted string.
    id_token: str, The current OAuth2 identity token, if present.
  """
  _EXPIRY_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

  def __init__(self, cred):
    if c_creds.IsOauth2ClientCredentials(cred):
      self.access_token = cred.access_token
      expiry = getattr(cred, 'token_expiry', None)
    else:
      self.access_token = cred.token
      expiry = getattr(cred, 'expiry', None)

    self.token_expiry = (
        expiry.strftime(Credential._EXPIRY_FORMAT) if expiry else None)

    # The cache blanks the token_response field, so if it's present that
    # indicates there's either no cache entry, or we just refreshed tokens.
    # Either way, the response is fresher.
    token_response = getattr(cred, 'token_response', None)

    if token_response:
      id_token = token_response.get('id_token', None)
    else:
      id_token = getattr(cred, 'id_tokenb64', None)

    self.id_token = id_token


class Configuration(object):
  """Holder for configuration data.

  Attributes:
    active_configuration: str, The name of the active configuration.
    properties: {str: {str: str}}, A dict of section names to properties and
      values.
  """

  def __init__(self, active_configuration, properties):
    self.active_configuration = active_configuration
    self.properties = properties


class Sentinels(object):
  """Holder for sentinel file locations.

  Attributes:
    config_sentinel: str, The path to the sentinel that indicates changes were
      made to properties or the active configuration.
  """

  def __init__(self, config_sentinel):
    self.config_sentinel = config_sentinel
