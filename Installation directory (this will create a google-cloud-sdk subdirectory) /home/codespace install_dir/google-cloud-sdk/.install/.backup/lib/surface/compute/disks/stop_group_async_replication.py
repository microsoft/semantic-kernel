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
"""Command for stopping group async replication on disks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags
from googlecloudsdk.core import properties

DETAILED_HELP = {
    'brief':
        'Consistently stops a group of asynchronously replicating disks',
    'DESCRIPTION':
        """\
        *{command}* consistently stops a group of asynchronously replicating
        disks. This command can be invoked in either in the primary or secondary
        scope of the replicating disks.
        """,
    'EXAMPLES':
        """\
        To stop group replication in the primary scope, include the zone or
        region of the primary disks. The URL of the disk consistency group
        resource policy always uses the region of the primary disks:

          $ {command} projects/my-project/regions/us-west1/resourcePolicies/my-policy --zone=us-west1-a

        Alternatively, you can stop replication in the secondary scope. Include
        the region or zone of the secondary disks. The URL of the disk
        consistency group resource policy always uses the region of the primary
        disks:

          $ {command} projects/my-project/regions/us-west1/resourcePolicies/my-policy --zone=us-west2-a
        """,
}


def _CommonArgs(parser):
  """Add arguments used for parsing in all command tracks."""
  disks_flags.AddStopGroupAsyncReplicationArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class StopGroupAsyncReplication(base.Command):
  """Stop Group Async Replication for a Consistency Group Resource Policy."""

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser)

  @classmethod
  def _GetApiHolder(cls, no_http=False):
    return base_classes.ComputeApiHolder(cls.ReleaseTrack(), no_http)

  def Run(self, args):
    return self._Run(args)

  def _Run(self, args):
    compute_holder = self._GetApiHolder()
    client = compute_holder.client

    policy_url = getattr(args, 'DISK_CONSISTENCY_GROUP_POLICY', None)
    project = properties.VALUES.core.project.GetOrFail()
    if args.IsSpecified('zone'):
      request = client.messages.ComputeDisksStopGroupAsyncReplicationRequest(
          project=project,
          zone=args.zone,
          disksStopGroupAsyncReplicationResource=client.messages
          .DisksStopGroupAsyncReplicationResource(
              resourcePolicy=policy_url))
      request = (client.apitools_client.disks, 'StopGroupAsyncReplication',
                 request)
    else:
      request = client.messages.ComputeRegionDisksStopGroupAsyncReplicationRequest(
          project=project,
          region=args.region,
          disksStopGroupAsyncReplicationResource=client.messages
          .DisksStopGroupAsyncReplicationResource(
              resourcePolicy=policy_url))
      request = (client.apitools_client.regionDisks,
                 'StopGroupAsyncReplication', request)
    return client.MakeRequests([request], no_followup=True)


StopGroupAsyncReplication.detailed_help = DETAILED_HELP


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class StopGroupAsyncReplicationBeta(StopGroupAsyncReplication):
  """Stop Group Async Replication for a Consistency Group Resource Policy."""

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser)

  def Run(self, args):
    return self._Run(args)


StopGroupAsyncReplicationBeta.detailed_help = DETAILED_HELP


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class StopGroupAsyncReplicationAlpha(StopGroupAsyncReplication):
  """Stop Group Async Replication for a Consistency Group Resource Policy."""

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser)

  def Run(self, args):
    return self._Run(args)


StopGroupAsyncReplicationAlpha.detailed_help = DETAILED_HELP
