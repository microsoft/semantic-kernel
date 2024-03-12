# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the compute routers commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.util.apis import arg_utils

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      region.basename(),
      network.basename()
    )"""

_MODE_CHOICES = {
    'DEFAULT': 'Default (Google-managed) BGP advertisements.',
    'CUSTOM': 'Custom (user-configured) BGP advertisements.',
}

_GROUP_CHOICES = {
    'ALL_SUBNETS': (
        'Automatically advertise all available subnets. This excludes '
        'any routes learned for subnets that use VPC Network Peering.'
    ),
}

_BFD_SESSION_INITIALIZATION_MODE_CHOICES = {
    'ACTIVE': (
        'The Cloud Router will initiate the BFD session for this BGP peer.'
    ),
    'PASSIVE': (
        'The Cloud Router will wait for the peer router to initiate the BFD '
        'session for this BGP peer.'
    ),
    'DISABLED': 'BFD is disabled for this BGP peer.',
}


class RoutersCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(RoutersCompleter, self).__init__(
        collection='compute.routers',
        list_command='compute routers list --uri',
        **kwargs
    )


def RouterArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='router',
      completer=RoutersCompleter,
      plural=plural,
      required=required,
      regional_collection='compute.routers',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION,
  )


def RouterArgumentForVpnTunnel(required=True):
  return compute_flags.ResourceArgument(
      resource_name='router',
      name='--router',
      completer=RoutersCompleter,
      plural=False,
      required=required,
      regional_collection='compute.routers',
      short_help='The Router to use for dynamic routing.',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION,
  )


def RouterArgumentForOtherResources(required=True, suppress_region=True):
  region_explanation = (
      'Should be the same as --region, if not specified, '
      'it will be inherited from --region.'
  )
  return compute_flags.ResourceArgument(
      resource_name='router',
      name='--router',
      completer=RoutersCompleter,
      plural=False,
      required=required,
      regional_collection='compute.routers',
      short_help='The Google Cloud Router to use for dynamic routing.',
      region_explanation=region_explanation,
      region_hidden=suppress_region,
  )


def RouterArgumentForNat():
  return compute_flags.ResourceArgument(
      resource_name='router',
      name='--router',
      completer=RoutersCompleter,
      plural=False,
      required=True,
      regional_collection='compute.routers',
      short_help='The Router to use for NAT.',
      region_hidden=True,
  )


def AddCreateRouterArgs(parser):
  """Adds common arguments for creating routers."""

  parser.add_argument(
      '--description', help='An optional description of this router.'
  )

  AddAsnArg(parser)


def AddKeepaliveIntervalArg(parser):
  """Adds keepalive interval argument for routers."""
  parser.add_argument(
      '--keepalive-interval',
      type=arg_parsers.Duration(
          default_unit='s', lower_bound='20s', upper_bound='60s'
      ),
      help=(
          'The interval between BGP keepalive messages that are sent to the'
          ' peer. If set, this value must be between 20 and 60 seconds. The'
          ' default is 20 seconds. See $ gcloud topic datetimes for information'
          ' on duration formats.\n\nBGP systems exchange keepalive messages to'
          ' determine whether a link or host has failed or is no longer'
          ' available. Hold time is the length of time in seconds that the BGP'
          ' session is considered operational without any activity. After the'
          ' hold time expires, the session is dropped.\n\nHold time is three'
          ' times the interval at which keepalive messages are sent, and the'
          ' hold time is the maximum number of seconds allowed to elapse'
          ' between successive keepalive messages that BGP receives from a'
          ' peer. BGP will use the smaller of either the local hold time value'
          " or the peer's  hold time value as the hold time for the BGP"
          ' connection between the two peers.'
      ),
  )


def AddBgpIdentifierRangeArg(parser):
  """Adds BGP identifier range argument for routers."""
  parser.add_argument(
      '--bgp-identifier-range',
      type=utils.IPV4RangeArgument,
      help=(
          'The range of valid BGP Identifiers for this Router. Must be a'
          ' link-local IPv4 range from 169.254.0.0/16, of size at least /30,'
          ' even if the BGP sessions are over IPv6. It must not overlap with'
          ' any IPv4 BGP session ranges. This is commonly called "router ID" by'
          ' other vendors.'
      ),
  )


def AddAsnArg(parser):
  """Adds Asn argument for routers."""
  parser.add_argument(
      '--asn',
      required=False,
      type=int,
      help=(
          'The optional BGP autonomous system number (ASN) for this router. '
          'Must be a 16-bit or 32-bit private ASN as defined in '
          'https://tools.ietf.org/html/rfc6996, for example `--asn=64512`.'
      ),
  )


def AddInterfaceArgs(parser, for_update=False, enable_ipv6_bgp=False):
  """Adds common arguments for routers add-interface or update-interface."""

  operation = 'added'
  if for_update:
    operation = 'updated'

  parser.add_argument(
      '--interface-name',
      required=True,
      help='The name of the interface being {0}.'.format(operation),
  )

  if enable_ipv6_bgp:
    parser.add_argument(
        '--ip-address',
        type=utils.IPArgument,
        help=(
            'The link local (IPv4) or ULA (IPv6) address of the router for this'
            ' interface.'
        ),
    )
    parser.add_argument(
        '--mask-length',
        type=arg_parsers.BoundedInt(lower_bound=0, upper_bound=126),
        help=(
            'The subnet mask for the IP range of the interface. The interface'
            ' IP address and BGP peer IP address must be selected from the'
            ' subnet defined by this range.'
        ),
    )
    parser.add_argument(
        '--ip-version',
        type=arg_utils.ChoiceToEnumName,
        choices={
            'IPV4': 'Interface with IPv4-based BGP.',
            'IPV6': 'Interface with IPv6-based BGP.',
        },
        help=(
            'IP version of the interface. Possible values are IPV4 and IPV6.'
            ' Defaults to IPV4.'
        ),
    )

  else:
    parser.add_argument(
        '--ip-address',
        type=utils.IPV4Argument,
        help='The link local address of the router for this interface.',
    )
    parser.add_argument(
        '--mask-length',
        type=arg_parsers.BoundedInt(lower_bound=0, upper_bound=31),
        help=(
            'The subnet mask for the link-local IP range of the interface. The'
            ' interface IP address and BGP peer IP address must be selected'
            ' from the subnet defined by this link-local range.'
        ),
    )

  if not for_update:
    parser.add_argument(
        '--redundant-interface',
        help='The interface that is redundant to the current interface.',
    )


def AddBgpPeerArgs(
    parser,
    for_add_bgp_peer=False,
    is_update=False,
    enable_ipv6_bgp=False,
    enable_route_policies=False,
):
  """Adds common arguments for managing BGP peers."""

  operation = 'updated'
  if for_add_bgp_peer:
    operation = 'added'

  parser.add_argument(
      '--peer-name',
      required=True,
      help='The name of the new BGP peer being {0}.'.format(operation),
  )

  parser.add_argument(
      '--interface',
      required=for_add_bgp_peer,
      help='The name of the interface for this BGP peer.',
  )

  parser.add_argument(
      '--peer-asn',
      required=for_add_bgp_peer,
      type=int,
      help=(
          'The BGP autonomous system number (ASN) for this BGP peer. '
          'Must be a 16-bit or 32-bit private ASN as defined in '
          'https://tools.ietf.org/html/rfc6996, for example `--asn=64512`.'
      ),
  )

  # For add_bgp_peer, we only require the interface and infer the IP instead.
  if not for_add_bgp_peer:
    if enable_ipv6_bgp:
      parser.add_argument(
          '--ip-address',
          type=utils.IPArgument,
          help=(
              'The address of the Cloud Router interface for this BGP peer.'
              ' Must be a link-local IPv4 address in  the range 169.254.0.0/16'
              ' or an ULA IPv6 address in the range fdff:1::/64. It must also'
              ' be in the same subnet as the interface address of the peer'
              ' router.'
          ),
      )
    else:
      parser.add_argument(
          '--ip-address',
          type=utils.IPV4Argument,
          help=(
              'The link-local address of the Cloud Router interface for this'
              ' BGP peer. Must be a link-local IPv4 address belonging to the'
              ' range 169.254.0.0/16 and must belong to same subnet as the'
              ' interface address of the peer router.'
          ),
      )

  if enable_ipv6_bgp:
    parser.add_argument(
        '--peer-ip-address',
        type=utils.IPArgument,
        help=(
            'The address of the peer router. Must be a link-local IPv4 address'
            ' in the the range 169.254.0.0/16 or an ULA IPv6 address in the'
            ' range fdff:1::/64.'
        ),
    )
  else:
    parser.add_argument(
        '--peer-ip-address',
        type=utils.IPV4Argument,
        help=(
            'The link-local address of the peer router. Must be a link-local '
            'IPv4 address belonging to the range 169.254.0.0/16.'
        ),
    )

  parser.add_argument(
      '--advertised-route-priority',
      type=arg_parsers.BoundedInt(lower_bound=0, upper_bound=65535),
      help=(
          'The priority of routes advertised to this BGP peer. In the case '
          'where there is more than one matching route of maximum length, '
          'the routes with lowest priority value win. 0 <= priority <= '
          '65535. If not specified, will use Google-managed priorities.'
      ),
  )

  bfd_group_help = (
      'Arguments to {0} BFD (Bidirectional Forwarding Detection) '
      'settings:'.format('update' if is_update else 'configure')
  )
  bfd_group = parser.add_group(help=bfd_group_help)
  bfd_group.add_argument(
      '--bfd-session-initialization-mode',
      choices=_BFD_SESSION_INITIALIZATION_MODE_CHOICES,
      type=lambda mode: mode.upper(),
      metavar='BFD_SESSION_INITIALIZATION_MODE',
      help=(
          'The BFD session initialization mode for this BGP peer. Must be one'
          ' of:\n\nACTIVE - The Cloud Router will initiate the BFD session for'
          ' this BGP peer.\n\nPASSIVE - The Cloud Router will wait for the peer'
          ' router to initiate the BFD session for this BGP peer.\n\nDISABLED -'
          ' BFD is disabled for this BGP peer.'
      ),
  )

  bfd_group.add_argument(
      '--bfd-min-transmit-interval',
      type=arg_parsers.Duration(
          default_unit='ms',
          lower_bound='1000ms',
          upper_bound='30000ms',
          parsed_unit='ms',
      ),
      help=(
          'The minimum transmit interval between BFD control packets. The '
          'default is 1000 milliseconds. See $ gcloud topic datetimes for '
          'information on duration formats.'
      ),
  )
  bfd_group.add_argument(
      '--bfd-min-receive-interval',
      type=arg_parsers.Duration(
          default_unit='ms',
          lower_bound='1000ms',
          upper_bound='30000ms',
          parsed_unit='ms',
      ),
      help=(
          'The minimum receive interval between BFD control packets. The '
          'default is 1000 milliseconds. See $ gcloud topic datetimes for '
          'information on duration formats.'
      ),
  )
  bfd_group.add_argument(
      '--bfd-multiplier',
      type=int,
      help=(
          'The number of consecutive BFD control packets that must be '
          'missed before BFD declares that a peer is unavailable.'
      ),
  )

  enabled_display_help = (
      'If enabled, the peer connection can be established with routing '
      'information. If disabled, any active session with the peer is '
      'terminated and all associated routing information is removed.'
  )

  if not is_update:
    enabled_display_help += ' Enabled by default.'
  parser.add_argument(
      '--enabled',
      action=arg_parsers.StoreTrueFalseAction,
      help=enabled_display_help,
  )

  enable_ipv6_display_help = (
      'If IPv6 is enabled, the peer connection can be established with '
      'IPv6 route exchange. If disabled, no IPv6 route exchange is allowed '
      'on any active session.'
  )
  if not is_update:
    enable_ipv6_display_help += ' Disabled by default.'
  parser.add_argument(
      '--enable-ipv6',
      action=arg_parsers.StoreTrueFalseAction,
      help=enable_ipv6_display_help,
  )

  if enable_ipv6_bgp:
    ipv6_nexthop_address_help = (
        'If IPv6 route exchange is enabled for IPv4-based BGP, the IPv6 next'
        ' hop address of the Cloud Router interface for this BGP peer.'
        ' Ignored otherwise. Must be a Google owned global unicast IPv6'
        ' address belonging to the range 2600:2d00:0:2:0:0:0:0/64 or'
        ' 2600:2d00:0:3:0:0:0:0/64 and must belong to same subnet as the'
        ' interface address of the peer router.'
    )
  else:
    ipv6_nexthop_address_help = (
        'The IPv6 next hop address of the Cloud Router interface '
        'for this BGP peer. Must be a Google owned global unicast IPv6 '
        'address belonging to the range 2600:2d00:0:2:0:0:0:0/64 or '
        '2600:2d00:0:3:0:0:0:0/64 and must belong to same subnet as '
        'the interface address of the peer router.'
    )
  parser.add_argument(
      '--ipv6-nexthop-address',
      type=utils.IPV6Argument,
      help=ipv6_nexthop_address_help,
  )

  if enable_ipv6_bgp:
    peer_ipv6_nexthop_address_help = (
        'If IPv6 route exchange is enabled for IPv4-based BGP, the IPv6 next'
        ' hop address of the peer router. Ignored otherwise. Must be a Google'
        ' owned global unicast IPv6 address belonging to the range'
        ' 2600:2d00:0:2:0:0:0:0/64 or 2600:2d00:0:3:0:0:0:0/64.'
    )
  else:
    peer_ipv6_nexthop_address_help = (
        'The IPv6 next hop address of the peer router. Must be a '
        'Google owned global unicast IPv6 address belonging to the range '
        '2600:2d00:0:2:0:0:0:0/64 or 2600:2d00:0:3:0:0:0:0/64.'
    )
  parser.add_argument(
      '--peer-ipv6-nexthop-address',
      type=utils.IPV6Argument,
      help=peer_ipv6_nexthop_address_help,
  )

  if enable_ipv6_bgp:
    enable_ipv4_display_help = (
        'If IPv4 is enabled, the peer connection can be established with '
        'IPv4 route exchange. If disabled, no IPv4 route exchange is allowed '
        'on any active session.'
    )
    if not is_update:
      enable_ipv4_display_help += (
          ' By default enabled for IPv4-based BGP sessions.'
      )
    parser.add_argument(
        '--enable-ipv4',
        action=arg_parsers.StoreTrueFalseAction,
        help=enable_ipv4_display_help,
    )

    parser.add_argument(
        '--ipv4-nexthop-address',
        type=utils.IPV4Argument,
        help=(
            'If IPv4 route exchange is enabled for IPv6-based BGP, the IPv4'
            ' next hop address of the Cloud Router interface for this BGP peer.'
            ' Ignored otherwise. Must be a Google owned link-local IPv4 address'
            ' in the range 169.254.0.0/16 and must belong to the same subnet as'
            ' the interface address of the peer router.'
        ),
    )

    parser.add_argument(
        '--peer-ipv4-nexthop-address',
        type=utils.IPV4Argument,
        help=(
            'If IPv4 route exchange is enabled for IPv6-based BGP, the IPv4'
            ' next hop address of the peer router. Ignored otherwise. Must be a'
            ' Google owned link-local IPv4 address in the range 169.254.0.0/16.'
        ),
    )

  parser.add_argument(
      '--md5-authentication-key',
      type=str,
      help=(
          'The MD5 authentication key for this BGP peer. Maximum length is '
          '80 characters. Can contain only printable ASCII characters.'
      ),
  )

  if is_update:
    parser.add_argument(
        '--clear-md5-authentication-key',
        action='store_true',
        default=None,
        help='If specified, remove MD5 authentication from the BGP peer.',
    )
  if enable_route_policies:
    parser.add_argument(
        '--export-policies',
        metavar='EXPORT_POLICY',
        type=arg_parsers.ArgList(),
        help=(
            'Comma-separated list of export policies. Passing an empty string'
            ' removes all export policies.'
        ),
        hidden=True,
    )
    parser.add_argument(
        '--import-policies',
        type=arg_parsers.ArgList(),
        metavar='IMPORT_POLICY',
        help=(
            'Comma-separated list of import policies. Passing an empty string'
            ' removes all import policies.'
        ),
        hidden=True,
    )


def AddUpdateCustomAdvertisementArgs(parser, resource_str):
  """Adds common arguments for setting/updating custom advertisements."""

  AddReplaceCustomAdvertisementArgs(parser, resource_str)
  AddIncrementalCustomAdvertisementArgs(parser, resource_str)


def AddReplaceCustomAdvertisementArgs(parser, resource_str):
  """Adds common arguments for replacing custom advertisements."""

  parser.add_argument(
      '--advertisement-mode',
      choices=_MODE_CHOICES,
      type=lambda mode: mode.upper(),
      metavar='MODE',
      help="""The new advertisement mode for this {0}.""".format(resource_str),
  )

  parser.add_argument(
      '--set-advertisement-groups',
      type=arg_parsers.ArgList(
          choices=_GROUP_CHOICES, element_type=lambda group: group.upper()
      ),
      metavar='GROUP',
      help="""The list of pre-defined groups of IP ranges to dynamically
              advertise on this {0}. This list can only be specified in
              custom advertisement mode.""".format(resource_str),
  )

  parser.add_argument(
      '--set-advertisement-ranges',
      type=arg_parsers.ArgDict(allow_key_only=True),
      metavar='CIDR_RANGE=DESC',
      help="""The list of individual IP ranges, in CIDR format, to dynamically
              advertise on this {0}. Each IP range can (optionally) be given a
              text description DESC. For example, to advertise a specific range,
              use `--set-advertisement-ranges=192.168.10.0/24`.  To store a
              description with the range, use
              `--set-advertisement-ranges=192.168.10.0/24=my-networks`. This
              list can only be specified in custom advertisement mode.""".format(
          resource_str
      ),
  )


def AddIncrementalCustomAdvertisementArgs(parser, resource_str):
  """Adds common arguments for incrementally updating custom advertisements."""

  incremental_args = parser.add_mutually_exclusive_group(required=False)

  incremental_args.add_argument(
      '--add-advertisement-groups',
      type=arg_parsers.ArgList(
          choices=_GROUP_CHOICES, element_type=lambda group: group.upper()
      ),
      metavar='GROUP',
      help="""A list of pre-defined groups of IP ranges to dynamically advertise
              on this {0}. This list is appended to any existing advertisements.
              This field can only be specified in custom advertisement mode.""".format(
          resource_str
      ),
  )

  incremental_args.add_argument(
      '--remove-advertisement-groups',
      type=arg_parsers.ArgList(
          choices=_GROUP_CHOICES, element_type=lambda group: group.upper()
      ),
      metavar='GROUP',
      help="""A list of pre-defined groups of IP ranges to remove from dynamic
              advertisement on this {0}. Each group in the list must exist in
              the current set of custom advertisements. This field can only be
              specified in custom advertisement mode.""".format(resource_str),
  )

  incremental_args.add_argument(
      '--add-advertisement-ranges',
      type=arg_parsers.ArgDict(allow_key_only=True),
      metavar='CIDR_RANGE=DESC',
      help="""A list of individual IP ranges, in CIDR format, to dynamically
              advertise on this {0}. This list is appended to any existing
              advertisements. Each IP range can (optionally) be given a text
              description DESC. For example, to advertise a specific range, use
              `--advertisement-ranges=192.168.10.0/24`.  To store a description
              with the range, use
              `--advertisement-ranges=192.168.10.0/24=my-networks`. This list
              can only be specified in custom advertisement mode.""".format(
          resource_str
      ),
  )

  incremental_args.add_argument(
      '--remove-advertisement-ranges',
      type=arg_parsers.ArgList(),
      metavar='CIDR_RANGE',
      help="""A list of individual IP ranges, in CIDR format, to remove from
              dynamic advertisement on this {0}. Each IP range in the list must
              exist in the current set of custom advertisements. This field can
              only be specified in custom advertisement mode.""".format(
          resource_str
      ),
  )


def AddUpdateCustomLearnedRoutesArgs(parser):
  """Adds common arguments for setting/updating custom learned routes.

  Args:
    parser: The parser to parse arguments.
  """

  AddReplaceCustomLearnedRoutesArgs(parser)
  AddIncrementalCustomLearnedRoutesArgs(parser)


def AddReplaceCustomLearnedRoutesArgs(parser):
  """Adds common arguments for replacing custom learned routes.

  Args:
    parser: The parser to parse arguments.
  """

  parser.add_argument(
      '--custom-learned-route-priority',
      type=arg_parsers.BoundedInt(lower_bound=0, upper_bound=65535),
      metavar='PRIORITY',
      help="""An integral value `0` <= priority <= `65535`, to be applied to all
              custom learned route IP address ranges for this peer. If not
              specified, a Google-managed priority value of 100 is used. The
              routes with the lowest priority value win.""",
  )

  parser.add_argument(
      '--set-custom-learned-route-ranges',
      type=arg_parsers.ArgList(),
      metavar='CIDR_RANGE',
      help="""The list of user-defined custom learned route IP address ranges
              for this peer. This list is a comma separated IP address ranges
              such as `1.2.3.4`,`6.7.0.0/16`,`2001:db8:abcd:12::/64` where each
              IP address range must be a valid CIDR-formatted prefix. If an IP
              address is provided without a subnet mask, it is interpreted as a
              /32 singular IP address range for IPv4, and /128 for IPv6.""",
  )


def AddIncrementalCustomLearnedRoutesArgs(parser):
  """Adds common arguments for incrementally updating custom learned routes.

  Args:
    parser: The parser to parse arguments.
  """

  incremental_args = parser.add_mutually_exclusive_group(required=False)

  incremental_args.add_argument(
      '--add-custom-learned-route-ranges',
      type=arg_parsers.ArgList(),
      metavar='CIDR_RANGE',
      help="""A list of user-defined custom learned route IP address ranges to
              be added to this peer. This list is a comma separated IP address
              ranges such as `1.2.3.4`,`6.7.0.0/16`,`2001:db8:abcd:12::/64`
              where each IP address range must be a valid CIDR-formatted prefix.
              If an IP address is provided without a subnet mask, it is
              interpreted as a /32 singular IP address range for IPv4, and /128
              for IPv6.""",
  )

  incremental_args.add_argument(
      '--remove-custom-learned-route-ranges',
      type=arg_parsers.ArgList(),
      metavar='CIDR_RANGE',
      help="""A list of user-defined custom learned route IP address ranges to
              be removed from this peer. This list is a comma separated IP
              address ranges such as `1.2.3.4`,`6.7.0.0/16`,`2001:db8:abcd:12::/64`
              where each IP address range must be a valid CIDR-formatted prefix.
              If an IP address is provided without a subnet mask, it is
              interpreted as a /32 singular IP address range for IPv4, and /128
              for IPv6.""",
  )


def AddGetNatMappingInfoArgs(parser):
  """Adds common arguments for get-nat-mapping-info."""

  parser.add_argument(
      '--nat-name',
      required=False,
      help='The NAT name to filter out NAT mapping information',
  )


def AddGetNatIpInfoArgs(parser):
  """Adds common arguments for get-ip-mapping-info."""

  parser.add_argument(
      '--nat-name',
      required=False,
      help='The NAT name to filter out NAT IP information',
  )


def AddEncryptedInterconnectRouter(parser):
  """Adds encrypted interconnect router flag."""
  parser.add_argument(
      '--encrypted-interconnect-router',
      required=False,
      action='store_true',
      default=None,
      help=(
          'Indicates if a router is dedicated for use with encrypted '
          'interconnect attachments (VLAN attachments).'
      ),
  )
