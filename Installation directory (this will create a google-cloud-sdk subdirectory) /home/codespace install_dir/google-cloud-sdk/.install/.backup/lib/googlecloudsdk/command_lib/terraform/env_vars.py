# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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

"""Extracts environment vars required for binary operations.

Binary operations like terraform tools requires extracting env vars. This file
exposes function that can be reused for extracting common env vars.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os.path

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials.store import GetFreshAccessToken
from googlecloudsdk.core.util import encoding


class EnvironmentVariables:
  """Extracts env vars.
  """

  def __init__(self):
    self._ExtractEnvironmentVariables()

  def _ExtractEnvironmentVariables(self):
    """ExtractEnvironmentVariables can be used to extract environment variables required for binary operations.
    """
    self.env_vars = {
        'GOOGLE_OAUTH_ACCESS_TOKEN':
            GetFreshAccessToken(account=properties.VALUES.core.account.Get()),
        'USE_STRUCTURED_LOGGING':
            'true',
    }

    proxy_env_names = [
        'HTTP_PROXY', 'http_proxy', 'HTTPS_PROXY', 'https_proxy', 'NO_PROXY',
        'no_proxy'
    ]

    # env names and orders are from
    # https://registry.terraform.io/providers/hashicorp/google/latest/docs/guides/provider_reference#full-reference
    project_env_names = [
        'GOOGLE_PROJECT',
        'GOOGLE_CLOUD_PROJECT',
        'GCLOUD_PROJECT',
    ]

    for env_key, env_val in os.environ.items():
      if env_key in proxy_env_names:
        self.env_vars[env_key] = env_val

    # project flag and CLOUDSDK_CORE_PROJECT env are linked with core property
    self.project = properties.VALUES.core.project.Get()
    if self.project:
      log.debug('Setting project to {} from properties'.format(self.project))
    else:
      for env_key in project_env_names:
        self.project = encoding.GetEncodedValue(os.environ, env_key)
        if self.project:
          log.debug(
              'Setting project to {} from env {}'.format(self.project, env_key)
          )
          break
      if not self.project:
        raise exceptions.Error(
            'Failed to retrieve the project id. Please specify the project id'
            ' using --project flag.'
        )
