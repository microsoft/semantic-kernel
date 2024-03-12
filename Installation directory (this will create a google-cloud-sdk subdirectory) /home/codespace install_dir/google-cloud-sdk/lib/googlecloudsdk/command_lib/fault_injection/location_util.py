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
"""Location util for Fault Injection Cloud SDK."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.fault_injection import constants
from googlecloudsdk.core.console import console_io


def PromptForLocation(available_locations=constants.SUPPORTED_LOCATION):
  """Prompt for Location from list of available locations.

  This method is referenced by the declaritive iam commands as a fallthrough
  for getting the location.

  Args:
    available_locations: list of the available locations to choose from

  Returns:
    The location specified by the user, str
  """

  if console_io.CanPrompt():
    all_locations = [available_locations]
    idx = console_io.PromptChoice(
        all_locations,
        message='Please specify a Location:\n', cancel_option=True
    )
    location = all_locations[idx]
    return location
