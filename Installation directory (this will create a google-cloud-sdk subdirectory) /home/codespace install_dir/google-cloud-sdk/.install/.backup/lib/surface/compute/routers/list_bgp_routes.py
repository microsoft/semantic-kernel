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

"""Command for listing bgp routes from a Compute Engine router."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routers import flags
from googlecloudsdk.command_lib.util.apis import arg_utils


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListBgpRoutes(base.ListCommand):
  """List route policies from a Compute Engine router.

  *{command}* lists all route policies from a Compute Engine router.
  """

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    ListBgpRoutes.ROUTER_ARG = flags.RouterArgument()
    ListBgpRoutes.ROUTER_ARG.AddArgument(parser, operation_type='list')
    parser.display_info.AddCacheUpdater(flags.RoutersCompleter)
    parser.add_argument(
        '--peer',
        help="""Limit results to routes learned from this peer (name).""",
        required=True,
    )
    parser.add_argument(
        '--address-family',
        type=arg_utils.ChoiceToEnumName,
        choices={
            'IPV4': 'Interface with IPv4-based BGP.',
            'IPV6': 'Interface with IPv6-based BGP.',
        },
        help="""Limit results to routes learned for this AFI.""",
        required=True,
    )
    parser.add_argument(
        '--route-direction',
        type=arg_utils.ChoiceToEnumName,
        choices={
            'INBOUND': 'Learned routes.',
            'OUTBOUND': 'Advertised routes.',
        },
        help="""Limit results to routes in this direction.""",
        required=True,
    )
    parser.add_argument(
        '--policy-applied',
        action='store_true',
        default=True,
        help="""Routes returned are post-policy evaluation.""",
    )
    parser.add_argument(
        '--destination-range',
        help="""Limit results to prefixes.""",
        metavar='CIDR_RANGE',
    )

  def Run(self, args):
    """Issues a request necessary for listing bgp routes from a Router."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    router_ref = ListBgpRoutes.ROUTER_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )
    address_family = client.messages.ComputeRoutersListBgpRoutesRequest.AddressFamilyValueValuesEnum(
        args.address_family
    )
    route_type = client.messages.ComputeRoutersListBgpRoutesRequest.RouteTypeValueValuesEnum(
        self.ConvertRouteDirection(args.route_direction)
    )

    request = client.messages.ComputeRoutersListBgpRoutesRequest(
        **router_ref.AsDict(),
        peer=args.peer,
        addressFamily=address_family,
        routeType=route_type,
        policyApplied=args.policy_applied,
        destinationPrefix=args.destination_range,
    )
    return list_pager.YieldFromList(
        client.apitools_client.routers,
        request,
        limit=args.limit,
        batch_size=args.page_size,
        method='ListBgpRoutes',
        field='result',
        current_token_attribute='pageToken',
        next_token_attribute='nextPageToken',
        batch_size_attribute='maxResults',
    )

  def ConvertRouteDirection(self, route_direction):
    if route_direction == 'INBOUND':
      return 'LEARNED'
    elif route_direction == 'OUTBOUND':
      return 'ADVERTISED'
    else:
      return route_direction
