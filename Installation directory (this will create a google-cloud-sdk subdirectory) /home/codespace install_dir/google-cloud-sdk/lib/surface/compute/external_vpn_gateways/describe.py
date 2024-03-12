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
"""Command to describe External VPN gateways."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.external_vpn_gateways import external_vpn_gateways_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.external_vpn_gateways import flags


_EXTERNAL_VPN_GATEWAY_ARG = flags.ExternalVpnGatewayArgument()


class Describe(base.DescribeCommand):
  """Describe a Compute Engine external VPN gateway.

  *{command}* is used to display all data associated with a Compute Engine
  external VPN gateway in a project.

  An external VPN gateway provides the information to Google Cloud
  about your on-premises side or another Cloud provider's VPN gateway.
  """

  detailed_help = {
      'EXAMPLES':
          """\
          To describe an external VPN gateway, run:

              $ {command} my-external-gateway"""
  }

  @staticmethod
  def Args(parser):
    _EXTERNAL_VPN_GATEWAY_ARG.AddArgument(parser, operation_type='describe')

  def Run(self, args):
    """Issues the request to describe an External VPN gateway."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    helper = external_vpn_gateways_utils.ExternalVpnGatewayHelper(holder)
    ref = _EXTERNAL_VPN_GATEWAY_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))
    return helper.Describe(ref)
