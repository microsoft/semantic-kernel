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
"""Delete resource policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.resource_policies import flags


class Delete(base.DeleteCommand):
  """Delete a Compute Engine resource policy."""

  @staticmethod
  def Args(parser):
    flags.MakeResourcePolicyArg().AddArgument(parser)
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    policy_ref = flags.MakeResourcePolicyArg().ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    messages = holder.client.messages
    request = messages.ComputeResourcePoliciesDeleteRequest(
        resourcePolicy=policy_ref.Name(),
        project=policy_ref.project,
        region=policy_ref.region)

    service = holder.client.apitools_client.resourcePolicies
    return client.MakeRequests([(service, 'Delete', request)])


Delete.detailed_help = {
    'DESCRIPTION':
        """\
Delete a Compute Engine resource policy.
""",
    'EXAMPLES':
        """\
The following command deletes a Compute Engine resource policy.

  $ {command} my-resource-policy --region=REGION
"""
}
