# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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

"""'logging settings update' command."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.kms import resource_args as kms_resource_args
from googlecloudsdk.command_lib.resource_manager import completers


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Update(base.Command):
  # pylint: disable=line-too-long
  """Update the settings for the Cloud Logging Logs Router.

  Use this command to update the *--kms-key-name, --storage-location and
  --disable-default-sink* associated with the Cloud Logging Logs Router.

  The Cloud KMS key must already exist and Cloud Logging must have
  permission to access it.

  The storage location must be allowed by Org Policy.

  Customer-managed encryption keys (CMEK) for the Logs Router can currently
  only be configured at the organization-level and will apply to all projects
  in the organization.

  ## EXAMPLES

  To enable CMEK for the Logs Router for an organization, run:

    $ {command} --organization=[ORGANIZATION_ID]
    --kms-key-name='projects/my-project/locations/my-location/keyRings/my-keyring/cryptoKeys/key'

  To disable CMEK for the Logs Router for an organization, run:

    $ {command} --organization=[ORGANIZATION_ID] --clear-kms-key

  To update storage location for the Logs Router for an organization, run:

    $ {command} --organization=[ORGANIZATION_ID]
    --storage-location=[LOCATION_ID]

  To update storage location for the Logs Router for a folder, run:

    $ {command} --folder=[FOLDER_ID] --storage-location=[LOCATION_ID]

  To disable default sink for the Logs Router for an organization, run:

    $ {command} --organization=[ORGANIZATION_ID] --disable-default-sink=true

  To enable default sink for the Logs Router for an organization, run:

    $ {command} --organization=[ORGANIZATION_ID] --disable-default-sink=false
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parent_group = parser.add_mutually_exclusive_group(required=True)
    parent_group.add_argument(
        '--organization',
        required=False,
        metavar='ORGANIZATION_ID',
        completer=completers.OrganizationCompleter,
        help='Organization to update Logs Router settings for.')

    parent_group.add_argument(
        '--folder',
        required=False,
        metavar='FOLDER_ID',
        help='Folder to update Logs Router settings for.')

    parser.add_argument(
        '--storage-location',
        required=False,
        help='Update the storage location for ```_Default``` bucket and '
        '```_Required``` bucket. Note: It only applies to the newly created '
        'projects and will not affect the projects created before.')
    parser.add_argument(
        '--disable-default-sink',
        action='store_true',
        help='Enable or disable ```_Default``` sink for the ```_Default``` '
        'bucket. Specify --no-disable-default-sink to enable a disabled '
        '```_Default``` sink. Note: It only applies to the newly created '
        'projects and will not affect the projects created before.')

    group = parser.add_mutually_exclusive_group(required=False)

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
      The updated settings.
    """
    settings = {}
    update_mask = []
    parameter_names = [
        '--kms-key-name | --clear-kms-key', '--storage-location',
        '--disable-default-sink'
    ]

    if args.IsSpecified('kms_key_name'):
      settings['kmsKeyName'] = (
          args.CONCEPTS.kms_key_name.Parse().RelativeName())
      update_mask.append('kms_key_name')

    if args.IsSpecified('clear_kms_key'):
      settings['kmsKeyName'] = ''
      update_mask.append('kms_key_name')

    if args.IsSpecified('storage_location'):
      settings['storageLocation'] = args.storage_location
      update_mask.append('storage_location')

    if args.IsSpecified('disable_default_sink'):
      settings['disableDefaultSink'] = args.disable_default_sink
      update_mask.append('disable_default_sink')

    if not update_mask:
      raise calliope_exceptions.MinimumArgumentException(
          parameter_names, 'Please specify at least one property to update.')

    parent_name = util.GetParentFromArgs(args)
    return util.GetClient().v2.UpdateSettings(
        util.GetMessages().LoggingUpdateSettingsRequest(
            name=parent_name,
            settings=util.GetMessages().Settings(**settings),
            updateMask=','.join(update_mask)))
