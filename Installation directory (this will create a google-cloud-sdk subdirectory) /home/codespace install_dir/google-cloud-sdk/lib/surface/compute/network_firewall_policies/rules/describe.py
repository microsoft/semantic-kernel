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
"""Command for describing network firewall policy rules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import firewall_policy_rule_utils as rule_utils
from googlecloudsdk.api_lib.compute.network_firewall_policies import client
from googlecloudsdk.api_lib.compute.network_firewall_policies import region_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.network_firewall_policies import flags


class Describe(base.DescribeCommand):
  """Describes a Compute Engine network firewall policy rule.

  *{command}* is used to describe network firewall policy rules.
  """

  NETWORK_FIREWALL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.NETWORK_FIREWALL_POLICY_ARG = flags.NetworkFirewallPolicyRuleArgument(
        required=True, operation="describe")
    cls.NETWORK_FIREWALL_POLICY_ARG.AddArgument(parser)
    flags.AddRulePriority(parser, operation="described")

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.NETWORK_FIREWALL_POLICY_ARG.ResolveAsResource(
        args, holder.resources)
    network_firewall_policy_rule_client = client.NetworkFirewallPolicyRule(
        ref=ref, compute_client=holder.client)
    if hasattr(ref, "region"):
      network_firewall_policy_rule_client = region_client.RegionNetworkFirewallPolicyRule(
          ref, compute_client=holder.client)

    return network_firewall_policy_rule_client.Describe(
        priority=rule_utils.ConvertPriorityToInt(args.priority),
        firewall_policy=args.firewall_policy,
        only_generate_request=False)


Describe.detailed_help = {
    "EXAMPLES":
        """\
    To describe a rule with priority ``10'' in a global network firewall policy
    with name ``my-policy'', run:

      $ {command} 10 \
          --firewall-policy=my-policy --global-firewall-policy

    To describe a rule with priority ``10'' in a regional network firewall
    policy with name ``my-policy'', in region ``region-a'', run:

      $ {command} 10 \
          --firewall-policy=my-policy --firewall-policy-region=region-a
    """,
}
