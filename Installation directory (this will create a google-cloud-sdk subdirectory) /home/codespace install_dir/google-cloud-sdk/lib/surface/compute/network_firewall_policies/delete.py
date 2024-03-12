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
"""Command for deleting network firewall policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.network_firewall_policies import client
from googlecloudsdk.api_lib.compute.network_firewall_policies import region_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.network_firewall_policies import flags


class Delete(base.DeleteCommand):
  """Delete a Compute Engine network firewall policy.

  *{command}* is used to delete network firewall policies. A network
  firewall policy is a set of rules that controls access to various resources.
  """

  FIREWALL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.FIREWALL_POLICY_ARG = flags.NetworkFirewallPolicyArgument(
        required=True, operation='delete')
    cls.FIREWALL_POLICY_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.NetworkFirewallPoliciesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.FIREWALL_POLICY_ARG.ResolveAsResource(args, holder.resources)

    network_firewall_policy = client.NetworkFirewallPolicy(
        ref, compute_client=holder.client)
    if hasattr(ref, 'region'):
      network_firewall_policy = region_client.RegionNetworkFirewallPolicy(
          ref, compute_client=holder.client)

    return network_firewall_policy.Delete(
        firewall_policy=ref.Name(), only_generate_request=False)


Delete.detailed_help = {
    'EXAMPLES':
        """\
    To delete a global network firewall policy with name ``my-policy'', run:

      $ {command} my-policy --global

    To delete a regional network firewall policy with name ``my-policy'',
    in region ``my-region'', run:

      $ {command} my-policy --region=my-region
    """,
}
