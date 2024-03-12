# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Flag definitions for gcloud billing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import completers as resource_manager_completers
from googlecloudsdk.command_lib.util import completers


class BillingAccountsCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(BillingAccountsCompleter, self).__init__(
        collection='cloudbilling.billingAccounts',
        list_command='billing accounts list --uri',
        **kwargs)


def GetOldAccountIdArgument(positional=True):
  metavar = 'ACCOUNT_ID'
  help_ = (
      'Specify a billing account ID. Billing account '
      'IDs are of the form `0X0X0X-0X0X0X-0X0X0X`. To see available IDs, run '
      '`$ gcloud billing accounts list`.'
  )
  if positional:
    # For a positional arg, the action always runs; we want to only show a
    # message if a value is specified.
    return base.Argument(
        'id',
        nargs='?',
        metavar=metavar,
        completer=BillingAccountsCompleter,
        action=actions.DeprecationAction(
            'ACCOUNT_ID',
            show_message=lambda x: x is not None,  # See note above
            removed=False,
            warn=('The `{flag_name}` argument has been renamed '
                  '`--billing-account`.')),
        help=help_)
  else:
    return base.Argument(
        '--account-id',
        dest='billing_account',
        metavar=metavar,
        completer=BillingAccountsCompleter,
        action=actions.DeprecationAction(
            '--account-id',
            removed=False,
            warn='The `{flag_name}` flag has been renamed `--billing-account`.'
        ),
        help=help_)


def GetAccountIdArgument(positional=True, required=False):
  metavar = 'ACCOUNT_ID'
  help_ = (
      'Specify a billing account ID. Billing account IDs are of the form '
      '`0X0X0X-0X0X0X-0X0X0X`. To see available IDs, run '
      '`$ gcloud billing accounts list`.')
  if positional:
    return base.Argument(
        'account_id',
        metavar=metavar,
        completer=BillingAccountsCompleter,
        help=help_)
  else:
    return base.Argument(
        '--billing-account',
        metavar=metavar,
        required=required,
        completer=BillingAccountsCompleter,
        help=help_)


def GetProjectIdArgument():
  return base.Argument(
      'project_id',
      completer=resource_manager_completers.ProjectCompleter,
      help='Specify a project id.'
  )
