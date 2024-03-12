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
"""Flags for data-catalog commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs

FILTER_FLAG_NO_SORTBY_DOC = base.Argument(
    '--filter',
    metavar='EXPRESSION',
    require_coverage_in_tests=False,
    category=base.LIST_COMMAND_FLAGS,
    help="""\
    Apply a Boolean filter _EXPRESSION_ to each resource item to be listed.
    If the expression evaluates `True`, then that item is listed. For more
    details and examples of filter expressions, run $ gcloud topic filters. This
    flag interacts with other flags that are applied in this order: *--flatten*,
    *--filter*, *--limit*.""")


LIMIT_FLAG_NO_SORTBY_DOC = base.Argument(
    '--limit',
    type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
    require_coverage_in_tests=False,
    category=base.LIST_COMMAND_FLAGS,
    help="""\
    Maximum number of resources to list. The default is *unlimited*.
    This flag interacts with other flags that are applied in this order:
    *--flatten*, *--filter*, *--limit*.
    """)


VOLUME_SNAPSHOT_AUTO_DELETE_BEHAVIOR_MAPPER = arg_utils.ChoiceEnumMapper(
    arg_name='--snapshot-auto-delete',
    message_enum=apis.GetMessagesModule(
        'baremetalsolution',
        'v2').Volume.SnapshotAutoDeleteBehaviorValueValuesEnum,
    custom_mappings={
        'NEWEST_FIRST': ('newest-first', 'Delete the newest snapshot first.'),
        'OLDEST_FIRST': ('oldest-first', 'Delete the oldest snapshot first.'),
        'DISABLED': ('disabled', ("Don't delete any snapshots. This disables "
                                  'new snapshot creation as long as the '
                                  'snapshot reserved space is full.')),
    },
    required=False,
    help_str='Behavior of the disk when snapshot reserved space is full.')


ASYNC_FLAG_DEFAULT_TRUE = base.Argument(
    '--async',
    action='store_true',
    dest='async_',
    default=True,
    help="""\
    Return immediately, without waiting for the operation in progress to
    complete.""")

IP_RESERVATION_SPEC = {
    'start-address': str,
    'end-address': str,
    'note': str
}

IP_RESERVATION_KEY_SPEC = {
    'start-address': str,
    'end-address': str,
}

NFS_ALLOWED_CLIENTS_HELP_TEXT = """
Adds an allowed client to the NFS share. This flag can be repeated to specify multiple allowed clients.

*network*::: The name of the network to allow.

*network-project-id*::: The project ID of the allowed client network.
If not present, the project ID of the NFS share will be used.

*cidr*::: The subnet of IP addresses permitted to access the NFS
share.

*mount-permissions*::: The mount permissions for the allowed client.
``MOUNT_PERMISSIONS'' must be one of: `READ_ONLY`, `READ_WRITE`.

*allow-dev*::: If ``yes'', allows creation of devices.

*allow-suid*::: If ``yes'', allows SUID.

