# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command to list all Project IDs linked with a billing account."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.billing import billing_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.billing import flags
from googlecloudsdk.command_lib.billing import utils


class List(base.ListCommand):
  """List all active projects associated with the specified billing account.

  *{command}* ACCOUNT_ID -- lists all active projects, for the specified
  billing account id.

  ## EXAMPLES

  To list projects linked to billing account `0X0X0X-0X0X0X-0X0X0X`, run:

      $ {command} 0X0X0X-0X0X0X-0X0X0X
  """

  @staticmethod
  def Args(parser):
    account_args_group = parser.add_mutually_exclusive_group(required=True)
    flags.GetOldAccountIdArgument().AddToParser(account_args_group)
    flags.GetAccountIdArgument(positional=False).AddToParser(account_args_group)

    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat("""
          table(
            projectId,
            billingAccountName.basename():label=BILLING_ACCOUNT_ID,
            billingEnabled
          )
    """)
    # No resource URIs.
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    """Run the list command."""
    client = billing_client.ProjectsClient()
    account_ref = utils.ParseAccount(args.id or args.billing_account)
    return client.List(account_ref, limit=args.limit)
