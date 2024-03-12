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
"""Command to describe VPN Gateways."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.vpn_gateways import vpn_gateways_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.vpn_gateways import flags

_VPN_GATEWAY_ARG = flags.GetVpnGatewayArgument()


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe a Compute Engine Highly Available VPN Gateway.

  *{command}* is used to display all data associated with a Compute Engine
  Highly Available VPN Gateway in a project.

  Highly Available VPN Gateway provides a means to create a VPN solution with a
  higher availability SLA compared to Classic Target VPN Gateway.
  Highly Available VPN gateways are simply referred to as VPN gateways in the
  API documentation and gcloud commands.
  A VPN Gateway can reference one or more VPN tunnels that connect it to
  external VPN gateways or Cloud VPN Gateways.
  """

  detailed_help = {
      'EXAMPLES':
          """\
          To describe a VPN gateway, run:

              $ {command} my-gateway --region=us-central1"""
  }

  @staticmethod
  def Args(parser):
    _VPN_GATEWAY_ARG.AddArgument(parser, operation_type='describe')

  def Run(self, args):
    """Issues the request to describe a VPN Gateway."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    helper = vpn_gateways_utils.VpnGatewayHelper(holder)
    ref = _VPN_GATEWAY_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))
    return helper.Describe(ref)
