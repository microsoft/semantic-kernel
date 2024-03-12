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
"""Command for starting async replication on disks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags

DETAILED_HELP = {
    'brief':
        'Start asynchronous replication on a Compute Engine persistent disk',
    'DESCRIPTION':
        """\
        *{command}* starts async replication on a Compute Engine persistent
        disk. This command must be invoked on the primary disk and
        `--secondary-disk` must be provided.
        """,
    'EXAMPLES':
        """\
        Start replication from the primary disk 'my-disk-1' in zone us-east1-a
        to the secondary disk 'my-disk-2' in zone us-west1-a:

          $ {command} my-disk-1 --zone=us-east1-a --secondary-disk=my-disk-2 --secondary-disk-zone=us-west1-a
        """,
}


def _CommonArgs(parser):
  """Add arguments used for parsing in all command tracks."""
  StartAsyncReplication.disks_arg.AddArgument(parser, scope_required=True)
  secondary_disk_category = 'SECONDARY DISK'
  StartAsyncReplication.secondary_disk_arg.AddArgument(
      parser, category=secondary_disk_category, scope_required=True
  )
  disks_flags.AddSecondaryDiskProject(parser, secondary_disk_category)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class StartAsyncReplication(base.Command):
  """Start Async Replication on Compute Engine persistent disks."""

  @classmethod
  def Args(cls, parser):
    StartAsyncReplication.disks_arg = disks_flags.MakeDiskArg(plural=False)
    StartAsyncReplication.secondary_disk_arg = disks_flags.MakeSecondaryDiskArg(
        required=True)
    _CommonArgs(parser)

  def GetAsyncSecondaryDiskUri(self, args, compute_holder):
    secondary_disk_ref = None
    if args.secondary_disk:
      secondary_disk_project = getattr(args, 'secondary_disk_project', None)
      secondary_disk_ref = self.secondary_disk_arg.ResolveAsResource(
          args, compute_holder.resources, source_project=secondary_disk_project
      )
      if secondary_disk_ref:
        return secondary_disk_ref.SelfLink()
    return None

  @classmethod
  def _GetApiHolder(cls, no_http=False):
    return base_classes.ComputeApiHolder(cls.ReleaseTrack(), no_http)

  def Run(self, args):
    return self._Run(args)

  def _Run(self, args):
    compute_holder = self._GetApiHolder()
    client = compute_holder.client

    disk_ref = StartAsyncReplication.disks_arg.ResolveAsResource(
        args,
        compute_holder.resources,
        scope_lister=flags.GetDefaultScopeLister(client))

    request = None
    secondary_disk_uri = self.GetAsyncSecondaryDiskUri(args, compute_holder)
    if disk_ref.Collection() == 'compute.disks':
      request = client.messages.ComputeDisksStartAsyncReplicationRequest(
          disk=disk_ref.Name(),
          project=disk_ref.project,
          zone=disk_ref.zone,
          disksStartAsyncReplicationRequest=client.messages
          .DisksStartAsyncReplicationRequest(
              asyncSecondaryDisk=secondary_disk_uri))
      request = (client.apitools_client.disks, 'StartAsyncReplication', request)
    elif disk_ref.Collection() == 'compute.regionDisks':
      request = client.messages.ComputeRegionDisksStartAsyncReplicationRequest(
          disk=disk_ref.Name(),
          project=disk_ref.project,
          region=disk_ref.region,
          regionDisksStartAsyncReplicationRequest=client.messages
          .RegionDisksStartAsyncReplicationRequest(
              asyncSecondaryDisk=secondary_disk_uri))
      request = (client.apitools_client.regionDisks, 'StartAsyncReplication',
                 request)
    return client.MakeRequests([request])


StartAsyncReplication.detailed_help = DETAILED_HELP


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class StartAsyncReplicationBeta(StartAsyncReplication):
  """Start Async Replication on Compute Engine persistent disks."""

  @classmethod
  def Args(cls, parser):
    StartAsyncReplication.disks_arg = disks_flags.MakeDiskArg(plural=False)
    StartAsyncReplication.secondary_disk_arg = disks_flags.MakeSecondaryDiskArg(
        required=True)
    _CommonArgs(parser)

  def Run(self, args):
    return self._Run(args)


StartAsyncReplicationBeta.detailed_help = DETAILED_HELP


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class StartAsyncReplicationAlpha(StartAsyncReplication):
  """Start Async Replication on Compute Engine persistent disks."""

  @classmethod
  def Args(cls, parser):
    StartAsyncReplication.disks_arg = disks_flags.MakeDiskArg(plural=False)
    StartAsyncReplication.secondary_disk_arg = disks_flags.MakeSecondaryDiskArg(
        required=True)
    _CommonArgs(parser)

  def Run(self, args):
    return self._Run(args)


StartAsyncReplicationAlpha.detailed_help = DETAILED_HELP
