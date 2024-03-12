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
"""Flags and helpers for the Cloud NetApp Files Volumes commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp import util as netapp_api_util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.netapp import util as netapp_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers


VOLUMES_LIST_FORMAT = """\
    table(
        name.basename():label=VOLUME_NAME:sort=1,
        name.segment(3):label=LOCATION,
        storagePool,
        capacityGib:label=CAPACITY_GB,
        serviceLevel,
        shareName,
        state
    )"""

## Helper functions to add args / flags for Volumes gcloud commands ##


def AddVolumeAssociatedStoragePoolArg(parser, required=True):
  concept_parsers.ConceptParser.ForResource(
      '--storage-pool',
      flags.GetStoragePoolResourceSpec(),
      'The Storage Pool to associate with Volume.',
      required=required,
      flag_name_overrides={'location': ''}).AddToParser(parser)


def AddVolumeNetworkArg(parser, required=True):
  """Adds a --network arg to the given parser.

  Args:
    parser: argparse parser.
    required: bool whether arg is required or not
  """

  network_arg_spec = {
      'name': str,
      'psa-range': str,
  }

  network_help = """\
        Network configuration for a Cloud NetApp Files Volume. Specifying
        `psa-range` is optional.
        *name*::: The name of the Google Compute Engine
        [VPC network](/compute/docs/networks-and-firewalls#networks) to which
        the volume is connected.
        *psa-range*::: The `psa-range` is the name of the allocated range of the
        Private Service Access connection. The range you specify can't
        overlap with either existing subnets or assigned IP address ranges for
        other Cloud NetApp Files Volumes in the selected VPC network.
  """

  parser.add_argument(
      '--network',
      type=arg_parsers.ArgDict(spec=network_arg_spec, required_keys=['name']),
      required=required,
      help=network_help)


def GetVolumeProtocolEnumFromArg(choice, messages):
  """Returns the Choice Enum for Protocols.

  Args:
    choice: The choice for protocol input as string
    messages: The messages module.

  Returns:
    the protocol enum
  """
  return arg_utils.ChoiceToEnum(
      choice=choice,
      enum_type=messages.Volume.ProtocolsValueListEntryValuesEnum)


def AddVolumeProtocolsArg(parser, required=True):
  """Adds the Protocols arg to the arg parser."""
  parser.add_argument(
      '--protocols',
      type=arg_parsers.ArgList(min_length=1, element_type=str),
      required=required,
      metavar='PROTOCOL',
      help="""Type of File System protocols for the Cloud NetApp Files Volume. \
Valid component values are:
            `NFSV3`, `NFSV4`, `SMB`.""")


def AddVolumeShareNameArg(parser, required=True):
  """Adds the Share name arg to the arg parser."""
  parser.add_argument(
      '--share-name',
      type=str,
      required=required,
      help="""Share name of the Mount path clients will use.""")


def AddVolumeExportPolicyArg(parser):
  """Adds the Export Policy (--export-policy) arg to the given parser.

  Args:
    parser: argparse parser.
  """
  export_policy_arg_spec = {
      'allowed-clients':
          str,
      'has-root-access':
          str,
      'access-type':
          str,
      'kerberos-5-read-only':
          arg_parsers.ArgBoolean(
              truthy_strings=netapp_util.truthy,
              falsey_strings=netapp_util.falsey
          ),
      'kerberos-5-read-write':
          arg_parsers.ArgBoolean(
              truthy_strings=netapp_util.truthy,
              falsey_strings=netapp_util.falsey
          ),
      'kerberos-5i-read-only':
          arg_parsers.ArgBoolean(
              truthy_strings=netapp_util.truthy,
              falsey_strings=netapp_util.falsey
          ),
      'kerberos-5i-read-write':
          arg_parsers.ArgBoolean(
              truthy_strings=netapp_util.truthy,
              falsey_strings=netapp_util.falsey
          ),
      'kerberos-5p-read-write':
          arg_parsers.ArgBoolean(
              truthy_strings=netapp_util.truthy,
              falsey_strings=netapp_util.falsey
          ),
      'kerberos-5p-read-only':
          arg_parsers.ArgBoolean(
              truthy_strings=netapp_util.truthy,
              falsey_strings=netapp_util.falsey
          ),
      'nfsv3':
          arg_parsers.ArgBoolean(
              truthy_strings=netapp_util.truthy,
              falsey_strings=netapp_util.falsey),
      'nfsv4':
          arg_parsers.ArgBoolean(
              truthy_strings=netapp_util.truthy,
              falsey_strings=netapp_util.falsey),
  }
  export_policy_help = """\
        Export Policy of a Cloud NetApp Files Volume.
        This will be a field similar to network
        in which export policy fields can be specified as such:
        `--export-policy=allowed-clients=ALLOWED_CLIENTS_IP_ADDRESSES,
        has-root-access=HAS_ROOT_ACCESS_BOOL,access=ACCESS_TYPE,nfsv3=NFSV3,
        nfsv4=NFSV4,kerberos-5-read-only=KERBEROS_5_READ_ONLY,
        kerberos-5-read-write=KERBEROS_5_READ_WRITE,
        kerberos-5i-read-only=KERBEROS_5I_READ_ONLY,
        kerberos-5i-read-write=KERBEROS_5I_READ_WRITE,
        kerberos-5p-read-only=KERBEROS_5P_READ_ONLY,
        kerberos-5p-read-write=KERBEROS_5P_READ_WRITE`
  """
  parser.add_argument(
      '--export-policy',
      type=arg_parsers.ArgDict(spec=export_policy_arg_spec),
      action='append',
      help=export_policy_help)


def AddVolumeUnixPermissionsArg(parser):
  """Adds the Unix Permissions arg to the arg parser."""
  parser.add_argument(
      '--unix-permissions',
      type=str,
      help="""Unix permissions the mount point will be created with. \
Unix permissions are only applicable with NFS protocol only""")


def GetVolumeSmbSettingsEnumFromArg(choice, messages):
  """Returns the Choice Enum for SMB Setting.

  Args:
    choice: The choice for SMB setting input as string
    messages: The messages module.

  Returns:
    The choice arg.
  """
  return arg_utils.ChoiceToEnum(
      choice=choice,
      enum_type=messages.Volume.SmbSettingsValueListEntryValuesEnum)


def AddVolumeSmbSettingsArg(parser):
  """Adds the --smb-settings arg to the arg parser."""
  parser.add_argument(
      '--smb-settings',
      type=arg_parsers.ArgList(min_length=1, element_type=str),
      metavar='SMB_SETTING',
      help="""List of settings specific to SMB protocol \
for a Cloud NetApp Files Volume. \
Valid component values are:
  `ENCRYPT_DATA`, `BROWSABLE`, `CHANGE_NOTIFY`, `NON_BROWSABLE`,
  `OPLOCKS`, `SHOW_SNAPSHOT`, `SHOW_PREVIOUS_VERSIONS`,
  `ACCESS_BASED_ENUMERATION`, `CONTINUOUSLY_AVAILABLE`.""")


def AddVolumeHourlySnapshotArg(parser):
  """Adds the --snapshot-hourly arg to the arg parser."""
  hourly_snapshot_arg_spec = {
      'snapshots-to-keep': float,
      'minute': float,
  }
  hourly_snapshot_help = """
  Make a snapshot every hour e.g. at 04:00, 05:20, 06:00
  """
  parser.add_argument(
      '--snapshot-hourly',
      type=arg_parsers.ArgDict(spec=hourly_snapshot_arg_spec),
      help=hourly_snapshot_help)


def AddVolumeDailySnapshotArg(parser):
  """Adds the --snapshot-daily arg to the arg parser."""
  daily_snapshot_arg_spec = {
      'snapshots-to-keep': float,
      'minute': float,
      'hour': float,
  }
  daily_snapshot_help = """
  Make a snapshot every day e.g. at 06:00, 05:20, 23:50
  """
  parser.add_argument(
      '--snapshot-daily',
      type=arg_parsers.ArgDict(spec=daily_snapshot_arg_spec),
      help=daily_snapshot_help)


def AddVolumeWeeklySnapshotArg(parser):
  """Adds the --snapshot-weekly arg to the arg parser."""
  weekly_snapshot_arg_spec = {
      'snapshots-to-keep': float,
      'minute': float,
      'hour': float,
      'day': str
  }
  weekly_snapshot_help = """
  Make a snapshot every week e.g. at Monday 04:00, Wednesday 05:20,
  Sunday 23:50
  """
  parser.add_argument(
      '--snapshot-weekly',
      type=arg_parsers.ArgDict(spec=weekly_snapshot_arg_spec),
      help=weekly_snapshot_help)


def AddVolumeMonthlySnapshotArg(parser):
  """Addss the --snapshot-monthly arg to the arg parser."""
  monthly_snapshot_arg_spec = {
      'snapshots-to-keep': float,
      'minute': float,
      'hour': float,
      'day': str
  }
  monthly_snapshot_help = """
  Make a snapshot once a month e.g. at 2nd 04:00, 7th 05:20, 24th 23:50
  """
  parser.add_argument(
      '--snapshot-monthly',
      type=arg_parsers.ArgDict(spec=monthly_snapshot_arg_spec),
      help=monthly_snapshot_help,
  )


def AddVolumeSnapReserveArg(parser):
  """Adds the --snap-reserve arg to the arg parser."""
  action = actions.DeprecationAction(
      'snap-reserve', warn='The {flag_name} option is deprecated', removed=False
  )
  parser.add_argument(
      '--snap-reserve',
      type=float,
      help="""The percentage of volume storage reserved for snapshot storage.
      The default value for this is 0 percent""",
      action=action,
  )


def AddVolumeSnapshotDirectoryArg(parser):
  """Adds the --snapshot-directory arg to the arg parser."""
  parser.add_argument(
      '--snapshot-directory',
      type=arg_parsers.ArgBoolean(
          truthy_strings=netapp_util.truthy, falsey_strings=netapp_util.falsey),
      default='true',
      help="""Snapshot Directory if enabled (true) makes the Volume
            contain a read-only .snapshot directory which provides access
            to each of the volume's snapshots
          """)


def GetVolumeSecurityStyleEnumFromArg(choice, messages):
  """Returns the Choice Enum for Security style.

  Args:
    choice: The choice for Security style input as string
    messages: The messages module.

  Returns:
    The choice arg.
  """
  return arg_utils.ChoiceToEnum(
      choice=choice,
      enum_type=messages.Volume.SecurityStyleValueValuesEnum)


def AddVolumeSecurityStyleArg(parser, messages):
  """Adds the --security-style arg to the arg parser."""
  security_style_arg = (
      arg_utils.ChoiceEnumMapper(
          '--security-style',
          messages.Volume.SecurityStyleValueValuesEnum,
          help_str="""The security style of the Volume. This can either be
          UNIX or NTFS.
        """,
          custom_mappings={
              'UNIX': ('unix', """UNIX security style for Volume"""),
              'NTFS': ('ntfs', """NTFS security style for Volume."""),
          },
          default='SECURITY_STYLE_UNSPECIFIED'))
  security_style_arg.choice_arg.AddToParser(parser)


def AddVolumeEnableKerberosArg(parser):
  """Adds the --enable-kerberos arg to the arg parser."""
  parser.add_argument(
      '--enable-kerberos',
      type=arg_parsers.ArgBoolean(
          truthy_strings=netapp_util.truthy, falsey_strings=netapp_util.falsey),
      help="""Boolean flag indicating whether Volume is a kerberos Volume or not"""
  )


def AddVolumeEnableLdapArg(parser):
  """Adds the --enable-ladp arg to the arg parser."""
  parser.add_argument(
      '--enable-ldap',
      type=arg_parsers.ArgBoolean(
          truthy_strings=netapp_util.truthy, falsey_strings=netapp_util.falsey),
      help="""Boolean flag indicating whether Volume is a NFS LDAP Volume or not"""
  )


def AddVolumeForceArg(parser):
  """Adds the --force arg to the arg parser."""
  parser.add_argument(
      '--force',
      action='store_true',
      help="""Forces the deletion of a volume and its child resources, such as snapshots."""
  )


def AddVolumeRevertSnapshotArg(parser, required=True):
  """Adds the --snapshot arg to the arg parser."""
  concept_parsers.ConceptParser.ForResource(
      '--snapshot',
      flags.GetSnapshotResourceSpec(source_snapshot_op=True, positional=False),
      required=required,
      flag_name_overrides={'location': '',
                           'volume': ''},
      group_help='The Snapshot to revert the Volume back to.').AddToParser(
          parser)


def AddVolumeSourceSnapshotArg(parser):
  """Adds the --source-snapshot arg to the arg parser."""
  concept_parsers.ConceptParser.ForResource(
      '--source-snapshot',
      flags.GetSnapshotResourceSpec(source_snapshot_op=True, positional=False),
      flag_name_overrides={'location': '',
                           'volume': ''},
      group_help='The source Snapshot to create the Volume from.').AddToParser(
          parser)


def AddVolumeSourceBackupArg(parser):
  """Adds the --source-backup arg to the arg parser."""
  concept_parsers.ConceptParser.ForResource(
      '--source-backup',
      flags.GetBackupResourceSpec(positional=False),
      flag_name_overrides={'location': ''},
      group_help='The source Backup to create the Volume from.',
  ).AddToParser(parser)


def GetVolumeRestrictedActionsEnumFromArg(choice, messages):
  """Returns the Choice Enum for Restricted Actions.

  Args:
      choice: The choice for restricted actions input as string.
      messages: The messages module.

  Returns:
      the Restricted Actions enum.
  """
  return arg_utils.ChoiceToEnum(
      choice=choice,
      enum_type=messages.Volume.RestrictedActionsValueListEntryValuesEnum)


def AddVolumeRestrictedActionsArg(parser):
  """Adds the --restricted-actions arg to the arg parser."""
  parser.add_argument(
      '--restricted-actions',
      type=arg_parsers.ArgList(min_length=1, element_type=str),
      metavar='RESTRICTED_ACTION',
      help="""Actions to be restricted for a volume. \
Valid restricted action options are:
          'DELETE'."""
  )


def AddVolumeBackupConfigArg(parser):
  """Adds the --backup-config arg to the arg parser."""
  backup_config_arg_spec = {
      'backup-policies':
          arg_parsers.ArgList(min_length=1,
                              element_type=str,
                              custom_delim_char='#'),
      'backup-vault':
          str,
      'enable-scheduled-backups':
          arg_parsers.ArgBoolean(
              truthy_strings=netapp_util.truthy,
              falsey_strings=netapp_util.falsey
          ),
  }
  backup_config_help = """\
Backup Config contains backup related config on a volume.

    Backup Config will have the following format
    `--backup-config=backup-policies=BACKUP_POLICIES,
    backup-vault=BACKUP_VAULT_NAME,
    enable-scheduled-backups=ENABLE_SCHEDULED_BACKUPS

backup-policies is a pound-separated (#) list of backup policy names, backup-vault can include
a single backup-vault resource name, and enable-scheduled-backups is a Boolean value indicating
whether or not scheduled backups are enabled on the volume.
  """
  parser.add_argument(
      '--backup-config',
      type=arg_parsers.ArgDict(spec=backup_config_arg_spec),
      help=backup_config_help)


def AddVolumeLargeCapacityArg(parser):
  """Adds the --large-capacity arg to the arg parser."""
  parser.add_argument(
      '--large-capacity',
      type=arg_parsers.ArgBoolean(
          truthy_strings=netapp_util.truthy, falsey_strings=netapp_util.falsey),
      help="""Boolean flag indicating whether Volume is a large capacity Volume or not"""
  )


def AddVolumeMultipleEndpointsArg(parser):
  """Adds the --multiple-endpoints arg to the arg parser."""
  parser.add_argument(
      '--multiple-endpoints',
      type=arg_parsers.ArgBoolean(
          truthy_strings=netapp_util.truthy, falsey_strings=netapp_util.falsey),
      help="""Boolean flag indicating whether Volume is a multiple endpoints Volume or not"""
  )

## Helper functions to combine Volumes args / flags for gcloud commands #


def AddVolumeCreateArgs(parser, release_track):
  """Add args for creating a Volume."""
  concept_parsers.ConceptParser([
      flags.GetVolumePresentationSpec('The Volume to create.')
  ]).AddToParser(parser)
  messages = netapp_api_util.GetMessagesModule(release_track=release_track)
  flags.AddResourceDescriptionArg(parser, 'Volume')
  flags.AddResourceCapacityArg(parser, 'Volume')
  AddVolumeAssociatedStoragePoolArg(parser)
  flags.AddResourceAsyncFlag(parser)
  AddVolumeProtocolsArg(parser)
  AddVolumeShareNameArg(parser)
  AddVolumeExportPolicyArg(parser)
  AddVolumeUnixPermissionsArg(parser)
  AddVolumeSmbSettingsArg(parser)
  AddVolumeSourceSnapshotArg(parser)
  AddVolumeHourlySnapshotArg(parser)
  AddVolumeDailySnapshotArg(parser)
  AddVolumeWeeklySnapshotArg(parser)
  AddVolumeMonthlySnapshotArg(parser)
  AddVolumeSnapReserveArg(parser)
  AddVolumeSnapshotDirectoryArg(parser)
  AddVolumeSecurityStyleArg(parser, messages)
  AddVolumeEnableKerberosArg(parser)
  AddVolumeRestrictedActionsArg(parser)
  if release_track == calliope_base.ReleaseTrack.BETA:
    AddVolumeBackupConfigArg(parser)
    AddVolumeSourceBackupArg(parser)
  if (release_track == calliope_base.ReleaseTrack.ALPHA or
      release_track == calliope_base.ReleaseTrack.BETA):
    AddVolumeLargeCapacityArg(parser)
    AddVolumeMultipleEndpointsArg(parser)
  labels_util.AddCreateLabelsFlags(parser)


def AddVolumeDeleteArgs(parser):
  """Add args for deleting a Volume."""
  concept_parsers.ConceptParser([
      flags.GetVolumePresentationSpec('The Volume to delete.')
  ]).AddToParser(parser)
  flags.AddResourceAsyncFlag(parser)
  AddVolumeForceArg(parser)


def AddVolumeUpdateArgs(parser, release_track):
  """Add args for updating a Volume."""
  concept_parsers.ConceptParser([
      flags.GetVolumePresentationSpec('The Volume to update.')
  ]).AddToParser(parser)
  messages = netapp_api_util.GetMessagesModule(release_track=release_track)
  flags.AddResourceDescriptionArg(parser, 'Volume')
  flags.AddResourceCapacityArg(parser, 'Volume', required=False)
  AddVolumeAssociatedStoragePoolArg(parser, required=False)
  flags.AddResourceAsyncFlag(parser)
  AddVolumeProtocolsArg(parser, required=False)
  AddVolumeShareNameArg(parser, required=False)
  AddVolumeExportPolicyArg(parser)
  AddVolumeUnixPermissionsArg(parser)
  AddVolumeSmbSettingsArg(parser)
  AddVolumeSourceSnapshotArg(parser)
  AddVolumeHourlySnapshotArg(parser)
  AddVolumeDailySnapshotArg(parser)
  AddVolumeWeeklySnapshotArg(parser)
  AddVolumeMonthlySnapshotArg(parser)
  AddVolumeSnapReserveArg(parser)
  AddVolumeSnapshotDirectoryArg(parser)
  AddVolumeSecurityStyleArg(parser, messages)
  AddVolumeEnableKerberosArg(parser)
  AddVolumeRestrictedActionsArg(parser)
  if release_track == calliope_base.ReleaseTrack.BETA:
    AddVolumeBackupConfigArg(parser)
    AddVolumeSourceBackupArg(parser)
  labels_util.AddUpdateLabelsFlags(parser)
