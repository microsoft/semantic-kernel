# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Bare Metal Solution interactive serial console SSH keys add command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import flags
from googlecloudsdk.core.util import files


DETAILED_HELP = {
    'DESCRIPTION':
        """
          Add a public SSH key to the project for accessing the interactive serial console in Bare Metal Solution."
        """,
    'EXAMPLES':
        """
          To add an SSH key called ``my-ssh-key'' in project ``my-project''
          with a public key ``ABC6695''

          $ {command} my-ssh-key --project=my-project --key=ABC6695

          To add an SSH key called ``my-ssh-key'' in project ``my-project''
          with a public key stored in /home/user/.ssh/id_rsa.pub

          $ {command} my-ssh-key --project=my-project --key-file=/home/user/.ssh/id_rsa.pub
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Add(base.CreateCommand):
  """Add a public SSH key to the project for accessing the interactive serial console in Bare Metal Solution."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddSerialConsoleSshKeyArgToParser(parser, positional=True)
    key_arg = parser.add_mutually_exclusive_group(required=True)
    key_arg.add_argument(
        '--key',
        help='The SSH public key to add for the interactive serial console')
    key_arg.add_argument(
        '--key-file',
        help=('The path to a file containing an SSH public key to add for the '
              'interactive serial console'))

  def Run(self, args):
    client = BmsClient()
    if args.key_file:
      public_key = files.ReadFileContents(args.key_file)
    else:
      public_key = args.key
    return client.CreateSshKey(
        resource=args.CONCEPTS.serial_console_ssh_key.Parse(),
        public_key=public_key)


Add.detailed_help = DETAILED_HELP
