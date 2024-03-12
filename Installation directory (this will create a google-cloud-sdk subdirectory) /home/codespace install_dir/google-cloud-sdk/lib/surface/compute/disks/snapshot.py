# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for snapshotting disks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.api_lib.compute import name_generator
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags
from googlecloudsdk.command_lib.compute.snapshots import flags as snap_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from six.moves import zip


DETAILED_HELP = {
    'brief': 'Create snapshots of Compute Engine persistent disks.',
    'DESCRIPTION': """
        *{command}* creates snapshots of persistent disks. Snapshots are useful
        for backing up data, copying a persistent disk, and even, creating a
        custom image. Snapshots can be created from persistent disks even while
        they are attached to running instances. Once created, snapshots may be
        managed (listed, deleted, etc.) via `gcloud compute snapshots`.

        Refer to the Snapshot best practices guide. https://cloud.google.com/compute/docs/disks/snapshot-best-practices

        {command} waits until the operation returns a status of `READY` or
        `FAILED`, or reaches the maximum timeout, and returns the last known
        details of the snapshot.

        Note: To create snapshots, the following IAM permissions are necessary
        ``compute.disks.createSnapshot'', ``compute.snapshots.create'',
        ``compute.snapshots.get'', and ``compute.zoneOperations.get''.
        """,
    'EXAMPLES': """
        To create a snapshot named `snapshot-test` of a persistent disk named `test`
        in zone `us-central1-a`, run:

          $ {command} test --zone=us-central1-a --snapshot-names=snapshot-test --description="This is an example snapshot"
    """
}


