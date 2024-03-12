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
"""Command for describing vpn tunnels."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.vpn_tunnels import vpn_tunnels_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.vpn_tunnels import flags


_VPN_TUNNEL_ARG = flags.VpnTunnelArgument()


class Describe(base.DescribeCommand):
  """Describe a Compute Engine VPN tunnel.

    *{command}* displays all data associated with a Compute Engine
  VPN tunnel in a project.
  """

  @staticmethod
  def Args(parser):
    """Adds arguments to the supplied parser."""
    _VPN_TUNNEL_ARG.AddArgument(parser, operation_type='describe')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    helper = vpn_tunnels_utils.VpnTunnelHelper(holder)

    vpn_tunnel_ref = _VPN_TUNNEL_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))
    return helper.Describe(vpn_tunnel_ref)
