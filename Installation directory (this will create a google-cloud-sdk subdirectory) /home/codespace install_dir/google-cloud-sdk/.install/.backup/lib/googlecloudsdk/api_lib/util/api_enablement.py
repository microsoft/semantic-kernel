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

"""Utilities for API enablement."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.core.console import console_io


API_ENABLEMENT_REGEX = re.compile(
    '.*Enable it by visiting https://console.(?:cloud|developers).google.com'
    '/apis/api/([^/]+)/overview\\?project=(\\S+) then retry. If you '
    'enabled this API recently, wait a few minutes for the action to propagate'
    ' to our systems and retry.\\w*')


_PROJECTS_NOT_TO_ENABLE = {'google.com:cloudsdktool'}


def ShouldAttemptProjectEnable(project):
  return project not in _PROJECTS_NOT_TO_ENABLE


def GetApiEnablementInfo(status_message):
  """Parses error message for API enablement messages.

  Args:
    status_message: str, error message to parse.

  Returns:
    tuple[str]: The project, service token to be used for prompting to enable
        the API.
  """
  match = API_ENABLEMENT_REGEX.match(status_message)
  if match:
    (project, service_token) = (match.group(2), match.group(1))
    if (project is not None and ShouldAttemptProjectEnable(project)
        and service_token is not None):
      return (project, service_token)
  return None


def PromptToEnableApi(project, service_token, enable_by_default=False):
  """Prompts to enable the API.

  Args:
    project (str): The project that the API is not enabled on.
    service_token (str): The service token of the API to prompt for.
    enable_by_default (bool): The default choice for the enablement prompt.

  Returns:
    bool, whether or not the API was attempted to be enabled
  """
  api_enable_attempted = console_io.PromptContinue(
      default=enable_by_default,
      prompt_string=('API [{}] not enabled on project [{}]. '
                     'Would you like to enable and retry (this will take a '
                     'few minutes)?').format(service_token, project))
  if api_enable_attempted:
    enable_api.EnableService(project, service_token)
  return api_enable_attempted
