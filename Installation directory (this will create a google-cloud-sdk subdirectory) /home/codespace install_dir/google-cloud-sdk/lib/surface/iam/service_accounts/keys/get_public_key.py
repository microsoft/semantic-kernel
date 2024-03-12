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

"""Command for listing service account keys."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class GetPublicKey(base.Command):
  """Get the public key for a service account key pair.

  Get the public key for a service account key pair in pem or raw format.
  """

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""
          To get the public key for some key ID for some service account
          (to validate a blob or JWT signature, for example), run:

            $ {command} keyid --output-file=key-file --iam-account=my-iam-account@my-project.iam.gserviceaccount.com
          """),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('key', metavar='KEY-ID', help='The key to get.')

    parser.add_argument(
        '--output-file',
        required=True,
        help='The output file to write the public key.')

    parser.add_argument(
        '--iam-account',
        required=True,
        type=iam_util.GetIamAccountFormatValidator(),
        help='A textual name to display for the account.')

    parser.add_argument(
        '--type',
        choices=['pem', 'raw'],
        default='pem',
        help='The type of the public key to get.')
    parser.display_info.AddFormat(iam_util.SERVICE_ACCOUNT_KEY_FORMAT)

  def Run(self, args):
    key_ref = resources.REGISTRY.Parse(
        args.key,
        collection='iam.projects.serviceAccounts.keys',
        params={
            'serviceAccountsId': args.iam_account,
            'projectsId': '-'
        })
    key = key_ref.keysId

    client, messages = util.GetClientAndMessages()
    result = client.projects_serviceAccounts_keys.Get(
        messages.IamProjectsServiceAccountsKeysGetRequest(
            name=key_ref.RelativeName(),
            publicKeyType=iam_util.PublicKeyTypeFromString(args.type)))
    log.WriteToFileOrStdout(
        args.output_file, content=result.publicKeyData, binary=True)

    log.status.Print('written key [{0}] for [{2}] as [{1}]'.format(
        key, args.output_file, args.iam_account))
