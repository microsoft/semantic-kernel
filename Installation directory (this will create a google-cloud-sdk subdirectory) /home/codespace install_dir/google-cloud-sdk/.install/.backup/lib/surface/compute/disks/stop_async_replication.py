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
"""Command for stopping async replication on disks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags

DETAILED_HELP = {
    'brief': 'Stop async replication on a Compute Engine persistent disk',
    'DESCRIPTION': """\
        *{command}* stops async replication on a Compute Engine persistent
        disk. This command can be invoked either on the primary or on the
        secondary disk.
        """,
    'EXAMPLES': """\
        Stop replication on the primary disk 'my-disk-1' in zone us-east1-a:

          $ {command} my-disk-1 --zone=us-east1-a

        Stop replication on the secondary disk 'my-disk-2' in zone us-west1-a:

          $ {command} my-disk-2 --zone=us-west1-a
        """,
}


def _CommonArgs(parser):
  """Add arguments used for parsing in all command tracks."""
  StopAsyncReplication.disks_arg.AddArgument(
      parser, operation_type='stop async replication')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class StopAsyncReplication(base.Command):
  """Stop Async Replication on Compute Engine persistent disks."""

  @classmethod
  def Args(cls, parser):
    StopAsyncReplication.disks_arg = disks_flags.MakeDiskArg(plural=False)
    _CommonArgs(parser)

  @classmethod
  def _GetApiHolder(cls, no_http=False):
    return base_classes.ComputeApiHolder(cls.ReleaseTrack(), no_http)

  def Run(self, args):
    return self._Run(args)

  def _Run(self, args):
    compute_holder = self._GetApiHolder()
    client = compute_holder.client

    disk_ref = StopAsyncReplication.disks_arg.ResolveAsResource(
        args,
        compute_holder.resources,
        scope_lister=flags.GetDefaultScopeLister(client))

    request = None
    if disk_ref.Collection() == 'compute.disks':
      request = client.messages.ComputeDisksStopAsyncReplicationRequest(
          disk=disk_ref.Name(),
          project=disk_ref.project,
          zone=disk_ref.zone,
      )
      request = (client.apitools_client.disks, 'StopAsyncReplication', request)
    elif disk_ref.Collection() == 'compute.regionDisks':
      request = client.messages.ComputeRegionDisksStopAsyncReplicationRequest(
          disk=disk_ref.Name(),
          project=disk_ref.project,
          region=disk_ref.region,
      )
      request = (client.apitools_client.regionDisks, 'StopAsyncReplication',
                 request)
    return client.MakeRequests([request])


StopAsyncReplication.detailed_help = DETAILED_HELP


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class StopAsyncReplicationBeta(StopAsyncReplication):
  """Stop Async Replication on Compute Engine persistent disks."""

  @classmethod
  def Args(cls, parser):
    StopAsyncReplication.disks_arg = disks_flags.MakeDiskArg(plural=False)
    _CommonArgs(parser)

  def Run(self, args):
    return self._Run(args)


StopAsyncReplicationBeta.detailed_help = DETAILED_HELP


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class StopAsyncReplicationAlpha(StopAsyncReplication):
  """Stop Async Replication on Compute Engine persistent disks."""

  @classmethod
  def Args(cls, parser):
    StopAsyncReplication.disks_arg = disks_flags.MakeDiskArg(plural=False)
    _CommonArgs(parser)

  def Run(self, args):
    return self._Run(args)


StopAsyncReplicationAlpha.detailed_help = DETAILED_HELP
