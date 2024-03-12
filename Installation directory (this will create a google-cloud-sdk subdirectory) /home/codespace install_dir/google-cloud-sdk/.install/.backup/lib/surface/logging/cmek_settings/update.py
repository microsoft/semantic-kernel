# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""'logging cmek-settings update' command."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import resource_args as kms_resource_args
from googlecloudsdk.command_lib.resource_manager import completers


class Update(base.Command):
  # pylint: disable=line-too-long
  """Update the CMEK settings for the Cloud Logging Logs Router.

  Use this command to update the *--kms-key-name* associated with the
  Cloud Logging Logs Router.

  The Cloud KMS key must already exist and Cloud Logging must have
  permission to access it.

  Customer-managed encryption keys (CMEK) for the Logs Router can currently
  only be configured at the organization-level and will apply to all projects
  in the organization.

  ## EXAMPLES

  To enable CMEK for the Logs Router for an organization, run:

    $ {command} --organization=[ORGANIZATION_ID]
    --kms-key-name='projects/my-project/locations/my-location/keyRings/my-keyring/cryptoKeys/key'

  To disable CMEK for the Logs Router for an organization, run:

    $ {command} --organization=[ORGANIZATION_ID] --clear-kms-key
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        '--organization',
        required=True,
        metavar='ORGANIZATION_ID',
        completer=completers.OrganizationCompleter,
        help='Organization to update Logs Router CMEK settings for.')

    group = parser.add_mutually_exclusive_group(required=True)

    kms_resource_args.AddKmsKeyResourceArg(
        group,
        resource='logs being processed by the Cloud Logging Logs Router',
        permission_info=('The Cloud KMS CryptoKey Encrypter/Decryper role must '
                         'be assigned to the Cloud Logging Logs Router service '
                         'account'),
        name='--kms-key-name')

    group.add_argument(
        '--clear-kms-key',
        action='store_true',
        help=('Disable CMEK for the Logs Router by clearing out Cloud KMS '
              'cryptokey in the organization\'s CMEK settings.'))

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The updated CMEK settings.
    """
    cmek_settings = {}
    if args.IsSpecified('kms_key_name'):
      cmek_settings['kmsKeyName'] = (
          args.CONCEPTS.kms_key_name.Parse().RelativeName())

    if args.IsSpecified('clear_kms_key'):
      cmek_settings['kmsKeyName'] = ''

    parent_name = util.GetParentFromArgs(args)
    return util.GetClient().organizations.UpdateCmekSettings(
        util.GetMessages().LoggingOrganizationsUpdateCmekSettingsRequest(
            name=parent_name,
            cmekSettings=util.GetMessages().CmekSettings(**cmek_settings),
            updateMask='kms_key_name'))
