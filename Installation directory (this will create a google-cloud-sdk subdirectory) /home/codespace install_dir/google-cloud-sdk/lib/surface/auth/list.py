# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""Command to list the available accounts."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import store as c_store


class List(base.ListCommand):
  # pylint: disable=g-docstring-has-escape
  """Lists credentialed accounts.

  Lists accounts whose credentials have been obtained using `gcloud init`,
  `gcloud auth login` and `gcloud auth activate-service-account`, and shows
  which account is active. The active account is used by gcloud and other Google
  Cloud CLI tools to access Google Cloud Platform. While there is no limit on
  the number of accounts with stored credentials, there is only one active
  account.

  ## EXAMPLES

  To set an existing account to be the current active account, run:

    $ gcloud config set core/account your-email-account@gmail.com

  If you don't have an existing account, create one using:

    $ gcloud init

  To list the active account name:

    $ gcloud auth list --filter=status:ACTIVE --format="value(account)"

  To list the inactive account names with prefix `test`:

    $ gcloud auth list --filter="-status:ACTIVE account:test*" \
--format="value(account)"
  """

  @staticmethod
  def Args(parser):
    base.URI_FLAG.RemoveFromParser(parser)
    parser.add_argument(
        '--filter-account',
        help="""\
        List only credentials for one account. Use
        --filter="account~_PATTERN_" to select accounts that match
        _PATTERN_.""")

  def Run(self, args):
    """Run the 'gcloud auth list' command to list the accounts.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation (i.e. group and command arguments combined).

    Returns:
      [googlecloudsdk.core.credentials.store.AcctInfo] or
        [googlecloudsdk.core.credentials.store.AcctInfoWithUniverseDomain]: A
        list of AcctInfo objects if all accounts are from googleapis.com,
        otherwise a list of AcctInfoWithUniverseDomain objects.
    """
    account_info_list = c_store.AllAccountsWithUniverseDomains()
    if args.filter_account:
      account_info_list = [
          account_info
          for account_info in account_info_list
          if account_info.account == args.filter_account
      ]

    # If any of the accounts are non-GDU, then we should output the universe
    # domain column.
    show_universe_domain = False
    for account_info in account_info_list:
      if (
          account_info.universe_domain
          != properties.VALUES.core.universe_domain.default
      ):
        show_universe_domain = True
        break

    if show_universe_domain:
      # Use the format with UNIVERSE_DOMAIN column.
      args.GetDisplayInfo().AddFormat(
          c_store.ACCOUNT_TABLE_WITH_UNIVERSE_DOMAIN_FORMAT
      )
    else:
      # Convert to AcctInfo list, which doesn't contain universe domain info.
      account_info_list = [
          c_store.AcctInfo(account_info.account, account_info.status)
          for account_info in account_info_list
      ]
      # Use the format without UNIVERSE_DOMAIN column.
      args.GetDisplayInfo().AddFormat(c_store.ACCOUNT_TABLE_FORMAT)

    return account_info_list

  def Epilog(self, resources_were_displayed):
    if resources_were_displayed:
      log.status.Print("""
To set the active account, run:
    $ gcloud config set account `ACCOUNT`
""")
    else:
      log.status.Print("""
No credentialed accounts.

To login, run:
  $ gcloud auth login `ACCOUNT`
""")
