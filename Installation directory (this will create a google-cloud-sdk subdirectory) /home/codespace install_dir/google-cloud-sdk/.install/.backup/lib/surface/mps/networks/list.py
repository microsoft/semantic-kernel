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

"""'Marketplace Solutions networks list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.api_lib.mps.mps_client import MpsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.mps import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector


DETAILED_HELP = {
    'DESCRIPTION':
        """
          List Marketplace Solutions networks in a project.
        """,
    'EXAMPLES':
        """
          To list networks in the region within the project ``us-central1'', run:

            $ {command} --region=us-central1

          Or:

          To list all networks in the project, run:

            $ {command}
    """,
}
NETWORK_LIST_FORMAT = """ table(
        name.segment(-1):label=NAME,
        name.segment(-5):label=PROJECT,
        name.segment(-3):label=REGION,
        cidr,
        uid,
        type,
        jumboFramesEnabled,
        vlanId
    )"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Marketplace Solution networks in a project."""
  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    # Remove unsupported default List flags.
    base.FILTER_FLAG.RemoveFromParser(parser)
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.SORT_BY_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)

    flags.AddRegionArgToParser(parser)
    # The default format picks out the components of the relative name:
    # given projects/myproject/locations/us-central1/clusterGroups/my-test
    # it takes -1 (my-test), -3 (us-central1), and -5 (myproject).

    parser.display_info.AddFormat(NETWORK_LIST_FORMAT)

  def Run(self, args):
    """Return network list information based on user request."""
    region = args.CONCEPTS.region.Parse()
    client = MpsClient()
    product = properties.VALUES.mps.product.Get(required=True)

    if region is None:
      project = properties.VALUES.core.project.Get(required=True)
      return client.AggregateListNetworks(project, product, limit=args.limit)
    return client.ListNetworks(product, region)

List.detailed_help = DETAILED_HELP

