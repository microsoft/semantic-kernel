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


def _CommonArgs(parser, api_version, track):
  """A helper function to build args based on different API version."""
  messages = apis.GetMessagesModule('compute', api_version)
  flags.MakeResourcePolicyArg().AddArgument(parser)
  flags.AddCommonArgs(parser)
  flags.AddGroupPlacementArgs(parser, messages, track)
  parser.display_info.AddCacheUpdater(None)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateGroupPlacement(base.CreateCommand):
  """Create a Compute Engine group placement resource policy."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, compute_api.COMPUTE_ALPHA_API_VERSION,
                base.ReleaseTrack.ALPHA)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    policy_ref = flags.MakeResourcePolicyArg().ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    messages = holder.client.messages
    resource_policy = util.MakeGroupPlacementPolicy(policy_ref, args, messages,
                                                    self.ReleaseTrack())
    create_request = messages.ComputeResourcePoliciesInsertRequest(
        resourcePolicy=resource_policy,
        project=policy_ref.project,
        region=policy_ref.region)

    service = holder.client.apitools_client.resourcePolicies
    return client.MakeRequests([(service, 'Insert', create_request)])[0]


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateGroupPlacementBeta(CreateGroupPlacement):
  """Create a Compute Engine group placement resource policy."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, compute_api.COMPUTE_BETA_API_VERSION,
                base.ReleaseTrack.BETA)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGroupPlacementGa(CreateGroupPlacement):
  """Create a Compute Engine group placement resource policy."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, compute_api.COMPUTE_GA_API_VERSION,
                base.ReleaseTrack.GA)


CreateGroupPlacement.detailed_help = {
    'DESCRIPTION':
        """\
Create a Compute Engine Group Placement Resource Policy.
""",
    'EXAMPLES':
        """\
To create a Compute Engine group placement policy with two
availability domains, run:
  $ {command} my-resource-policy --region=REGION --availability-domain-count=2
"""
}
