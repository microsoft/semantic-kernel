# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command for updating the reservations in Compute Engine commitments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.commitments import flags
from googlecloudsdk.command_lib.compute.commitments import reservation_helper


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class UpdateReservationsAlpha(base.UpdateCommand):
  """Update the resource shape of reservations within the commitment."""
  detailed_help = {
      'EXAMPLES': '''
        To update reservations of the commitment called ``commitment-1'' in
        the ``us-central1'' region with values from ``reservations.yaml'', run:

          $ {command} commitment-1 --reservations-from-file=reservations.yaml

        For detailed examples, please refer to [](https://cloud.google.com/compute/docs/instances/reserving-zonal-resources#modifying_reservations_that_are_attached_to_commitments)
      '''
  }

  @staticmethod
  def Args(parser):
    flags.MakeCommitmentArg(False).AddArgument(
        parser, operation_type='update reservation')
    flags.AddUpdateReservationGroup(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    resources = holder.resources
    commitment_ref = flags.MakeCommitmentArg(False).ResolveAsResource(
        args,
        resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))
    service = client.apitools_client.regionCommitments
    messages = client.messages
    update_reservation_request = messages.RegionCommitmentsUpdateReservationsRequest(
        reservations=reservation_helper.MakeUpdateReservations(
            args, messages, resources))
    request = messages.ComputeRegionCommitmentsUpdateReservationsRequest(
        commitment=commitment_ref.Name(),
        project=commitment_ref.project,
        region=commitment_ref.region,
        regionCommitmentsUpdateReservationsRequest=update_reservation_request)
    return client.MakeRequests([(service, 'UpdateReservations', request)])
