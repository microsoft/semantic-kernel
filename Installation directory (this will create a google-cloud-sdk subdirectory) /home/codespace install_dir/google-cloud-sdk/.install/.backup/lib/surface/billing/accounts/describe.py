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

"""Command to show metadata for a specified project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.billing import billing_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.billing import flags
from googlecloudsdk.command_lib.billing import utils


class Describe(base.DescribeCommand):
  """Show metadata for a billing account."""

  detailed_help = {
      'DESCRIPTION': """\
          This command shows info for a billing account, given its ID.

          This call can fail for the following reasons:

          * The account specified does not exist.
          * The active user does not have permission to access the given
            account.
          """,
      'EXAMPLES': """\
          To see details for billing account `0X0X0X-0X0X0X-0X0X0X`, run:

              $ {command} 0X0X0X-0X0X0X-0X0X0X
          """,
      'API REFERENCE': """\
          This command uses the *cloudbilling/v1* API. The full documentation
          for this API can be found at:
          https://cloud.google.com/billing/v1/getting-started
          """
  }

  @staticmethod
  def Args(parser):
    flags.GetAccountIdArgument().AddToParser(parser)

  def Run(self, args):
    client = billing_client.AccountsClient()
    account_ref = utils.ParseAccount(args.account_id)
    return client.Get(account_ref)
