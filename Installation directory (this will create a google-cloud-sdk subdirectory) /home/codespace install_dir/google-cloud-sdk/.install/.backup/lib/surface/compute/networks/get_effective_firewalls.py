# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Command for getting effective firewalls of GCP networks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import firewalls_utils
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.networks import flags
from googlecloudsdk.core import log


class GetEffectiveFirewalls(base.DescribeCommand, base.ListCommand):
  """Get the effective firewalls of a Compute Engine network.

  *{command}* is used to get the effective firewalls applied to the network.

  ## EXAMPLES

  To get the effective firewalls for a network, run:

    $ {command} example-network

  gets the effective firewalls applied on the network 'example-network'.
  """

  @staticmethod
  def Args(parser):
    flags.NetworkArgument().AddArgument(
        parser, operation_type='get effective firewalls')
    parser.display_info.AddFormat(
        firewalls_utils.EFFECTIVE_FIREWALL_LIST_FORMAT)
    lister.AddBaseListerArgs(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    network_ref = flags.NetworkArgument().ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    request = client.messages.ComputeNetworksGetEffectiveFirewallsRequest(
        **network_ref.AsDict())
    responses = client.MakeRequests([(client.apitools_client.networks,
                                      'GetEffectiveFirewalls', request)])
    res = responses[0]
    org_firewall = []
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
            client.messages
            .NetworksGetEffectiveFirewallsResponseEffectiveFirewallPolicy(
                name=fp.name, rules=firewall_policy_rule, type=fp.type))
        all_firewall_policy.append(fp_response)
    elif hasattr(res, 'organizationFirewalls'):
      for sp in res.organizationFirewalls:
        org_firewall_rule = firewalls_utils.SortOrgFirewallRules(
            client, sp.rules)
        org_firewall.append(
            client.messages
            .NetworksGetEffectiveFirewallsResponseOrganizationFirewallPolicy(
                id=sp.id, rules=org_firewall_rule))

    if args.IsSpecified('format') and args.format == 'json':
      if org_firewall:
        return client.messages.NetworksGetEffectiveFirewallsResponse(
            organizationFirewalls=org_firewall,
            firewalls=network_firewall,
            firewallPolicys=all_firewall_policy)
      else:
        return client.messages.NetworksGetEffectiveFirewallsResponse(
            firewalls=network_firewall, firewallPolicys=all_firewall_policy)

    result = []
    for fp in all_firewall_policy:
      result.extend(
          firewalls_utils.ConvertFirewallPolicyRulesToEffectiveFwRules(
              client, fp, True))
    for sp in org_firewall:
      result.extend(
          firewalls_utils.ConvertOrgSecurityPolicyRulesToEffectiveFwRules(sp))
    result.extend(
        firewalls_utils.ConvertNetworkFirewallRulesToEffectiveFwRules(
            network_firewall))
    return result

  def Epilog(self, resources_were_displayed):
    del resources_were_displayed
    log.status.Print('\n' + firewalls_utils.LIST_NOTICE)


GetEffectiveFirewalls.detailed_help = {
    'EXAMPLES':
        """\
    To get the effective firewalls of network with name example-network, run:

      $ {command} example-network

    To show all fields of the firewall rules, please show in JSON format with
    option --format=json

    To list more the fields of the rules of network example-network in table
    format, run:

      $ {command} example-network --format="table(
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
        targetResources:label=TARGET_RESOURCES)"
        """,
}
