# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command for creating network attachments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.network_attachments import flags
from googlecloudsdk.command_lib.compute.networks.subnets import flags as subnetwork_flags


def GetConnectionPreference(args, messages):
  """Get connection preference of the network attachment."""
  if args.connection_preference == 'ACCEPT_AUTOMATIC':
    return messages.NetworkAttachment.ConnectionPreferenceValueValuesEnum.ACCEPT_AUTOMATIC
  if args.connection_preference == 'ACCEPT_MANUAL':
    return messages.NetworkAttachment.ConnectionPreferenceValueValuesEnum.ACCEPT_MANUAL

  return None


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Create(base.CreateCommand):
  """Create a Google Compute Engine network attachment."""

  detailed_help = {
      'brief': 'Create a Google Compute Engine network attachment.',
      'DESCRIPTION': """\
      *{command}* is used to create network attachments. A service consumer
      creates network attachments and makes it available to producers.
      Service producers then use a multi-NIC VM to form a bi-directional,
      non-NAT'd communication channel.
      """,
      'EXAMPLES': """\

        $ {command} NETWORK_ATTACHMENT_NAME --region=us-central1 --subnets=MY_SUBNET --connection-preference=ACCEPT_MANUAL --producer-accept-list=PROJECT1,PROJECT2 --producer-reject-list=PROJECT3,PROJECT4

      To create a network attachment with a textual description, run:

        $ {command} NETWORK_ATTACHMENT_NAME --region=us-central1 --subnets=MY_SUBNET --connection-preference=ACCEPT_MANUAL --producer-accept-list=PROJECT1,PROJECT2 --producer-reject-list=PROJECT3,PROJECT4 --description='default network attachment'

      """,
  }

  NETWORK_ATTACHMENT_ARG = None
  SUBNETWORK_ARG = None

  @classmethod
  def Args(cls, parser):
    """Create a Google Compute Engine network attachment.

    Args:
      parser: the parser that parses the input from the user.
    """
    cls.NETWORK_ATTACHMENT_ARG = flags.NetworkAttachmentArgument()
    cls.NETWORK_ATTACHMENT_ARG.AddArgument(parser, operation_type='create')
    cls.SUBNETWORK_ARG = subnetwork_flags.SubnetworkArgumentForNetworkAttachment(
    )
    cls.SUBNETWORK_ARG.AddArgument(parser)

    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    parser.display_info.AddCacheUpdater(flags.NetworkAttachmentsCompleter)

    flags.AddDescription(parser)
    flags.AddConnectionPreference(parser)
    flags.AddProducerRejectList(parser)
    flags.AddProducerAcceptList(parser)

  def Run(self, args):
    """Issue a network attachment INSERT request."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    network_attachment_ref = self.NETWORK_ATTACHMENT_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.REGION)
    subnetwork_refs = self.SUBNETWORK_ARG.ResolveAsResource(
        args,
        holder.resources,
        default_scope=compute_scope.ScopeEnum.REGION,
        scope_lister=compute_flags.GetDefaultScopeLister(client))
    subnetworks = [
        subnetwork_ref.SelfLink() for subnetwork_ref in subnetwork_refs
    ]

    network_attachment = client.messages.NetworkAttachment(
        description=args.description,
        name=network_attachment_ref.Name(),
        connectionPreference=GetConnectionPreference(args, client.messages),
        subnetworks=subnetworks)

    if args.IsSpecified('producer_reject_list'):
      network_attachment.producerRejectLists = args.producer_reject_list
    if args.IsSpecified('producer_accept_list'):
      network_attachment.producerAcceptLists = args.producer_accept_list

    request = client.messages.ComputeNetworkAttachmentsInsertRequest(
        project=network_attachment_ref.project,
        region=network_attachment_ref.region,
        networkAttachment=network_attachment)
    collection = client.apitools_client.networkAttachments
    return client.MakeRequests([(collection, 'Insert', request)])
