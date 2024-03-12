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
"""list network endpoints command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import filter_rewrite
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.network_endpoint_groups import flags
from googlecloudsdk.core.resource import resource_projection_spec

DETAILED_HELP = {
    'EXAMPLES': """
To list network endpoints of a network endpoint group named ``my-neg''
in zone ``us-central1-a'':

  $ {command} my-neg --zone=us-central1-a
""",
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListNetworkEndpoints(base.ListCommand):
  """List network endpoints in a network endpoint group."""

  detailed_help = DETAILED_HELP
  display_info_format = """\
        table(
          networkEndpoint.instance,
          networkEndpoint.ipAddress,
          networkEndpoint.port,
          networkEndpoint.fqdn
        )"""

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat(cls.display_info_format)
    base.URI_FLAG.RemoveFromParser(parser)
    flags.MakeNetworkEndpointGroupsArg().AddArgument(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    neg_ref = flags.MakeNetworkEndpointGroupsArg().ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )

    display_info = args.GetDisplayInfo()
    defaults = resource_projection_spec.ProjectionSpec(
        symbols=display_info.transforms, aliases=display_info.aliases
    )
    args.filter, filter_expr = filter_rewrite.Rewriter().Rewrite(
        args.filter, defaults=defaults
    )

    if hasattr(neg_ref, 'zone'):
      request = (
          messages.ComputeNetworkEndpointGroupsListNetworkEndpointsRequest(
              networkEndpointGroup=neg_ref.Name(),
              project=neg_ref.project,
              zone=neg_ref.zone,
              filter=filter_expr,
          )
      )
      service = client.apitools_client.networkEndpointGroups
    elif hasattr(neg_ref, 'region'):
      request = messages.ComputeRegionNetworkEndpointGroupsListNetworkEndpointsRequest(
          networkEndpointGroup=neg_ref.Name(),
          project=neg_ref.project,
          region=neg_ref.region,
          filter=filter_expr,
      )
      service = client.apitools_client.regionNetworkEndpointGroups
    else:
      request = messages.ComputeGlobalNetworkEndpointGroupsListNetworkEndpointsRequest(
          networkEndpointGroup=neg_ref.Name(),
          project=neg_ref.project,
          filter=filter_expr,
      )
      service = client.apitools_client.globalNetworkEndpointGroups

    return list_pager.YieldFromList(
        service,
        request,
        method='ListNetworkEndpoints',
        field='items',
        limit=args.limit,
        batch_size=None,
    )


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class BetaListNetworkEndpoints(ListNetworkEndpoints):
  """List network endpoints in a network endpoint group."""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaListNetworkEndpoints(ListNetworkEndpoints):
  """List network endpoints in a network endpoint group."""

  display_info_format = """\
      table(
        networkEndpoint.instance,
        networkEndpoint.ipAddress,
        networkEndpoint.ipv6Address,
        networkEndpoint.port,
        networkEndpoint.fqdn,
        networkEndpoint.clientPort
      )"""
