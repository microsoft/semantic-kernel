# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to list all Violations that belong to a given Assured Workloads environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.assured import endpoint_util
from googlecloudsdk.api_lib.assured import message_util
from googlecloudsdk.api_lib.assured import violations as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.base import ReleaseTrack
from googlecloudsdk.command_lib.assured import flags

_DETAILED_HELP = {
    'DESCRIPTION':
        'List all Violations that belong to the given Assured Workloads '
        'environment.',
    'EXAMPLES':
        """ \
        The following example command lists all violations with these properties:

        * belonging to an organization with ID 123
        * belonging to the assured workload with ID w123
        * located in the `us-central1` region
        * returning no more than 30 results
        * requesting 10 results at a time from the backend

          $ {command} --organization=123 --location=us-central1 --workload=w123 --limit=30 --page-size=10
        """,
}


@base.ReleaseTracks(ReleaseTrack.GA, ReleaseTrack.BETA, ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List all Assured Workloads violations that belong to a assured workloads environment."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddListViolationsFlags(parser)

  def Run(self, args):
    """Run the list command."""
    with endpoint_util.AssuredWorkloadsEndpointOverridesFromRegion(
        release_track=self.ReleaseTrack(), region=args.location):
      client = apis.ViolationsClient(release_track=self.ReleaseTrack())
      return client.List(
          parent=message_util.CreateAssuredWorkloadsParent(
              args.organization, args.location, args.workload),
          limit=args.limit,
          page_size=args.page_size)