def _CommonArgs(parser):
  """Add parser arguments common to all tracks."""
  SnapshotDisks.disks_arg.AddArgument(parser)

  parser.add_argument(
      '--description',
      help=('Text to describe the snapshots being created.'))
  parser.add_argument(
      '--snapshot-names',
      type=arg_parsers.ArgList(min_length=1),
      metavar='SNAPSHOT_NAME',
      help="""\
      Names to assign to the created snapshots. Without this option, the
      name of each snapshot will be a random 12-character alphanumeric
      string that starts with a letter. The values of
      this option run parallel to the disks specified. For example,

          {command} my-disk-1 my-disk-2 my-disk-3 --snapshot-names snapshot-1,snapshot-2,snapshot-3

      will result in `my-disk-1` being snapshotted as
      `snapshot-1`, `my-disk-2` as `snapshot-2`, and so on. The name must match
      the `(?:[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?)` regular expression, which
      means it must start with an alphabetic character followed by one or more
      alphanumeric characters or dashes. The name must not exceed 63 characters
      and must not contain special symbols. All characters must be lowercase.
      """)
  snap_flags.AddChainArg(parser)
  flags.AddGuestFlushFlag(parser, 'snapshot')
  flags.AddStorageLocationFlag(parser, 'snapshot')
  csek_utils.AddCsekKeyArgs(parser, flags_about_creation=False)

  base.ASYNC_FLAG.AddToParser(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class SnapshotDisks(base.SilentCommand):
  """Create snapshots of Google Compute Engine persistent disks."""

  @classmethod
  def Args(cls, parser):
    SnapshotDisks.disks_arg = disks_flags.MakeDiskArg(plural=True)
    labels_util.AddCreateLabelsFlags(parser)
    _CommonArgs(parser)

  def Run(self, args):
    return self._Run(args)

  def _Run(self, args):
    """Returns a list of requests necessary for snapshotting disks."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())

    disk_refs = SnapshotDisks.disks_arg.ResolveAsResource(
        args, holder.resources,
        scope_lister=flags.GetDefaultScopeLister(holder.client))
    if args.snapshot_names:
      if len(disk_refs) != len(args.snapshot_names):
        raise exceptions.InvalidArgumentException(
            '--snapshot-names',
            '[--snapshot-names] must have the same number of values as disks '
            'being snapshotted.')
      snapshot_names = args.snapshot_names
    else:
      # Generates names like "d52jsqy3db4q".
      snapshot_names = [name_generator.GenerateRandomName()
                        for _ in disk_refs]

    snapshot_refs = [
        holder.resources.Parse(
            snapshot_name,
            params={
                'project': properties.VALUES.core.project.GetOrFail,
            },
            collection='compute.snapshots')
        for snapshot_name in snapshot_names]

    client = holder.client.apitools_client
    messages = holder.client.messages

    requests = []

    for disk_ref, snapshot_ref in zip(disk_refs, snapshot_refs):
      csek_keys = csek_utils.CsekKeyStore.FromArgs(args, True)
      snapshot_key_or_none = csek_utils.MaybeLookupKeyMessage(
          csek_keys, snapshot_ref, client)
      disk_key_or_none = csek_utils.MaybeLookupKeyMessage(
          csek_keys, disk_ref, client)

      snapshot_message = messages.Snapshot(
          name=snapshot_ref.Name(),
          description=args.description,
          snapshotEncryptionKey=snapshot_key_or_none,
          sourceDiskEncryptionKey=disk_key_or_none,
          chainName=args.chain_name)

      if (hasattr(args, 'storage_location') and
          args.IsSpecified('storage_location')):
        snapshot_message.storageLocations = [args.storage_location]
      if (hasattr(args, 'labels') and args.IsSpecified('labels')):
        snapshot_message.labels = labels_util.ParseCreateArgs(
            args, messages.Snapshot.LabelsValue)

      if disk_ref.Collection() == 'compute.disks':
        request = messages.ComputeDisksCreateSnapshotRequest(
            disk=disk_ref.Name(),
            snapshot=snapshot_message,
            project=disk_ref.project,
            zone=disk_ref.zone,
            guestFlush=args.guest_flush)
        requests.append((client.disks, 'CreateSnapshot', request))
      elif disk_ref.Collection() == 'compute.regionDisks':
        request = messages.ComputeRegionDisksCreateSnapshotRequest(
            disk=disk_ref.Name(),
            snapshot=snapshot_message,
            project=disk_ref.project,
            region=disk_ref.region)
        if hasattr(request, 'guestFlush'):  # only available in alpha API
          guest_flush = getattr(args, 'guest_flush', None)
          if guest_flush is not None:
            request.guestFlush = guest_flush
        requests.append((client.regionDisks, 'CreateSnapshot', request))

    errors_to_collect = []
    responses = holder.client.AsyncRequests(requests, errors_to_collect)
    for r in responses:
      err = getattr(r, 'error', None)
      if err:
        errors_to_collect.append(poller.OperationErrors(err.errors))
    if errors_to_collect:
      raise core_exceptions.MultiError(errors_to_collect)

    operation_refs = [holder.resources.Parse(r.selfLink) for r in responses]

    if args.async_:
      for operation_ref in operation_refs:
        log.status.Print('Disk snapshot in progress for [{}].'
                         .format(operation_ref.SelfLink()))
      log.status.Print('Use [gcloud compute operations describe URI] command '
                       'to check the status of the operation(s).')
      return responses

    operation_poller = poller.BatchPoller(
        holder.client, client.snapshots, snapshot_refs)
    return waiter.WaitFor(
        operation_poller, poller.OperationBatch(operation_refs),
        'Creating snapshot(s) {0}'
        .format(', '.join(s.Name() for s in snapshot_refs)),
        max_wait_ms=None
    )


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class SnapshotDisksBeta(SnapshotDisks):
  """Create snapshots of Google Compute Engine persistent disks beta."""

  @classmethod
  def Args(cls, parser):
    SnapshotDisks.disks_arg = disks_flags.MakeDiskArg(plural=True)
    labels_util.AddCreateLabelsFlags(parser)
    _CommonArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SnapshotDisksAlpha(SnapshotDisksBeta):
  """Create snapshots of Google Compute Engine persistent disks alpha."""

  @classmethod
  def Args(cls, parser):
    SnapshotDisks.disks_arg = disks_flags.MakeDiskArg(plural=True)
    labels_util.AddCreateLabelsFlags(parser)
    _CommonArgs(parser)

  def Run(self, args):
    return self._Run(args)


SnapshotDisks.detailed_help = DETAILED_HELP
