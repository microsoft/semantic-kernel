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

"""Command for listing spokes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_api
from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_connectivity import flags
from googlecloudsdk.command_lib.network_connectivity import util


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListSpokes(base.ListCommand):
  """List hub spokes.

  Retrieve and display a list of all spokes associated with a hub.
  """

  @staticmethod
  def Args(parser):
    # Remove URI flag to match surface spec
    base.URI_FLAG.RemoveFromParser(parser)

    # Add flags to identify region
    flags.AddSpokeLocationsFlag(parser)
    flags.AddViewFlag(parser)
    flags.AddHubResourceArg(parser, """associated with the returned list of
                            spokes""")

    # Table formatting
    parser.display_info.AddFormat(util.LIST_SPOKES_FORMAT)

  def Run(self, args):
    release_track = self.ReleaseTrack()
    view = ViewToEnum(args.view, release_track)
    client = networkconnectivity_api.HubsClient(release_track)
    hub_ref = args.CONCEPTS.hub.Parse()
    return client.ListHubSpokes(
        hub_ref,
        spoke_locations=args.spoke_locations,
        limit=args.limit,
        order_by=None,  # Do all sorting client-side
        filter_expression=None,  # Do all filtering client-side
        view=view)


def ViewToEnum(view, release_track):
  """Converts the typed view into its Enum value."""
  list_hub_spokes_req = networkconnectivity_util.GetMessagesModule(release_track).NetworkconnectivityProjectsLocationsGlobalHubsListSpokesRequest  # pylint: disable=line-too-long
  if view == 'detailed':
    return list_hub_spokes_req.ViewValueValuesEnum.DETAILED
  return list_hub_spokes_req.ViewValueValuesEnum.BASIC

ListSpokes.detailed_help = {
    'EXAMPLES': """ \
  To list all spokes in the ``us-central1'' region and the global location, run:

        $ {command} --spoke-locations=us-central1,global
  """,
    'API REFERENCE': """ \
  This command uses the networkconnectivity/v1 API. The full documentation
  for this API can be found at:
  https://cloud.google.com/network-connectivity/docs/reference/networkconnectivity/rest
  """,
}
