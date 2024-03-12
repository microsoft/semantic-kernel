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
"""Command for creating target VPN Gateways."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.networks import flags as network_flags
from googlecloudsdk.command_lib.compute.target_vpn_gateways import flags


class Create(base.CreateCommand):
  """Create a Cloud VPN Classic Target VPN Gateway.

    *{command}* is used to create a Cloud VPN Classic Target VPN Gateway. A
  Target VPN Gateway can reference one or more VPN tunnels that connect it to
  the remote tunnel endpoint. A Target VPN Gateway may also be referenced by
  one or more forwarding rules that define which packets the
  gateway is responsible for routing.
  """

  NETWORK_ARG = None
  TARGET_VPN_GATEWAY_ARG = None

  @classmethod
  def Args(cls, parser):
    """Adds arguments to the supplied parser."""
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    cls.NETWORK_ARG = network_flags.NetworkArgumentForOtherResource(
        """\
        A reference to a network in this project to
        contain the VPN Gateway.
        """)
    cls.NETWORK_ARG.AddArgument(parser)
    cls.TARGET_VPN_GATEWAY_ARG = flags.TargetVpnGatewayArgument()
    cls.TARGET_VPN_GATEWAY_ARG.AddArgument(parser, operation_type='create')

    parser.add_argument(
        '--description',
        help='An optional, textual description for the target VPN Gateway.')

    parser.display_info.AddCacheUpdater(flags.TargetVpnGatewaysCompleter)

  def Run(self, args):
    """Issues API requests to construct Target VPN Gateways.

    Args:
      args: argparse.Namespace, The arguments received by this command.

    Returns:
      [protorpc.messages.Message], A list of responses returned
      by the compute API.
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    target_vpn_gateway_ref = self.TARGET_VPN_GATEWAY_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))
    network_ref = self.NETWORK_ARG.ResolveAsResource(args, holder.resources)

    request = client.messages.ComputeTargetVpnGatewaysInsertRequest(
        project=target_vpn_gateway_ref.project,
        region=target_vpn_gateway_ref.region,
        targetVpnGateway=client.messages.TargetVpnGateway(
            description=args.description,
            name=target_vpn_gateway_ref.Name(),
            network=network_ref.SelfLink()
            ))
    return client.MakeRequests([(client.apitools_client.targetVpnGateways,
                                 'Insert', request)])
