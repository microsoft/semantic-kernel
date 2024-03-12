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
"""Create resource policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.resource_policies import flags
from googlecloudsdk.command_lib.compute.resource_policies import util

DETAILED_HELP = {
    'DESCRIPTION': """\
        Create a Compute Engine disk consistency group resource policy.
        """,
    'EXAMPLES': """\
        Create a disk consistency group policy:

          $ {command} my-resource-policy --region=REGION
        """
}


def _CommonArgs(parser):
  """A helper function to build args based on different API version."""
  CreateDiskConsistencyGroup.resource_policy_arg.AddArgument(parser)
  flags.AddCommonArgs(parser)
  parser.display_info.AddCacheUpdater(None)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateDiskConsistencyGroup(base.CreateCommand):
  """Create a Compute Engine Disk Consistency Group resource policy."""

  @staticmethod
  def Args(parser):
    CreateDiskConsistencyGroup.resource_policy_arg = (
        flags.MakeResourcePolicyArg())
    _CommonArgs(parser)

  def Run(self, args):
    return self._Run(args)

  def _Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    policy_ref = self.resource_policy_arg.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    messages = holder.client.messages
    resource_policy = util.MakeDiskConsistencyGroupPolicy(
        policy_ref, args, messages)
    create_request = messages.ComputeResourcePoliciesInsertRequest(
        resourcePolicy=resource_policy,
        project=policy_ref.project,
        region=policy_ref.region)

    service = holder.client.apitools_client.resourcePolicies
    return client.MakeRequests([(service, 'Insert', create_request)])[0]


CreateDiskConsistencyGroup.detailed_help = DETAILED_HELP


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateDiskConsistencyGroupBeta(CreateDiskConsistencyGroup):
  """Create a Compute Engine Disk Consistency Group resource policy."""

  @staticmethod
  def Args(parser):
    CreateDiskConsistencyGroup.resource_policy_arg = (
        flags.MakeResourcePolicyArg())
    _CommonArgs(parser)

  def Run(self, args):
    return self._Run(args)


CreateDiskConsistencyGroupBeta.detailed_help = DETAILED_HELP


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateDiskConsistencyGroupAlpha(CreateDiskConsistencyGroup):
  """Create a Compute Engine Disk Consistency Group resource policy."""

  @staticmethod
  def Args(parser):
    CreateDiskConsistencyGroup.resource_policy_arg = (
        flags.MakeResourcePolicyArg())
    _CommonArgs(parser)

  def Run(self, args):
    return self._Run(args)


CreateDiskConsistencyGroupAlpha.detailed_help = DETAILED_HELP
