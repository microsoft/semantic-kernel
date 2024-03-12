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
"""Command to update a trigger."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.eventarc import triggers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.eventarc import flags
from googlecloudsdk.command_lib.eventarc import types
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
        To update the trigger ``my-trigger'' by setting its destination Cloud Run service to ``my-service'', run:

          $ {command} my-trigger --destination-run-service=my-service
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update an Eventarc trigger."""

  detailed_help = _DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    flags.AddTriggerResourceArg(parser, 'The trigger to update.', required=True)
    flags.AddEventFiltersArg(parser, cls.ReleaseTrack())
    flags.AddEventFiltersPathPatternArg(parser, cls.ReleaseTrack())
    flags.AddEventDataContentTypeArg(parser, cls.ReleaseTrack())
    flags.AddUpdateDestinationArgs(parser, cls.ReleaseTrack())
    base.ASYNC_FLAG.AddToParser(parser)

    service_account_group = parser.add_mutually_exclusive_group()
    flags.AddServiceAccountArg(service_account_group)
    flags.AddClearServiceAccountArg(service_account_group)

  def Run(self, args):
    """Run the update command."""
    client = triggers.CreateTriggersClient(self.ReleaseTrack())
    trigger_ref = args.CONCEPTS.trigger.Parse()
    event_filters = flags.GetEventFiltersArg(args, self.ReleaseTrack())
    event_filters_path_pattern = flags.GetEventFiltersPathPatternArg(
        args, self.ReleaseTrack())
    event_data_content_type = flags.GetEventDataContentTypeArg(
        args, self.ReleaseTrack()
    )
    update_mask = client.BuildUpdateMask(
        event_filters=event_filters is not None,
        event_filters_path_pattern=event_filters_path_pattern is not None,
        event_data_content_type=event_data_content_type is not None,
        service_account=args.IsSpecified('service_account')
        or args.clear_service_account,
        destination_run_service=args.IsSpecified('destination_run_service'),
        destination_run_job=args.IsSpecified('destination_run_job'),
        destination_run_path=args.IsSpecified('destination_run_path')
        or args.clear_destination_run_path,
        destination_run_region=args.IsSpecified('destination_run_region'),
        destination_gke_namespace=args.IsSpecified('destination_gke_namespace'),
        destination_gke_service=args.IsSpecified('destination_gke_service'),
        destination_gke_path=args.IsSpecified('destination_gke_path')
        or args.clear_destination_gke_path,
        destination_workflow=args.IsSpecified('destination_workflow'),
        destination_workflow_location=args.IsSpecified(
            'destination_workflow_location'
        ),
        destination_function=args.IsSpecified('destination_function'),
        destination_function_location=args.IsSpecified(
            'destination_function_location'
        ),
    )
    old_trigger = client.Get(trigger_ref)
    # The type can't be updated, so it's safe to use the old trigger's type.
    # In the async case, this is the only way to get the type.
    self._event_type = client.GetEventType(old_trigger)
    destination_message = None
    if (args.IsSpecified('destination_run_service') or
        args.IsSpecified('destination_run_job') or
        args.IsSpecified('destination_run_region') or
        args.IsSpecified('destination_run_path') or
        args.clear_destination_run_path):
      destination_message = client.BuildCloudRunDestinationMessage(
          args.destination_run_service, args.destination_run_job,
          args.destination_run_path, args.destination_run_region)
    elif (args.IsSpecified('destination_gke_namespace') or
          args.IsSpecified('destination_gke_service') or
          args.IsSpecified('destination_gke_path') or
          args.clear_destination_gke_path):
      destination_message = client.BuildGKEDestinationMessage(
          None, None, args.destination_gke_namespace,
          args.destination_gke_service, args.destination_gke_path)
    elif (args.IsSpecified('destination_workflow') or
          args.IsSpecified('destination_workflow_location')):
      location = self.GetWorkflowDestinationLocation(args, old_trigger)
      workflow = self.GetWorkflowDestination(args, old_trigger)
      destination_message = client.BuildWorkflowDestinationMessage(
          trigger_ref.Parent().Parent().Name(), workflow, location)
    elif (args.IsSpecified('destination_function') or
          args.IsSpecified('destination_function_location')):
      location = self.GetFunctionDestinationLocation(args, old_trigger)
      function = self.GetFunctionDestination(args, old_trigger)
      destination_message = client.BuildFunctionDestinationMessage(
          trigger_ref.Parent().Parent().Name(), function, location)
    trigger_message = client.BuildTriggerMessage(
        trigger_ref,
        event_filters,
        event_filters_path_pattern,
        event_data_content_type,
        args.service_account,
        destination_message,
        None,
        None,
    )
    operation = client.Patch(trigger_ref, trigger_message, update_mask)
    if args.async_:
      return operation
    return client.WaitFor(operation, 'Updating', trigger_ref)

  def Epilog(self, resources_were_displayed):
    if resources_were_displayed and types.IsAuditLogType(self._event_type):
      log.warning(
          'It may take up to {} minutes for the update to take full effect.'
          .format(triggers.MAX_ACTIVE_DELAY_MINUTES))

  def GetWorkflowDestinationLocation(self, args, old_trigger):
    if args.IsSpecified('destination_workflow_location'):
      return args.destination_workflow_location
    if old_trigger.destination.workflow:
      return old_trigger.destination.workflow.split('/')[3]
    raise exceptions.InvalidArgumentException(
        '--destination-workflow',
        'The specified trigger is not for a workflow destination.')

  def GetWorkflowDestination(self, args, old_trigger):
    if args.IsSpecified('destination_workflow'):
      return args.destination_workflow
    if old_trigger.destination.workflow:
      return old_trigger.destination.workflow.split('/')[5]
    raise exceptions.InvalidArgumentException(
        '--destination-workflow-location',
        'The specified trigger is not for a workflow destination.')

  def GetFunctionDestinationLocation(self, args, old_trigger):
    if args.IsSpecified('destination_function_location'):
      return args.destination_function_location
    if old_trigger.destination.cloudFunction:
      return old_trigger.destination.cloudFunction.split('/')[3]
    raise exceptions.InvalidArgumentException(
        '--destination-function',
        'The specified trigger is not for a function destination.')

  def GetFunctionDestination(self, args, old_trigger):
    if args.IsSpecified('destination_function'):
      return args.destination_function
    if old_trigger.destination.cloudFunction:
      return old_trigger.destination.cloudFunction.split('/')[5]
    raise exceptions.InvalidArgumentException(
        '--destination-function-location',
        'The specified trigger is not for a function destination.')


