# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Create resource policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils as compute_api
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.resource_policies import flags
from googlecloudsdk.command_lib.compute.resource_policies import util


def _CommonArgs(parser, api_version):
  """A helper function to build args based on different API version."""
  messages = apis.GetMessagesModule('compute', api_version)
  flags.MakeResourcePolicyArg().AddArgument(parser)
  flags.AddCommonArgs(parser)
  flags.AddCycleFrequencyArgs(
      parser,
      flag_suffix='schedule',
      start_time_help="""\
Start time for the disk snapshot schedule in UTC. For example, `--start-time="15:00"`.
""",
      cadence_help='Snapshot schedule',
      supports_weekly=True,
      supports_hourly=True)
  flags.AddSnapshotScheduleArgs(parser, messages)
  parser.display_info.AddCacheUpdater(None)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateSnapshotSchedule(base.CreateCommand):
  """Create a Compute Engine Snapshot Schedule Resource Policy."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, api_version=compute_api.COMPUTE_BETA_API_VERSION)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    policy_ref = flags.MakeResourcePolicyArg().ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    messages = holder.client.messages
    resource_policy = util.MakeDiskSnapshotSchedulePolicy(
        policy_ref, args, messages)
    create_request = messages.ComputeResourcePoliciesInsertRequest(
        resourcePolicy=resource_policy,
        project=policy_ref.project,
        region=policy_ref.region)

    service = holder.client.apitools_client.resourcePolicies
    return client.MakeRequests([(service, 'Insert', create_request)])[0]


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateSnapshotScheduleBeta(CreateSnapshotSchedule):
  """Create a Compute Engine Snapshot Schedule Resource Policy."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, api_version=compute_api.COMPUTE_ALPHA_API_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateSnapshotScheduleAlpha(CreateSnapshotScheduleBeta):
  """Create a Compute Engine Snapshot Schedule Resource Policy."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, api_version=compute_api.COMPUTE_ALPHA_API_VERSION)


CreateSnapshotSchedule.detailed_help = {
    'DESCRIPTION':
        """\
Create a Compute Engine Snapshot Schedule Resource Policy.
""",
    'EXAMPLES':
        """\
The following command creates a Compute Engine Snapshot Schedule Resource Policy with a daily snapshot taken at 13:00Z and a one day snapshot retention policy.

  $ {command} my-resource-policy --region=REGION --start-time=13:00 --daily-schedule --max-retention-days=1
"""
}
