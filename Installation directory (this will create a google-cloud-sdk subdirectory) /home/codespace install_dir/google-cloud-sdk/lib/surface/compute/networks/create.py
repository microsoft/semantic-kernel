# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for creating networks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import networks_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.networks import flags
from googlecloudsdk.command_lib.compute.networks import network_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_projector


def EpilogText(network_name):
  """Text for firewall warning."""
  message = """\

      Instances on this network will not be reachable until firewall rules
      are created. As an example, you can allow all internal traffic between
      instances as well as SSH, RDP, and ICMP by running:

      $ gcloud compute firewall-rules create <FIREWALL_NAME> --network {0} --allow tcp,udp,icmp --source-ranges <IP_RANGE>
      $ gcloud compute firewall-rules create <FIREWALL_NAME> --network {0} --allow tcp:22,tcp:3389,icmp
      """.format(network_name)
  log.status.Print(textwrap.dedent(message))


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  r"""Create a Compute Engine network.

  *{command}* is used to create virtual networks. A network
  performs the same function that a router does in a home
  network: it describes the network range and gateway IP
  address, handles communication between instances, and serves
  as a gateway between instances and callers outside the
  network.

  ## EXAMPLES

  To create a regional auto subnet mode network with the name 'network-name',
  run:

    $ {command} network-name

  To create a global custom subnet mode network with the name 'network-name',
  run:

    $ {command} network-name \
      --bgp-routing-mode=global \
      --subnet-mode=custom

  """

  NETWORK_ARG = None
  _support_firewall_order = True

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    cls.NETWORK_ARG = flags.NetworkArgument()
    cls.NETWORK_ARG.AddArgument(parser, operation_type='create')

    network_utils.AddCreateBaseArgs(parser)
    network_utils.AddCreateSubnetModeArg(parser)
    network_utils.AddCreateBgpRoutingModeArg(parser)
    network_utils.AddMtuArg(parser)
    network_utils.AddInternalIpv6RangeArg(parser)
    network_utils.AddEnableUlaInternalIpv6Arg(parser)
    network_utils.AddNetworkFirewallPolicyEnforcementOrderArg(parser)

    parser.display_info.AddCacheUpdater(flags.NetworksCompleter)

  def Run(self, args):
    """Issues the request necessary for adding the network."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    network_utils.CheckRangeLegacyModeOrRaise(args)

    network_ref = self.NETWORK_ARG.ResolveAsResource(args, holder.resources)
    self._network_name = network_ref.Name()
    network_resource = networks_utils.CreateNetworkResourceFromArgs(
        messages=messages,
        network_ref=network_ref,
        network_args=args,
        support_firewall_order=self._support_firewall_order)

    request = (client.apitools_client.networks, 'Insert',
               client.messages.ComputeNetworksInsertRequest(
                   network=network_resource, project=network_ref.project))
    response = client.MakeRequests([request])

    resource_dict = resource_projector.MakeSerializable(response[0])
    return networks_utils.AddModesForListFormat(resource_dict)

  def Epilog(self, resources_were_displayed=True):
    EpilogText(self._network_name)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create a Compute Engine network.

  *{command}* is used to create virtual networks. A network
  performs the same function that a router does in a home
  network: it describes the network range and gateway IP
  address, handles communication between instances, and serves
  as a gateway between instances and callers outside the
  network.
  """
  _support_firewall_order = True

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    cls.NETWORK_ARG = flags.NetworkArgument()
    cls.NETWORK_ARG.AddArgument(parser, operation_type='create')

    network_utils.AddCreateBaseArgs(parser)
    network_utils.AddCreateSubnetModeArg(parser)
    network_utils.AddCreateBgpRoutingModeArg(parser)
    network_utils.AddMtuArg(parser)
    network_utils.AddInternalIpv6RangeArg(parser)
    network_utils.AddEnableUlaInternalIpv6Arg(parser)
    network_utils.AddNetworkFirewallPolicyEnforcementOrderArg(parser)
    network_utils.AddRdmaArg(parser)
    network_utils.AddBgpBestPathSelectionArgGroup(parser)

    parser.display_info.AddCacheUpdater(flags.NetworksCompleter)
