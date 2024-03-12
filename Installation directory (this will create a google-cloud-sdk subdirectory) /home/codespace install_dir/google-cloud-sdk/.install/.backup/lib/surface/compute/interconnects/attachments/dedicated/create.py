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
"""Command for creating dedicated interconnect attachments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.interconnects.attachments import client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.interconnects import flags as interconnect_flags
from googlecloudsdk.command_lib.compute.interconnects.attachments import flags as attachment_flags
from googlecloudsdk.command_lib.compute.routers import flags as router_flags
from googlecloudsdk.core import log

_DOCUMENTATION_LINK = 'https://cloud.google.com/interconnect/docs/how-to/dedicated/creating-vlan-attachments'


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Create(base.CreateCommand):
  """Create a Compute Engine dedicated interconnect attachment.

  *{command}* is used to create a dedicated interconnect attachments. An
  interconnect attachment is what binds the underlying connectivity of an
  interconnect to a path into and out of the customer's cloud network.
  """
  INTERCONNECT_ATTACHMENT_ARG = None
  INTERCONNECT_ARG = None
  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.INTERCONNECT_ARG = (
        interconnect_flags.InterconnectArgumentForOtherResource(
            'The interconnect for the interconnect attachment'))
    cls.INTERCONNECT_ARG.AddArgument(parser)

    cls.ROUTER_ARG = router_flags.RouterArgumentForOtherResources()
    cls.ROUTER_ARG.AddArgument(parser)

    cls.INTERCONNECT_ATTACHMENT_ARG = (
        attachment_flags.InterconnectAttachmentArgument())
    cls.INTERCONNECT_ATTACHMENT_ARG.AddArgument(parser, operation_type='create')
    attachment_flags.AddDescription(parser)
    attachment_flags.AddAdminEnabled(parser, default_behavior=True)
    attachment_flags.AddVlan(parser)
    attachment_flags.AddCandidateSubnets(parser)
    attachment_flags.AddBandwidth(parser, required=False)
    attachment_flags.AddMtu(parser)
    attachment_flags.AddEncryption(parser)
    attachment_flags.GetIpsecInternalAddressesFlag().AddToParser(parser)
    attachment_flags.AddStackType(parser)
    attachment_flags.AddCandidateIpv6Subnets(parser)
    attachment_flags.AddCloudRouterIpv6InterfaceId(parser)
    attachment_flags.AddCustomerRouterIpv6InterfaceId(parser)
    attachment_flags.AddSubnetLength(parser)

  def _Run(self, args):
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

    if args.router_region is None:
      args.router_region = attachment_ref.region

    if args.router_region != attachment_ref.region:
      raise parser_errors.ArgumentException(
          'router-region must be same as the attachment region.')

    router_ref = None
    if args.router is not None:
      router_ref = self.ROUTER_ARG.ResolveAsResource(args, holder.resources)

    admin_enabled = attachment_flags.GetAdminEnabledFlag(args)

    ipsec_internal_addresses_urls = None
    region = attachment_ref.region
    if args.ipsec_internal_addresses is not None:
      ipsec_internal_addresses_urls = [
          attachment_flags.GetAddressRef(
              holder.resources, name, region, attachment_ref.project
          ).SelfLink()
          for name in args.ipsec_internal_addresses
      ]

    return interconnect_attachment.Create(
        description=args.description,
        interconnect=interconnect_ref,
        attachment_type='DEDICATED',
        router=router_ref,
        vlan_tag_802_1q=args.vlan,
        admin_enabled=admin_enabled,
        candidate_subnets=args.candidate_subnets,
        bandwidth=getattr(args, 'bandwidth', None),
        validate_only=getattr(args, 'dry_run', None),
        mtu=getattr(args, 'mtu', None),
        encryption=getattr(args, 'encryption', None),
        ipsec_internal_addresses=ipsec_internal_addresses_urls,
        stack_type=getattr(args, 'stack_type', None),
        candidate_ipv6_subnets=args.candidate_ipv6_subnets,
        cloud_router_ipv6_interface_id=getattr(
            args, 'cloud_router_ipv6_interface_id', None
        ),
        customer_router_ipv6_interface_id=getattr(
            args, 'customer_router_ipv6_interface_id', None
        ),
        subnet_length=getattr(args, 'subnet_length', None),
        multicast_enabled=getattr(args, 'enable_multicast', None),
    )

  def Epilog(self, resources_were_displayed):
    message = ('You must configure your Cloud Router with an interface '
               'and BGP peer for your created VLAN attachment. See also {} for '
               'more detailed help.'.format(_DOCUMENTATION_LINK))
    log.status.Print(message)

  def Run(self, args):
    """See base.CreateCommand."""
    return self._Run(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create a Compute Engine dedicated interconnect attachment.

  *{command}* is used to create a dedicated interconnect attachments. An
  interconnect attachment is what binds the underlying connectivity of an
  interconnect to a path into and out of the customer's cloud network.
  """

  @classmethod
  def Args(cls, parser):
    super(CreateAlpha, cls).Args(parser)
    attachment_flags.AddEnableMulticast(parser)
    attachment_flags.AddDryRun(parser)

  def Run(self, args):
    """See base.CreateCommand."""
    return self._Run(args)
