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
"""Utilities for Cloud Workflows poller."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.api_lib.workflows import codes


class OperationsClient(object):
  """Client for Operations service in the Cloud Workflows API."""

  def __init__(self, client, messages):
    self.client = client
    self.messages = messages
    self._service = self.client.projects_locations_operations

  def Get(self, operation_ref):
    """Gets an Operation.

    Args:
      operation_ref: Resource reference to the Operation to get.

    Returns:
      Operation: The operation if it exists, None otherwise.
    """
    get_req = self.messages.WorkflowsProjectsLocationsOperationsGetRequest(
        name=operation_ref.RelativeName())
    try:
      return self._service.Get(get_req)
    except exceptions.HttpNotFoundError:
      return None


class WorkflowsOperationPoller(waiter.OperationPoller):
  """Implementation of OperationPoller for Workflows Operations."""

  def __init__(self, workflows, operations, workflow_ref):
    """Creates the poller.

    Args:
      workflows: the Workflows API client used to get the resource after
        operation is complete.
      operations: the Operations API client used to poll for the operation.
      workflow_ref: a reference to a workflow that is the subject of this
        operation.
    """
    self.workflows = workflows
    self.operations = operations
    self.workflow_ref = workflow_ref

  def IsDone(self, operation):
    """Overrides."""
    if operation.done:
      if operation.error:
        raise waiter.OperationError(_ExtractErrorMessage(operation.error))
      return True
    return False

  def Poll(self, operation_ref):
    """Overrides."""
    return self.operations.Get(operation_ref)

  def GetResult(self, operation):
    """Overrides."""
    return self.workflows.Get(self.workflow_ref)


class ExecutionsPoller(waiter.OperationPoller):
  """Implementation of OperationPoller for Workflows Executions."""

  def __init__(self, workflow_execution):
    """Creates the execution poller.

    Args:
      workflow_execution: the Workflows Executions API client used to get the
        execution resource.
    """
    self.workflow_execution = workflow_execution

  def IsDone(self, execution):
    """Overrides."""
    return execution.state.name != 'ACTIVE' and execution.state.name != 'QUEUED'

  def Poll(self, execution_ref):
    """Overrides."""
    return self.workflow_execution.Get(execution_ref)

  def GetResult(self, execution):
    """Overrides."""
    return execution


def _ExtractErrorMessage(error):
  """Extracts the error message for better format."""

  if hasattr(error, 'code'):
    code_name = codes.Code(error.code).name
  else:
    code_name = 'UNKNOWN'

  if hasattr(error, 'message'):
    error_message = error.message
  else:
    # Returns the entire error object if no message field is available.
    error_message = error

  return '[{code}] {message}'.format(code=code_name, message=error_message)
