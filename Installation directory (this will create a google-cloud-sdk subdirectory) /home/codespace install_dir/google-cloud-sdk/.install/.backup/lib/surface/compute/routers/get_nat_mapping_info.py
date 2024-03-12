# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Command for listing Compute Engine routers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routers import flags as routers_flags


class GetNatMappingInfo(base.ListCommand):
  """Display NAT Mapping information in a router."""

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ROUTER_ARG = routers_flags.RouterArgument()
    cls.ROUTER_ARG.AddArgument(parser, operation_type='get NAT mapping info')
    routers_flags.AddGetNatMappingInfoArgs(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    router_ref = self.ROUTER_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    params = router_ref.AsDict()
    if args.nat_name:
      params['natName'] = args.nat_name

    request = client.messages.ComputeRoutersGetNatMappingInfoRequest(**params)

    return list_pager.YieldFromList(
        client.apitools_client.routers,
        request,
        limit=args.limit,
        batch_size=args.page_size,
        method='GetNatMappingInfo',
        field='result',
        current_token_attribute='pageToken',
        next_token_attribute='nextPageToken',
        batch_size_attribute='maxResults',
    )


GetNatMappingInfo.detailed_help = {
    'DESCRIPTION':
        """
        $ {command}

        shows a mapping of IP:port-ranges
        allocated to each VM's interface that is configured to use NAT via the
        specified router.""",
    'EXAMPLES':
        """\
        To show NAT mappings from all NATs in router 'r1' in region
        'us-central1', run:

            $ {command} r1 --region=us-central1
        """
}
