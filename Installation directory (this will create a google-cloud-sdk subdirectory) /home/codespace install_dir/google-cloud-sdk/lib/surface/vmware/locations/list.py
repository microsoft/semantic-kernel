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
"""'vmware locations list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.locations import LocationsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          List supported VMware Engine locations.
        """,
    'EXAMPLES':
        """
          To list VMware Engine locations, run:

            $ {command}
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Google Cloud VMware Engine locations."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddProjectArgToParser(parser, positional=False)
    parser.display_info.AddFormat("""\
            table(
          locationId:label=ID,
          name
      )""")

  def Run(self, args):
    project = args.CONCEPTS.project.Parse()
    client = LocationsClient()
    return client.List(project)
