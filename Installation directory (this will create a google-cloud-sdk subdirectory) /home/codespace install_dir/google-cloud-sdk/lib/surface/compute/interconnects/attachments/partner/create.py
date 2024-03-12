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
"""Command for creating partner customer interconnect attachments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.interconnects.attachments import client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.interconnects.attachments import flags as attachment_flags
from googlecloudsdk.command_lib.compute.routers import flags as router_flags
from googlecloudsdk.core import log


def PrintPairingKeyEpilog(pairing_key):
  """Prints the pairing key help text upon command completion."""
  message = """\
      Please use the pairing key to provision the attachment with your partner:
      {0}
      """.format(pairing_key)
  log.status.Print(message)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Compute Engine partner interconnect attachment.

  *{command}* is used to create partner interconnect attachments. A partner
  interconnect attachment binds the underlying connectivity of a provider's
  Interconnect to a path into and out of the customer's cloud network.
  """
  INTERCONNECT_ATTACHMENT_ARG = None
  INTERCONNECT_ARG = None
  ROUTER_ARG = None
  _support_partner_ipv6 = False

  @classmethod
  def Args(cls, parser):

    cls.ROUTER_ARG = router_flags.RouterArgumentForOtherResources()
    cls.ROUTER_ARG.AddArgument(parser)

    cls.INTERCONNECT_ATTACHMENT_ARG = (
        attachment_flags.InterconnectAttachmentArgument())
    cls.INTERCONNECT_ATTACHMENT_ARG.AddArgument(parser, operation_type='create')

    attachment_flags.AddAdminEnabled(parser, default_behavior=False)
    attachment_flags.AddEdgeAvailabilityDomain(parser)
    attachment_flags.AddDescription(parser)
    attachment_flags.AddMtu(parser)
    attachment_flags.AddEncryption(parser)
    attachment_flags.GetIpsecInternalAddressesFlag().AddToParser(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    attachment_ref = self.INTERCONNECT_ATTACHMENT_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    interconnect_attachment = client.InterconnectAttachment(
        attachment_ref, compute_client=holder.client)

    if args.router_region is None:
      args.router_region = attachment_ref.region

    if args.router_region != attachment_ref.region:
      raise parser_errors.ArgumentException(
          'router-region must be same as the attachment region.')

    router_ref = None
    if args.router is not None:
      router_ref = self.ROUTER_ARG.ResolveAsResource(args, holder.resources)

    ipsec_internal_addresses_urls = None
    region = attachment_ref.region
    if args.ipsec_internal_addresses is not None:
      ipsec_internal_addresses_urls = [
          attachment_flags.GetAddressRef(holder.resources, name, region,
                                         attachment_ref.project).SelfLink()
          for name in args.ipsec_internal_addresses
      ]

    admin_enabled = attachment_flags.GetAdminEnabledFlag(args)

    attachment = interconnect_attachment.Create(
        description=args.description,
        router=router_ref,
        attachment_type='PARTNER',
        edge_availability_domain=args.edge_availability_domain,
        admin_enabled=admin_enabled,
        validate_only=getattr(args, 'dry_run', None),
        mtu=getattr(args, 'mtu', None),
        encryption=getattr(args, 'encryption', None),
        ipsec_internal_addresses=ipsec_internal_addresses_urls,
        stack_type=getattr(args, 'stack_type', None),
    )
    self._pairing_key = attachment.pairingKey
    return attachment

  def Epilog(self, resources_were_displayed=True):
    PrintPairingKeyEpilog(self._pairing_key)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a Compute Engine partner interconnect attachment.

  *{command}* is used to create partner interconnect attachments. A partner
  interconnect attachment binds the underlying connectivity of a provider's
  Interconnect to a path into and out of the customer's cloud network.
  """

  _support_partner_ipv6 = True

  @classmethod
  def Args(cls, parser):
    super(CreateBeta, cls).Args(parser)
    attachment_flags.AddStackType(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create a Compute Engine partner interconnect attachment.

  *{command}* is used to create partner interconnect attachments. A partner
  interconnect attachment binds the underlying connectivity of a provider's
  Interconnect to a path into and out of the customer's cloud network.
  """
  _support_partner_ipv6 = True

  @classmethod
  def Args(cls, parser):
    super(CreateAlpha, cls).Args(parser)
    attachment_flags.AddDryRun(parser)
