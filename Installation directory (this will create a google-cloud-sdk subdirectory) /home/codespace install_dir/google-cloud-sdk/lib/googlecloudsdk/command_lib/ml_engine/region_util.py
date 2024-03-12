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
"""Utilities for handling region flag."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.ml_engine import constants
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


def _PromptForRegion():
  """Prompt for region from list of available regions.

  Returns:
    The region specified by the user, str
  """

  if not console_io.CanPrompt():
    return None
  all_regions = constants.SUPPORTED_REGIONS_WITH_GLOBAL
  idx = console_io.PromptChoice(
      all_regions, message=('Please specify a region:\n'
                            '(For the global endpoint the region needs to be '
                            'specified as \'global\'.)\n'),
      cancel_option=True)
  region = all_regions[idx]
  log.status.Print(
      'To make this the default region, run '
      '`gcloud config set ai_platform/region {}`.\n'.format(region))
  return region


def GetRegion(args):
  """Gets the region and prompt for region if not provided.

  Note: region can be either `global` or one of supported regions.

    Region is decided in the following order:
  - region argument;
  - ai_platform/region gcloud config;
  - prompt user input.

  Args:
    args: Namespace, The args namespace.

  Returns:
    A str representing region.
  """
  if args.IsSpecified('region'):
    return args.region
  if properties.VALUES.ai_platform.region.IsExplicitlySet():
    return properties.VALUES.ai_platform.region.Get()
  region = _PromptForRegion()
  # In unit test, it's not allowed to prompt for asking the choices. Default to
  # us-central1.
  return region or 'us-central1'
