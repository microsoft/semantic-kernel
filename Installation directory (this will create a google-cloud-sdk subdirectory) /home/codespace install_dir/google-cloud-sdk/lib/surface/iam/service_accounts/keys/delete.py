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

"""Command for deleting a service account key."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io


class Delete(base.Command):
  """Delete a service account key.

  If the service account does not exist, this command returns a
  `PERMISSION_DENIED` error.
  """

  detailed_help = {
      'EXAMPLES': textwrap.dedent("""
          To delete a key with ID `b4f1037aeef9ab37deee9` for the service
          account `my-iam-account@my-project.iam.gserviceaccount.com`, run:

            $ {command} b4f1037aeef9ab37deee9 --iam-account=my-iam-account@my-project.iam.gserviceaccount.com
      """),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('--iam-account',
                        required=True,
                        type=iam_util.GetIamAccountFormatValidator(),
                        help="""\
                          The service account from which to delete a key.

                          To list all service accounts in the project, run:

                            $ gcloud iam service-accounts list
                        """)

    parser.add_argument('key',
                        metavar='KEY-ID',
                        help='The key to delete.')

  def Run(self, args):
    key_ref = resources.REGISTRY.Parse(
        args.key,
        collection='iam.projects.serviceAccounts.keys',
        params={
            'serviceAccountsId': args.iam_account,
            'projectsId': '-'
        })
    key = key_ref.keysId
    console_io.PromptContinue(
        message='You are about to delete key [{0}] for service '
        'account [{1}].'.format(args.key, args.iam_account),
        cancel_on_no=True)

    client, messages = util.GetClientAndMessages()
    client.projects_serviceAccounts_keys.Delete(
        messages.IamProjectsServiceAccountsKeysDeleteRequest(
            name=key_ref.RelativeName()))

    log.status.Print('deleted key [{1}] for service account [{0}]'.format(
        args.iam_account, key))
