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
"""Command for creating network firewall policy associations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import firewall_policy_association_utils as association_utils
from googlecloudsdk.api_lib.compute.network_firewall_policies import client
from googlecloudsdk.api_lib.compute.network_firewall_policies import region_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.network_firewall_policies import flags


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a new association between a firewall policy and a network.

  *{command}* is used to create network firewall policy associations. A
  network firewall policy is a set of rules that controls access to various
  resources.
  """
  NEWORK_FIREWALL_POLICY_ARG = None
  _support_priority = False

  @classmethod
  def Args(cls, parser):
    cls.NETWORK_FIREWALL_POLICY_ARG = (
        flags.NetworkFirewallPolicyAssociationArgument(
            required=True, operation='create'))
    cls.NETWORK_FIREWALL_POLICY_ARG.AddArgument(parser, operation_type='create')
    flags.AddArgsCreateAssociation(parser, cls._support_priority)
    parser.display_info.AddCacheUpdater(flags.NetworkFirewallPoliciesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.NETWORK_FIREWALL_POLICY_ARG.ResolveAsResource(
        args, holder.resources)

    network_firewall_policy = client.NetworkFirewallPolicy(
        ref, compute_client=holder.client)
    if hasattr(ref, 'region'):
      network_firewall_policy = region_client.RegionNetworkFirewallPolicy(
          ref, compute_client=holder.client)

    network_ref = flags.NetworkArgumentForOtherResource(
        'The network to which the firewall policy attaches.').ResolveAsResource(
            args, holder.resources)

    name = None
    if args.IsSpecified('name'):
      name = args.name
    else:
      name = 'network-' + network_ref.Name()

    attachment_target = network_ref.SelfLink()

    priority = None
    if self._support_priority and args.IsSpecified('priority'):
      priority = association_utils.ConvertPriorityToInt(args.priority)

    replace_existing_association = False
    if args.replace_association_on_target:
      replace_existing_association = True

    association = None
    if self._support_priority and priority is not None:
      association = holder.client.messages.FirewallPolicyAssociation(
          attachmentTarget=attachment_target, name=name, priority=priority
      )
    else:
      association = holder.client.messages.FirewallPolicyAssociation(
          attachmentTarget=attachment_target, name=name
      )

    return network_firewall_policy.AddAssociation(
        association=association,
        firewall_policy=args.firewall_policy,
        replace_existing_association=replace_existing_association,
        only_generate_request=False)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a new association between a firewall policy and a network.

  *{command}* is used to create network firewall policy associations. A
  network firewall policy is a set of rules that controls access to various
  resources.
  """

  _support_priority = False


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create a new association between a firewall policy and a network.

  *{command}* is used to create network firewall policy associations. A
  network firewall policy is a set of rules that controls access to various
  resources.
  """

  _support_priority = True


Create.detailed_help = {
    'EXAMPLES':
        """\
    To associate a global network firewall policy with name ``my-policy''
    to network ``my-network'' with an association named ``my-association'', run:

      $ {command}
          --firewall-policy=my-policy
          --network=my-network
          --name=my-association
          --global-firewall-policy

    To associate a network firewall policy with name ``my-region-policy'' in
    region ``region-a''
    to network ``my-network'' with an association named ``my-association'', run:

      $ {command}
          --firewall-policy=my-policy
          --network=my-network
          --name=my-association
          --firewall-policy-region=region-a
    """,
}
