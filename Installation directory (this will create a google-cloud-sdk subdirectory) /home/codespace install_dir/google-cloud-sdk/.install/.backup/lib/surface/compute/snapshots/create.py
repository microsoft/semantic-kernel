# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command for creating snapshots."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.snapshots import flags as snap_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def _GAArgs(parser):
  """Set Args based on Release Track."""

  # GA specific args
  parser.add_argument('name', help='The name of the snapshot.')
  snap_flags.AddChainArg(parser)
  snap_flags.AddSourceDiskCsekKey(parser)
  flags.AddGuestFlushFlag(
      parser,
      'snapshot',
      custom_help="""
  Create an application-consistent snapshot by informing the OS
  to prepare for the snapshot process. Currently only supported
  for creating snapshots of disks attached to Windows instances.
  """,
  )
  flags.AddStorageLocationFlag(parser, 'snapshot')
  labels_util.AddCreateLabelsFlags(parser)
  csek_utils.AddCsekKeyArgs(parser, flags_about_creation=False)
  base.ASYNC_FLAG.AddToParser(parser)
  parser.add_argument(
      '--description', help='Text to describe the new snapshot.'
  )
  snap_flags.SOURCE_DISK_ARG.AddArgument(parser)
  snap_flags.AddSnapshotType(parser)
  snap_flags.SOURCE_DISK_FOR_RECOVERY_CHECKPOINT_ARG.AddArgument(parser)
  snap_flags.SOURCE_INSTANT_SNAPSHOT_ARG.AddArgument(parser)
  snap_flags.AddSourceInstantSnapshotCsekKey(parser)


def _BetaArgs(parser):
  _GAArgs(parser)


def _AlphaArgs(parser):
  _GAArgs(parser)
  snap_flags.AddMaxRetentionDays(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create snapshots of Google Compute Engine persistent disks."""

  @staticmethod
  def Args(parser):
    _GAArgs(parser)

  def Run(self, args):
    return self._Run(args)

  def _Run(
      self,
      args,
      support_max_retention_days=False,
  ):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = holder.client.messages
    snap_ref = holder.resources.Parse(
        args.name,
        params={
            'project': properties.VALUES.core.project.GetOrFail,
        },
        collection='compute.snapshots',
    )

    snapshot_message = messages.Snapshot(
        name=snap_ref.Name(), description=args.description
    )
    # This feature is only exposed in alpha/beta
    allow_rsa_encrypted = self.ReleaseTrack() in [
        base.ReleaseTrack.ALPHA,
        base.ReleaseTrack.BETA,
    ]
    if args.source_disk:
      disk_ref = snap_flags.SOURCE_DISK_ARG.ResolveAsResource(
          args,
          holder.resources,
          scope_lister=flags.GetDefaultScopeLister(holder.client),
      )
      snapshot_message.sourceDisk = disk_ref.SelfLink()
      if args.source_disk_key_file:
        source_keys = csek_utils.CsekKeyStore.FromFile(
            args.source_disk_key_file, allow_rsa_encrypted
        )
        disk_key_or_none = csek_utils.MaybeLookupKeyMessage(
            source_keys, disk_ref, client
        )
        snapshot_message.sourceDiskEncryptionKey = disk_key_or_none
    if args.source_disk_for_recovery_checkpoint:
      source_disk_for_recovery_checkpoint_ref = (
          snap_flags.SOURCE_DISK_FOR_RECOVERY_CHECKPOINT_ARG.ResolveAsResource(
              args,
              holder.resources,
              default_scope=compute_scope.ScopeEnum.REGION,
          )
      )
      snapshot_message.sourceDiskForRecoveryCheckpoint = (
          source_disk_for_recovery_checkpoint_ref.SelfLink()
      )
    if args.csek_key_file:
      csek_keys = csek_utils.CsekKeyStore.FromArgs(args, allow_rsa_encrypted)
      snap_key_or_none = csek_utils.MaybeLookupKeyMessage(
          csek_keys, snap_ref, client
      )
      snapshot_message.snapshotEncryptionKey = snap_key_or_none
    if hasattr(args, 'labels') and args.IsSpecified('labels'):
      snapshot_message.labels = labels_util.ParseCreateArgs(
          args, messages.Snapshot.LabelsValue
      )
    if args.storage_location:
      snapshot_message.storageLocations = [args.storage_location]
    if args.guest_flush:
      snapshot_message.guestFlush = True
    if args.chain_name:
      snapshot_message.chainName = args.chain_name
    if args.source_instant_snapshot:
      iss_ref = snap_flags.SOURCE_INSTANT_SNAPSHOT_ARG.ResolveAsResource(
          args,
          holder.resources,
          scope_lister=flags.GetDefaultScopeLister(holder.client),
      )
      snapshot_message.sourceInstantSnapshot = iss_ref.SelfLink()
      if args.source_instant_snapshot_key_file:
        source_keys = csek_utils.CsekKeyStore.FromFile(
            args.source_instant_snapshot_key_file, allow_rsa_encrypted
        )
        instant_snapshot_key_or_none = csek_utils.MaybeLookupKeyMessage(
            source_keys, iss_ref, client
        )
        snapshot_message.sourceInstantSnapshotEncryptionKey = (
            instant_snapshot_key_or_none
        )

    if args.IsSpecified('snapshot_type'):
      snapshot_message.snapshotType = (
          snapshot_message.SnapshotTypeValueValuesEnum(args.snapshot_type)
      )

    if support_max_retention_days and args.IsSpecified('max_retention_days'):
      snapshot_message.maxRetentionDays = int(args.max_retention_days)

    request = messages.ComputeSnapshotsInsertRequest(
        snapshot=snapshot_message, project=snap_ref.project
    )
    result = client.snapshots.Insert(request)
    operation_ref = resources.REGISTRY.Parse(
        result.name,
        params={'project': snap_ref.project},
        collection='compute.globalOperations',
    )
    if args.async_:
      log.UpdatedResource(
          operation_ref,
          kind='gce snapshot {0}'.format(snap_ref.Name()),
          is_async=True,
          details=(
              'Use [gcloud compute operations describe] command '
              'to check the status of this operation.'
          ),
      )
      return result
    operation_poller = poller.Poller(client.snapshots, snap_ref)
    return waiter.WaitFor(
        operation_poller,
        operation_ref,
        'Creating gce snapshot {0}'.format(snap_ref.Name()),
    )


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):

  @staticmethod
  def Args(parser):
    _BetaArgs(parser)

  def Run(self, args):
    return self._Run(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):

  @staticmethod
  def Args(parser):
    _AlphaArgs(parser)

  def Run(self, args):
    return self._Run(
        args,
        support_max_retention_days=True,
    )


Create.detailed_help = {
    'brief': 'Create Compute Engine snapshots',
    'DESCRIPTION': """\
    *{command}* creates snapshot of persistent disk. Snapshots are useful for
    backing up persistent disk data and for creating custom images.
    For more information, see https://cloud.google.com/compute/docs/disks/create-snapshots.
    """,
    'EXAMPLES': """\
    To create a snapshot 'my-snap' from a disk 'my-disk' in zone 'us-east1-a', run:

        $ {command} my-snap --source-disk=my-disk --source-disk-zone=us-east1-a
    """,
}
