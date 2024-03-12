# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Utilities for working with long running operations go/long-running-operation.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions

import enum

from googlecloudsdk.api_lib.app import exceptions as app_exceptions
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.api_lib.util import requests
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
import six

# Default is to retry every 5 seconds for 1 hour.
DEFAULT_OPERATION_RETRY_INTERVAL = 5
DEFAULT_OPERATION_MAX_TRIES = (60 // DEFAULT_OPERATION_RETRY_INTERVAL) * 60


def CallAndCollectOpErrors(method, *args, **kwargs):
  """Wrapper for method(...) which re-raises operation-style errors.

  Args:
    method: Original method to call.
    *args: Positional arguments to method.
    **kwargs: Keyword arguments to method.

  Raises:
    MiscOperationError: If the method call itself raises one of the exceptions
      listed below. Otherwise, the original exception is raised. Preserves
      stack trace. Re-uses the error string from original error or in the case
      of HttpError, we synthesize human-friendly string from HttpException.
      However, HttpException is neither raised nor part of the stack trace.

  Returns:
    Result of calling method(*args, **kwargs).
  """
  try:
    return method(*args, **kwargs)
  except apitools_exceptions.HttpError as http_err:
    # Create HttpException locally only to get its human friendly string
    _ReraiseMiscOperationError(api_exceptions.HttpException(http_err))
  except (OperationError, OperationTimeoutError, app_exceptions.Error) as err:
    _ReraiseMiscOperationError(err)


def _ReraiseMiscOperationError(err):
  """Transform and re-raise error helper."""
  exceptions.reraise(MiscOperationError(six.text_type(err)))


class MiscOperationError(exceptions.Error):
  """Wrapper exception for errors treated as operation failures."""


class OperationError(exceptions.Error):
  pass


class OperationTimeoutError(exceptions.Error):
  pass


class Status(enum.Enum):
  PENDING = 1
  COMPLETED = 2
  ERROR = 3


class Operation(object):
  """Wrapper around Operation response objects for console output.

  Attributes:
    project: String, name of the project.
    id: String, ID of operation.
    start_time: String, time the operation started.
    status: Status enum, either PENDING, COMPLETED, or Error.
    op_resource: messages.Operation, the original Operation resource.
  """

  def __init__(self, op_response):
    """Creates the operation wrapper object."""
    res = resources.REGISTRY.ParseRelativeName(op_response.name,
                                               'appengine.apps.operations')
    self.project = res.appsId
    self.id = res.Name()
    self.start_time = _GetInsertTime(op_response)
    self.status = GetStatus(op_response)
    self.op_resource = op_response

  def __eq__(self, other):
    return (isinstance(other, Operation) and
            self.project == other.project and
            self.id == other.id and
            self.start_time == other.start_time and
            self.status == other.status and
            self.op_resource == other.op_resource)


def GetStatus(operation):
  """Returns string status for given operation.

  Args:
    operation: A messages.Operation instance.

  Returns:
    The status of the operation in string form.
  """
  if not operation.done:
    return Status.PENDING.name
  elif operation.error:
    return Status.ERROR.name
  else:
    return Status.COMPLETED.name


def _GetInsertTime(operation):
  """Finds the insertTime property and return its string form.

  Args:
    operation: A messages.Operation instance.

  Returns:
    The time the operation started in string form or None if N/A.
  """
  if not operation.metadata:
    return None
  properties = operation.metadata.additionalProperties
  for prop in properties:
    if prop.key == 'insertTime':
      return prop.value.string_value


class AppEngineOperationPoller(waiter.OperationPoller):
  """A poller for appengine operations."""

  def __init__(self, operation_service, operation_metadata_type=None):
    """Sets up poller for appengine operations.

    Args:
      operation_service: apitools.base.py.base_api.BaseApiService, api service
        for retrieving information about ongoing operation.
      operation_metadata_type: Message class for the Operation metadata (for
        instance, OperationMetadataV1, or OperationMetadataV1Beta).
    """
    self.operation_service = operation_service
    self.operation_metadata_type = operation_metadata_type
    self.warnings_seen = set()

  def IsDone(self, operation):
    """Overrides."""
    self._LogNewWarnings(operation)
    if operation.done:
      log.debug('Operation [{0}] complete. Result: {1}'.format(
          operation.name,
          json.dumps(encoding.MessageToDict(operation), indent=4)))
      if operation.error:
        raise OperationError(requests.ExtractErrorMessage(
            encoding.MessageToPyValue(operation.error)))
      return True
    log.debug('Operation [{0}] not complete. Waiting to retry.'.format(
        operation.name))
    return False

  def Poll(self, operation_ref):
    """Overrides.

    Args:
      operation_ref: googlecloudsdk.core.resources.Resource.

    Returns:
      fetched operation message.
    """
    request_type = self.operation_service.GetRequestType('Get')
    request = request_type(name=operation_ref.RelativeName())
    operation = self.operation_service.Get(request)
    self._LogNewWarnings(operation)
    return operation

  def _LogNewWarnings(self, operation):
    if self.operation_metadata_type:
      # Log any new warnings to the end user.
      new_warnings = GetWarningsFromOperation(
          operation, self.operation_metadata_type) - self.warnings_seen
      for warning in new_warnings:
        log.warning(warning + '\n')
        self.warnings_seen.add(warning)

  def GetResult(self, operation):
    """Simply returns the operation.

    Args:
      operation: api_name_messages.Operation.

    Returns:
      the 'response' field of the Operation.
    """
    return operation


class AppEngineOperationBuildPoller(AppEngineOperationPoller):
  """Waits for a build to be present, or for the operation to finish."""

  def __init__(self, operation_service, operation_metadata_type):
    """Sets up poller for appengine operations.

    Args:
      operation_service: apitools.base.py.base_api.BaseApiService, api service
        for retrieving information about ongoing operation.
      operation_metadata_type: Message class for the Operation metadata (for
        instance, OperationMetadataV1, or OperationMetadataV1Beta).
    """
    super(AppEngineOperationBuildPoller, self).__init__(operation_service,
                                                        operation_metadata_type)

  def IsDone(self, operation):
    if GetBuildFromOperation(operation, self.operation_metadata_type):
      return True
    return super(AppEngineOperationBuildPoller, self).IsDone(operation)


def GetMetadataFromOperation(operation, operation_metadata_type):
  if not operation.metadata:
    return None
  return encoding.JsonToMessage(
      operation_metadata_type,
      encoding.MessageToJson(operation.metadata))


def GetBuildFromOperation(operation, operation_metadata_type):
  metadata = GetMetadataFromOperation(operation, operation_metadata_type)
  if not metadata or not metadata.createVersionMetadata:
    return None
  return metadata.createVersionMetadata.cloudBuildId


def GetWarningsFromOperation(operation, operation_metadata_type):
  metadata = GetMetadataFromOperation(operation, operation_metadata_type)
  if not metadata:
    return set()
  return set(warning for warning in metadata.warning)


def WaitForOperation(operation_service, operation,
                     max_retries=None,
                     retry_interval=None,
                     operation_collection='appengine.apps.operations',
                     message=None,
                     poller=None):
  """Wait until the operation is complete or times out.

  Args:
    operation_service: The apitools service type for operations
    operation: The operation resource to wait on
    max_retries: Maximum number of times to poll the operation
    retry_interval: Frequency of polling in seconds
    operation_collection: The resource collection of the operation.
    message: str, the message to display while progress tracker displays.
    poller: AppEngineOperationPoller to poll with, defaulting to done.
  Returns:
    The operation resource when it has completed
  Raises:
    OperationError: if the operation contains an error.
    OperationTimeoutError: when the operation polling times out

  """
  poller = poller or AppEngineOperationPoller(operation_service)
  if poller.IsDone(operation):
    return poller.GetResult(operation)
  operation_ref = resources.REGISTRY.ParseRelativeName(
      operation.name,
      operation_collection)
  if max_retries is None:
    max_retries = DEFAULT_OPERATION_MAX_TRIES - 1
  if retry_interval is None:
    retry_interval = DEFAULT_OPERATION_RETRY_INTERVAL
  if message is None:
    message = 'Waiting for operation [{}] to complete'.format(
        operation_ref.RelativeName())
  # Convert to milliseconds
  retry_interval *= 1000
  try:
    completed_operation = waiter.WaitFor(
        poller,
        operation_ref,
        message,
        pre_start_sleep_ms=1000,
        max_retrials=max_retries,
        exponential_sleep_multiplier=1.0,
        sleep_ms=retry_interval)
  except waiter.TimeoutError:
    raise OperationTimeoutError(('Operation [{0}] timed out. This operation '
                                 'may still be underway.').format(
                                     operation.name))
  return completed_operation
