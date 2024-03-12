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
"""Command to list all billing accounts associated with the active user."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.billing import billing_client
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources


class List(base.ListCommand):
  """List all active billing accounts.

  `{command}` lists all billing accounts and subaccounts owned by the currently
  authenticated user. Subaccounts have a non-empty MASTER_ACCOUNT_ID value.

  ## EXAMPLES

  To list only open billing accounts, run:

      $ {command} --filter=open=true

  ## API REFERENCE

  This command uses the *cloudbilling/v1* API. The full documentation for this
  API can be found at: https://cloud.google.com/billing/v1/getting-started
  """

  @staticmethod
  def ToSelfLink(account):
    return resources.REGISTRY.Parse(
        account.name, collection='cloudbilling.billingAccounts').SelfLink()

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
          table(
            name.basename():label=ACCOUNT_ID,
            displayName:label=NAME,
            open,
            masterBillingAccount.basename():label=MASTER_ACCOUNT_ID
          )
    """)
    parser.display_info.AddUriFunc(List.ToSelfLink)

  def Run(self, args):
    """Run the list command."""
    client = billing_client.AccountsClient()
    return client.List(limit=args.limit)
