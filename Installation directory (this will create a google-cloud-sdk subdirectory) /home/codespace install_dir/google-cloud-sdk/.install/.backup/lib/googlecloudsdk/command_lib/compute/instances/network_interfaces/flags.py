# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the compute instances network-interfaces commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.apis import arg_utils


def AddNetworkInterfaceArgForUpdate(parser):
  parser.add_argument(
      '--network-interface',
      default='nic0',
      help='The name of the network interface to update.',
  )


def AddParentNicNameArg(parser):
  parser.add_argument(
      '--parent-nic-name',
      type=str,
      help="""
        Name of the parent network interface of a VLAN based network interface.
        If this field is specified, vlan must be set.
      """,
  )


def AddVlanArg(parser):
  parser.add_argument(
      '--vlan',
      type=int,
      help="""
        VLAN tag of a VLAN based network interface, must be in range from 2 to
        4094 inclusively. This field is mandatory if the parent network
        interface name is set.
      """,
  )


def AddNetworkArg(parser):
  parser.add_argument(
      '--network',
      type=str,
      help='Specifies the network this network interface belongs to.',
  )


def AddSubnetworkArg(parser):
  parser.add_argument(
      '--subnetwork',
      type=str,
      help='Specifies the subnetwork this network interface belongs to.',
  )


def AddPrivateNetworkIpArg(parser, add_network_interface=False):
  """Adds --private-network-ip argument to the parser."""
  if add_network_interface:
    help_text = """
        Specifies the RFC1918 IP to assign to the network interface. The IP
        should be in the subnet IP range.
      """
  else:
    help_text = """
        Assign the given IP address to the interface. Can be specified only
        together with --network and/or --subnetwork to choose the IP address
        in the new subnetwork. If unspecified, then the previous IP address
        will be allocated in the new subnetwork. If the previous IP address is
        not available in the new subnetwork, then another available IP address
        will be allocated automatically from the new subnetwork CIDR range.
      """
  parser.add_argument(
      '--private-network-ip',
      dest='private_network_ip',
      type=str,
      help=help_text,
  )


def AddAliasesArg(parser, add_network_interface=False):
  """Adds --aliases argument to the parser."""
  if add_network_interface:
    help_text = """
        The IP alias ranges to allocate for this interface. If there are
        multiple IP alias ranges, they are separated by semicolons.

        For example:

            --aliases="10.128.1.0/24;range1:/32"

        Each IP alias range consists of a range name and an IP range
        separated by a colon, or just the IP range.
        The range name is the name of the range within the network
        interface's subnet from which to allocate an IP alias range. If
        unspecified, it defaults to the primary IP range of the subnet.
        The IP range can be a CIDR range (e.g. `192.168.100.0/24`), a single
        IP address (e.g. `192.168.100.1`), or a netmask in CIDR format (e.g.
        `/24`). If the IP range is specified by CIDR range or single IP
        address, it must belong to the CIDR range specified by the range
        name on the subnet. If the IP range is specified by netmask, the
        IP allocator will pick an available range with the specified netmask
        and allocate it to this network interface.
      """
  else:
    help_text = """
        The IP alias ranges to allocate for this interface. If there are
        multiple IP alias ranges, they are separated by semicolons.

        Can be specified together with --network and/or --subnetwork to choose
        IP alias ranges in the new subnetwork. If unspecified, then the previous
        IP alias ranges will be allocated in the new subnetwork. If the previous
        IP alias ranges are not available in the new subnetwork, then other
        available IP alias ranges of the same size will be allocated in the new
        subnetwork.

        For example:

            --aliases="10.128.1.0/24;r1:/32"
      """
  parser.add_argument(
      '--aliases',
      type=str,
      help=help_text,
  )


def AddStackTypeArg(parser):
  parser.add_argument(
      '--stack-type',
      choices={
          'IPV4_ONLY': 'The network interface will be assigned IPv4 addresses.',
          'IPV4_IPV6': (
              'The network interface can have both IPv4 and IPv6 addresses.'
          ),
      },
      type=arg_utils.ChoiceToEnumName,
      help=(
          'The stack type for the default network interface. Determines if '
          'IPv6 is enabled on the default network interface.'
      ),
  )


