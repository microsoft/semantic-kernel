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
"""'Bare Metal Solution volumes list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import flags
from googlecloudsdk.command_lib.bms import util


DETAILED_HELP = {
    'DESCRIPTION':
        """
          List Bare Metal Solution volumes in a project.
        """,
    'EXAMPLES':
        """
          To list volumes within the project in the region ``us-central1'', run:

            $ {command} --region=us-central1

          Or:

          To list all volumes in the project, run:

            $ {command}
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Bare Metal Solution volumes in a project."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    # Remove unsupported default List flags.
    base.FILTER_FLAG.RemoveFromParser(parser)
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.SORT_BY_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    flags.FILTER_FLAG_NO_SORTBY_DOC.AddToParser(parser)

    flags.AddRegionArgToParser(parser)
    # The default format picks out the components of the relative name:
    # given projects/myproject/locations/us-central1/volumes/my-test
    # it takes -1 (my-test), -3 (us-central1), and -5 (myproject).
    parser.display_info.AddFormat(
        'table(name.segment(-1):label=NAME,id:label=ID,'
        'name.segment(-5):label=PROJECT,name.segment(-3):label=REGION,'
        'requestedSizeGib,storageType,state)')

  def Run(self, args):
    region = util.FixParentPathWithGlobalRegion(args.CONCEPTS.region.Parse())
    client = BmsClient()
    return client.ListVolumes(region, limit=args.limit)


List.detailed_help = DETAILED_HELP
