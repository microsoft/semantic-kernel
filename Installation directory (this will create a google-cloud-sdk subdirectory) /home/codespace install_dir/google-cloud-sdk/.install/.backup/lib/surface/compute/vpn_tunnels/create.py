# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command for creating VPN tunnels."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import re

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.vpn_tunnels import vpn_tunnels_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.external_vpn_gateways import (
    flags as external_vpn_gateway_flags)
from googlecloudsdk.command_lib.compute.routers import flags as router_flags
from googlecloudsdk.command_lib.compute.target_vpn_gateways import (
    flags as target_vpn_gateway_flags)
from googlecloudsdk.command_lib.compute.vpn_gateways import (flags as
                                                             vpn_gateway_flags)
from googlecloudsdk.command_lib.compute.vpn_tunnels import flags


_PRINTABLE_CHARS_PATTERN = r'[ -~]+'

_ROUTER_ARG = router_flags.RouterArgumentForVpnTunnel(required=False)
_VPN_TUNNEL_ARG = flags.VpnTunnelArgument()


class DeprecatedArgumentException(exceptions.ToolException):

  def __init__(self, arg, msg):
    super(DeprecatedArgumentException, self).__init__(
        '{0} is deprecated. {1}'.format(arg, msg))


def ValidateSimpleSharedSecret(possible_secret):
  """ValidateSimpleSharedSecret checks its argument is a vpn shared secret.

  ValidateSimpleSharedSecret(v) returns v iff v matches [ -~]+.

  Args:
    possible_secret: str, The data to validate as a shared secret.

  Returns:
    The argument, if valid.

  Raises:
    ArgumentTypeError: The argument is not a valid vpn shared secret.
  """

  if not possible_secret:
    raise argparse.ArgumentTypeError(
        '--shared-secret requires a non-empty argument.')

  if re.match(_PRINTABLE_CHARS_PATTERN, possible_secret):
    return possible_secret

  raise argparse.ArgumentTypeError(
      'The argument to --shared-secret is not valid it contains '
      'non-printable charcters.')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class CreateGA(base.CreateCommand):
  """Create a VPN tunnel.

    *{command}* is used to create a Classic VPN tunnel between a target VPN
  gateway in Google Cloud Platform and a peer address; or create Highly
  Available VPN tunnel between HA VPN gateway and another HA VPN gateway, or
  Highly Available VPN tunnel between HA VPN gateway and an external VPN
  gateway.
  """

  _TARGET_VPN_GATEWAY_ARG = (
      target_vpn_gateway_flags.TargetVpnGatewayArgumentForVpnTunnel(
          required=False))
  _VPN_GATEWAY_ARG = (
      vpn_gateway_flags.GetVpnGatewayArgumentForOtherResource(required=False))

  _EXTERNAL_VPN_GATEWAY_ARG = (
      external_vpn_gateway_flags.ExternalVpnGatewayArgumentForVpnTunnel(
          required=False))

  _PEER_GCP_GATEWAY_ARG = (
      vpn_gateway_flags.GetPeerVpnGatewayArgumentForOtherResource(
          required=False))

  @classmethod
  def _AddCommonFlags(cls, parser):
    _ROUTER_ARG.AddArgument(parser)

    parser.add_argument(
        '--description',
        help='An optional, textual description for the VPN tunnel.')

    parser.add_argument(
        '--ike-version',
        choices=[1, 2],
        type=int,
        help='Internet Key Exchange protocol version number. Default is 2.')

    parser.add_argument(
        '--shared-secret',
        type=ValidateSimpleSharedSecret,
        required=True,
        help="""\
        Shared secret consisting of printable characters.  Valid
        arguments match the regular expression """ + _PRINTABLE_CHARS_PATTERN)

    parser.add_argument(
        '--ike-networks',
        type=arg_parsers.ArgList(min_length=1),
        hidden=True,
        help='THIS ARGUMENT NEEDS HELP TEXT.')

  @classmethod
  def Args(cls, parser):
    """Adds arguments to the supplied parser."""
    # TODO(b/129011963): add e2e tests for HA VPN tunnels
    parser.display_info.AddFormat(flags.HA_VPN_LIST_FORMAT)

    _VPN_TUNNEL_ARG.AddArgument(parser, operation_type='create')
    vpn_gateway_group_parser = parser.add_mutually_exclusive_group(
        required=True)
    cls._TARGET_VPN_GATEWAY_ARG.AddArgument(vpn_gateway_group_parser)
    cls._VPN_GATEWAY_ARG.AddArgument(vpn_gateway_group_parser)

    peer_vpn_gateway_group_parser = parser.add_mutually_exclusive_group(
        required=True)
    cls._EXTERNAL_VPN_GATEWAY_ARG.AddArgument(peer_vpn_gateway_group_parser)
    cls._PEER_GCP_GATEWAY_ARG.AddArgument(peer_vpn_gateway_group_parser)
    peer_vpn_gateway_group_parser.add_argument(
        '--peer-address',
        required=False,
        help='Valid IPV4 address representing the remote tunnel endpoint, '
        'the peer address must be specified when creating Classic VPN '
        'tunnels from Classic Target VPN gateway')

    cls._AddCommonFlags(parser)

    parser.add_argument(
        '--local-traffic-selector',
        type=arg_parsers.ArgList(min_length=1),
        metavar='CIDR',
        help=("""\
        Traffic selector is an agreement between IKE peers to permit traffic
        through a tunnel if the traffic matches a specified pair of local and
        remote addresses.

        --local-traffic-selector allows to configure the local addresses that are
        permitted. The value should be a comma separated list of CIDR formatted
        strings. Example: 192.168.0.0/16,10.0.0.0/24.

        Local traffic selector must be specified only for VPN tunnels that
        do not use dynamic routing with a Cloud Router. Omit this flag when
        creating a tunnel using dynamic routing, including a tunnel for a
        Highly Available VPN gateway."""))

    parser.add_argument(
        '--remote-traffic-selector',
        type=arg_parsers.ArgList(min_length=1),
        metavar='CIDR',
        help=("""\
        Traffic selector is an agreement between IKE peers to permit traffic
        through a tunnel if the traffic matches a specified pair of local and
        remote addresses.

        --remote-traffic-selector allows to configure the remote addresses that
        are permitted. The value should be a comma separated list of CIDR
        formatted strings. Example: 192.168.0.0/16,10.0.0.0/24.

        Remote traffic selector must be specified for VPN tunnels that do
        not use dynamic routing with a Cloud Router. Omit this flag when
        creating a tunnel using dynamic routing, including a tunnel for a
        Highly Available VPN gateway."""))

    parser.add_argument(
        '--interface',
        choices=[0, 1],
        type=int,
        required=False,
        help="""\
        Numeric interface ID of the VPN gateway with which this VPN tunnel
        is associated. This flag is required if the tunnel is being attached
        to a Highly Available VPN gateway. This option is only available
        for use with Highly Available VPN gateway and must be omitted if the
        tunnel is going to be connected to a Classic VPN gateway.""")

    parser.add_argument(
        '--peer-external-gateway-interface',
        choices=[0, 1, 2, 3],
        type=int,
        required=False,
        help="""\
        Interface ID of the external VPN gateway to which this VPN tunnel
        is connected to.
        This flag is required if the tunnel is being created from
        a Highly Available VPN gateway to an External Vpn Gateway.""")

    parser.display_info.AddCacheUpdater(flags.VpnTunnelsCompleter)

  def _ValidateHighAvailabilityVpnArgs(self, args):
    if args.IsSpecified('vpn_gateway'):
      if not args.IsSpecified('interface'):
        raise exceptions.InvalidArgumentException(
            '--interface',
            'When creating Highly Available VPN tunnels, the VPN gateway '
            'interface must be specified using the --interface flag.')
      if not args.IsSpecified('router'):
        raise exceptions.InvalidArgumentException(
            '--router',
            'When creating Highly Available VPN tunnels, a Cloud Router '
            'must be specified using the --router flag.')
      if not args.IsSpecified('peer_gcp_gateway') and not args.IsSpecified(
          'peer_external_gateway'):
        raise exceptions.InvalidArgumentException(
            '--peer-gcp-gateway',
            'When creating Highly Available VPN tunnels, either '
            '--peer-gcp-gateway or --peer-external-gateway must be specified.')
      if args.IsSpecified('peer_external_gateway') and not args.IsSpecified(
          'peer_external_gateway_interface'):
        raise exceptions.InvalidArgumentException(
            '--peer-external-gateway-interface',
            'The flag --peer-external-gateway-interface must be specified along'
            ' with --peer-external-gateway.')
      if args.IsSpecified('local_traffic_selector'):
        raise exceptions.InvalidArgumentException(
            '--local-traffic-selector',
            'Cannot specify local traffic selector with Highly Available '
            'VPN tunnels.')
      if args.IsSpecified('remote_traffic_selector'):
        raise exceptions.InvalidArgumentException(
            '--remote-traffic-selector',
            'Cannot specify remote traffic selector with Highly Available '
            'VPN tunnels.')
      if args.IsSpecified('peer_address'):
        raise exceptions.InvalidArgumentException(
            '--peer-address',
            'Cannot specify the flag peer address with Highly Available '
            'VPN tunnels.')

  def _ValidateClassicVpnArgs(self, args):
    if args.IsSpecified('target_vpn_gateway'):
      if not args.IsSpecified('peer_address'):
        raise exceptions.InvalidArgumentException(
            '--peer-address',
            'When creating Classic VPN tunnels, the peer address '
            'must be specified.')

  def _GetPeerGcpGateway(self, api_resource_registry, args):
    if args.IsSpecified('peer_gcp_gateway'):
      peer_gcp_gateway = self._PEER_GCP_GATEWAY_ARG.ResolveAsResource(
          args, api_resource_registry).SelfLink()
      return peer_gcp_gateway
    return None

  def _GetPeerExternalGateway(self, api_resource_registry, args):
    if args.IsSpecified('peer_external_gateway'):
      peer_external_gateway = self._EXTERNAL_VPN_GATEWAY_ARG.ResolveAsResource(
          args, api_resource_registry).SelfLink()
      return peer_external_gateway
    return None

  def _Run(self, args, is_vpn_gateway_supported):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    helper = vpn_tunnels_utils.VpnTunnelHelper(holder)

    # TODO(b/38253176) Add test coverage
    if args.ike_networks is not None:
      raise DeprecatedArgumentException(
          '--ike-networks',
          'It has been renamed to --local-traffic-selector.')

    vpn_tunnel_ref = _VPN_TUNNEL_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    router_link = None
    if args.IsSpecified('router'):
      args.router_region = vpn_tunnel_ref.region
      router_ref = _ROUTER_ARG.ResolveAsResource(args, holder.resources)
      router_link = router_ref.SelfLink()

    target_vpn_gateway = None
    vpn_gateway = None
    vpn_gateway_interface = None
    peer_external_gateway = None
    peer_external_gateway_interface = None
    peer_gcp_gateway = None

    if is_vpn_gateway_supported and args.IsSpecified('vpn_gateway'):
      self._ValidateHighAvailabilityVpnArgs(args)
      args.vpn_gateway_region = vpn_tunnel_ref.region
      vpn_gateway = self._VPN_GATEWAY_ARG.ResolveAsResource(
          args, holder.resources).SelfLink()
      vpn_gateway_interface = args.interface
      peer_external_gateway = self._GetPeerExternalGateway(
          holder.resources, args)
      peer_external_gateway_interface = args.peer_external_gateway_interface
      peer_gcp_gateway = self._GetPeerGcpGateway(holder.resources, args)
    else:
      self._ValidateClassicVpnArgs(args)
      args.target_vpn_gateway_region = vpn_tunnel_ref.region
      target_vpn_gateway = self._TARGET_VPN_GATEWAY_ARG.ResolveAsResource(
          args, holder.resources).SelfLink()

    if target_vpn_gateway:
      vpn_tunnel_to_insert = helper.GetClassicVpnTunnelForInsert(
          name=vpn_tunnel_ref.Name(),
          description=args.description,
          ike_version=args.ike_version,
          peer_ip=args.peer_address,
          shared_secret=args.shared_secret,
          target_vpn_gateway=target_vpn_gateway,
          router=router_link,
          local_traffic_selector=args.local_traffic_selector,
          remote_traffic_selector=args.remote_traffic_selector)
    else:
      vpn_tunnel_to_insert = helper.GetHighAvailabilityVpnTunnelForInsert(
          name=vpn_tunnel_ref.Name(),
          description=args.description,
          ike_version=args.ike_version,
          # TODO(b/127839209): remove peer_ip for HA tunnels once peer gateway
          # feature is enabled in Arcus.
          peer_ip=args.peer_address,
          shared_secret=args.shared_secret,
          vpn_gateway=vpn_gateway,
          vpn_gateway_interface=vpn_gateway_interface,
          router=router_link,
          peer_external_gateway=peer_external_gateway,
          peer_external_gateway_interface=peer_external_gateway_interface,
          peer_gcp_gateway=peer_gcp_gateway)

    operation_ref = helper.Create(vpn_tunnel_ref, vpn_tunnel_to_insert)
    return helper.WaitForOperation(vpn_tunnel_ref, operation_ref,
                                   'Creating VPN tunnel')

  def Run(self, args):
    """Issues API requests to construct VPN Tunnels."""
    return self._Run(args, is_vpn_gateway_supported=True)
