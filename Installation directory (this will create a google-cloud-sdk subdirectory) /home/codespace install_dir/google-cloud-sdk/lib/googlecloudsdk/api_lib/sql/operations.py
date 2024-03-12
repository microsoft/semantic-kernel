# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Common utility functions for sql operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import time

from apitools.base.py import exceptions as base_exceptions

from googlecloudsdk.api_lib.sql import exceptions
from googlecloudsdk.core.console import progress_tracker as console_progress_tracker
from googlecloudsdk.core.util import retry

_MS_PER_SECOND = 1000
# Default timeout for operations.
_OPERATION_TIMEOUT_SECONDS = 600


class _BaseOperations(object):
  """Common utility functions for sql operations."""

  _PRE_START_SLEEP_SEC = 1
  _INITIAL_SLEEP_MS = 2000
  _WAIT_CEILING_MS = 20000
  _HTTP_MAX_RETRY_MS = 2000

  @classmethod
  def WaitForOperation(cls,
                       sql_client,
                       operation_ref,
                       message,
                       max_wait_seconds=_OPERATION_TIMEOUT_SECONDS):
    """Wait for a Cloud SQL operation to complete.

    No operation is done instantly. Wait for it to finish following this logic:
    First wait 1s, then query, then retry waiting exponentially more from 2s.
    We want to limit to 20s between retries to maintain some responsiveness.
    Finally, we want to limit the whole process to a conservative 300s. If we
    get to that point it means something is wrong and we can throw an exception.

    Args:
      sql_client: apitools.BaseApiClient, The client used to make requests.
      operation_ref: resources.Resource, A reference for the operation to poll.
      message: str, The string to print while polling.
      max_wait_seconds: integer or None, the number of seconds before the
          poller times out.

    Returns:
      Operation: The polled operation.

    Raises:
      OperationError: If the operation has an error code, is in UNKNOWN state,
          or if the operation takes more than max_wait_seconds when a value is
          specified.
    """

    def ShouldRetryFunc(result, state):
      # In case of HttpError, retry for up to _HTTP_MAX_RETRY_MS at most.
      if isinstance(result, base_exceptions.HttpError):
        if state.time_passed_ms > _BaseOperations._HTTP_MAX_RETRY_MS:
          raise result
        return True
      # In case of other Exceptions, raise them immediately.
      if isinstance(result, Exception):
        raise result
      # Otherwise let the retryer do it's job until the Operation is done.
      is_operation_done = result.status == sql_client.MESSAGES_MODULE.Operation.StatusValueValuesEnum.DONE
      return not is_operation_done

    # Set the max wait time.
    max_wait_ms = None
    if max_wait_seconds:
      max_wait_ms = max_wait_seconds * _MS_PER_SECOND
    with console_progress_tracker.ProgressTracker(
        message, autotick=False) as pt:
      time.sleep(_BaseOperations._PRE_START_SLEEP_SEC)
      retryer = retry.Retryer(
          exponential_sleep_multiplier=2,
          max_wait_ms=max_wait_ms,
          wait_ceiling_ms=_BaseOperations._WAIT_CEILING_MS)
      try:
        return retryer.RetryOnResult(
            cls.GetOperation, [sql_client, operation_ref],
            {'progress_tracker': pt},
            should_retry_if=ShouldRetryFunc,
            sleep_ms=_BaseOperations._INITIAL_SLEEP_MS)
      except retry.WaitException:
        raise exceptions.OperationError(
            ('Operation {0} is taking longer than expected. You can continue '
             'waiting for the operation by running `{1}`').format(
                 operation_ref, cls.GetOperationWaitCommand(operation_ref)))


class OperationsV1Beta4(_BaseOperations):
  """Common utility functions for sql operations V1Beta4."""

  @staticmethod
  def GetOperation(sql_client, operation_ref, progress_tracker=None):
    """Helper function for getting the status of an operation for V1Beta4 API.

    Args:
      sql_client: apitools.BaseApiClient, The client used to make requests.
      operation_ref: resources.Resource, A reference for the operation to poll.
      progress_tracker: progress_tracker.ProgressTracker, A reference for the
          progress tracker to tick, in case this function is used in a Retryer.

    Returns:
      Operation: if the operation succeeded without error or  is not yet done.
      OperationError: If the operation has an error code or is in UNKNOWN state.
      Exception: Any other exception that can occur when calling Get
    """

    if progress_tracker:
      progress_tracker.Tick()
    try:
      op = sql_client.operations.Get(
          sql_client.MESSAGES_MODULE.SqlOperationsGetRequest(
              project=operation_ref.project, operation=operation_ref.operation))
    except Exception as e:  # pylint:disable=broad-except
      # Since we use this function in a retryer.RetryOnResult block, where we
      # retry for different exceptions up to different amounts of time, we
      # have to catch all exceptions here and return them.
      return e
    if op.error and op.error.errors:
      error_object = op.error.errors[0]
      # If there's an error message to show, show it in addition to the code.
      error = '[{}]'.format(error_object.code)
      if error_object.message:
        error += ' ' + error_object.message
      return exceptions.OperationError(error)
    if op.status == sql_client.MESSAGES_MODULE.Operation.StatusValueValuesEnum.SQL_OPERATION_STATUS_UNSPECIFIED:
      return exceptions.OperationError(op.status)
    return op

  @staticmethod
  def GetOperationWaitCommand(operation_ref):
    return 'gcloud beta sql operations wait --project {0} {1}'.format(
        operation_ref.project, operation_ref.operation)
