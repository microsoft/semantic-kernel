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
"""Command for updating network firewall policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.network_firewall_policies import client
from googlecloudsdk.api_lib.compute.network_firewall_policies import region_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.network_firewall_policies import flags


class Update(base.UpdateCommand):
  """Update a Compute Engine network firewall policy.

  *{command}* is used to update network firewall policies. A network
  firewall policy is a set of rules that controls access to various resources.
  """

  NETWORK_FIREWALL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.NETWORK_FIREWALL_POLICY_ARG = flags.NetworkFirewallPolicyArgument(
        required=True, operation='update')
    cls.NETWORK_FIREWALL_POLICY_ARG.AddArgument(parser, operation_type='update')
    flags.AddArgsUpdateNetworkFirewallPolicy(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.NETWORK_FIREWALL_POLICY_ARG.ResolveAsResource(
        args, holder.resources)

    network_firewall_policy = client.NetworkFirewallPolicy(
        ref, compute_client=holder.client)
    if hasattr(ref, 'region'):
      network_firewall_policy = region_client.RegionNetworkFirewallPolicy(
          ref, compute_client=holder.client)

    existing_firewall_policy = network_firewall_policy.Describe(
        only_generate_request=False)[0]
    firewall_policy = holder.client.messages.FirewallPolicy(
        description=args.description,
        fingerprint=existing_firewall_policy.fingerprint)
    return network_firewall_policy.Update(
        firewall_policy=firewall_policy, only_generate_request=False)


Update.detailed_help = {
    'EXAMPLES':
        """\
    To update a global network firewall policy with name ``my-policy'',
    to change the description to ``New description'', run:

      $ {command} my-policy \
          --description='New description' \
          --global

    To update a regional network firewall policy with name ``my-policy'',
    in region ``my-region'',
    to change the description to ``New description'', run:

      $ {command} my-policy \
          --description='New description' \
          --region=my-region
    """,
}
