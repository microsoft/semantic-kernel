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
"""Flags and helpers for the Cloud Quotas related commands."""

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import completers


def AddConsumerFlags(parser, help_string):
  """Parse consumer flag in the command.

  Args:
    parser: An argparse parser that you can use to add arguments that go on the
      command line after this command. Positional arguments are allowed.
    help_string: text that is prepended to help for each argument.
  """
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument(
      '--project',
      metavar='PROJECT_ID_OR_NUMBER',
      help='Project of the {0}.'.format(help_string),
  )

  group.add_argument(
      '--folder',
      metavar='FOLDER_ID',
      help='Folder of the {0}.'.format(help_string),
  )

  group.add_argument(
      '--organization',
      completer=completers.OrganizationCompleter,
      metavar='ORGANIZATION_ID',
      help='Organization of the {0}.'.format(help_string),
  )


def QuotaId(
    positional=True,
    text='ID of the quota, which is unique within the service.',
):
  if positional:
    return base.Argument('QUOTA_ID', type=str, help=text)
  else:
    return base.Argument('--quota-id', type=str, required=True, help=text)


def PreferrenceId(
    positional=True,
    text='ID of the Quota Preference object, must be unique under its parent.',
):
  if positional:
    return base.Argument('PREFERENCE_ID', type=str, help=text)
  else:
    return base.Argument('--preference-id', type=str, required=False, help=text)


def Service():
  return base.Argument(
      '--service',
      required=True,
      help='Name of the service in which the quota is defined.',
  )


def PreferredValue():
  return base.Argument(
      '--preferred-value',
      required=True,
      help=(
          'Preferred value. Must be greater than or equal to -1. If set to'
          ' -1, it means the value is "unlimited".'
      ),
  )


def Dimensions():
  return base.Argument(
      '--dimensions',
      type=arg_parsers.ArgDict(),
      metavar='KEY=VALUE',
      action=arg_parsers.UpdateAction,
      help='Dimensions of the quota.',
  )


def AllowsQuotaDecreaseBelowUsage():
  return base.Argument(
      '--allow-quota-decrease-below-usage',
      action='store_true',
      help=(
          'If specified, allows consumers to reduce their effective limit below'
          ' their quota usage. Default is false.'
      ),
  )


def AllowHighPercentageQuotaDecrease():
  return base.Argument(
      '--allow-high-percentage-quota-decrease',
      action='store_true',
      help=(
          'If specified, allows consumers to reduce their effective limit by'
          ' more than 10 percent. Default is false.'
      ),
  )


def Email():
  return base.Argument(
      '--email',
      help=(
          'An optional email address that can be used for quota related'
          ' communication between the Google Cloud and the user in case the'
          ' Google Cloud needs further information to make a decision on'
          ' whether the user preferred quota can be granted. The Google account'
          ' for the email address must have quota update permission for the'
          ' project, folder or organization this quota preference is for. If no'
          ' contact email address is provided, or the provided email address'
          ' does not have the required quota update permission, the quota'
          ' preference request will be denied in case further information is'
          ' required to make a decision.'
      ),
  )


def Justification():
  return base.Argument(
      '--justification',
      help='A short statement to justify quota increase requests.',
  )


def AllowMissing():
  return base.Argument(
      '--allow-missing',
      action='store_true',
      help=(
          'If specified and the quota preference is not found, a new one will'
          ' be created. Default is false.'
      ),
  )


def ValidateOnly():
  return base.Argument(
      '--validate-only',
      action='store_true',
      help=(
          'If specified, only validates the request, but does not actually'
          ' update. Note that a request being valid does not mean that the'
          ' request is guaranteed to be fulfilled. Default is false.'
      ),
  )


def PageToken():
  return base.Argument(
      '--page-token',
      default=None,
      help=(
          'A token identifying a page of results the server should return.'
          ' Default is none.'
      ),
  )


def ReconcilingOnly():
  return base.Argument(
      '--reconciling-only',
      action='store_true',
      help=(
          'If specified, only displays quota preferences in unresolved states.'
          ' Default is false.'
      ),
  )
