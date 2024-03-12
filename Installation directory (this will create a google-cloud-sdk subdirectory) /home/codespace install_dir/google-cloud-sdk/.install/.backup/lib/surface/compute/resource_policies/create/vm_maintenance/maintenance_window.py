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
"""Create VM maintenance resource policy maintenance-window command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.resource_policies import flags
from googlecloudsdk.command_lib.compute.resource_policies import util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateVmMaintenanceMaintenanceWindow(base.CreateCommand):
  """Create a Compute Engine VM Maintenance Resource Policy.

  *{command} creates a Compute Engine VM Maintenance Resource Policy
  that, contains a window in which maintenance should start.
  """

  @staticmethod
  def Args(parser):
    flags.MakeResourcePolicyArg().AddArgument(parser)
    flags.AddCommonArgs(parser)
    flags.AddCycleFrequencyArgs(
        parser,
        flag_suffix='window',
        start_time_help=('Start time of a four-hour window in which '
                         'maintenance should start in daily cadence.'),
        cadence_help='Maintenance activity window',
        has_restricted_start_times=True)
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    policy_ref = flags.MakeResourcePolicyArg().ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    messages = holder.client.messages
    resource_policy = util.MakeVmMaintenanceMaintenanceWindow(policy_ref,
                                                              args, messages)
    create_request = messages.ComputeResourcePoliciesInsertRequest(
        resourcePolicy=resource_policy,
        project=policy_ref.project,
        region=policy_ref.region)

    service = holder.client.apitools_client.resourcePolicies
    return client.MakeRequests([(service, 'Insert', create_request)])[0]


CreateVmMaintenanceMaintenanceWindow.detailed_help = {
    'DESCRIPTION':
    """\
Create a Compute Engine VM Maintenance Resource Policy that
contains time window in which maintenance should start.
""",
    'EXAMPLES':
    """\
  The following command creates a Compute Engine VM Maintenance Resource
  Policy with a daily maintenance activity window that starts at 04:00Z.

    $ {command} my-resource-policy --region=REGION --start-time=04:00 --daily-window
"""
}
