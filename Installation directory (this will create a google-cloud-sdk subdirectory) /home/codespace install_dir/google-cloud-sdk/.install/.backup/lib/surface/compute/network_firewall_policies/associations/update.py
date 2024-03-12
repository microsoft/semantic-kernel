# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command for updating network firewall policy associations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import firewall_policy_association_utils as association_utils
from googlecloudsdk.api_lib.compute.network_firewall_policies import region_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.network_firewall_policies import flags


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update association between a firewall policy and a network.

  *{command}* is used to update network firewall policy associations. A
  network firewall policy is a set of rules that controls access to various
  resources.
  """

  NETWORK_FIREWALL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.NETWORK_FIREWALL_POLICY_ARG = (
        flags.NetworkFirewallPolicyAssociationArgument(
            required=True, operation='update', allow_global=False
        )
    )
    cls.NETWORK_FIREWALL_POLICY_ARG.AddArgument(parser, operation_type='update')
    flags.AddArgsUpdateAssociation(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.NETWORK_FIREWALL_POLICY_ARG.ResolveAsResource(
        args, holder.resources
    )

    network_firewall_policy = region_client.RegionNetworkFirewallPolicy(
        ref, compute_client=holder.client
    )

    priority = association_utils.ConvertPriorityToInt(args.priority)

    association = holder.client.messages.FirewallPolicyAssociation(
        name=args.name, priority=priority
    )

    return network_firewall_policy.PatchAssociation(
        association=association,
        firewall_policy=args.firewall_policy,
        only_generate_request=False,
    )


Update.detailed_help = {
    'EXAMPLES': """\
  To update priority of association named ``my-association'' on network
  firewall policy with name ``my-policy'' in region ``region-a'', run:

    $ {command}
        --firewall-policy=my-policy
        --name=my-association
        --firewall-policy-region=region-a
        --priority=new-priority
  """,
}
