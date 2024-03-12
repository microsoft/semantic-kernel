# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command to list all event providers available in Eventarc API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.eventarc import providers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.eventarc import flags

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
        To list all providers in location `us-central1`, run:

          $ {command} --location=us-central1

        To list all providers in all locations, run:

          $ {command} --location=-

        or

          $ {command}
        """,
}

_FORMAT = """ \
table(
name.scope("providers"):label=NAME,
name.scope("locations").segment(0):label=LOCATION
)
"""

_FILTER = 'name:/providers/'


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List event providers available in Eventarc."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddLocationResourceArg(
        parser,
        'The location in which to list event providers.',
        required=False)
    flags.AddProjectResourceArg(parser)
    flags.AddProviderNameArg(parser)
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(providers.GetProvidersURI)

  def Run(self, args):
    """Run the list command."""
    client = providers.ProvidersClient(self.ReleaseTrack())
    args.CONCEPTS.project.Parse()
    location_ref = args.CONCEPTS.location.Parse()
    if args.name:
      args.GetDisplayInfo().AddFilter(_FILTER + args.name)
    return client.List(
        location_ref.RelativeName(), limit=args.limit, page_size=args.page_size)
