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
"""Command to create a new VPN gateway."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.vpn_gateways import vpn_gateways_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.networks import flags as network_flags
from googlecloudsdk.command_lib.compute.vpn_gateways import flags

_VPN_GATEWAY_ARG = flags.GetVpnGatewayArgument()
_NETWORK_ARG = network_flags.NetworkArgumentForOtherResource("""\
  A reference to a network to which the VPN gateway is attached.
  """)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a new Compute Engine Highly Available VPN gateway.

  *{command}* creates a new Highly Available VPN gateway.

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
          To create a VPN gateway, run:

              $ {command} my-vpn-gateway --region=us-central1 --network=default
          """
  }

  _ipv6_only_vpn_enabled = False

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command."""
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    _NETWORK_ARG.AddArgument(parser)
    _VPN_GATEWAY_ARG.AddArgument(parser, operation_type='create')
    flags.GetDescriptionFlag().AddToParser(parser)
    flags.GetInterconnectAttachmentsFlag().AddToParser(parser)
    flags.GetStackType(cls._ipv6_only_vpn_enabled).AddToParser(parser)
    parser.display_info.AddCacheUpdater(flags.VpnGatewaysCompleter)

  def _Run(self, args, support_outer_vpn_ipv6=None):
    """Issues the request to create a new VPN gateway."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    helper = vpn_gateways_utils.VpnGatewayHelper(holder)
    vpn_gateway_ref = _VPN_GATEWAY_ARG.ResolveAsResource(args, holder.resources)
    network_ref = _NETWORK_ARG.ResolveAsResource(args, holder.resources)
    vpn_interfaces_with_interconnect_attachments = None
    if args.interconnect_attachments is not None:
      vpn_interfaces_with_interconnect_attachments = (
          self._mapInterconnectAttachments(
              args,
              holder.resources,
              vpn_gateway_ref.region,
              vpn_gateway_ref.project,
          )
      )
    if support_outer_vpn_ipv6:
      vpn_gateway_to_insert = helper.GetVpnGatewayForInsert(
          name=vpn_gateway_ref.Name(),
          description=args.description,
          network=network_ref.SelfLink(),
          vpn_interfaces_with_interconnect_attachments=vpn_interfaces_with_interconnect_attachments,
          stack_type=args.stack_type,
          gateway_ip_version=args.gateway_ip_version,
      )
    else:
      vpn_gateway_to_insert = helper.GetVpnGatewayForInsert(
          name=vpn_gateway_ref.Name(),
          description=args.description,
          network=network_ref.SelfLink(),
          vpn_interfaces_with_interconnect_attachments=vpn_interfaces_with_interconnect_attachments,
          stack_type=args.stack_type,
      )
    operation_ref = helper.Create(vpn_gateway_ref, vpn_gateway_to_insert)
    return helper.WaitForOperation(vpn_gateway_ref, operation_ref,
                                   'Creating VPN Gateway')

  def _mapInterconnectAttachments(self, args, resources, region, project):
    """Returns dict {interfaceId : interconnectAttachmentUrl} based on initial order of names in input interconnectAttachmentName and region and project of VPN Gateway.

    Args:
      args: Namespace, argparse.Namespace.
      resources: Generates resource references.
      region: VPN Gateway region.
      project: VPN Gateway project.
    """
    attachment_refs = args.interconnect_attachments
    result = {
        0:
            flags.GetInterconnectAttachmentRef(resources, attachment_refs[0],
                                               region, project).SelfLink(),
        1:
            flags.GetInterconnectAttachmentRef(resources, attachment_refs[1],
                                               region, project).SelfLink()
    }
    return result

  def Run(self, args):
    """See base.CreateCommand."""
    return self._Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a new Compute Engine Highly Available VPN gateway.

  *{command}* creates a new Highly Available VPN gateway.

  Highly Available VPN Gateway provides a means to create a VPN solution with a
  higher availability SLA compared to Classic Target VPN Gateway.
  Highly Available VPN gateways are simply referred to as VPN gateways in the
  API documentation and gcloud commands.
  A VPN Gateway can reference one or more VPN tunnels that connect it to
  external VPN gateways or Cloud VPN Gateways.
  """

  ROUTER_ARG = None
  INSTANCE_ARG = None

  _support_outer_vpn_ipv6 = True
  _ipv6_only_vpn_enabled = True

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command."""
    super(CreateBeta, cls).Args(parser)
    flags.GetGatewayIpVersion().AddToParser(parser)

  def Run(self, args):
    """See base.CreateCommand."""
    return self._Run(args, support_outer_vpn_ipv6=True)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create a new Compute Engine Highly Available VPN gateway.

  *{command}* creates a new Highly Available VPN gateway.

  Highly Available VPN Gateway provides a means to create a VPN solution with a
  higher availability SLA compared to Classic Target VPN Gateway.
  Highly Available VPN gateways are simply referred to as VPN gateways in the
  API documentation and gcloud commands.
  A VPN Gateway can reference one or more VPN tunnels that connect it to
  external VPN gateways or Cloud VPN Gateways.
  """

  ROUTER_ARG = None
  INSTANCE_ARG = None

  _support_outer_vpn_ipv6 = True
  _ipv6_only_vpn_enabled = True

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command."""
    super(CreateAlpha, cls).Args(parser)
    flags.GetGatewayIpVersion().AddToParser(parser)

  def Run(self, args):
    """See base.CreateCommand."""
    return self._Run(args, support_outer_vpn_ipv6=True)
