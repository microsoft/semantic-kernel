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
"""Command to list all Assured Operations belonging to a given parent Organization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.assured import endpoint_util
from googlecloudsdk.api_lib.assured import message_util
from googlecloudsdk.api_lib.assured import operations as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.base import ReleaseTrack
from googlecloudsdk.command_lib.assured import flags

_DETAILED_HELP = {
    'DESCRIPTION':
        'List all Assured Workloads operations that belong to a given parent '
        'organization.',
    'EXAMPLES':
        """ \
        The following example command lists all Assured Workloads operations
        with these properties:

        * belonging to an organization with ID 123
        * located in the `us-central1` region
        * return no more than 30 results
        * requesting 10 results at a time from the backend

          $ {command} organizations/123/locations/us-central1 --limit=30 --page-size=10
        """,
}


@base.ReleaseTracks(ReleaseTrack.GA, ReleaseTrack.BETA, ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List all Assured Workloads operations that belong to a given parent organization."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddListOperationsFlags(parser)

  def Run(self, args):
    """Run the list command."""
    with endpoint_util.AssuredWorkloadsEndpointOverridesFromRegion(
        release_track=self.ReleaseTrack(), region=args.location):
      client = apis.OperationsClient(release_track=self.ReleaseTrack())
      return client.List(
          parent=message_util.CreateAssuredParent(args.organization,
                                                  args.location),
          limit=args.limit,
          page_size=args.page_size)
