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
"""Command for get_effective_firewalls of network with network firewall policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import firewalls_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.networks import flags as network_flags
from googlecloudsdk.core import properties


class GetEffectiveFirewalls(base.DescribeCommand, base.ListCommand):
  """Get the effective firewalls for a network.

  *{command}* is used to get the effective firewalls applied to the network,
  including regional firewalls in a specified region.

  ## EXAMPLES

  To get the effective firewalls for a network, run:

    $ {command} --network=network-a --region=us-central1

  gets the effective firewalls applied on the network network-a, including
  organization firewall policies, global network firewall policies, and regional
  network firewall policies in region us-central1.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--network',
        required=True,
        help='The network to get the effective firewalls for.')
    parser.add_argument(
        '--region', help='The region to get the effective regional firewalls.')
    parser.display_info.AddFormat(
        firewalls_utils.EFFECTIVE_FIREWALL_LIST_FORMAT)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages

    if hasattr(args, 'project') and args.project:
      project = args.project
    else:
      project = properties.VALUES.core.project.GetOrFail()

    if hasattr(args, 'region') and args.region:
      region = args.region
    else:
      region = properties.VALUES.compute.region.GetOrFail()

    network = network_flags.NetworkArgumentForOtherResource(
        short_help=None).ResolveAsResource(args, holder.resources)
    network_ref = network.SelfLink() if network else None

    request = messages.ComputeRegionNetworkFirewallPoliciesGetEffectiveFirewallsRequest(
        project=project, region=region, network=network_ref)

    responses = client.MakeRequests([
        (client.apitools_client.regionNetworkFirewallPolicies,
         'GetEffectiveFirewalls', request)
    ])
    res = responses[0]
    network_firewall = []
    all_firewall_policy = []

    if hasattr(res, 'firewalls'):
      network_firewall = firewalls_utils.SortNetworkFirewallRules(
          client, res.firewalls)

    if hasattr(res, 'firewallPolicys') and res.firewallPolicys:
      for fp in res.firewallPolicys:
        firewall_policy_rule = firewalls_utils.SortFirewallPolicyRules(
            client, fp.rules)
        fp_response = (
            client.messages.
            RegionNetworkFirewallPoliciesGetEffectiveFirewallsResponseEffectiveFirewallPolicy(
                name=fp.name, rules=firewall_policy_rule, type=fp.type))
        all_firewall_policy.append(fp_response)

    if args.IsSpecified('format') and args.format == 'json':
      return client.messages.RegionNetworkFirewallPoliciesGetEffectiveFirewallsResponse(
          firewalls=network_firewall, firewallPolicys=all_firewall_policy)

    result = []
    for fp in all_firewall_policy:
      result.extend(
          firewalls_utils.ConvertFirewallPolicyRulesToEffectiveFwRules(
              client, fp, True, support_region_network_firewall_policy=True))
    result.extend(
        firewalls_utils.ConvertNetworkFirewallRulesToEffectiveFwRules(
            network_firewall))
    return result


GetEffectiveFirewalls.detailed_help = {
    'EXAMPLES':
        """\
    To get the effective firewalls of network with name ``example-network'',
    including effective regional firewalls for that network, in region
    ``region-a'', run:

      $ {command} --network=example-network --region=region-a

    To show all fields of the firewall rules, please show in JSON format with
    option --format=json

    To list more the fields of the rules of network ``example-network'' in table
    format, run:

      $ {command} --network=example-network --region=region-a --format="table(
        type,
        firewall_policy_name,
        priority,
        action,
        direction,
        ip_ranges.list():label=IP_RANGES,
        target_svc_acct,
        enableLogging,
        description,
        name,
        disabled,
        target_tags,
        src_svc_acct,
        src_tags,
        ruleTupleCount,
        targetResources:label=TARGET_RESOURCES)" """,
}
