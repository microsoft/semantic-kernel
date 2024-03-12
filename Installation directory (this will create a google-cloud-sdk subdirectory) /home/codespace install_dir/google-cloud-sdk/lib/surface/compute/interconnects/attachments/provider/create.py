# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command for creating partner provider interconnect attachments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.interconnects.attachments import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.interconnects import flags as interconnect_flags
from googlecloudsdk.command_lib.compute.interconnects.attachments import flags as attachment_flags


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Create(base.CreateCommand):
  """Create a Compute Engine partner provider interconnect attachment.

  *{command}* is used to create partner provider interconnect attachments. An
  interconnect attachment binds the underlying connectivity of an Interconnect
  to a path into and out of the customer's cloud network. Partner provider
  attachments can only be created by approved network partners.
  """
  INTERCONNECT_ATTACHMENT_ARG = None
  INTERCONNECT_ARG = None
  ROUTER_ARG = None
  _support_partner_ipv6_byoip = False

  @classmethod
  def Args(cls, parser):

    cls.INTERCONNECT_ARG = (
        interconnect_flags.InterconnectArgumentForOtherResource(
            'The interconnect for the interconnect attachment'))
    cls.INTERCONNECT_ARG.AddArgument(parser)

    cls.INTERCONNECT_ATTACHMENT_ARG = (
        attachment_flags.InterconnectAttachmentArgument())
    cls.INTERCONNECT_ATTACHMENT_ARG.AddArgument(parser, operation_type='create')

    attachment_flags.AddBandwidth(parser, required=True)
    attachment_flags.AddVlan(parser)
    attachment_flags.AddPartnerAsn(parser)
    attachment_flags.AddPartnerMetadata(parser, required=True)
    attachment_flags.AddPairingKey(parser)
    attachment_flags.AddDescription(parser)
    attachment_flags.AddCandidateSubnets(parser)
    attachment_flags.AddSubnetLength(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    attachment_ref = self.INTERCONNECT_ATTACHMENT_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    interconnect_attachment = client.InterconnectAttachment(
        attachment_ref, compute_client=holder.client)

    interconnect_ref = None
    if args.interconnect is not None:
      interconnect_ref = self.INTERCONNECT_ARG.ResolveAsResource(
          args, holder.resources)

    candidate_ipv6_subnets = None
    cloud_router_ipv6_interface_id = None
    customer_router_ipv6_interface_id = None
    if self._support_partner_ipv6_byoip:
      candidate_ipv6_subnets = args.candidate_ipv6_subnets
      cloud_router_ipv6_interface_id = getattr(
          args, 'cloud_router_ipv6_interface_id', None
      )
      customer_router_ipv6_interface_id = getattr(
          args, 'customer_router_ipv6_interface_id', None
      )

    return interconnect_attachment.Create(
        description=args.description,
        interconnect=interconnect_ref,
        vlan_tag_802_1q=args.vlan,
        attachment_type='PARTNER_PROVIDER',
        bandwidth=args.bandwidth,
        pairing_key=args.pairing_key,
        candidate_subnets=args.candidate_subnets,
        partner_asn=args.partner_asn,
        partner_name=args.partner_name,
        partner_interconnect=args.partner_interconnect_name,
        partner_portal_url=args.partner_portal_url,
        subnet_length=getattr(args, 'subnet_length', None),
        validate_only=getattr(args, 'dry_run', None),
        candidate_ipv6_subnets=candidate_ipv6_subnets,
        cloud_router_ipv6_interface_id=cloud_router_ipv6_interface_id,
        customer_router_ipv6_interface_id=customer_router_ipv6_interface_id,
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create a Compute Engine partner provider interconnect attachment.

  *{command}* is used to create partner provider interconnect attachments. An
  interconnect attachment binds the underlying connectivity of an Interconnect
  to a path into and out of the customer's cloud network. Partner provider
  attachments can only be created by approved network partners.
  """
  _support_partner_ipv6_byoip = True

  @classmethod
  def Args(cls, parser):
    super(CreateAlpha, cls).Args(parser)
    attachment_flags.AddDryRun(parser)
    attachment_flags.AddCandidateIpv6Subnets(parser)
    attachment_flags.AddCloudRouterIpv6InterfaceId(parser)
    attachment_flags.AddCustomerRouterIpv6InterfaceId(parser)
