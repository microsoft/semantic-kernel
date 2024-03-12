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

"""Command for listing spokes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_connectivity import flags
from googlecloudsdk.command_lib.network_connectivity import util


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List spokes.

  Retrieve and display a list of all spokes in the specified project.
  """

  @staticmethod
  def Args(parser):
    # Remove URI flag to match surface spec
    base.URI_FLAG.RemoveFromParser(parser)

    # Add flags to identify region
    flags.AddRegionResourceArg(parser, 'to display')
    flags.AddRegionGroup(
        parser, supports_region_wildcard=True, hide_global_arg=False)

    # Table formatting
    parser.display_info.AddFormat(util.LIST_FORMAT)

  def Run(self, args):
    client = networkconnectivity_api.SpokesClient(
        release_track=self.ReleaseTrack())
    region_ref = args.CONCEPTS.region.Parse()
    return client.List(
        region_ref,
        limit=args.limit,
        filter_expression=None,  # Do all filtering client-side.
        page_size=args.page_size)


List.detailed_help = {
    'EXAMPLES':
        """ \
  To list all spokes in the ``us-central1'' region, run:

        $ {command} --region=us-central1

  To list all spokes in all regions, run:

        $ {command}
  """,
    'API REFERENCE':
        """ \
  This command uses the networkconnectivity/v1 API. The full documentation
  for this API can be found at:
  https://cloud.google.com/network-connectivity/docs/reference/networkconnectivity/rest
  """,
}
