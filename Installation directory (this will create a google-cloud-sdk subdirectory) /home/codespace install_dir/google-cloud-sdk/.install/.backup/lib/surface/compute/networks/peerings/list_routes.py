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
"""Command for listing internal IP addresses in a network."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class ListRoutes(base.ListCommand):
  """List received or advertised routes for a VPC network peering."""

  example = """\
    List received routes for VPC network peering in us-central1:

      $ {command} peering-name \
        --network=network-name --region=us-central1 --direction=INCOMING
  """

  detailed_help = {
      'brief':
          'List received or advertised routes for a VPC network peering.',
      'DESCRIPTION':
          """\
      *{command}* is used to list received or advertised routes for a VPC
      network peering. This includes subnetwork routes, static custom routes,
      and dynamic custom routes.
      """,
      'EXAMPLES':
          example
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('name', help='Name of the peering to list routes for.')
    parser.add_argument(
        '--network', required=True, help='Network of the peering.')
    parser.add_argument(
        '--region', required=True, help='Region to list the routes for.')
    parser.add_argument(
        '--direction',
        required=True,
        choices={
            'INCOMING': 'To list received routes.',
            'OUTGOING': 'To list advertised routes.',
        },
        type=lambda x: x.upper(),
        help="""\
        Direction of the routes to list. To list received routes, use
        `INCOMING`. To list advertised routes, use `OUTGOING`.
        """)
    parser.display_info.AddFormat("""\
        table(
            dest_range,
            type,
            next_hop_region,
            priority,
            status)
    """)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = client.MESSAGES_MODULE
    project = properties.VALUES.core.project.Get(required=True)

    list_request = messages.ComputeNetworksListPeeringRoutesRequest
    request = list_request(
        project=project,
        network=args.network,
        peeringName=args.name,
        region=args.region)
    directions = list_request.DirectionValueValuesEnum
    if args.direction == 'INCOMING':
      request.direction = directions.INCOMING
    else:
      request.direction = directions.OUTGOING

    items = list_pager.YieldFromList(
        client.networks,
        request,
        method='ListPeeringRoutes',
        field='items',
        limit=args.limit,
        batch_size=None)

    def _TransformStatus(direction, imported):
      """Create customized status field based on direction and imported."""
      if imported:
        if direction == 'INCOMING':
          return 'accepted'
        else:
          return 'accepted by peer'
      else:
        if direction == 'INCOMING':
          return 'rejected by config'
        else:
          return 'rejected by peer config'

    for item in items:
      route = resource_projector.MakeSerializable(item)
      # Set "status" to "Imported" or "Imported by peer" based on direction.
      route['status'] = _TransformStatus(args.direction, route['imported'])
      yield route
