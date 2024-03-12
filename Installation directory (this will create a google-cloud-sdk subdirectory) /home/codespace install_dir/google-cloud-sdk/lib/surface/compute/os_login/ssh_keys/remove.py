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

"""Implements command to remove an SSH public key from the OS Login profile."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.oslogin import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.oslogin import flags
from googlecloudsdk.command_lib.oslogin import oslogin_utils
from googlecloudsdk.core import properties


class Remove(base.Command):
  """Remove an SSH public key from an OS Login profile."""

  def __init__(self, *args, **kwargs):
    super(Remove, self).__init__(*args, **kwargs)

  @staticmethod
  def Args(parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    additional_help = (' Key value can either be the SSH key or the '
                       'OS Login fingerprint of the key.')
    flags.AddKeyFlags(parser, 'remove from', additional_help=additional_help)

  def Run(self, args):
    """See ssh_utils.BaseSSHCLICommand.Run."""
    key = flags.GetKeyFromArgs(args)
    oslogin_client = client.OsloginClient(self.ReleaseTrack())
    user_email = (properties.VALUES.auth.impersonate_service_account.Get()
                  or properties.VALUES.core.account.Get())

    keys = oslogin_utils.GetKeyDictionaryFromProfile(user_email, oslogin_client)
    fingerprint = oslogin_utils.FindKeyInKeyList(key, keys)
    if fingerprint:
      return oslogin_client.DeleteSshPublicKey(user_email, fingerprint)
    else:
      raise client.OsloginKeyNotFoundError('Cannot find requested SSH key.')


Remove.detailed_help = {
    'brief': 'Remove an SSH public key from an OS Login profile.',
    'DESCRIPTION': """\
      *{command}* accepts either a string containing an SSH public
      key or a filename for an SSH public key and removes that key from the
      user's OS Login profile. The key value used can either be the
      full SSH key or the OS Login fingerprint for that key.
    """,
    'EXAMPLES': """
      To remove the key that is stored in `/home/user/.ssh/id_rsa.pub`, run:

        $ {command} --key-file=/home/user/.ssh/id_rsa.pub

      To remove the key with fingerprint
      'e0d96d6fad35a61a0577f467940509b5aa08b6dea8d99456ec19a6e47126bc52', run:

        $ {command} --key='e0d96d6fad35a61a0577f467940509b5aa08b6dea8d99456ec19a6e47126bc52'

      To remove the SSH public key
      'AAAAB3NzaC1yc2EAAAADAQABAAAB...ZrPg+DZJIwPab2wPlveLh+ut1Lxs5QTR/9QfEa7', run:

        $ {command} --key='AAAAB3NzaC1yc2EAAAADAQABAAAB...ZrPg+DZJIwPab2wPlveLh+ut1Lxs5QTR/9QfEa7'
    """,
}

