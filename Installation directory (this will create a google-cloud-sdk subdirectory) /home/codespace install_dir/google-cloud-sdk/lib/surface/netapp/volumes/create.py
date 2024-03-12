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
"""Create a Cloud NetApp Volume."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.volumes  import client as volumes_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.volumes import flags as volumes_flags
from googlecloudsdk.command_lib.util.args import labels_util

from googlecloudsdk.core import log


def _CommonArgs(parser, release_track):
  volumes_flags.AddVolumeCreateArgs(parser, release_track=release_track)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Cloud NetApp Volume."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  detailed_help = {
      'DESCRIPTION': """\
          Create a Cloud NetApp Volume
          """,
      'EXAMPLES': """\
          The following command creates a NFS Volume named NAME asynchronously using the specified arguments

              $ {command} NAME --capacity=1024 --protocols=nfsv3,nfsv4 --share-name=share1 --storage-pool=sp1 --description="test description" --enable-kerberos=true --unix-permissions=0755 --async

          The following command creates a SMB Volume named NAME asynchronously using the specified arguments

              $ {command} NAME --capacity=1024 --protocols=smb --share-name=share2 --storage-pool=sp2 --description="test smb" --security-style=ntfs --smb-settings=SHOW_SNAPSHOT,SHOW_PREVIOUS_VERSIONS,ACCESS_BASED_ENUMERATION --snap-reserve=0.1 --async
          """,
  }

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, Create._RELEASE_TRACK)

  def Run(self, args):
    """Create a Cloud NetApp Volume in the current project."""
    volume_ref = args.CONCEPTS.volume.Parse()
    client = volumes_client.VolumesClient(self._RELEASE_TRACK)
    ## Fill in protocol types into list
    protocols = []
    for protocol in args.protocols:
      protocol_enum = volumes_flags.GetVolumeProtocolEnumFromArg(
          protocol, client.messages)
      protocols.append(protocol_enum)
    capacity_in_gib = args.capacity >> 30
    smb_settings = []
    if args.smb_settings:
      for smb_setting in args.smb_settings:
        smb_setting_enum = (
            volumes_flags.GetVolumeSmbSettingsEnumFromArg(
                smb_setting, client.messages))
        smb_settings.append(smb_setting_enum)
    snapshot_policy = {}
    for name, snapshot_schedule in {
        'hourly_snapshot': args.snapshot_hourly,
        'daily_snapshot': args.snapshot_daily,
        'weekly_snapshot': args.snapshot_weekly,
        'monthly_snapshot': args.snapshot_monthly
    }.items():
      if snapshot_schedule:  # snapshot schedule is set
        snapshot_policy[name] = snapshot_schedule
    if not snapshot_policy:
      # if no snapshot_schedule was set in args, change to None type for
      # ParseVolumeConfig to easily parse
      snapshot_policy = None
    security_style = volumes_flags.GetVolumeSecurityStyleEnumFromArg(
        args.security_style, client.messages
    )
    restricted_actions = []
    if args.restricted_actions:
      for restricted_action in args.restricted_actions:
        restricted_action_enum = (
            volumes_flags.GetVolumeRestrictedActionsEnumFromArg(
                restricted_action, client.messages
            )
        )
        restricted_actions.append(restricted_action_enum)
    labels = labels_util.ParseCreateArgs(
        args, client.messages.Volume.LabelsValue
    )
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
    if (self._RELEASE_TRACK == base.ReleaseTrack.ALPHA or
        self._RELEASE_TRACK == base.ReleaseTrack.BETA):
      large_capacity = args.large_capacity
      multiple_endpoints = args.multiple_endpoints
    else:
      large_capacity = None
      multiple_endpoints = None

    volume = client.ParseVolumeConfig(
        name=volume_ref.RelativeName(),
        capacity=capacity_in_gib,
        description=args.description,
        labels=labels,
        storage_pool=args.storage_pool,
        protocols=protocols,
        share_name=args.share_name,
        export_policy=args.export_policy,
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
        backup_config=backup_config,
        large_capacity=large_capacity,
        multiple_endpoints=multiple_endpoints)
    result = client.CreateVolume(volume_ref, args.async_, volume)
    if args.async_:
      command = 'gcloud {} netapp volumes list'.format(
          self.ReleaseTrack().prefix)
      log.status.Print(
          'Check the status of the new volume by listing all volumes:\n  '
          '$ {} '.format(command))
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a Cloud NetApp Volume."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, CreateBeta._RELEASE_TRACK)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create a Cloud NetApp Volume."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, CreateAlpha._RELEASE_TRACK)