*enable-root-squash*::: If ``yes'', enables root squashing which
is a special mapping of the remote superuser (root) identity when
using identity authentication .
"""


def _ValidateNFSMountPermissions(mount_permissions_input):
  """Validates NFS mount permissions field, throws exception if invalid."""
  mount_permissions = mount_permissions_input.upper()
  if mount_permissions not in NFS_MOUNT_PERMISSIONS_CHOICES:
    raise exceptions.InvalidArgumentException(
        '--allowed-client',
        'Invalid value {} for mount-permissions'.format(
            mount_permissions_input))
  return mount_permissions

NFS_ALLOWED_CLIENT_SPEC = {
    'network': str,
    'network-project-id': str,
    'cidr': str,
    'mount-permissions': _ValidateNFSMountPermissions,
    'allow-dev': arg_parsers.ArgBoolean(),
    'allow-suid': arg_parsers.ArgBoolean(),
    'enable-root-squash': arg_parsers.ArgBoolean(),
}
REQUIRED_NFS_ALLOWED_CLIENT_KEYS = [  # Only network-project-id is optional.
    'network',
    'cidr',
    'mount-permissions',
    'allow-dev',
    'allow-suid',
    'enable-root-squash',
]
NFS_MOUNT_PERMISSIONS_CHOICES = ('READ_ONLY', 'READ_WRITE')
REMOVE_NFS_ALLOWED_CLIENT_SPEC = {
    'network': str,
    'network-project-id': str,
    'cidr': str,
}
REQUIRED_REMOVE_NFS_ALLOWED_CLIENT_KEYS = [
    # Only network-project-id is optional.
    'network',
    'cidr',
]


def AddInstanceArgToParser(parser, positional=False):
  """Sets up an argument for the instance resource."""
  if positional:
    name = 'instance'
  else:
    name = '--instance'
  instance_data = yaml_data.ResourceYAMLData.FromPath(
      'bms.instance')
  resource_spec = concepts.ResourceSpec.FromYaml(instance_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='instance.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddRegionArgToParser(parser, positional=False):
  """Parses region flag."""
  region_data = yaml_data.ResourceYAMLData.FromPath('bms.region')
  resource_spec = concepts.ResourceSpec.FromYaml(region_data.GetData())
  if positional:
    name = 'region'
  else:
    name = '--region'
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=False,
      group_help='region.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddVolumeArgToParser(parser, positional=False, group_help_text=None):
  """Sets up an argument for the instance resource."""
  if positional:
    name = 'volume'
  else:
    name = '--volume'
  volume_data = yaml_data.ResourceYAMLData.FromPath(
      'bms.volume')
  resource_spec = concepts.ResourceSpec.FromYaml(volume_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help=group_help_text or 'volume.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddSnapshotSchedulePolicyArgToParser(parser,
                                         positional=False,
                                         required=True,
                                         name=None,
                                         group=None):
  """Sets up an argument for the snapshot schedule policy resource."""
  if not name:
    if positional:
      name = 'snapshot_schedule_policy'
    else:
      name = '--snapshot-schedule-policy'
  policy_data = yaml_data.ResourceYAMLData.FromPath(
      'bms.snapshot_schedule_policy')
  resource_spec = concepts.ResourceSpec.FromYaml(policy_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      group=group,
      concept_spec=resource_spec,
      required=required,
      flag_name_overrides={'region': ''},
      group_help='snapshot_schedule_policy.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddSnapshotScheduleArgListToParser(parser, required=True):
  """Sets up an argument for a snapshot schedule."""
  spec = {
      'crontab_spec': str,
      'retention_count': int,
      'prefix': str,
  }
  parser.add_argument(
      '--schedule',
      required=required,
      type=arg_parsers.ArgDict(spec=spec,
                               max_length=len(spec),
                               required_keys=spec.keys()),
      action='append',
      metavar='CRONTAB_SPEC,RETENTION_COUNT,PREFIX',
      help="""
              Adds a schedule for taking snapshots of volumes under this policy.
              This flag may be repeated to specify up to 5 schedules.

              *crontab_spec*::: Specification of the times at which snapshots
              will be taken. This should be in Crontab format:
              http://en.wikipedia.org/wiki/Cron#Overview

              *retention_count*::: The maximum number of snapshots to retain in
              this schedule.

              *prefix*::: Value to append to the name of snapshots created by
              this schedule.

           """,
      )


def AddNetworkArgToParser(parser, positional=False):
  """Sets up an argument for the network resource."""
  if positional:
    name = 'network'
  else:
    name = '--network'
  policy_data = yaml_data.ResourceYAMLData.FromPath(
      'bms.network')
  resource_spec = concepts.ResourceSpec.FromYaml(policy_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='network.')

  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddLunArgToParser(parser):
  """Sets up an argument for a volume snapshot policy."""
  name = 'lun'
  snapshot_data = yaml_data.ResourceYAMLData.FromPath('bms.lun')
  resource_spec = concepts.ResourceSpec.FromYaml(snapshot_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='lun.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddVolumeSnapshotArgToParser(parser, positional=False):
  """Sets up an argument for a volume snapshot policy."""
  if positional:
    name = 'snapshot'
  else:
    name = '--snapshot'
  snapshot_data = yaml_data.ResourceYAMLData.FromPath('bms.snapshot')
  resource_spec = concepts.ResourceSpec.FromYaml(snapshot_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='snapshot.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddVolumeSnapshotAutoDeleteBehaviorArgToParser(parser):
  """Sets up an argument for a volume snapshot auto-delete-behavior enum."""
  VOLUME_SNAPSHOT_AUTO_DELETE_BEHAVIOR_MAPPER.choice_arg.AddToParser(parser)


def AddNfsShareArgToParser(parser, positional=False):
  """Sets up an argument for an nfs-share resource."""
  if positional:
    name = 'nfs_share'
  else:
    name = '--nfs_share'
  nfs_data = yaml_data.ResourceYAMLData.FromPath(
      'bms.nfs_share')
  resource_spec = concepts.ResourceSpec.FromYaml(nfs_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='nfs_share.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddOsImageArgToParser(parser, positional=False):
  """Sets up an argument for an os-image resource."""
  if positional:
    name = 'os_image'
  else:
    name = '--os-image'
  os_image_data = yaml_data.ResourceYAMLData.FromPath(
      'bms.os_image')
  resource_spec = concepts.ResourceSpec.FromYaml(os_image_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='os_image.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddSerialConsoleSshKeyArgToParser(parser, positional=False, name=None):
  """Sets up an argument for the serial-console-ssh-key resource."""
  name = 'serial_console_ssh_key' if positional else '--serial-console-ssh-key'
  ssh_key_data = yaml_data.ResourceYAMLData.FromPath(
      'bms.serial_console_ssh_key'
  )
  resource_spec = concepts.ResourceSpec.FromYaml(ssh_key_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      flag_name_overrides={'region': ''},
      group_help='serial_console_ssh_key.',
  )
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddProvisioningSshKeyArgToParser(
    parser, positional=False, name=None, required=True, plural=False
):
  group_parser = parser.add_mutually_exclusive_group(required=required)
  AddSshKeyArgToParser(
      group_parser,
      positional=positional,
      name=name,
      plural=plural,
      required=required,
  )
  AddClearSshKeyToParser(group_parser)


def AddSshKeyArgToParser(
    parser, positional=False, name=None, required=True, plural=False
):
  """Sets up an argument for the ssh-key resource."""
  name = 'ssh_key' if positional else '--ssh-key'
  ssh_key_data = yaml_data.ResourceYAMLData.FromPath('bms.ssh_key')
  resource_spec = concepts.ResourceSpec.FromYaml(ssh_key_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name if not plural else f'{name}s',
      concept_spec=resource_spec,
      required=required,
      flag_name_overrides={'region': ''},
      group_help='ssh_key.',
      plural=plural,
      )
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddClearSshKeyToParser(parser):
  parser.add_argument(
      '--clear-ssh-keys',
      action='store_true',
      help="""Provisions the instance without any SSH keys.""",
      required=False,
  )


def AddNewNameArgToParser(parser, obj_name):
  parser.add_argument(
      '--new-name',
      type=str,
      help="""New {name} name for renaming an already existing {name}.""".format(
          name=obj_name),
      required=True)


def AddInstanceOsImageToParser(parser, hidden):
  parser.add_argument(
      '--os-image',
      type=str,
      help="""OS image to install on the server.""",
      hidden=hidden)


def AddInstanceEnableHyperthreadingToParser(parser, hidden):
  parser.add_argument(
      '--enable-hyperthreading',
      action=arg_parsers.StoreTrueFalseAction,
      help="""Enable hyperthreading for the server.""",
      hidden=hidden)


def AddNetworkIpReservationToParser(parser, hidden):
  """Adds the flags for network IP range reservation to parser."""
  group_arg = parser.add_mutually_exclusive_group(required=False)
  group_arg.add_argument(
      '--add-ip-range-reservation',
      type=arg_parsers.ArgDict(spec=IP_RESERVATION_SPEC),
      metavar='PROPERTY=VALUE',
      help="""
              Add a reservation of a range of IP addresses in the network.

              *start_address*::: The first address of this reservation block.
              Must be specified as a single IPv4 address, e.g. `10.1.2.2`.

              *end_address*::: The last address of this reservation block,
              inclusive. I.e., for cases when reservations are only single
              addresses, end_address and start_address will be the same.
              Must be specified as a single IPv4 address, e.g. `10.1.2.2`.

              *note*::: A note about this reservation, intended for human consumption.
            """,
      hidden=hidden)
  group_arg.add_argument(
      '--remove-ip-range-reservation',
      type=arg_parsers.ArgDict(spec=IP_RESERVATION_KEY_SPEC),
      metavar='PROPERTY=VALUE',
      help="""
              Remove a reservation of a range of IP addresses in the network.

              *start_address*::: The first address of the reservation block to remove.

              *end_address*::: The last address of the reservation block to remove.
            """,
      hidden=hidden)
  group_arg.add_argument(
      '--clear-ip-range-reservations',
      action='store_true',
      help="""Removes all IP range reservations in the network.""",
      hidden=hidden)


def AddNfsSizeGibArg(parser):
  """Adds size GiB argument for NFS."""
  parser.add_argument(
      '--size-gib',
      help='The requested size of the NFS share in GiB',
      type=int,
      required=True)


def AddNfsStorageTypeArg(parser):
  """Adds storage type argument for NFS."""
  parser.add_argument(
      '--storage-type',
      choices={
          'SSD':
              'The storage type of the underlying volume will be SSD',
          'HDD':
              'The storage type of the underlying volume will be HDD'
      },
      required=True,
      type=arg_utils.ChoiceToEnumName,
      help=('Specifies the storage type of the underlying volume which will be'
            ' created for the NFS share.'))


def AddNfsAllowedClientArg(parser):
  parser.add_argument(
      '--allowed-client',
      type=arg_parsers.ArgDict(spec=NFS_ALLOWED_CLIENT_SPEC,
                               required_keys=REQUIRED_NFS_ALLOWED_CLIENT_KEYS,
                               ),
      required=True,
      action='append',
      metavar='PROPERTY=VALUE',
      help=NFS_ALLOWED_CLIENTS_HELP_TEXT,
      )


def AddNfsUpdateAllowedClientArgs(parser, hidden):
  """Adds NFS update allowed clients arguments group."""
  group_arg = parser.add_mutually_exclusive_group(required=False, hidden=hidden)
  group_arg.add_argument(
      '--add-allowed-client',
      type=arg_parsers.ArgDict(
          spec=NFS_ALLOWED_CLIENT_SPEC,
          required_keys=REQUIRED_NFS_ALLOWED_CLIENT_KEYS,
      ),
      action='append',
      metavar='PROPERTY=VALUE',
      help=NFS_ALLOWED_CLIENTS_HELP_TEXT,
  )
  group_arg.add_argument(
      '--remove-allowed-client',
      type=arg_parsers.ArgDict(
          spec=REMOVE_NFS_ALLOWED_CLIENT_SPEC,
          required_keys=REQUIRED_REMOVE_NFS_ALLOWED_CLIENT_KEYS,
      ),
      action='append',
      metavar='PROPERTY=VALUE',
      help="""
              Removes an allowed client for the NFS share given its network name and cidr. This flag can be repeated to remove multiple allowed clients.

              *network*::: The name of the network of the allowed client to remove.

              *network-project-id*::: The project ID of the allowed client network.
              If not present, the project ID of the NFS share will be used.

              *cidr*::: The subnet of permitted IP addresses of the allowed client to remove.
            """)
  group_arg.add_argument(
      '--clear-allowed-clients',
      action='store_true',
      help="""Removes all IP range reservations in the network.""")


def AddKMSCryptoKeyVersionToParser(parser, hidden):
  parser.add_argument(
      '--kms-crypto-key-version',
      type=str,
      help="""
      Resource ID of a KMS CryptoKeyVersion used to encrypt the initial password.

      https://cloud.google.com/kms/docs/resource-hierarchy#key_versions
      """,
      hidden=hidden,
  )
