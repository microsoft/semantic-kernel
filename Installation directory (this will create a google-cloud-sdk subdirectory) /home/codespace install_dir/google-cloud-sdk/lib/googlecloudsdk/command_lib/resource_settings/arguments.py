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
"""Utilities for defining Resource Settings arguments on a parser."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.resource_manager import completers
from googlecloudsdk.command_lib.util.args import common_args


def AddSettingsNameArgToParser(parser):
  """Adds argument for the settings name to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      'setting_name',
      metavar='SETTING_NAME',
      help=(
          'Name of the resource settings. The list of available settings'
          ' can be fetched using the list command: \n'
          ' $ gcloud resource-settings list'
      ))


# Mirror the implementation in command_lib.org_policies.arguments
def AddResourceFlagsToParser(parser):
  """Adds flags for the resource ID to the parser.

  Adds --organization, --folder, and --project flags to the parser. The flags
  are added as a required group with a mutex condition, which ensures that the
  user passes in exactly one of the flags.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  resource_group = parser.add_mutually_exclusive_group(
      required=True,
      help='Resource that is associated with the resource settings.')
  resource_group.add_argument(
      '--organization',
      metavar='ORGANIZATION_ID',
      completer=completers.OrganizationCompleter,
      help='Organization ID.')
  resource_group.add_argument(
      '--folder', metavar='FOLDER_ID', help='Folder ID.')
  common_args.ProjectArgument(
      help_text_to_overwrite='Project ID.').AddToParser(resource_group)
