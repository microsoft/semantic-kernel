# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command for updating network attachments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.network_attachments import flags
from googlecloudsdk.command_lib.compute.networks.subnets import flags as subnetwork_flags


def _DetailedHelp():
  return {
      'brief': 'Update a Google Compute Engine network attachment.',
      'DESCRIPTION': """\
      *{command}* is used to update network attachments. You can update the
      following fields: description, subnets, producer-accept-list and
      producer-reject-list. If you update the producer-accept-list or
      producer-reject-list, the full new list should be specified.
      """,
      'EXAMPLES': """\
      To update all the parameters with the new list, run:

        $ {command} NETWORK_ATTACHMENT_NAME --region=us-central1 --subnets=MY_SUBNET2 --description='default network attachment' --producer-accept-list=PROJECT5,PROJECT6 --producer-reject-list=PROJECT7,PROJECT8

      To update a network attachment to change only the subnet to MY_SUBNET3, run:

        $ {command} NETWORK_ATTACHMENT_NAME --region=us-central1 --subnets=MY_SUBNET3

      """,
  }


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Update(base.UpdateCommand):
  """Update a Google Compute Engine network attachment."""

  NETWORK_ATTACHMENT_ARG = None
  detailed_help = _DetailedHelp()

  @classmethod
  def Args(cls, parser):
    cls.NETWORK_ATTACHMENT_ARG = flags.NetworkAttachmentArgument()
    cls.NETWORK_ATTACHMENT_ARG.AddArgument(parser, operation_type='update')
    cls.SUBNETWORK_ARG = (
        subnetwork_flags.SubnetworkArgumentForNetworkAttachment(required=False)
    )
    cls.SUBNETWORK_ARG.AddArgument(parser)

    flags.AddDescription(parser)
    flags.AddProducerRejectList(parser)
    flags.AddProducerAcceptList(parser)

  def _GetOldResource(self, client, network_attachment_ref):
    """Returns the existing NetworkAttachment resource."""
    request = client.messages.ComputeNetworkAttachmentsGetRequest(
        **network_attachment_ref.AsDict()
    )
    collection = client.apitools_client.networkAttachments
    return client.MakeRequests([(collection, 'Get', request)])[0]

  def _GetSubnetworks(self, holder, args):
    """Returns subnetwork urls from the argument."""
    subnetwork_refs = self.SUBNETWORK_ARG.ResolveAsResource(
        args,
        holder.resources,
        default_scope=compute_scope.ScopeEnum.REGION,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client),
    )
    subnetworks = [
        subnetwork_ref.SelfLink() for subnetwork_ref in subnetwork_refs
    ]
    return subnetworks

  def _GetPatchRequest(self, client, network_attachment_ref, replacement):
    """Returns a request to update the network attachment."""
    return (
        client.apitools_client.networkAttachments,
        'Patch',
        client.messages.ComputeNetworkAttachmentsPatchRequest(
            project=network_attachment_ref.project,
            region=network_attachment_ref.region,
            networkAttachment=network_attachment_ref.Name(),
            networkAttachmentResource=replacement,
        ),
    )

  def _Modify(self, holder, args, old_resource, cleared_fields):
    """Returns the updated network attachment."""
    replacement = encoding.CopyProtoMessage(old_resource)
    is_updated = False

    if args.IsSpecified('subnets'):
      new_subnetworks = sorted(self._GetSubnetworks(holder, args))
      if old_resource.subnetworks is None or new_subnetworks != sorted(
          old_resource.subnetworks
      ):
        replacement.subnetworks = new_subnetworks
        is_updated = True

    if args.IsSpecified('description'):
      if args.description != old_resource.description:
        replacement.description = args.description
        is_updated = True

    if args.IsSpecified('producer_reject_list'):
      new_reject_list = sorted(args.producer_reject_list)
      if old_resource.producerRejectLists is None or new_reject_list != sorted(
          old_resource.producerRejectLists
      ):
        replacement.producerRejectLists = new_reject_list
        is_updated = True
        if not new_reject_list:
          # The user can clear up the reject list
          cleared_fields.append('producerRejectLists')

    if args.IsSpecified('producer_accept_list'):
      new_accept_list = sorted(args.producer_accept_list)
      if old_resource.producerAcceptLists is None or new_accept_list != sorted(
          old_resource.producerAcceptLists
      ):
        replacement.producerAcceptLists = new_accept_list
        is_updated = True
        if not new_accept_list:
          # The user can clear up the accept list
          cleared_fields.append('producerAcceptLists')

    if is_updated:
      return replacement
    return None

  def Run(self, args):
    """Issue a network attachment PATCH request."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    network_attachment_ref = self.NETWORK_ATTACHMENT_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.REGION
    )
    old_resource = self._GetOldResource(client, network_attachment_ref)
    cleared_fields = []
    replacement = self._Modify(holder, args, old_resource, cleared_fields)
    if replacement is None:
      return old_resource

    with client.apitools_client.IncludeFields(cleared_fields):
      return client.MakeRequests(
          [self._GetPatchRequest(client, network_attachment_ref, replacement)]
      )
