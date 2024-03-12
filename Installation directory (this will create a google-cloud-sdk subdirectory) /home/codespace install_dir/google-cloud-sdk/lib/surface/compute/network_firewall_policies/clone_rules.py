# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command for replacing the rules of organization firewall policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.network_firewall_policies import client
from googlecloudsdk.api_lib.compute.network_firewall_policies import region_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.network_firewall_policies import flags


class CloneRules(base.UpdateCommand):
  """Replace the rules of a Compute Engine network firewall policy with rules from another policy.

  *{command}* is used to replace the rules of network firewall policies. A
   network firewall policy is a set of rules that controls access to
   various resources.
  """

  NETWORK_FIREWALL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.NETWORK_FIREWALL_POLICY_ARG = flags.NetworkFirewallPolicyArgument(
        required=True, operation='clone the rules to')
    cls.NETWORK_FIREWALL_POLICY_ARG.AddArgument(
        parser, operation_type='clone-rules')
    flags.AddArgsCloneRules(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.NETWORK_FIREWALL_POLICY_ARG.ResolveAsResource(
        args, holder.resources)
    scope = compute_scope.ScopeEnum.GLOBAL
    network_firewall_policy = client.NetworkFirewallPolicy(
        ref, compute_client=holder.client)
    if hasattr(ref, 'region'):
      network_firewall_policy = region_client.RegionNetworkFirewallPolicy(
          ref, compute_client=holder.client)
      scope = compute_scope.ScopeEnum.REGION

    src_firewall_policy_ref = flags.NetworkSrcFirewallPolicyRuleArgument(
    ).ResolveAsResource(
        args, holder.resources, default_scope=scope)

    return network_firewall_policy.CloneRules(
        source_firewall_policy=src_firewall_policy_ref.SelfLink(),
        only_generate_request=False)

CloneRules.detailed_help = {
    'EXAMPLES':
        """\
    To clone the rules of a global network firewall policy with NAME
    ``my-policy'',
    from another network firewall policy with NAME
    ``source-policy'', run:

      $ {command} my-policy --source-firewall-policy=source-policy --global

    To clone the rules of a region network firewall policy with NAME
    ``my-region-policy'', in region ``region-a'',
    from another network firewall policy with NAME
    ``source-policy'', run:

      $ {command} my-region-policy \
          --source-firewall-policy=source-policy \
          --region=region-a
    """,
}
