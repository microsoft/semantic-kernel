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
"""Acknowledge an existing Assured Workloads compliance violation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.assured import endpoint_util
from googlecloudsdk.api_lib.assured import violations as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.base import ReleaseTrack
from googlecloudsdk.command_lib.assured import flags

_DETAILED_HELP = {
    'DESCRIPTION': (
        'Acknowledge an existing Assured Workloads compliance violation.'
    ),
    'EXAMPLES': """ \
        To acknowledge an Assured Workloads Violation in the `us-central1` region, belonging to an organization with ID `123`, with workload ID `456`,  with violation ID `789` and comment as `test ack`, run:

          $ {command} organizations/123/locations/us-central1/workloads/456/violations/789 --comment="test ack"
        """,
}


@base.ReleaseTracks(ReleaseTrack.GA, ReleaseTrack.BETA, ReleaseTrack.ALPHA)
class Acknowledge(base.UpdateCommand):
  """Acknowledge an existing Assured Workloads compliance violation."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddAcknowledgeViolationsFlags(parser)

  def Run(self, args):
    """Run the acknowledge command."""
    violation_resource = args.CONCEPTS.violation.Parse()
    region = violation_resource.Parent().Parent().Name()
    violation = violation_resource.RelativeName()
    with endpoint_util.AssuredWorkloadsEndpointOverridesFromRegion(
        release_track=self.ReleaseTrack(), region=region
    ):
      client = apis.ViolationsClient(release_track=self.ReleaseTrack())
      if self.ReleaseTrack() == ReleaseTrack.GA:
        return client.Acknowledge(
            name=violation,
            comment=args.comment
        )
      return client.Acknowledge(
          name=violation,
          comment=args.comment,
          acknowledge_type=args.acknowledge_type,
      )
