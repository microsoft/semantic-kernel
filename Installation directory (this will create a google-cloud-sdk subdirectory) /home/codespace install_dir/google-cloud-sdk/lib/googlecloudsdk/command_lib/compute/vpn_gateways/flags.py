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
"""Flags and helpers for the compute vpn-gateways commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.util.apis import arg_utils

# The default output format for the list sub-command.
DEFAULT_LIST_FORMAT = """\
    table(
      name,
      vpnInterfaces[0].ipAddress:label=INTERFACE0,
      vpnInterfaces[1].ipAddress:label=INTERFACE1,
      vpnInterfaces[0].ipv6Address:label=INTERFACE0_IPV6,
      vpnInterfaces[1].ipv6Address:label=INTERFACE1_IPV6,
      network.basename(),
      region.basename()
    )"""


class VpnGatewaysCompleter(compute_completers.ListCommandCompleter):
  """A VPN gateway completer for a resource argument."""

  def __init__(self, **kwargs):
    super(VpnGatewaysCompleter, self).__init__(
        collection='compute.vpnGateways',
        list_command='alpha compute vpn-gateways list --uri',
        **kwargs)


def GetVpnGatewayArgument(required=True, plural=False):
  """Returns the resource argument object for the VPN gateway flag."""
  return compute_flags.ResourceArgument(
      resource_name='VPN Gateway',
      completer=VpnGatewaysCompleter,
      plural=plural,
      custom_plural='VPN Gateways',
      required=required,
      regional_collection='compute.vpnGateways',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def GetVpnGatewayArgumentForOtherResource(required=False):
  """Returns the flag for specifying the VPN gateway."""
  return compute_flags.ResourceArgument(
      name='--vpn-gateway',
      resource_name='VPN Gateway',
      completer=VpnGatewaysCompleter,
      plural=False,
      required=required,
      regional_collection='compute.vpnGateways',
      short_help=('Reference to a VPN gateway, this flag is used for creating '
                  'HA VPN tunnels.'),
      region_explanation=('Should be the same as region, if not specified, '
                          'it will be automatically set.'),
      detailed_help="""\
        Reference to a Highly Available VPN gateway.
        """)


def GetPeerVpnGatewayArgumentForOtherResource(required=False):
  """Returns the flag for specifying the peer VPN gateway."""
  return compute_flags.ResourceArgument(
      name='--peer-gcp-gateway',
      resource_name='VPN Gateway',
      completer=VpnGatewaysCompleter,
      plural=False,
      required=required,
      regional_collection='compute.vpnGateways',
      short_help=(
          'Peer side Highly Available VPN gateway representing the remote '
          'tunnel endpoint, this flag is used when creating HA VPN tunnels '
          'from Google Cloud to Google Cloud.'
          'Either --peer-external-gateway or --peer-gcp-gateway must be specified when '
          'creating VPN tunnels from High Available VPN gateway.'),
      region_explanation=('Should be the same as region, if not specified, '
                          'it will be automatically set.'),
      detailed_help="""\
        Reference to the peer side Highly Available VPN gateway.
        """)


def GetDescriptionFlag():
  """Returns the flag for VPN gateway description."""
  return base.Argument(
      '--description',
      help='An optional, textual description for the VPN gateway.')


def GetInterconnectAttachmentsFlag():
  """Returns the flag for interconnect attachments (VLAN attachments) associated with a VPN gateway."""
  return base.Argument(
      '--interconnect-attachments',
      type=arg_parsers.ArgList(max_length=2),
      required=False,
      metavar='INTERCONNECT_ATTACHMENTS',
      help="""\
      Names of interconnect attachments (VLAN attachments) associated with the
      VPN gateway interfaces. You must specify this field when using a VPN gateway
      for HA VPN over Cloud Interconnect. Otherwise, this field is optional.

      For example,
      `--interconnect-attachments attachment-a-zone1,attachment-a-zone2`
      associates VPN gateway with attachment from zone1 on interface 0 and with
      attachment from zone2 on interface 1.
      """)


def GetInterconnectAttachmentRef(resources, name, region, project):
  """Generates an interconnect attachment reference from the specified name, region and project."""
  return resources.Parse(
      name,
      collection='compute.interconnectAttachments',
      params={
          'project': project,
          'region': region
      })


def GetStackType(ipv6_only_vpn_enabled=False):
  """Returns the flag for VPN gateway stack type.

  Args:
    ipv6_only_vpn_enabled: Whether to include IPV6_ONLY stack type.

  Return:
    An enum presents the stack type for the VPN gateway.
  """
  choices = {
      'IPV4_ONLY': 'Only IPv4 protocol is enabled on this VPN gateway.',
      'IPV4_IPV6': (
          'Both IPv4 and IPv6 protocols are enabled on this VPN gateway.'
      ),
  }
  if ipv6_only_vpn_enabled:
    choices['IPV6_ONLY'] = 'Only IPv6 protocol is enabled on this VPN gateway.'
  return base.Argument(
      '--stack-type',
      choices=choices,
      type=arg_utils.ChoiceToEnumName,
      help="""\
      The stack type of the protocol(s) enabled on this VPN gateway.
      If not provided, `IPV4_ONLY` will be used.
      """,
  )


def GetGatewayIpVersion():
  """Returns the flag for VPN gateway IP version.

  Return:
    An enum presents the gateway IP version for the VPN gateway.
  """
  return base.Argument(
      '--gateway-ip-version',
      choices={
          'IPV4': (
              'Every HA-VPN gateway interface is configured with an IPv4'
              ' address.'
          ),
          'IPV6': (
              'Every HA-VPN gateway interface is configured with an IPv6'
              ' address.'
          ),
      },
      type=arg_utils.ChoiceToEnumName,
      help="""\
      The IP family of the gateway IPs for the HA-VPN gateway interfaces. If not
      specified, `IPV4` will be used.
      """,
  )
