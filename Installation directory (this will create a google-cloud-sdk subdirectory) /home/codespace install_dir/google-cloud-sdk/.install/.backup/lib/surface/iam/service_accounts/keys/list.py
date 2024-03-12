# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Command for listing service account keys."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core.util import times


class List(base.ListCommand):
  """List the keys for a service account.

  If the service account does not exist, this command returns a
  `PERMISSION_DENIED` error.
  """

  detailed_help = {
      'EXAMPLES': textwrap.dedent("""
          To list all user-managed keys created before noon on July 19th, 2015
          (to perform key rotation, for example), run:

            $ {command} --iam-account=my-iam-account@my-project.iam.gserviceaccount.com --managed-by=user --created-before=2015-07-19T12:00:00Z
          """),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('--managed-by',
                        choices=['user', 'system', 'any'],
                        default='any',
                        help='The types of keys to list.')

    parser.add_argument(
        '--created-before',
        type=arg_parsers.Datetime.Parse,
        help=('Return only keys created before the specified time. '
              'Common time formats are accepted. This is equivalent to '
              '--filter="validAfterTime<DATE_TIME". See '
              '$ gcloud topic datetimes for information on time formats.'))

    parser.add_argument('--iam-account',
                        required=True,
                        type=iam_util.GetIamAccountFormatValidator(),
                        help='A textual name to display for the account.')
    parser.display_info.AddFormat(iam_util.SERVICE_ACCOUNT_KEY_FORMAT)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    client, messages = util.GetClientAndMessages()
    result = client.projects_serviceAccounts_keys.List(
        messages.IamProjectsServiceAccountsKeysListRequest(
            name=iam_util.EmailToAccountResourceName(args.iam_account),
            keyTypes=iam_util.ManagedByFromString(args.managed_by)))

    keys = result.keys
    if args.created_before:
      ts = args.created_before
      keys = [
          key for key in keys if times.ParseDateTime(key.validAfterTime) < ts
      ]

    return keys
