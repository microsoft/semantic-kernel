# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Code that's shared between multiple networks subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.command_lib.util.apis import arg_utils

RANGE_HELP_TEXT = """\
    Specifies the IPv4 address range of legacy mode networks. The range
    must be specified in CIDR format:
    [](http://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing)

    This flag only works if mode is
    [legacy](https://cloud.google.com/compute/docs/vpc/legacy).

    Using legacy networks is **DEPRECATED**, given that many newer Google
    Cloud Platform features are not supported on legacy networks. Please be
    advised that legacy networks may not be supported in the future.
    """

_RANGE_NON_LEGACY_MODE_ERROR = (
    '--range can only be used with --subnet-mode=legacy.'
)

_BGP_ROUTING_MODE_CHOICES = {
    'global': (
        'Cloud Routers in this network advertise subnetworks from all '
        'regions to their BGP peers, and program instances in all '
        "regions with the router's best learned BGP routes."
    ),
    'regional': (
        'Cloud Routers in this network advertise subnetworks from '
        'their local region only to their BGP peers, and program '
        "instances in their local region only with the router's best "
        'learned BGP routes.'
    ),
}

_NETWORK_FIREWALL_POLICY_ENFORCEMENT_ORDER_CHOICES = {
    'AFTER_CLASSIC_FIREWALL': (
        'Network Firewall Policy is enforced after classic firewall.'
    ),
    'BEFORE_CLASSIC_FIREWALL': (
        'Network Firewall Policy is enforced before classic firewall.'
    ),
}

_CREATE_SUBNET_MODE_CHOICES = {
    'auto': (
        'Subnets are created automatically.  This is the recommended selection.'
    ),
    'custom': 'Create subnets manually.',
    'legacy': (
        '[Deprecated] Create an old style network that has a range and cannot '
        'have subnets.  This is not recommended for new networks.'
    ),
}


def AddCreateBaseArgs(parser):
  """Adds common arguments for creating a network."""

  parser.add_argument(
      '--description', help='An optional, textual description for the network.'
  )

  parser.add_argument('--range', help=RANGE_HELP_TEXT)


def AddCreateSubnetModeArg(parser):
  """Adds the --subnet-mode flag."""
  parser.add_argument(
      '--subnet-mode',
      choices=_CREATE_SUBNET_MODE_CHOICES,
      type=lambda mode: mode.lower(),
      metavar='MODE',
      help="""The subnet mode of the network. If not specified, defaults to
              AUTO.""",
  )


def AddMtuArg(parser):
  """Adds the --mtu flag."""
  parser.add_argument(
      '--mtu',
      type=int,
      help="""Maximum transmission unit (MTU) is the size of the largest
              IP packet that can be transmitted on this network. Default value
              is 1460 bytes. The minimum value is 1300 bytes and the maximum
              value is 8896 bytes. The MTU advertised via DHCP to all instances
              attached to this network.""",
  )


def AddRdmaArg(parser):
  """Adds the --rdma flag."""
  parser.add_argument(
      '--rdma',
      hidden=True,
      action=arg_parsers.StoreTrueFalseAction,
      help="""Enable/disable RDMA on this network.""",
  )


def AddBgpBestPathSelectionArgGroup(parser):
  """Adds the BGP Best Path Selection flags.

  Args:
    parser (parser_arguments.ArgumentInterceptor): Argument parser
  """
  group = parser.add_argument_group(help="""BGP Best Path Selection flags""")
  group.add_argument(
      '--bgp-best-path-selection-mode',
      choices={
          'LEGACY': (
              'Dynamic routes are ranked based on MED BGP attribute. When'
              ' global routing is enabled, MED of the routes received from'
              ' other regions is original MED plus region-to-region cost.'
          ),
          'STANDARD': (
              'Dynamic routes are ranked based on AS Path, Origin, Neighbor ASN'
              ' and MED BGP attributes. When global routing is enabled,'
              ' region-to-region cost is used as a tiebreaker. This mode offers'
              ' customizations to fine-tune BGP best path routing with'
              ' additional knobs like --bgp-bps-always-compare-med and'
              ' --bgp-bps-inter-region-cost'
          ),
      },
      help="""The BGP best selection algorithm to be employed. MODE can be LEGACY or STANDARD.""",
      type=arg_utils.ChoiceToEnumName,
  )
  group.add_argument(
      '--bgp-bps-always-compare-med',
      action=arg_parsers.StoreTrueFalseAction,
      help="""Enables/disables the comparison of MED across routes with different NeighborAsn. This value can only be set if the --bgp-best-path-selection-mode is STANDARD.""",
  )
  group.add_argument(
      '--bgp-bps-inter-region-cost',
      choices={
          'DEFAULT': (
              'MED is compared as originally received from peers. Cost is'
              ' evaluated as a next step when MED is the same.'
          ),
          'ADD_COST_TO_MED': (
              'Adds inter-region cost to the MED before comparing MED value.'
              ' When multiple routes have the same value after the'
              ' Add-cost-to-med comparison, the route selection continues and'
              ' prefers the route with lowest cost.'
          ),
      },
      help="""Allows to define preferred approach for handling inter-region cost in the selection process. This value can only be set if the --bgp-best-path-selection-mode is STANDARD.""",
      type=arg_utils.ChoiceToEnumName,
  )


