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
"""'Bare Metal Solution interactive serial console SSH keys remove command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import flags
from googlecloudsdk.core.console import console_io


DETAILED_HELP = {
    'DESCRIPTION':
        """
          Remove an SSH key that is used to access the interactive serial console in Bare Metal Solution given its name.
        """,
    'EXAMPLES':
        """
          To remove an SSH key called ``my-ssh-key'' run:

          $ {command} my-ssh-key
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Remove(base.DeleteCommand):
  """Remove an SSH key that is used to access the interactive serial console in Bare Metal Solution given its name."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddSerialConsoleSshKeyArgToParser(parser, positional=True)

  def Run(self, args):
    ssh_key = args.CONCEPTS.serial_console_ssh_key.Parse()
    message = 'You are about to remove the SSH key [{}]'.format(ssh_key.Name())
    console_io.PromptContinue(message=message, cancel_on_no=True)
    client = BmsClient()
    return client.DeleteSshKey(ssh_key)


Remove.detailed_help = DETAILED_HELP
