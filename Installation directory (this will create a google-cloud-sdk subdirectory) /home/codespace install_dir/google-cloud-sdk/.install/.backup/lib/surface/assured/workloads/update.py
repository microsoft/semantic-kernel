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
"""Command to update a new Assured Workload."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.assured import endpoint_util
from googlecloudsdk.api_lib.assured import message_util
from googlecloudsdk.api_lib.assured import workloads as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.base import ReleaseTrack
from googlecloudsdk.command_lib.assured import flags
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION':
        'Update a given Assured Workloads environment.',
    'EXAMPLES':
        """ \
        To update a given Assured Workloads environment in the us-central1
        region, belonging to an organization with ID 123, with workload ID 456
        and an etag of 789 with a new display name of 'Test-Workload-2' and a
        new set of labels (including any required existing labels) of
        (key = 'ExistingLabelKey1', value = 'ExistingLabelValue1') and
        (key = 'NewLabelKey2', value = 'NewLabelValue2'), run:

          $ {command} organizations/123/locations/us-central1/workloads/456 --display-name=Test-Workload-2 --labels=ExistingLabelKey1=ExistingLabelValue1,NewLabelKey2=NewLabelValue2 --etag=789
        """,
    # TODO(b/166449888): add support for multiple resource input formats
}


@base.ReleaseTracks(ReleaseTrack.GA, ReleaseTrack.BETA, ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update Assured Workloads environments."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddUpdateWorkloadFlags(parser)

  def Run(self, args):
    """Run the update command."""
    workload_resource = args.CONCEPTS.workload.Parse()
    region = workload_resource.Parent().Name()
    workload_name = workload_resource.RelativeName()
    with endpoint_util.AssuredWorkloadsEndpointOverridesFromRegion(
        release_track=self.ReleaseTrack(), region=region):
      update_mask = message_util.CreateUpdateMask(
          args.display_name, args.labels, args.violation_notifications_enabled
      )
      workload = message_util.CreateAssuredWorkload(
          display_name=args.display_name,
          labels=args.labels,
          etag=args.etag,
          violation_notifications_enabled=args.violation_notifications_enabled,
          release_track=self.ReleaseTrack(),
      )
      client = apis.WorkloadsClient(release_track=self.ReleaseTrack())
      self.updated_resource = client.Update(
          workload=workload, name=workload_name, update_mask=update_mask)
      return self.updated_resource

  def Epilog(self, resources_were_displayed):
    log.UpdatedResource(self.updated_resource.name,
                        kind='Assured Workloads environment')
