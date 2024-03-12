# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

_DEPRECATION_WARNING = """
`create-snapshot-schedule` is deprecated.
Use `compute resource-policies create snapshot-schedule` instead.
"""


def _CommonArgs(parser, api_version):
  """A helper function to build args based on different API version."""
  messages = apis.GetMessagesModule('compute', api_version)
  flags.MakeResourcePolicyArg().AddArgument(parser)
  flags.AddCommonArgs(parser)
  flags.AddCycleFrequencyArgs(
      parser,
      flag_suffix='schedule',
      start_time_help="""\
Start time for the disk snapshot schedule. See $ gcloud topic datetimes for information on time formats.
""",
      cadence_help='Snapshot schedule',
      supports_weekly=True,
      supports_hourly=True)
  flags.AddSnapshotScheduleArgs(parser, messages)
  parser.display_info.AddCacheUpdater(None)


@base.Deprecate(is_removed=False, warning=_DEPRECATION_WARNING)
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateSnapshotScheduleBeta(base.CreateCommand):
  """Create a Compute Engine Snapshot Schedule Resource Policy.

  *{command} creates a Resource Policy which can be attached to disks and
  specifies a schedule for taking disk snapshots and how long these snapshots
  should be retained.
  """

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


@base.Deprecate(is_removed=False, warning=_DEPRECATION_WARNING)
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateSnapshotScheduleAlpha(CreateSnapshotScheduleBeta):
  """Create a Compute Engine Snapshot Schedule Resource Policy.

  *{command} creates a Resource Policy which can be attached to disks and
  specifies a schedule for taking disk snapshots and how long these snapshots
  should be retained.
  """

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, api_version=compute_api.COMPUTE_ALPHA_API_VERSION)


CreateSnapshotScheduleBeta.detailed_help = {
    'DESCRIPTION':
        """\
Create a Compute Engine Snapshot Schedule Resource Policy.
""",
    'EXAMPLES':
        """\
The following command creates a Compute Engine Snapshot Schedule Resource Policy with a daily snapshot and a one day snapshot retention policy.

  $ {command} my-resource-policy --region=REGION --start-time=04:00Z --daily-schedule --max-retention-days=1
"""
}