def AddEnableUlaInternalIpv6Arg(parser):
  """Adds the --enable-ula-internal-ipv6 flag."""
  parser.add_argument(
      '--enable-ula-internal-ipv6',
      action=arg_parsers.StoreTrueFalseAction,
      help="""Enable/disable ULA internal IPv6 on this network. Enabling this
      feature will assign a /48 from google defined ULA prefix fd20::/20.""",
  )


def AddInternalIpv6RangeArg(parser):
  """Adds the --internal-ipv6-range flag."""
  parser.add_argument(
      '--internal-ipv6-range',
      type=str,
      help="""When enabling ULA internal IPv6, caller can optionally specify
      the /48 range they want from the google defined ULA prefix fd20::/20.
      ULA_IPV6_RANGE must be a valid /48 ULA IPv6 address and within the
      fd20::/20. Operation will fail if the speficied /48 is already in used
      by another resource. If the field is not speficied, then a /48 range
      will be randomly allocated from fd20::/20 and returned via this field.""",
  )


def AddNetworkFirewallPolicyEnforcementOrderArg(parser):
  """Adds the --network-firewall-policy-enforcement-order flag."""
  parser.add_argument(
      '--network-firewall-policy-enforcement-order',
      choices=_NETWORK_FIREWALL_POLICY_ENFORCEMENT_ORDER_CHOICES,
      metavar='NETWORK_FIREWALL_POLICY_ENFORCEMENT_ORDER',
      help="""The Network Firewall Policy enforcement order of this network. If
              not specified, defaults to AFTER_CLASSIC_FIREWALL.""",
  )


def AddCreateBgpRoutingModeArg(parser):
  """Adds the --bgp-routing-mode flag."""
  parser.add_argument(
      '--bgp-routing-mode',
      choices=_BGP_ROUTING_MODE_CHOICES,
      default='regional',
      type=lambda mode: mode.lower(),
      metavar='MODE',
      help="""The BGP routing mode for this network. If not specified, defaults
              to regional.""",
  )


def AddUpdateArgs(parser):
  """Adds arguments for updating a network."""

  mode_args = parser.add_mutually_exclusive_group(required=False)

  mode_args.add_argument(
      '--switch-to-custom-subnet-mode',
      action='store_true',
      help="""Switch to custom subnet mode. This action cannot be undone.""",
  )

  mode_args.add_argument(
      '--bgp-routing-mode',
      choices=_BGP_ROUTING_MODE_CHOICES,
      type=lambda mode: mode.lower(),
      metavar='MODE',
      help="""The target BGP routing mode for this network.""",
  )

  AddMtuArg(parser)
  AddInternalIpv6RangeArg(parser)
  AddEnableUlaInternalIpv6Arg(parser)

  AddNetworkFirewallPolicyEnforcementOrderArg(parser)


def CheckRangeLegacyModeOrRaise(args):
  """Checks for range being used with incompatible mode and raises an error."""
  if (
      args.IsSpecified('range')
      and args.IsSpecified('subnet_mode')
      and args.subnet_mode != 'legacy'
  ):
    raise parser_errors.ArgumentError(_RANGE_NON_LEGACY_MODE_ERROR)
