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
"""Command for listing interconnect attachments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import filter_rewrite
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projection_spec


class List(base.ListCommand):
  """List InterconnectAttachments."""

  INTERCONNECT_ATTACHMENT_ARG = None

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat("""
        table(
          name,
          region.basename(),
          type.basename(),
          interconnect.basename(),
          router.basename()
        )
    """)

  def _GetListPage(self, compute_interconnect_attachments, request):
    response = compute_interconnect_attachments.AggregatedList(request)
    interconnect_attachments_lists = []
    for attachment_in_scope in response.items.additionalProperties:
      interconnect_attachments_lists += (
          attachment_in_scope.value.interconnectAttachments)
    return interconnect_attachments_lists, response.nextPageToken

  def Run(self, args):
    client = base_classes.ComputeApiHolder(
        self.ReleaseTrack()).client.apitools_client

    compute_interconnect_attachments = client.interconnectAttachments

    messages = client.MESSAGES_MODULE
    project = properties.VALUES.core.project.GetOrFail()
    display_info = args.GetDisplayInfo()
    defaults = resource_projection_spec.ProjectionSpec(
        symbols=display_info.transforms, aliases=display_info.aliases)
    args.filter, filter_expr = filter_rewrite.Rewriter().Rewrite(
        args.filter, defaults=defaults)

    request = messages.ComputeInterconnectAttachmentsAggregatedListRequest(
        project=project, filter=filter_expr)

    # TODO(b/34871930): Write and use helper for handling listing.
    interconnect_attachments_lists, next_page_token = self._GetListPage(
        compute_interconnect_attachments, request)
    while next_page_token:
      request.pageToken = next_page_token
      interconnect_attachments_list_page, next_page_token = self._GetListPage(
          compute_interconnect_attachments, request)
      interconnect_attachments_lists += interconnect_attachments_list_page

    return interconnect_attachments_lists


List.detailed_help = base_classes.GetRegionalListerHelp(
    'interconnect attachments')
