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
"""Command to list Discovered Workloads that can be added to an application in the Project/Location."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.apphub import discovered_workloads as apis
from googlecloudsdk.api_lib.apphub import utils as api_lib_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apphub import flags


_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To list DiscoveredWorkloads that could be added to an application in
        location `us-east1`, run:

          $ {command} --location=us-east1
        """,
}

_FORMAT = """
  table(
    name.scope("discoveredWorkloads"):label=ID,
    workloadReference,
    workloadProperties
  )
"""


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Apphub discovered workloads that could be added to an application."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddListDiscoveredWorkloadFlags(parser)
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(
        api_lib_utils.MakeGetUriFunc(
            'apphub.projects.locations.discoveredWorkloads',
            release_track=base.ReleaseTrack.GA,
        )
    )

  def Run(self, args):
    """Run the list command."""
    client = apis.DiscoveredWorkloadsClient(release_track=base.ReleaseTrack.GA)
    location_ref = args.CONCEPTS.location.Parse()
    return client.List(
        limit=args.limit,
        page_size=args.page_size,
        parent=location_ref.RelativeName(),
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(base.ListCommand):
  """List Apphub discovered workloads."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddListDiscoveredWorkloadFlags(parser)
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(
        api_lib_utils.MakeGetUriFunc(
            'apphub.projects.locations.discoveredWorkloads',
            release_track=base.ReleaseTrack.ALPHA,
        )
    )

  def Run(self, args):
    """Run the list command."""
    client = apis.DiscoveredWorkloadsClient(
        release_track=base.ReleaseTrack.ALPHA
    )
    location_ref = args.CONCEPTS.location.Parse()
    return client.List(
        limit=args.limit,
        page_size=args.page_size,
        parent=location_ref.RelativeName(),
    )
