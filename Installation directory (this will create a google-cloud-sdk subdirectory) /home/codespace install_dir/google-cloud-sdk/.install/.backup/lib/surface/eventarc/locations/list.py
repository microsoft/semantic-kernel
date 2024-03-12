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
"""Command to list all locations available in Eventarc API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.eventarc import locations
from googlecloudsdk.calliope import base

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
        To list all locations, run:

          $ {command}
        """,
}

_FORMAT = 'table(locationId:label=NAME)'


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List locations available for Eventarc."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(locations.GetLocationsURI)

  def Run(self, args):
    """Run the list command."""
    client = locations.LocationsClient(self.ReleaseTrack())
    return client.List(limit=args.limit, page_size=args.page_size)


@base.Deprecate(
    is_removed=False,
    warning=(
        'This command is deprecated. '
        'Please use `gcloud eventarc locations list` instead.'
    ),
    error=(
        'This command has been removed. '
        'Please use `gcloud eventarc locations list` instead.'
    ),
)
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(List):
  """List locations available for Eventarc."""
