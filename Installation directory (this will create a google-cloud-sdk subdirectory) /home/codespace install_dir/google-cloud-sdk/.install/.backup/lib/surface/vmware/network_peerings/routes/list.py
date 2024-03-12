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
"""VMware Engine VPC network peering routes list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware import networkpeeringroutes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware.network_peerings import flags
from googlecloudsdk.core.resource import resource_projector

DETAILED_HELP = {
    'DESCRIPTION':
        """
          List VPC network peering routes across all locations in your project.

        """,
    'EXAMPLES':
        """
          To list peering routes imported from peer network via my-peering:

            $ {command} --network-peering=my-peering --filter="direction=INCOMING"

          To list peering routes exported to peer network via my-peering:

            $ {command} --network-peering=my-peering --filter="direction=OUTGOING"

          In above examples, the location is taken as `global`.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Google Cloud VMware Engine VPC network peering routes."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddNetworkPeeringToParser(parser)
    parser.display_info.AddFormat("""\
        table(
            dest_range,
            type,
            next_hop_region,
            status,
            direction)
    """)

  def Run(self, args):
    networkpeering = args.CONCEPTS.network_peering.Parse()
    client = networkpeeringroutes.NetworkPeeringRoutesClient()
    items = client.List(networkpeering)

    def _TransformStatus(direction, imported):
      """Create customized status field based on direction and imported."""
      if imported:
        if direction == 'INCOMING':
          return 'accepted'
        return 'accepted by peer'
      if direction == 'INCOMING':
        return 'rejected by config'
      return 'rejected by peer config'

    for item in items:
      route = resource_projector.MakeSerializable(item)
      # Set "status" to "Imported" or "Imported by peer" based on direction.
      route['status'] = _TransformStatus(
          route['direction'], route.get('imported', False)
      )
      yield route
