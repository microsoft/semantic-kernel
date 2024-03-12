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
"""Command for creating network firewall policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.network_firewall_policies import client
from googlecloudsdk.api_lib.compute.network_firewall_policies import region_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.network_firewall_policies import flags


class Create(base.CreateCommand):
  """Create a Compute Engine Network firewall policy.

  *{command}* is used to create network firewall policies. A network
  firewall policy is a set of rules that controls access to various resources.
  """

  NETWORK_FIREWALL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.NETWORK_FIREWALL_POLICY_ARG = flags.NetworkFirewallPolicyArgument(
        required=True, operation='create')
    cls.NETWORK_FIREWALL_POLICY_ARG.AddArgument(parser, operation_type='create')
    flags.AddArgNetworkFirewallPolicyCreation(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.NETWORK_FIREWALL_POLICY_ARG.ResolveAsResource(
        args, holder.resources)

    network_firewall_policy = client.NetworkFirewallPolicy(
        ref, compute_client=holder.client)
    if hasattr(ref, 'region'):
      network_firewall_policy = region_client.RegionNetworkFirewallPolicy(
          ref, compute_client=holder.client)

    firewall_policy = holder.client.messages.FirewallPolicy(
        description=args.description, name=ref.Name())

    return network_firewall_policy.Create(
        firewall_policy=firewall_policy, only_generate_request=False)


Create.detailed_help = {
    'EXAMPLES':
        """\
    To create a global network firewall policy named ``my-policy'' under project
    with ID ``test-project'', run:

      $ {command} my-policy \
          --project=test-project \
          --global

    To create a regional network firewall policy named ``my-region-policy'' under project
    with ID ``test-project'', in region ``my-region'', run:

      $ {command} my-region-policy \
          --project=test-project \
          --region=my-region
    """,
}
