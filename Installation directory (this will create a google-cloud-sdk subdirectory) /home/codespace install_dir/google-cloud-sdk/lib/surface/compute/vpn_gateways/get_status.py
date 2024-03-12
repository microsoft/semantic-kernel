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

"""Command for getting the status of Compute Engine VPN Gateways."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.vpn_gateways import flags


class Describe(base.DescribeCommand):
  """Get status of a Compute Engine Highly Available VPN Gateway.

  *{command}* is used to display high availability configuration status for the
  Cloud VPN gateway, the command will show you the high availability
  configuration status for VPN tunnels associated with each peer gateway
  to which the Cloud VPN gateway is connected; the peer gateway could be either
  a Cloud VPN gateway or an external VPN gateway.
  """

  detailed_help = {
      'EXAMPLES':
          """\
          To get status of a VPN gateway, run:

              $ {command} my-gateway --region=us-central1"""
  }

  VPN_GATEWAY_ARG = None

  @staticmethod
  def Args(parser):
    Describe.VPN_GATEWAY_ARG = flags.GetVpnGatewayArgument()
    Describe.VPN_GATEWAY_ARG.AddArgument(parser, operation_type='describe')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    gateway_ref = Describe.VPN_GATEWAY_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    request = client.messages.ComputeVpnGatewaysGetStatusRequest(
        **gateway_ref.AsDict())

    return client.MakeRequests([(client.apitools_client.vpnGateways,
                                 'GetStatus', request)])[0]
