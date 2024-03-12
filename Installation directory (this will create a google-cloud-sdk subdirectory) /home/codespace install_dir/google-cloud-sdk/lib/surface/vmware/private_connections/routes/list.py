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
"""private connection peering routes list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.privateconnectionroutes import PrivateConnectionPeeringRoutesClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core.resource import resource_projector

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Lists the private connection routes exchanged over a peering connection.
        """,
    'EXAMPLES':
        """
          To list all the peering routes of private connection called `my-private-connection` in project `my-project` and region `us-west1`, run:

            $ {command} --private-connection=my-private-connection --location=us-west1 --project=my-project

          Or:

            $ {command} --private-connection=my-private-connection

          In the last example, the project and the location are taken from gcloud properties core/project and compute/region, respectively.
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Google Cloud private connection peering routes."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivateConnectionToParser(parser)
    parser.display_info.AddFormat("""\
        table(
            dest_range,
            type,
            next_hop_region,
            status,
            direction)
    """)

  def Run(self, args):
    privateconnection = args.CONCEPTS.private_connection.Parse()
    client = PrivateConnectionPeeringRoutesClient()
    items = client.List(privateconnection)

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
