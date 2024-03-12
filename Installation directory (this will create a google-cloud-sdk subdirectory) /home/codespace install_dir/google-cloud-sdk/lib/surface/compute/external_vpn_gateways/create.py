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
"""Command to create a new external VPN gateway."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.external_vpn_gateways import external_vpn_gateways_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.external_vpn_gateways import flags


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a new Compute Engine external VPN gateway.

  *{command}* creates a new external VPN gateway.

  External VPN gateway is the on-premises VPN gateway or another cloud
  provider's VPN gateway that connects to your Google Cloud VPN gateway.
  To create a highly available VPN from Google Cloud to your on-premises side
  or another Cloud provider's VPN gateway, you must create an external VPN
  gateway resource in Google Cloud, which provides the information to
  Google Cloud about your external VPN gateway.
  """

  detailed_help = {'EXAMPLES': """\
          To create an external VPN gateway, run:

              $ {command} my-external-gateway --interfaces=0=8.9.9.9"""}

  _is_ipv6_supported = False

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command."""
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    cls.EXTERNAL_VPN_GATEWAY_ARG = flags.ExternalVpnGatewayArgument()
    cls.EXTERNAL_VPN_GATEWAY_ARG.AddArgument(parser, operation_type='create')
    flags.AddCreateExternalVpnGatewayArgs(
        parser, is_ipv6_supported=cls._is_ipv6_supported
    )
    parser.display_info.AddCacheUpdater(flags.ExternalVpnGatewaysCompleter)

  def Run(self, args):
    """Issues the request to create a new external VPN gateway."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    helper = external_vpn_gateways_utils.ExternalVpnGatewayHelper(holder)
    ref = self.EXTERNAL_VPN_GATEWAY_ARG.ResolveAsResource(
        args, holder.resources
    )
    messages = holder.client.messages

    interfaces = flags.ParseInterfaces(
        args.interfaces, messages, is_ipv6_supported=self._is_ipv6_supported
    )
    redundancy_type = flags.InferAndGetRedundancyType(args.interfaces, messages)

    external_vpn_gateway_to_insert = helper.GetExternalVpnGatewayForInsert(
        name=ref.Name(),
        description=args.description,
        interfaces=interfaces,
        redundancy_type=redundancy_type,
    )
    operation_ref = helper.Create(ref, external_vpn_gateway_to_insert)
    ret = helper.WaitForOperation(
        ref, operation_ref, 'Creating external VPN gateway'
    )
    return ret


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a new Compute Engine external VPN gateway.

  *{command}* creates a new external VPN gateway.

  External VPN gateway is the on-premises VPN gateway or another cloud
  provider's VPN gateway that connects to your Google Cloud VPN gateway.
  To create a highly available VPN from Google Cloud to your on-premises side
  or another Cloud provider's VPN gateway, you must create an external VPN
  gateway resource in Google Cloud, which provides the information to
  Google Cloud about your external VPN gateway.
  """

  _is_ipv6_supported = True


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create a new Compute Engine external VPN gateway.

  *{command}* creates a new external VPN gateway.

  External VPN gateway is the on-premises VPN gateway or another cloud
  provider's VPN gateway that connects to your Google Cloud VPN gateway.
  To create a highly available VPN from Google Cloud to your on-premises side
  or another Cloud provider's VPN gateway, you must create an external VPN
  gateway resource in Google Cloud, which provides the information to
  Google Cloud about your external VPN gateway.
  """

  _is_ipv6_supported = True
