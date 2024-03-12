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
"""Flags and helpers for the compute external-vpn-gateways commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags

# The default output format for the list sub-command.
DEFAULT_LIST_FORMAT = """\
    table(
      name,
      redundancyType
    )"""

ALLOWED_METAVAR = 'ID=IP_ADDRESS'

ALLOWED_INTERFACE_IDS = {0, 1, 2, 3}

EXTERNAL_VPN_GATEWAY_TYPE__MAP = {
    1: 'SINGLE_IP_INTERNALLY_REDUNDANT',
    2: 'TWO_IPS_REDUNDANCY',
    4: 'FOUR_IPS_REDUNDANCY',
}

LEGAL_SPECS = re.compile(
    r"""

    (?P<id>[0-3]) # The id group.

    (=(?P<ipAddress>(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)))
                                  # The ip_address group.

    $                             # End of input marker.
    """,
    re.VERBOSE,
)

LEGAL_IPV6_SPECS = re.compile(
    r"""

    (?P<id>[0-3]) # The id group.

    (=(?P<ipv6Address>(
    (([0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4}){0,6})?::(([0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4})?)
    |
    (([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4})
    )))
                                  # The ipv6_address group.

    $                             # End of input marker.
    """,
    re.VERBOSE,
)


class ExternalVpnGatewaysCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ExternalVpnGatewaysCompleter, self).__init__(
        collection='compute.externalVpnGateways',
        list_command='alpha compute external-vpn-gateways list --uri',
        **kwargs
    )


def ExternalVpnGatewayArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='external VPN gateway',
      completer=ExternalVpnGatewaysCompleter,
      plural=plural,
      required=required,
      global_collection='compute.externalVpnGateways',
  )


def ExternalVpnGatewayArgumentForVpnTunnel(required=False):
  return compute_flags.ResourceArgument(
      name='--peer-external-gateway',
      resource_name='external VPN gateway',
      completer=ExternalVpnGatewaysCompleter,
      required=required,
      short_help=(
          'Peer side external VPN gateway representing the remote '
          'tunnel endpoint, this flag is used when creating HA VPN '
          'tunnels from Google Cloud to your external VPN gateway.'
          'Either --peer-external-gateway or --peer-gcp-gateway must be'
          ' specified when creating VPN tunnels from High Available '
          'VPN gateway.'
      ),
      global_collection='compute.externalVpnGateways',
  )


def AddCreateExternalVpnGatewayArgs(parser, is_ipv6_supported=None):
  """Adds common arguments for creating external VPN gateways."""

  parser.add_argument(
      '--description', help='Textual description of the External VPN Gateway.'
  )

  if is_ipv6_supported:
    parser.add_argument(
        '--interfaces',
        required=True,
        metavar=ALLOWED_METAVAR,
        type=arg_parsers.ArgList(min_length=0, max_length=4),
        help="""\
        Map of interfaces from interface ID to interface IP address for the External VPN Gateway.

        There can be one, two, or four interfaces in the map.

        For example, to create an external VPN gateway with one interface:

          $ {command} MY-EXTERNAL-GATEWAY --interfaces 0=192.0.2.0

        To create an external VPN gateway with two interfaces:
          $ {command} MY-EXTERNAL-GATEWAY --interfaces 0=192.0.2.0,1=192.0.2.1

        To create an external VPN gateway with four interfaces:
          $ {command} MY-EXTERNAL-GATEWAY --interfaces 0=192.0.2.0,1=192.0.2.1,2=192.0.2.3,3=192.0.2.4

        To create an external VPN gateway with IPv6 addresses on four interfaces:
          $ {command} MY-EXTERNAL-GATEWAY --interfaces 0=2001:db8::1,1=2001:db8::2,2=2001:db8::3,3=2001:db8::4

        Note that the redundancy type of the gateway will be automatically inferred based on the number
        of interfaces provided:

          1 interface: `SINGLE_IP_INTERNALLY_REDUNDANT`

          2 interfaces: `TWO_IPS_REDUNDANCY`

          4 interfaces: `FOUR_IPS_REDUNDANCY`
        """,
    )
  else:
    parser.add_argument(
        '--interfaces',
        required=True,
        metavar=ALLOWED_METAVAR,
        type=arg_parsers.ArgList(min_length=0, max_length=4),
        help="""\
        Map of interfaces from interface ID to interface IP address for the External VPN Gateway.

        There can be one, two, or four interfaces in the map.

        For example, to create an external VPN gateway with one interface:

          $ {command} MY-EXTERNAL-GATEWAY --interfaces 0=8.9.9.9

        To create an external VPN gateway with two interfaces:
          $ {command} MY-EXTERNAL-GATEWAY --interfaces 0=8.9.9.9,1=8.9.9.10

        To create an external VPN gateway with four interfaces:
          $ {command} MY-EXTERNAL-GATEWAY --interfaces 0=8.9.9.9,1=8.9.9.10,2=8.9.9.11,3=8.9.9.12

        Note that the redundancy type of the gateway will be automatically inferred based on the number
        of interfaces provided:

          1 interface: `SINGLE_IP_INTERNALLY_REDUNDANT`

          2 interfaces: `TWO_IPS_REDUNDANCY`

          4 interfaces: `FOUR_IPS_REDUNDANCY`
        """,
    )


def ParseInterfaces(interfaces, message_classes, is_ipv6_supported=None):
  """Parses id=ip_address mappings from --interfaces command line."""
  if len(interfaces) != 1 and len(interfaces) != 2 and len(interfaces) != 4:
    raise exceptions.ArgumentError(
        'Number of interfaces must be either one, two, or four; received [{0}] '
        'interface(s).'.format(len(interfaces))
    )

  interface_list = []
  for spec in interfaces or []:
    match_ipv4 = LEGAL_SPECS.match(spec)
    if match_ipv4:
      interface_id = match_ipv4.group('id')
      ip_address = match_ipv4.group('ipAddress')
      interface = message_classes.ExternalVpnGatewayInterface(
          id=int(interface_id), ipAddress=ip_address
      )
      interface_list.append(interface)
      continue

    match_ipv6 = False
    if is_ipv6_supported:
      match_ipv6 = LEGAL_IPV6_SPECS.match(spec)
      if match_ipv6:
        interface_id = match_ipv6.group('id')
        ipv6_address = match_ipv6.group('ipv6Address')
        interface = message_classes.ExternalVpnGatewayInterface(
            id=int(interface_id), ipv6Address=ipv6_address
        )
        interface_list.append(interface)
        continue

    if not match_ipv4 and not match_ipv6:
      raise exceptions.ArgumentError(
          'Interfaces must be of the form {0}, ID must be an integer value in '
          '[0,1,2,3], IP_ADDRESS must be a valid IP address; received [{1}].'
          .format(ALLOWED_METAVAR, spec)
      )

  return interface_list


def InferAndGetRedundancyType(interfaces, messages):
  """Converts the interconnect type flag to a message enum.

  Args:
    interfaces: List of the interfaces provided by user.
    messages: The API messages holder.

  Returns:
    An InterconnectTypeValueValuesEnum of the flag value, or None if absent.
  """
  if (
      interfaces is None
      or EXTERNAL_VPN_GATEWAY_TYPE__MAP[len(interfaces)] is None
  ):
    return None
  else:
    return messages.ExternalVpnGateway.RedundancyTypeValueValuesEnum(
        EXTERNAL_VPN_GATEWAY_TYPE__MAP[len(interfaces)]
    )
