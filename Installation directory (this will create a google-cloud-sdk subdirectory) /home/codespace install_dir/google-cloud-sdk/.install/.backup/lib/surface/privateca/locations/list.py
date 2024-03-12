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
"""List supported locations for the Private CA API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import locations
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List supported locations for the Private CA GA API."""

  detailed_help = {
      'DESCRIPTION':
          """\
          Returns supported locations where resources can be managed through
          the Private CA GA API.""",
      'EXAMPLES':
          """\
          To list the locations available for the Private CA GA API:

          $ {command}

          """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('table(locationId:label=LOCATION_ID)')

  def Run(self, args):
    """Runs the command."""
    messages = privateca_base.GetMessagesModule('v1')
    return [
        messages.Location(locationId=location)
        for location in locations.GetSupportedLocations('v1')
    ]
