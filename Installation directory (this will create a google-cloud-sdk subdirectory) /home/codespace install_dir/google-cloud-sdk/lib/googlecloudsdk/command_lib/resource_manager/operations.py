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
"""CRM operations utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import tags
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources


class OperationError(exceptions.Error):
  pass


class ReturnOperationPoller(waiter.CloudOperationPoller):
  """Polls for operations that retrieve the operation rather than the resource.

  This is needed for Delete operations, where the response is Empty. It is also
  needed for services that do not have a Get* method, such as TagBindings.
  """

  def __init__(self, operation_service):
    """Sets up poller for polling operations.

    Args:
      operation_service: apitools.base.py.base_api.BaseApiService, api service
        for retrieving information about ongoing operation.
    """
    self.operation_service = operation_service

  def GetResult(self, operation):
    """Overrides.

    Response for Deletion Operation is of type google.protobuf.Empty and hence
    we can return the operation itself as the result. For operations without a
    Get[Resource] method, we have no choice but to return the operation.

    Args:
      operation: api_name_messages.Operation.

    Returns:
      operation
    """
    return operation


def WaitForReturnOperation(operation, message):
  """Waits for the given google.longrunning.Operation to complete.

  Args:
    operation: The operation to poll.
    message: String to display for default progress_tracker.

  Raises:
    apitools.base.py.HttpError: if the request returns an HTTP error

  Returns:
    operation
  """
  poller = ReturnOperationPoller(tags.OperationsService())
  return _WaitForOperation(operation, message, poller)


def WaitForOperation(operation, message, service):
  """Waits for the given google.longrunning.Operation to complete.

  Args:
    operation: The operation to poll.
    message: String to display for default progress_tracker.
    service: The service to get the resource after the long running operation
      completes.

  Raises:
    apitools.base.py.HttpError: if the request returns an HTTP error

  Returns:
    The TagKey or TagValue resource.
  """
  poller = waiter.CloudOperationPoller(service, tags.OperationsService())
  return _WaitForOperation(operation, message, poller)


def _WaitForOperation(operation, message, poller):
  if poller.IsDone(operation):
    # Use the poller to get the result so it prints the same regardless if the
    # Operation is immediately done or not.
    return poller.GetResult(operation)

  operation_ref = resources.REGISTRY.Parse(
      operation.name, collection='cloudresourcemanager.operations')
  return waiter.WaitFor(poller, operation_ref, message)
