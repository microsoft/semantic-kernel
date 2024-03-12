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


class Update(base.Command):
  """Update an SSH public key from an OS Login profile."""

  def __init__(self, *args, **kwargs):
    super(Update, self).__init__(*args, **kwargs)

  @staticmethod
  def Args(parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    additional_help = (' Key value can either be the SSH key or the '
                       'OS Login fingerprint of the key.')
    flags.AddKeyFlags(parser, 'update', additional_help=additional_help)
    flags.AddTtlFlag(parser, required=True)

  def Run(self, args):
    """See ssh_utils.BaseSSHCLICommand.Run."""
    key = flags.GetKeyFromArgs(args)
    oslogin_client = client.OsloginClient(self.ReleaseTrack())
    user_email = (properties.VALUES.auth.impersonate_service_account.Get()
                  or properties.VALUES.core.account.Get())

    keys = oslogin_utils.GetKeyDictionaryFromProfile(user_email, oslogin_client)
    fingerprint = oslogin_utils.FindKeyInKeyList(key, keys)

    expiry = oslogin_utils.ConvertTtlArgToExpiry(args.ttl)

    if fingerprint:
      return oslogin_client.UpdateSshPublicKey(user_email, fingerprint,
                                               keys[fingerprint],
                                               'expirationTimeUsec',
                                               expiration_time=expiry)
    else:
      raise client.OsloginKeyNotFoundError('Cannot find requested SSH key.')


Update.detailed_help = {
    'brief': 'Update an SSH public key in an OS Login profile.',
    'DESCRIPTION': """\
      *{command}* accepts either a string containing an SSH public
      key or a filename for an SSH public key, and updates the key
      in the user's OS Login profile. Currently, only the expiration time,
      ``--ttl'', can be updated.
    """,
    'EXAMPLES': """
      To update the SSH public key found in `/home/user/.ssh/id_rsa.pub` with
      an expiration time of one week from now, run:

        $ {command} --ttl=7d --key-file=/home/user/.ssh/id_rsa.pub

      To update the SSH public key with a fingerprint of
      'e0d96d6fad35a61a0577f467940509b5aa08b6dea8d99456ec19a6e47126bc52' and
      an expiration time of five years from now, run:

        $ {command} --ttl=5y --key='e0d96d6fad35a61a0577f467940509b5aa08b6dea8d99456ec19a6e47126bc52'
    """,
}

