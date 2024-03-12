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
from googlecloudsdk.command_lib.oslogin import oslogin_utils
from googlecloudsdk.core import properties


def _TransformExpiry(resource, undefined=None):
  display = None
  value = resource.get('value')
  if value:
    display = oslogin_utils.ConvertUsecToRfc3339(
        value.get('expirationTimeUsec'))

  return display or undefined


class List(base.ListCommand):
  """List the SSH public keys from an OS Login profile."""

  def __init__(self, *args, **kwargs):
    super(List, self).__init__(*args, **kwargs)

  @staticmethod
  def Args(parser):
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat("""
          table(
            key:label=FINGERPRINT,
            expiry():label=EXPIRY
          )
        """)

    parser.display_info.AddTransforms({
        'expiry': _TransformExpiry
    })

  def Run(self, args):
    """See ssh_utils.BaseSSHCLICommand.Run."""

    oslogin_client = client.OsloginClient(self.ReleaseTrack())
    user_email = (properties.VALUES.auth.impersonate_service_account.Get()
                  or properties.VALUES.core.account.Get())

    keys = oslogin_utils.GetKeysFromProfile(user_email, oslogin_client)
    return keys

List.detailed_help = {
    'brief': 'List SSH public keys from an OS Login profile.',
    'DESCRIPTION': """
      *{command}* lists the SSH public keys in an OS Login profile. By
      default, the command only displays the fingerprints and experation
      time for the keys. Additional data can be displayed using the `--format`
      flag.
    """,
    'EXAMPLES': """
      To list the keys in your OS Login profile, run:

        $ {command}

      To show all of the SSH public key information, in YAML format, run:

        $ {command} --format=yaml
    """,
}

