# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for describing target vpn gateways."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.target_vpn_gateways import flags


class Describe(base.DescribeCommand):
  """Describe a Compute Engine Cloud VPN Classic Target VPN Gateway.

  *{command}* displays all data associated with a Compute Engine
  Cloud VPN Target VPN Gateway in a project.
  """

  TARGET_VPN_GATEWAY_ARG = None

  @staticmethod
  def Args(parser):
    """Adds arguments to the supplied parser."""
    Describe.TARGET_VPN_GATEWAY_ARG = flags.TargetVpnGatewayArgument()
    Describe.TARGET_VPN_GATEWAY_ARG.AddArgument(
        parser, operation_type='describe')

  def Run(self, args):
    """Issues the request necessary for describing a target VPN gateway."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    target_vpn_gateway_ref = self.TARGET_VPN_GATEWAY_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    request = client.messages.ComputeTargetVpnGatewaysGetRequest(
        **target_vpn_gateway_ref.AsDict())

    return client.MakeRequests([(client.apitools_client.targetVpnGateways,
                                 'Get', request)])[0]
