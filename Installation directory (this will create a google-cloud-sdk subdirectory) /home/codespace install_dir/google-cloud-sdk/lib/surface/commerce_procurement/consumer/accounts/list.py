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
"""Implementation of gcloud Procurement consumer accounts list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.commerce_procurement import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.commerce_procurement import resource_args


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """Returns the List of Account objects resulting from the List API."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: argparse.ArgumentParser to register arguments with.
    """
    resource_args.AddBillingAccountResourceArg(
        parser, 'Parent Cloud Billing account to list accounts.')
    base.FILTER_FLAG.RemoveFromParser(parser)
    base.LIMIT_FLAG.RemoveFromParser(parser)
    base.SORT_BY_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.add_argument(
        '--page-token',
        help=('Token that specifies the next page in the list.'))

  def Run(self, args):
    """Runs the command.

    Args:
      args: The arguments that were provided to this command invocation.

    Returns:
      List of accounts and next token if applicable.
    """
    billing_account_ref = args.CONCEPTS.billing_account.Parse()
    return apis.Accounts.List(billing_account_ref.RelativeName(),
                              args.page_size, args.page_token)
