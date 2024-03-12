# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""'notebooks locations list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.notebooks import locations as loc_util
from googlecloudsdk.api_lib.notebooks import util
from googlecloudsdk.calliope import base

DETAILED_HELP = {
    'DESCRIPTION': """
        Request for listing locations.
    """,
    'EXAMPLES': """
    To list locations, run:
      $ {command}
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class List(base.ListCommand):
  """Request for listing locations."""

  @classmethod
  def Args(cls, parser):
    """Register flags for this command."""
    parser.display_info.AddFormat('table(locationId)')
    parser.display_info.AddUriFunc(loc_util.GetLocationURI)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    release_track = self.ReleaseTrack()
    client = util.GetClient(release_track)
    messages = util.GetMessages(release_track)
    location_service = client.projects_locations
    return list_pager.YieldFromList(
        location_service,
        loc_util.CreateLocationListRequest(args, messages),
        field='locations',
        limit=args.limit,
        batch_size_attribute='pageSize')


List.detailed_help = DETAILED_HELP
