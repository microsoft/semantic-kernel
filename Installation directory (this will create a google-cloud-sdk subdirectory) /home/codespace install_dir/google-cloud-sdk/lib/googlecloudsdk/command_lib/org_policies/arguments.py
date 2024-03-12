# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Utilities for defining Org Policy arguments on a parser."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.resource_manager import completers
from googlecloudsdk.command_lib.util.args import common_args


def AddConstraintArgToParser(parser):
  """Adds argument for the constraint name to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      'constraint',
      metavar='CONSTRAINT',
      help=(
          'Name of the org policy constraint. The list of available constraints'
          ' can be found here: '
          'https://cloud.google.com/resource-manager/docs/organization-policy/org-policy-constraints'
      ))


def AddCustomConstraintArgToParser(parser):
  """Adds argument for the custom constraint name to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      'custom_constraint',
      metavar='CUSTOM_CONSTRAINT',
      help=('Name of the custom constraint.'))


def AddValueArgToParser(parser):
  """Adds argument for a list of values to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      'value',
      metavar='VALUE',
      nargs='*',
      help=(
          'Values to add to the policy. The set of valid values corresponding '
          'to the different constraints are covered here: '
          'https://cloud.google.com/resource-manager/docs/organization-policy/org-policy-constraints'
      ))


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
      help='Resource that is associated with the organization policy.')
  resource_group.add_argument(
      '--organization',
      metavar='ORGANIZATION_ID',
      completer=completers.OrganizationCompleter,
      help='Organization ID.')
  resource_group.add_argument(
      '--folder', metavar='FOLDER_ID', help='Folder ID.')
  common_args.ProjectArgument(
      help_text_to_overwrite='Project ID.').AddToParser(resource_group)


def AddOrganizationResourceFlagsToParser(parser):
  """Adds flag for the organization ID to the parser.

  Adds --organization flag to the parser. The flag
  is added as required.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      '--organization',
      metavar='ORGANIZATION_ID',
      required=True,
      help=('Organization ID.'))


def AddUpdateMaskArgToParser(parser):
  """Adds argument for the update-mask flag to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      '--update-mask',
      metavar='UPDATE_MASK',
      help=('Field mask used to specify the fields to be overwritten in the '
            'policy by the set. The fields specified in the update_mask are '
            'relative to the policy, not the full request. The update-mask '
            'flag can be empty, or have values `policy.spec`, '
            '`policy.dry_run_spec` or `*`. If the policy does not contain '
            'the dry_run_spec and update-mask flag is not provided, '
            'then it defaults to `policy.spec`.'))