@base.Deprecate(
    is_removed=False,
    warning=(
        'This command is deprecated. '
        'Please use `gcloud eventarc triggers update` instead.'
    ),
    error=(
        'This command has been removed. '
        'Please use `gcloud eventarc triggers update` instead.'
    ),
)
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Update an Eventarc trigger."""

  def Run(self, args):
    """Run the update command."""
    client = triggers.CreateTriggersClient(self.ReleaseTrack())
    trigger_ref = args.CONCEPTS.trigger.Parse()
    event_filters = flags.GetEventFiltersArg(args, self.ReleaseTrack())
    update_mask = client.BuildUpdateMask(
        event_filters=event_filters is not None,
        event_data_content_type=None,
        service_account=args.IsSpecified('service_account')
        or args.clear_service_account,
        destination_run_service=args.IsSpecified('destination_run_service'),
        destination_run_job=None,  # Not supported in BETA release track or API
        destination_run_path=args.IsSpecified('destination_run_path')
        or args.clear_destination_run_path,
        destination_run_region=args.IsSpecified('destination_run_region'),
    )
    old_trigger = client.Get(trigger_ref)
    # The type can't be updated, so it's safe to use the old trigger's type.
    # In the async case, this is the only way to get the type.
    self._event_type = client.GetEventType(old_trigger)
    destination_message = client.BuildCloudRunDestinationMessage(
        args.destination_run_service, None, args.destination_run_path,
        args.destination_run_region)
    trigger_message = client.BuildTriggerMessage(trigger_ref, event_filters,
                                                 None, None,
                                                 args.service_account,
                                                 destination_message, None,
                                                 None)
    operation = client.Patch(trigger_ref, trigger_message, update_mask)
    if args.async_:
      return operation
    return client.WaitFor(operation, 'Updating', trigger_ref)
