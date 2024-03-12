# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the Distributed Cloud Edge Network routers related commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import ipaddress

from googlecloudsdk.api_lib.edge_cloud.networking import utils
from googlecloudsdk.calliope import arg_parsers


def AddDescriptionFlag(parser):
  """Adds a --description flag to the given parser."""
  help_text = """Description for the subnet."""
  parser.add_argument('--description', help=help_text, required=False)


def AddInterfaceArgs(parser, for_update=False):
  """Adds common arguments for routers add-interface or update-interface."""

  help_text = (
      """The argument group for configuring the interface for the router."""
  )

  operation = 'added'
  if for_update:
    operation = 'updated'

  parser.add_argument(
      '--interface-name',
      help='The name of the interface being {0}.'.format(operation),
      required=True,
  )
  interface_group = parser.add_argument_group(
      mutex=True, help=help_text, required=True
  )
  southbound_interface_group = interface_group.add_argument_group(
      help='The argument group for adding southbound interfaces to edge router.'
  )
  southbound_interface_group.add_argument(
      '--subnetwork',
      help='Subnetwork of the interface being {0}.'.format(operation),
  )
  northbound_interface_group = interface_group.add_argument_group(
      help='The argument group for adding northbound interfaces to edge router.'
  )
  northbound_interface_group.add_argument(
      '--interconnect-attachment',
      help='Interconnect attachment of the interface being {0}.'.format(
          operation
      ),
  )

  northbound_interface_group.add_argument(
      '--ip-address',
      type=utils.IPArgument,
      help='Link-local address of the router for this interface.',
  )
  northbound_interface_group.add_argument(
      '--ip-mask-length',
      type=arg_parsers.BoundedInt(lower_bound=0, upper_bound=128),
      help=(
          'Subnet mask for the link-local IP range of the interface. The'
          ' interface IP address and BGP peer IP address must be selected'
          ' from the subnet defined by this link-local range.'
      ),
  )

  loopback_interface_group = interface_group.add_argument_group(
      help='The argument group for adding loopback interfaces to edge router.'
  )
  loopback_interface_group.add_argument(
      '--loopback-ip-addresses',
      type=arg_parsers.ArgList(),
      metavar='LOOPBACK_IP_ADDRESSES',
      help='The list of ip ranges for the loopback interface.',
  )


def AddBgpPeerArgs(parser, for_update=False, enable_peer_ipv6_range=False):
  """Adds common arguments for managing BGP peers."""

  operation = 'added'
  if for_update:
    operation = 'updated'

  parser.add_argument(
      '--interface',
      required=not for_update,
      help='The name of the interface for this BGP peer.')
  parser.add_argument(
      '--peer-name',
      required=True,
      help='The name of the new BGP peer being {0}.'.format(operation))
  parser.add_argument(
      '--peer-asn',
      required=not for_update,
      type=int,
      help='The BGP autonomous system number (ASN) for this BGP peer. '
      'Must be a 16-bit or 32-bit private ASN as defined in '
      'https://tools.ietf.org/html/rfc6996, for example `--asn=64512`.')
  ip_address_parser = parser.add_mutually_exclusive_group(
      required=not for_update
  )
  ip_address_parser.add_argument(
      '--peer-ipv4-range',
      help='The IPv4 link-local address range of the peer router.',
  )
  if enable_peer_ipv6_range:
    ip_address_parser.add_argument(
        '--peer-ipv6-range',
        help='The IPv6 link-local address range of the peer router.',
    )


def AddUpdateArgs(parser):
  """Adds arguments for Update."""

  def helptext(verb, prep):
    return ('{} the comma-separated list of CIDRs {} the set of range '
            'advertisements.').format(verb, prep)

  def cidrlist(argstr):
    split = argstr.split(',')
    parsed = map(ipaddress.ip_network, split)
    retlist = sorted(parsed)
    retset = set(retlist)
    if len(retlist) != len(retset):
      raise ValueError('CIDR list contained duplicates.')
    return retlist

  adv_group = parser.add_argument_group(mutex=True)
  adv_group.add_argument(
      '--add-advertisement-ranges',
      help=helptext('add', 'to'),
      type=cidrlist,
      default=[])
  adv_group.add_argument(
      '--set-advertisement-ranges',
      help=helptext('replace', 'with'),
      type=cidrlist,
      default=[])
  adv_group.add_argument(
      '--remove-advertisement-ranges',
      help=helptext('remove', 'from'),
      type=cidrlist,
      default=[])
