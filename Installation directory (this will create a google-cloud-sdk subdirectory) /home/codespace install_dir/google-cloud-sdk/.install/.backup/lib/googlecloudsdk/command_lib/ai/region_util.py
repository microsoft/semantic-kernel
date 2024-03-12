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

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


def GetPromptForRegionFunc(available_regions=constants.SUPPORTED_REGION):
  """Returns a no argument function that prompts available regions and catches the user selection."""
  return lambda: PromptForRegion(available_regions)


def PromptForRegion(available_regions=constants.SUPPORTED_REGION):
  """Prompt for region from list of available regions.

  This method is referenced by the declaritive iam commands as a fallthrough
  for getting the region.

  Args:
    available_regions: list of the available regions to choose from

  Returns:
    The region specified by the user, str
  """

  if console_io.CanPrompt():
    all_regions = list(available_regions)
    idx = console_io.PromptChoice(
        all_regions, message='Please specify a region:\n', cancel_option=True)
    region = all_regions[idx]
    log.status.Print('To make this the default region, run '
                     '`gcloud config set ai/region {}`.\n'.format(region))
    return region


def PromptForOpRegion():
  """Prompt for region from list of online prediction available regions.

  This method is referenced by the declaritive iam commands as a fallthrough
  for getting the region.

  Returns:
    The region specified by the user, str

  Raises:
    RequiredArgumentException: If can not prompt a console for region.
  """

  if console_io.CanPrompt():
    all_regions = list(constants.SUPPORTED_OP_REGIONS)
    idx = console_io.PromptChoice(
        all_regions, message='Please specify a region:\n', cancel_option=True)
    region = all_regions[idx]
    log.status.Print('To make this the default region, run '
                     '`gcloud config set ai/region {}`.\n'.format(region))
    return region
  raise exceptions.RequiredArgumentException(
      '--region',
      ('Cannot prompt a console for region. Region is required. '
       'Please specify `--region` to select a region.'))


def PromptForDeploymentResourcePoolSupportedRegion():
  """Prompt for region from list of deployment resource pool available regions.

  This method is referenced by the declaritive iam commands as a fallthrough
  for getting the region.

  Returns:
    The region specified by the user, str

  Raises:
    RequiredArgumentException: If can not prompt a console for region.
  """

  if console_io.CanPrompt():
    all_regions = list(constants.SUPPORTED_DEPLOYMENT_RESOURCE_POOL_REGIONS)
    idx = console_io.PromptChoice(
        all_regions, message='Please specify a region:\n', cancel_option=True)
    region = all_regions[idx]
    log.status.Print('To make this the default region, run '
                     '`gcloud config set ai/region {}`.\n'.format(region))
    return region
  raise exceptions.RequiredArgumentException(
      '--region',
      ('Cannot prompt a console for region. Region is required. '
       'Please specify `--region` to select a region.'))


def GetRegion(args, prompt_func=PromptForRegion):
  """Gets the region and prompt for region if not provided.

    Region is decided in the following order:
  - region argument;
  - ai/region gcloud config;
  - prompt user input.

  Args:
    args: Namespace, The args namespace.
    prompt_func: Function, To prompt for region from list of available regions.

  Returns:
    A str representing region.
  """
  if getattr(args, 'region', None):
    return args.region
  if properties.VALUES.ai.region.IsExplicitlySet():
    return properties.VALUES.ai.region.Get()
  region = prompt_func()
  if region:
    return region
  # In unit test, it's not allowed to prompt for asking the choices. Raising the
  # error immediately.
  raise exceptions.RequiredArgumentException('--region', 'Region is required')
