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

"""Command for signing blobs for service accounts."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


class SignBlob(base.Command):
  """Sign a blob with a managed service account key.

  This command signs a file containing arbitrary binary data (a blob) using a
  system-managed service account key.

  If the service account does not exist, this command returns a
  `PERMISSION_DENIED` error.
  """

  detailed_help = {
      'EXAMPLES': textwrap.dedent("""
          To sign a blob file with a system-managed service account key,
          run:

            $ {command} --iam-account=my-iam-account@my-project.iam.gserviceaccount.com input.bin output.bin
          """),
      'SEE ALSO': textwrap.dedent("""
        For more information on how this command ties into the wider cloud
        infrastructure, please see
        [](https://cloud.google.com/appengine/docs/java/appidentity/)
        """),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('--iam-account',
                        required=True,
                        help='The service account to sign as.')

    parser.add_argument('input',
                        metavar='INPUT-FILE',
                        help='A path to the blob file to be signed.')

    parser.add_argument('output',
                        metavar='OUTPUT-FILE',
                        help='A path the resulting signed blob will be '
                        'written to.')

  def Run(self, args):
    client, messages = util.GetIamCredentialsClientAndMessages()
    response = client.projects_serviceAccounts.SignBlob(
        messages.IamcredentialsProjectsServiceAccountsSignBlobRequest(
            name=iam_util.EmailToAccountResourceName(args.iam_account),
            signBlobRequest=messages.SignBlobRequest(
                payload=files.ReadBinaryFileContents(args.input))))

    log.WriteToFileOrStdout(
        args.output, content=response.signedBlob, binary=True)
    log.status.Print(
        'signed blob [{0}] as [{1}] for [{2}] using key [{3}]'.format(
            args.input, args.output, args.iam_account, response.keyId))
