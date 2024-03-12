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
"""Base ResourceBuilder for Cloud Run Integrations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.command_lib.run.integrations.typekits import base


class RedisTypeKit(base.TypeKit):
  """The redis integration typekit."""

  def GetCreateSelectors(self, integration_name):
    """Returns create selectors for given integration and service.

    Args:
      integration_name: str, name of integration.

    Returns:
      list of dict typed names.
    """
    selectors = super(RedisTypeKit, self).GetCreateSelectors(integration_name)
    selectors.append({'type': 'vpc', 'name': '*'})
    return selectors

  def GetDeleteSelectors(self, integration_name):
    """Selectors for deleting the integration.

    Args:
      integration_name: str, name of integration.

    Returns:
      list of dict typed names.
    """
    selectors = super(RedisTypeKit, self).GetDeleteSelectors(integration_name)
    selectors.append({'type': 'vpc', 'name': '*'})
    return selectors
