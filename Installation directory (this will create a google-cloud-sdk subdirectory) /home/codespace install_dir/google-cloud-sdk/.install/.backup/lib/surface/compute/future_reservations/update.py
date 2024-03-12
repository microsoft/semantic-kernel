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
"""Command for compute future reservations update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.future_reservations import flags as fr_flags
from googlecloudsdk.command_lib.compute.future_reservations import util


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(base.UpdateCommand):
  """Update Compute Engine future reservations."""

  fr_arg = None

  detailed_help = {
      'EXAMPLES':
          """
        To update total count, start and end time of a Compute Engine future reservation in ``us-central1-a'', run:

            $ {command} my-future-reservation --total-count=1000 --start-time=2021-11-10T07:00:00Z
          --end-time=2021-12-10T07:00:00Z --zone=us-central1-a
        """
  }

  @classmethod
  def Args(cls, parser):
    cls.fr_arg = compute_flags.ResourceArgument(
        resource_name='future reservation',
        plural=False,
        name='FUTURE_RESERVATION',
        zonal_collection='compute.futureReservations',
        zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION,
    )

    cls.fr_arg.AddArgument(parser, operation_type='update')
    fr_flags.AddUpdateFlags(
        parser,
        support_fleet=False,
        support_planning_status=True,
        support_local_ssd_count=True,
        support_share_setting=True,
        support_auto_delete=True,
        support_require_specific_reservation=False,
    )

  def _ValidateArgs(self, update_mask):
    """Validates that at least one field to update is specified.

    Args:
      update_mask: The arguments being updated.
    """

    if not update_mask:
      parameter_names = [
          '--planning-status',
          '--description',
          '--name-prefix',
          '--total-count',
          '--min-cpu-platform',
          '--local-ssd',
          '--clear-local-ssd',
          '--accelerator',
          '--clear-accelerator',
          '--maintenance-interval',
          '--start-time',
          '--end-time',
          '--duration',
          '--machine-type',
          '--share-setting',
          '--share-with',
          '--clear-share-settings',
          '--auto-delete-auto-created-reservations',
          '--no-auto-delete-auto-created-reservations',
          '--auto-created-reservations-delete-time',
          '--auto-created-reservations-duration',
          '--require-specific-reservation',
          '--no-require-specific-reservation',
      ]
      raise exceptions.MinimumArgumentException(
          parameter_names, 'Please specify at least one property to update'
      )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    resources = holder.resources
    fr_ref = self.fr_arg.ResolveAsResource(
        args,
        resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    messages = holder.client.messages
    service = holder.client.apitools_client.futureReservations

    # Set updated properties and build update mask.
    update_mask = []

    if args.IsSpecified('planning_status'):
      update_mask.append('planningStatus')
    if args.IsSpecified('total_count'):
      update_mask.append('specificSkuProperties.totalCount')
    if args.IsSpecified('name_prefix') or args.IsSpecified('clear_name_prefix'):
      update_mask.append('namePrefix')
    if args.IsSpecified('description'):
      update_mask.append('description')
    if args.IsSpecified('min_cpu_platform'):
      update_mask.append(
          'specificSkuProperties.instanceProperties.minCpuPlatform'
      )
    if args.IsSpecified('machine_type'):
      update_mask.append('specificSkuProperties.instanceProperties.machineType')
    if args.IsSpecified('accelerator') or args.IsSpecified('clear_accelerator'):
      update_mask.append(
          'specificSkuProperties.instanceProperties.guestAccelerator'
      )
    if args.IsSpecified('local_ssd') or args.IsSpecified('clear_local_ssd'):
      update_mask.append('specificSkuProperties.instanceProperties.localSsd')
    if hasattr(args, 'maintenance_interval') and args.IsSpecified(
        'maintenance_interval'
    ):
      update_mask.append(
          'specificSkuProperties.intanceProperties.maintenanceInterval'
      )
    if args.IsSpecified('start_time'):
      update_mask.append('timeWindow.startTime')
    if args.IsSpecified('end_time'):
      update_mask.append('timeWindow.endTime')
    if args.IsSpecified('duration'):
      update_mask.append('timeWindow.duration')

    if (
        args.IsSpecified('clear_share_settings')
        or args.IsSpecified('share_setting')
        or args.IsSpecified('share_with')
    ):
      update_mask.append('shareSettings')

    if args.IsSpecified('auto_delete_auto_created_reservations'):
      update_mask.append('autoDeleteAutoCreatedReservations')
    if args.IsSpecified('auto_created_reservations_delete_time'):
      update_mask.append('autoCreatedReservationsDeleteTime')
    if args.IsSpecified('auto_created_reservations_duration'):
      update_mask.append('autoCreatedReservationsDuration')

    require_specific_reservation = getattr(
        args, 'require_specific_reservation', None
    )

    if require_specific_reservation is not None:
      update_mask.append('specificReservationRequired')
    self._ValidateArgs(update_mask=update_mask)

    fr_resource = util.MakeFutureReservationMessageFromArgs(
        messages, resources, args, fr_ref
    )
    fr_resource.description = args.description
    fr_resource.namePrefix = args.name_prefix

    # Build update request.
    fr_update_request = messages.ComputeFutureReservationsUpdateRequest(
        futureReservation=fr_ref.Name(),
        futureReservationResource=fr_resource,
        project=fr_ref.project,
        updateMask=','.join(update_mask),
        zone=fr_ref.zone)

    # Invoke futureReservation.update API.
    errors = []
    result = list(
        request_helper.MakeRequests(
            requests=[(service, 'Update', fr_update_request)],
            http=holder.client.apitools_client.http,
            batch_url=holder.client.batch_url,
            errors=errors))
    if errors:
      utils.RaiseToolException(errors)
    return result


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  """Update Compute Engine future reservations."""

  fr_arg = None

  detailed_help = {'EXAMPLES': """
        To update total count, start and end time of a Compute Engine future reservation in ``us-central1-a'', run:

            $ {command} my-future-reservation --total-count=1000 --start-time=2021-11-10T07:00:00Z
          --end-time=2021-12-10T07:00:00Z --zone=us-central1-a
        """}

  @classmethod
  def Args(cls, parser):
    cls.fr_arg = compute_flags.ResourceArgument(
        resource_name='future reservation',
        plural=False,
        name='FUTURE_RESERVATION',
        zonal_collection='compute.futureReservations',
        zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION,
    )

    cls.fr_arg.AddArgument(parser, operation_type='update')
    fr_flags.AddUpdateFlags(
        parser,
        support_fleet=True,
        support_planning_status=True,
        support_local_ssd_count=True,
        support_share_setting=True,
        support_auto_delete=True,
        support_require_specific_reservation=True,
    )
