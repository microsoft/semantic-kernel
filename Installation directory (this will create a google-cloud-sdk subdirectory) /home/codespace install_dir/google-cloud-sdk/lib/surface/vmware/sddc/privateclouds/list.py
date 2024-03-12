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
"""'vmware sddc privateclouds list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.sddc.privateclouds import PrivatecloudsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware.sddc import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          List VMware Engine private clouds in a region.
        """,
    'EXAMPLES':
        """
          To list private clouds in the region ``us-central1'', run:

            $ {command} --region=us-central1

          Or:

            $ {command}

          In the second example, the region is taken from gcloud properties
          vmware/region.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List VMware Engine private clouds in a region."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddRegionArgToParser(parser)
    # The default format picks out the components of the relative name:
    # given projects/myproject/locations/us-central1/clusterGroups/my-test
    # it takes -1 (my-test), -3 (us-central1), and -5 (myproject).
    parser.display_info.AddFormat(
        'table(name.segment(-1):label=NAME,name.segment(-5):label=PROJECT,'
        'name.segment(-3):label=REGION,createTime,status)')

  def Run(self, args):
    region = args.CONCEPTS.region.Parse()
    client = PrivatecloudsClient()
    return client.List(region)


List.detailed_help = DETAILED_HELP
