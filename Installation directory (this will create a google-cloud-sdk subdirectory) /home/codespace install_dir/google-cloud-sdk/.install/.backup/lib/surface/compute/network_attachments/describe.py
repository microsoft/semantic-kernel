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
"""Command for describing a network attachment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.network_attachments import flags


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Describe(base.DescribeCommand):
  """Describes a Google Compute Engine network attachment."""

  detailed_help = {
      'EXAMPLES': """\
          To describe a network attachment, run:

              $ {command} NETWORK_ATTACHMENT_NAME --region=us-central1"""
  }

  ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ARG = flags.NetworkAttachmentArgument()
    cls.ARG.AddArgument(parser, operation_type='describe')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    network_attachment_ref = self.ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.REGION)
    request = client.messages.ComputeNetworkAttachmentsGetRequest(
        **network_attachment_ref.AsDict())

    return client.MakeRequests([(client.apitools_client.networkAttachments,
                                 'Get', request)])[0]
