# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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

"""Command for listing named sets from a Compute Engine router."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routers import flags


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListNamedSets(base.ListCommand):
  """List named sets from a Compute Engine router.

  *{command}* lists all named sets from a Compute Engine router.
  """

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    ListNamedSets.ROUTER_ARG = flags.RouterArgument()
    ListNamedSets.ROUTER_ARG.AddArgument(parser, operation_type='list')
    parser.display_info.AddCacheUpdater(flags.RoutersCompleter)
    parser.display_info.AddFormat('table(name, type)')

  def Run(self, args):
    """Issues a request necessary for listing named sets from a Router."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    router_ref = ListNamedSets.ROUTER_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )

    request = client.messages.ComputeRoutersListNamedSetsRequest(
        **router_ref.AsDict()
    )
    return list_pager.YieldFromList(
        client.apitools_client.routers,
        request,
        limit=args.limit,
        batch_size=args.page_size,
        method='ListNamedSets',
        field='result',
        current_token_attribute='pageToken',
        next_token_attribute='nextPageToken',
        batch_size_attribute='maxResults',
    )
