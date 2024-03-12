# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Common helper methods for Services commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.api_lib.util import apis_internal
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import transport
from googlecloudsdk.core.credentials import transports
from googlecloudsdk.core.util import retry


OP_BASE_CMD = 'gcloud services operations '
OP_DESCRIBE_CMD = OP_BASE_CMD + 'describe {0}'
OP_WAIT_CMD = OP_BASE_CMD + 'wait {0}'
SERVICES_COLLECTION = 'servicemanagement.services'


def GetMessagesModule():
  # pylint:disable=protected-access
  return apis_internal._GetMessagesModule('servicemanagement', 'v1')


def GetClientInstance():
  """Get a client instance for service management without resource quota."""
  # pylint:disable=protected-access
  # Specifically disable resource quota in all cases for service management.
  # We need to use this API to turn on APIs and sometimes the user doesn't have
  # this API turned on. We should always used the shared project to do this
  # so we can bootstrap users getting the appropriate APIs enabled. If the user
  # has explicitly set the quota project, then respect that.

  enable_resource_quota = (
      properties.VALUES.billing.quota_project.IsExplicitlySet())
  http_client = transports.GetApitoolsTransport(
      response_encoding=transport.ENCODING,
      enable_resource_quota=enable_resource_quota)
  return apis_internal._GetClientInstance(
      'servicemanagement', 'v1', http_client=http_client)


def GetValidatedProject(project_id):
  """Validate the project ID, if supplied, otherwise return the default project.

  Args:
    project_id: The ID of the project to validate. If None, gcloud's default
                project's ID will be returned.

  Returns:
    The validated project ID.
  """
  if project_id:
    properties.VALUES.core.project.Validate(project_id)
  else:
    project_id = properties.VALUES.core.project.Get(required=True)
  return project_id


def WaitOperation(name, get_op_func):
  """Wait till the operation is done.

  Args:
    name: The name of operation.
    get_op_func: The function that gets the operation.

  Raises:
    exceptions.OperationErrorException: when the getting operation API fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the service.

  Returns:
    The result of the operation
  """

  def _CheckOp(name, result):
    op = get_op_func(name)
    if op.done:
      result.append(op)
    return not op.done

  # Wait for no more than 30 minutes while retrying the Operation retrieval
  result = []
  try:
    retry.Retryer(
        exponential_sleep_multiplier=1.1,
        wait_ceiling_ms=10000,
        max_wait_ms=30 * 60 * 1000).RetryOnResult(
            _CheckOp, [name, result], should_retry_if=True, sleep_ms=2000)
  except retry.MaxRetrialsException:
    raise exceptions.TimeoutError('Timed out while waiting for '
                                  'operation {0}. Note that the operation '
                                  'is still pending.'.format(name))
  return result[0] if result else None


def PrintOperation(op):
  """Print the operation.

  Args:
    op: The long running operation.

  Raises:
    OperationErrorException: if the operation fails.

  Returns:
    Nothing.
  """
  if not op.done:
    log.status.Print('Operation "{0}" is still in progress.'.format(op.name))
    return
  if op.error:
    raise exceptions.OperationErrorException(
        'The operation "{0}" resulted in a failure "{1}".\nDetails: "{2}".'.
        format(op.name, op.error.message, op.error.details))
  log.status.Print('Operation "{0}" finished successfully.'.format(op.name))


def PrintOperationWithResponse(op):
  """Print the operation with response.

  Args:
    op: The long running operation.

  Raises:
    OperationErrorException: if the operation fails.

  Returns:
    Nothing.
  """
  if not op.done:
    log.status.Print('Operation "{0}" is still in progress.'.format(op.name))
    return
  if op.error:
    raise exceptions.OperationErrorException(
        'The operation "{0}" resulted in a failure "{1}".\nDetails: "{2}".'.
        format(op.name, op.error.message, op.error.details))
  if op.response:
    log.status.Print('Operation [{0}] complete. Result: {1}'.format(
        op.name,
        json.dumps(
            encoding.MessageToDict(op.response),
            sort_keys=True,
            indent=4,
            separators=(',', ':'))))
  else:
    log.status.Print('Operation "{0}" finished successfully.'.format(op.name))