def AddNetworkTierArg(parser):
  parser.add_argument(
      '--network-tier',
      choices={
          'PREMIUM': 'High quality, Google-grade network tier.',
          'STANDARD': 'Public internet quality.',
          'FIXED_STANDARD': 'Public internet quality with fixed bandwidth.',
      },
      type=arg_utils.ChoiceToEnumName,
      help="""
        Specifies the network tier that will be used to configure the instance
        network interface. ``NETWORK_TIER'' must be one of: `PREMIUM`,
        `STANDARD`, `FIXED_STANDARD`. The default value is `PREMIUM`.
      """,
  )


def AddIpv6NetworkTierArg(parser):
  parser.add_argument(
      '--ipv6-network-tier',
      choices={'PREMIUM': 'High quality, Google-grade network tier.'},
      type=arg_utils.ChoiceToEnumName,
      help=(
          'Specifies the IPv6 network tier that will be used to configure '
          'the instance network interface IPv6 access config.'
      ),
  )


def AddAddressArgs(parser):
  """Adds --address and --no-address mutex arguments to the parser."""
  addresses = parser.add_mutually_exclusive_group()
  addresses.add_argument(
      '--address',
      type=str,
      help="""
        Assigns the given external address to the network interface. The
        address might be an IP address or the name or URI of an address
        resource. Specifying an empty string will assign an ephemeral IP.
        Mutually exclusive with no-address. If neither key is present the
        network interface will get an ephemeral IP.
      """,
  )
  addresses.add_argument(
      '--no-address',
      action='store_true',
      help="""
        If specified the network interface will have no external IP.
        Mutually exclusive with address. If neither key is present the network
        interfaces will get an ephemeral IP.
      """,
  )


def AddExternalIpv6AddressArg(parser):
  parser.add_argument(
      '--external-ipv6-address',
      type=str,
      help="""
        Assigns the given external IPv6 address to an instance.
        The address must be the first IP in the range. This option is applicable
        only to dual-stack instances with stack-type=IPV4_ONLY.
      """,
  )


def AddExternalIpv6PrefixLengthArg(parser):
  parser.add_argument(
      '--external-ipv6-prefix-length',
      type=int,
      help="""
        The prefix length of the external IPv6 address range. This flag should be used together
        with `--external-ipv6-address`. Currently only `/96` is supported and the default value
        is `96`.
      """,
  )


def AddInternalIpv6AddressArg(parser):
  parser.add_argument(
      '--internal-ipv6-address',
      type=str,
      help="""
        Assigns the given internal IPv6 address or range to an instance.
        The address must be the first IP address in the range or a /96 IP
        address range. This option can only be used on a dual stack instance
        network interface.
      """,
  )


def AddInternalIpv6PrefixLengthArg(parser):
  parser.add_argument(
      '--internal-ipv6-prefix-length',
      type=int,
      help="""
        Optional field that indicates the prefix length of the internal IPv6
        address range, should be used together with
        `--internal-ipv6-address=fd20::`. Only /96 IP address range is supported
        and the default value is 96. If not set, then  either the prefix length
        from `--internal-ipv6-address=fd20::/96` will be used or the default
        value of 96 will be assigned.
      """,
  )


def AddIpv6AddressArg(parser):
  parser.add_argument(
      '--ipv6-address',
      type=str,
      help="""
        Assigns the given external IPv6 address to an instance.
        The address must be the first IP in the range. This option is applicable
        only to dual-stack instances with stack-type=IPV4_ONLY.
      """,
  )


def AddIpv6PrefixLengthArg(parser):
  parser.add_argument(
      '--ipv6-prefix-length',
      type=int,
      help="""
        The prefix length of the external IPv6 address range. This flag should be used together
        with `--ipv6-address`. Currently only `/96` is supported and the default value
        is `96`.
      """,
  )
