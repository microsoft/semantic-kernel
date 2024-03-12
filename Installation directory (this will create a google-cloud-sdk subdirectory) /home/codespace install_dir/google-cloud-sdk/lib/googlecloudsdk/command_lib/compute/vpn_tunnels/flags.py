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
"""Flags and helpers for the compute vpn-tunnels commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      region.basename(),
      vpn_tunnel_gateway().basename():label=GATEWAY,
      peerIp:label=PEER_ADDRESS
    )"""

HA_VPN_LIST_FORMAT = """\
    table(
      name,
      region.basename(),
      vpn_tunnel_gateway().basename():label=GATEWAY,
      vpn_gateway_interface:label=VPN_INTERFACE,
      peerIp:label=PEER_ADDRESS
    )"""


class VpnTunnelsCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(VpnTunnelsCompleter, self).__init__(
        collection='compute.vpnTunnels',
        list_command='compute vpn-tunnels list --uri',
        **kwargs)


def VpnTunnelArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='VPN Tunnel',
      completer=VpnTunnelsCompleter,
      plural=plural,
      required=required,
      regional_collection='compute.vpnTunnels',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def VpnTunnelArgumentForRoute(required=True):
  return compute_flags.ResourceArgument(
      resource_name='vpn tunnel',
      name='--next-hop-vpn-tunnel',
      completer=VpnTunnelsCompleter,
      plural=False,
      required=required,
      regional_collection='compute.vpnTunnels',
      short_help='The target VPN tunnel that will receive forwarded traffic.',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def VpnTunnelArgumentForRouter(required=True, operation_type='added'):
  return compute_flags.ResourceArgument(
      resource_name='vpn tunnel',
      name='--vpn-tunnel',
      completer=VpnTunnelsCompleter,
      plural=False,
      required=required,
      regional_collection='compute.vpnTunnels',
      short_help='The tunnel of the interface being {0}.'.format(
          operation_type),
      region_explanation=(
          'If not specified it will be set to the region of the router.'))
