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
"""Updates a Cloud NetApp Volume."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.volumes import client as volumes_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.volumes import flags as volumes_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


def _CommonArgs(parser, release_track):
  volumes_flags.AddVolumeUpdateArgs(parser, release_track=release_track)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Cloud NetApp Volume."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  detailed_help = {
      'DESCRIPTION': """\
          Update a Cloud NetApp Volume and its specified parameters
          """,
      'EXAMPLES': """\
          The following command updates a Volume named NAME and its specified parameters

              $ {command} NAME --location=us-central1 --capacity=4096 --description="new description" --enable-kerberos=false --storage-pool=sp3 --unix-permissions=0777
          """,
  }

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, Update._RELEASE_TRACK)

  def Run(self, args):
    """Update a Cloud NetApp Volume in the current project."""
    volume_ref = args.CONCEPTS.volume.Parse()
    client = volumes_client.VolumesClient(self._RELEASE_TRACK)
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    original_volume = client.GetVolume(volume_ref)

    # Update labels
    if labels_diff.MayHaveUpdates():
      labels = labels_diff.Apply(client.messages.Volume.LabelsValue,
                                 original_volume.labels).GetOrNone()
    else:
      labels = None

    protocols = []
    if args.protocols:
      for protocol in args.protocols:
        protocol_enum = volumes_flags.GetVolumeProtocolEnumFromArg(
            protocol, client.messages
        )
        protocols.append(protocol_enum)
    capacity_in_gib = args.capacity >> 30 if args.capacity else None
    smb_settings = []
    if args.smb_settings:
      for smb_setting in args.smb_settings:
        smb_setting_enum = volumes_flags.GetVolumeSmbSettingsEnumFromArg(
            smb_setting, client.messages
        )
        smb_settings.append(smb_setting_enum)
    restricted_actions = []
    if args.restricted_actions:
      for restricted_action in args.restricted_actions:
        restricted_action_enum = (
            volumes_flags.GetVolumeRestrictedActionsEnumFromArg(
                restricted_action, client.messages
            )
        )
        restricted_actions.append(restricted_action_enum)
    snapshot_policy = {}
    for name, snapshot_schedule in (
        ('hourly_snapshot', args.snapshot_hourly),
        ('daily_snapshot', args.snapshot_daily),
        ('weekly_snapshot', args.snapshot_weekly),
        ('monthly_snapshot', args.snapshot_monthly),
    ):
      if snapshot_schedule:  # snapshot schedule is set
        snapshot_policy[name] = snapshot_schedule
    if not snapshot_policy:
      # if no snapshot_schedule was set in args, change to None type for
      # ParseVolumeConfig to easily parse
      snapshot_policy = None
    if args.security_style:
      security_style = volumes_flags.GetVolumeSecurityStyleEnumFromArg(
          args.security_style, client.messages
      )
    else:
      security_style = None
    backup_config = (
        args.backup_config
        if self._RELEASE_TRACK == base.ReleaseTrack.BETA
        else None
    )
    source_backup = (
        args.source_backup
        if self._RELEASE_TRACK == base.ReleaseTrack.BETA
        else None
    )
    volume = client.ParseUpdatedVolumeConfig(
        original_volume,
        description=args.description,
        labels=labels,
        storage_pool=args.storage_pool,
        protocols=protocols,
        share_name=args.share_name,
        export_policy=args.export_policy,
        capacity=capacity_in_gib,
        unix_permissions=args.unix_permissions,
        smb_settings=smb_settings,
        snapshot_policy=snapshot_policy,
        snap_reserve=args.snap_reserve,
        snapshot_directory=args.snapshot_directory,
        security_style=security_style,
        enable_kerberos=args.enable_kerberos,
        snapshot=args.source_snapshot,
        backup=source_backup,
        restricted_actions=restricted_actions,
        backup_config=backup_config)

    updated_fields = []
    # add possible updated volume fields
    # TODO(b/243601146) add config mapping and separate config file for update
    if args.IsSpecified('capacity'):
      updated_fields.append('capacityGib')
    if args.IsSpecified('storage_pool'):
      updated_fields.append('storagePool')
    if args.IsSpecified('share_name'):
      updated_fields.append('shareName')
    if args.IsSpecified('export_policy'):
      updated_fields.append('exportPolicy')
    if args.IsSpecified('protocols'):
      updated_fields.append('protocols')
    if args.IsSpecified('unix_permissions'):
      updated_fields.append('unixPermissions')
    if args.IsSpecified('smb_settings'):
      updated_fields.append('smbSettings')
    if (args.IsSpecified('snapshot_hourly') or
        args.IsSpecified('snapshot_daily') or
        args.IsSpecified('snapshot_weekly') or
        args.IsSpecified('snapshot_monthly')):
      updated_fields.append('snapshotPolicy')
    if args.IsSpecified('snap_reserve'):
      updated_fields.append('snapReserve')
    if args.IsSpecified('snapshot_directory'):
      updated_fields.append('snapshotDirectory')
    if args.IsSpecified('security_style'):
      updated_fields.append('securityStyle')
    if args.IsSpecified('enable_kerberos'):
      updated_fields.append('kerberosEnabled')
    if args.IsSpecified('source_snapshot'):
      updated_fields.append('restoreParameters')
    if args.IsSpecified('restricted_actions'):
      updated_fields.append('restrictedActions')
    if self._RELEASE_TRACK == base.ReleaseTrack.BETA:
      if args.IsSpecified('source_backup'):
        updated_fields.append('restoreParameters')
      if backup_config is not None:
        if backup_config.get('backup-policies', []):
          updated_fields.append('backupConfig.backupPolicies')
        if backup_config.get('backup-vault', ''):
          updated_fields.append('backupConfig.backupVault')
        if backup_config.get('enable-scheduled-backups', False):
          updated_fields.append('backupConfig.scheduledBackupEnabled')
    if args.IsSpecified('description'):
      updated_fields.append('description')
    if (
        args.IsSpecified('update_labels')
        or args.IsSpecified('remove_labels')
        or args.IsSpecified('clear_labels')
    ):
      updated_fields.append('labels')
    update_mask = ','.join(updated_fields)

    result = client.UpdateVolume(volume_ref, volume, update_mask, args.async_)
    if args.async_:
      command = 'gcloud {} netapp volumes list'.format(
          self.ReleaseTrack().prefix
      )
      log.status.Print(
          'Check the status of the updated volume by listing all volumes:\n  '
          '$ {} '.format(command)
      )
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Update a Cloud NetApp Volume."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, UpdateBeta._RELEASE_TRACK)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  """Update a Cloud NetApp Volume."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, UpdateAlpha._RELEASE_TRACK)

