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
"""Command for creating routes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import ipaddress

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.forwarding_rules import flags as ilb_flags
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags
from googlecloudsdk.command_lib.compute.networks import flags as network_flags
from googlecloudsdk.command_lib.compute.routes import flags
from googlecloudsdk.command_lib.compute.vpn_tunnels import flags as vpn_flags
from googlecloudsdk.core import properties


def _AddGaHops(next_hop_group):
  """Attach arguments for GA next-hops to the a parser group."""

  next_hop_group.add_argument(
      '--next-hop-instance',
      help="""\
      Specifies the name of an instance that should handle traffic
      matching this route. When this flag is specified, the zone of
      the instance must be specified using
      ``--next-hop-instance-zone''.
      """)

  next_hop_group.add_argument(
      '--next-hop-address',
      help="""\
      Specifies the IP address of an instance that should handle
      matching packets. The instance must have IP forwarding enabled
      (i.e., include ``--can-ip-forward'' when creating the instance
      using `gcloud compute instances create`)
      """)

  flags.NEXT_HOP_GATEWAY_ARG.AddArgument(next_hop_group)

  next_hop_group.add_argument(
      '--next-hop-vpn-tunnel',
      help=('The target VPN tunnel that will receive forwarded traffic.'))


def _Args(parser):
  """Add arguments for route creation."""

  parser.add_argument(
      '--description', help='An optional, textual description for the route.')

  parser.add_argument(
      '--network',
      default='default',
      help='Specifies the network to which the route will be applied.')

  parser.add_argument(
      '--tags',
      type=arg_parsers.ArgList(min_length=1),
      default=[],
      metavar='TAG',
      help="""\
      Identifies the set of instances that this route will apply to. If no
      tags are provided, the route will apply to all instances in the network.
      """)

  parser.add_argument(
      '--destination-range',
      required=True,
      help="""\
      The destination range of outgoing packets that the route will
      apply to. To match all traffic, use ``0.0.0.0/0''.
      """)

  parser.add_argument(
      '--priority',
      default=1000,
      type=int,
      help="""\
      Specifies the priority of this route relative to other routes
      with the same specificity. The lower the value, the higher the
      priority.
      """)

  next_hop = parser.add_mutually_exclusive_group(required=True)

  _AddGaHops(next_hop)

  parser.add_argument(
      '--next-hop-instance-zone',
      action=actions.StoreProperty(properties.VALUES.compute.zone),
      help=('The zone of the next hop instance. ' +
            instance_flags.ZONE_PROPERTY_EXPLANATION))

  parser.add_argument(
      '--next-hop-vpn-tunnel-region',
      help=('The region of the next hop vpn tunnel. ' +
            compute_flags.REGION_PROPERTY_EXPLANATION))

  next_hop.add_argument(
      '--next-hop-ilb',
      help="""\
      Specifies the name or IP address of a forwarding rule for an internal TCP/UDP
      load balancer. The forwarding rule's `--load-balancing-scheme` must be
      `INTERNAL`. You can use any `--destination-range` that doesn't exactly
      match the destination of a subnet route and isn't more specific (has a
      longer subnet mask) than the destination of a subnet route. For
      more information, see
      https://cloud.google.com/load-balancing/docs/internal/ilb-next-hop-overview#destination_range.
      """)
  parser.add_argument(
      '--next-hop-ilb-region',
      help=('The region of the next hop forwarding rule. ' +
            compute_flags.REGION_PROPERTY_EXPLANATION))

  parser.display_info.AddCacheUpdater(completers.RoutesCompleter)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  r"""Create a new route.

    *{command}* is used to create routes. A route is a rule that
  specifies how certain packets should be handled by the virtual
  network. Routes are associated with virtual machine instances
  by tag, and the set of routes for a particular VM is called
  its routing table. For each packet leaving a virtual machine,
  the system searches that machine's routing table for a single
  best matching route.

  Routes match packets by destination IP address, preferring
  smaller or more specific ranges over larger ones (see
  `--destination-range`). If there is a tie, the system selects
  the route with the smallest priority value. If there is still
  a tie, it uses the layer 3 and 4 packet headers to
  select just one of the remaining matching routes. The packet
  is then forwarded as specified by `--next-hop-address`,
  `--next-hop-instance`, `--next-hop-vpn-tunnel`, or
  `--next-hop-gateway` of the winning route. Packets that do
  not match any route in the sending virtual machine routing
  table will be dropped.

  Exactly one of `--next-hop-address`, `--next-hop-gateway`,
  `--next-hop-vpn-tunnel`, or `--next-hop-instance` must be
  provided with this command.

  ## EXAMPLES

  To create a route with the name 'route-name' with destination range
  '0.0.0.0/0' and with next hop gateway 'default-internet-gateway', run:

    $ {command} route-name \
      --destination-range=0.0.0.0/0 \
      --next-hop-gateway=default-internet-gateway

  """

  NETWORK_ARG = None
  INSTANCE_ARG = None
  VPN_TUNNEL_ARG = None
  ILB_ARG = None
  ROUTE_ARG = None

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    cls.NETWORK_ARG = network_flags.NetworkArgumentForOtherResource(
        'Specifies the network to which the route will be applied.',
        required=False)
    cls.INSTANCE_ARG = instance_flags.InstanceArgumentForRoute(required=False)
    cls.VPN_TUNNEL_ARG = vpn_flags.VpnTunnelArgumentForRoute(required=False)
    cls.ILB_ARG = ilb_flags.ForwardingRuleArgumentForRoute(required=False)
    cls.ROUTE_ARG = flags.RouteArgument()
    cls.ROUTE_ARG.AddArgument(parser, operation_type='create')
    _Args(parser)

  def Run(self, args):
    """Issue API requests for route creation, callable from multiple tracks."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    network_uri = self.NETWORK_ARG.ResolveAsResource(
        args, holder.resources).SelfLink()

    route_ref = self.ROUTE_ARG.ResolveAsResource(args, holder.resources)

    if args.next_hop_instance:
      next_hop_instance_uri = self.INSTANCE_ARG.ResolveAsResource(
          args,
          holder.resources,
          scope_lister=instance_flags.GetInstanceZoneScopeLister(
              client)).SelfLink()
    else:
      if args.next_hop_instance_zone:
        raise compute_exceptions.ArgumentError(
            '[--next-hop-instance-zone] can only be specified in conjunction '
            'with [--next-hop-instance].')
      next_hop_instance_uri = None

    if args.next_hop_gateway:
      next_hop_gateway_ref = flags.NEXT_HOP_GATEWAY_ARG.ResolveAsResource(
          args, holder.resources)
      next_hop_gateway_uri = next_hop_gateway_ref.SelfLink()
    else:
      next_hop_gateway_uri = None

    next_hop_vpn_tunnel_uri = None

    if args.next_hop_vpn_tunnel:
      next_hop_vpn_tunnel_uri = self.VPN_TUNNEL_ARG.ResolveAsResource(
          args,
          holder.resources,
          scope_lister=compute_flags.GetDefaultScopeLister(client)).SelfLink()
    elif args.next_hop_vpn_tunnel_region:
      raise compute_exceptions.ArgumentError(
          '[--next-hop-vpn-tunnel-region] can only be specified in '
          'conjunction with [--next-hop-vpn-tunnel].')

    next_hop_ilb_uri = None

    if args.next_hop_ilb:
      try:
        ipaddress.ip_address(args.next_hop_ilb)
        if args.next_hop_ilb_region:
          raise exceptions.InvalidArgumentException(
              '--next-hop-ilb-region', 'This should not be specified if '
              'an IP address is used for [--next-hop-ilb].')
        next_hop_ilb_uri = args.next_hop_ilb
      except ValueError:
        next_hop_ilb_uri = self.ILB_ARG.ResolveAsResource(
            args,
            holder.resources,
            scope_lister=compute_flags.GetDefaultScopeLister(
                client)).SelfLink()
    elif args.next_hop_ilb_region:
      raise exceptions.InvalidArgumentException(
          '--next-hop-ilb-region', 'This can only be specified in '
          'conjunction with [--next-hop-ilb].')

    request = client.messages.ComputeRoutesInsertRequest(
        project=route_ref.project,
        route=client.messages.Route(
            description=args.description,
            destRange=args.destination_range,
            name=route_ref.Name(),
            network=network_uri,
            nextHopInstance=next_hop_instance_uri,
            nextHopIp=args.next_hop_address,
            nextHopGateway=next_hop_gateway_uri,
            nextHopVpnTunnel=next_hop_vpn_tunnel_uri,
            priority=args.priority,
            tags=args.tags,
        ))
    request.route.nextHopIlb = next_hop_ilb_uri

    return client.MakeRequests([(client.apitools_client.routes, 'Insert',
                                 request)])


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class CreateAlphaBeta(Create):
  r"""Create a new route.

    *{command}* is used to create routes. A route is a rule that
  specifies how certain packets should be handled by the virtual
  network. Routes are associated with virtual machine instances
  by tag, and the set of routes for a particular VM is called
  its routing table. For each packet leaving a virtual machine,
  the system searches that machine's routing table for a single
  best matching route.

  Routes match packets by destination IP address, preferring
  smaller or more specific ranges over larger ones (see
  ``--destination-range''). If there is a tie, the system selects
  the route with the smallest priority value. If there is still
  a tie, it uses the layer 3 and 4 packet headers to
  select just one of the remaining matching routes. The packet
  is then forwarded as specified by ``--next-hop-address'',
  ``--next-hop-instance'', ``--next-hop-vpn-tunnel'', ``--next-hop-gateway'',
  or ``--next-hop-ilb'' of the winning route. Packets that do
  not match any route in the sending virtual machine routing
  table will be dropped.

  Exactly one of ``--next-hop-address'', ``--next-hop-gateway'',
  ``--next-hop-vpn-tunnel'', ``--next-hop-instance'', or ``--next-hop-ilb''
  must be provided with this command.

  ## EXAMPLES

  To create a route with the name 'route-name' with destination range
  '0.0.0.0/0' and with next hop gateway 'default-internet-gateway', run:

    $ {command} route-name \
      --destination-range=0.0.0.0/0 \
      --next-hop-gateway=default-internet-gateway

  """
