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
"""Common utility functions for sql reschedule-maintenance commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from dateutil import tz
from googlecloudsdk.api_lib.sql import exceptions as sql_exceptions
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_lex
from googlecloudsdk.core.resource import resource_property
from googlecloudsdk.core.util import times
import six


def ParseRescheduleType(sql_messages, reschedule_type):
  if reschedule_type:
    return sql_messages.Reschedule.RescheduleTypeValueValuesEnum.lookup_by_name(
        reschedule_type.upper())
  return None


def RunRescheduleMaintenanceCommand(args, client):
  """Reschedule maintenance for a Cloud SQL instance.

  Args:
    args: argparse.Namespace, The arguments that this command was invoked with.
    client: SqlClient instance, with sql_client and sql_messages props, for use
      in generating messages and making API calls.

  Returns:
    None

  Raises:
    HttpException: An HTTP error response was received while executing API
        request.
    ArgumentError: The schedule_time argument was missing, in an invalid format,
        or not within the reschedule maintenance bounds.
    InvalidStateException: The Cloud SQL instance was not in an appropriate
        state for the requested command.
    ToolException: Any other error that occurred while executing the command.
  """
  sql_client = client.sql_client
  sql_messages = client.sql_messages

  reschedule_type = ParseRescheduleType(sql_messages, args.reschedule_type)
  schedule_time = args.schedule_time

  # Start argument validation.
  validate.ValidateInstanceName(args.instance)
  instance_ref = client.resource_parser.Parse(
      args.instance,
      params={'project': properties.VALUES.core.project.GetOrFail},
      collection='sql.instances')

  if reschedule_type == sql_messages.Reschedule.RescheduleTypeValueValuesEnum.SPECIFIC_TIME:
    if schedule_time is None:
      raise sql_exceptions.ArgumentError(
          'argument --schedule-time: Must be specified for SPECIFIC_TIME.')

  # Get the instance the user is operating on.
  try:
    instance_resource = sql_client.instances.Get(
        sql_messages.SqlInstancesGetRequest(
            project=instance_ref.project, instance=instance_ref.instance))
  except apitools_exceptions.HttpError as error:
    # TODO(b/64292220): Remove once API gives helpful error message.
    log.debug('operation : %s', six.text_type(instance_ref))
    exc = exceptions.HttpException(error)
    if resource_property.Get(exc.payload.content,
                             resource_lex.ParseKey('error.errors[0].reason'),
                             None) == 'notAuthorized':
      raise exceptions.HttpException(
          'You are either not authorized to access the instance or it does not '
          'exist.'
      )
    raise

  # Start validation against instance properties.
  if instance_resource.scheduledMaintenance is None:
    raise sql_exceptions.InvalidStateError(
        'This instance does not have any scheduled maintenance at this time.')

  if not instance_resource.scheduledMaintenance.canReschedule:
    raise sql_exceptions.InvalidStateError(
        'Cannot reschedule this instance\'s maintenance.')

  if reschedule_type == sql_messages.Reschedule.RescheduleTypeValueValuesEnum.SPECIFIC_TIME:
    # Ensure we have a valid scheduledMaintenance.startTime to prevent
    # validation errors elsewhere in the pipeline.
    try:
      start_time = times.ParseDateTime(
          instance_resource.scheduledMaintenance.startTime, tzinfo=tz.tzutc())
    except ValueError:
      raise sql_exceptions.InvalidStateError(
          'Cannot reschedule this instance\'s maintenance.')
    if schedule_time < start_time:
      raise sql_exceptions.ArgumentError(
          'argument --schedule-time: Must be after original scheduled time.')

  # Convert the schedule_time to the format the backend expects, if it exists.
  schedule_time = times.LocalizeDateTime(
      schedule_time, times.UTC).isoformat().replace(
          '+00:00', 'Z') if schedule_time is not None else None

  # Perform the requested reschedule operation.
  reschedule_maintenance_request = sql_messages.SqlProjectsInstancesRescheduleMaintenanceRequest(
      instance=instance_ref.instance,
      project=instance_ref.project,
      sqlInstancesRescheduleMaintenanceRequestBody=sql_messages
      .SqlInstancesRescheduleMaintenanceRequestBody(
          reschedule=sql_messages.Reschedule(
              rescheduleType=reschedule_type,
              scheduleTime=schedule_time)))

  result_operation = sql_client.projects_instances.RescheduleMaintenance(
      reschedule_maintenance_request)

  operation_ref = client.resource_parser.Create(
      'sql.operations',
      operation=result_operation.name,
      project=instance_ref.project)

  operations.OperationsV1Beta4.WaitForOperation(sql_client, operation_ref,
                                                'Rescheduling maintenance.')

  log.status.write('Maintenance rescheduled.\n')

  return
