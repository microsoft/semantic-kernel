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

"""Utilities to support long running operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import time

from apitools.base.py import encoding
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import retry
import six


_TIMEOUT_MESSAGE = (
    'The operations may still be underway remotely and may still succeed; '
    'use gcloud list and describe commands or '
    'https://console.developers.google.com/ to check resource state.')


class TimeoutError(exceptions.Error):
  pass


class AbortWaitError(exceptions.Error):
  pass


class OperationError(exceptions.Error):
  pass


class OperationPoller(six.with_metaclass(abc.ABCMeta, object)):
  """Interface for defining operation which can be polled and waited on.

  This construct manages operation_ref, operation and result abstract objects.
  Operation_ref is an identifier for operation which is a proxy for result
  object. OperationPoller has three responsibilities:
    1. Given operation object determine if it is done.
    2. Given operation_ref fetch operation object
    3. Given operation object fetch result object
  """

  @abc.abstractmethod
  def IsDone(self, operation):
    """Given result of Poll determines if result is done.

    Args:
      operation: object representing operation returned by Poll method.

    Returns:

    """
    return True

  @abc.abstractmethod
  def Poll(self, operation_ref):
    """Retrieves operation given its reference.

    Args:
      operation_ref: str, some id for operation.

    Returns:
      object which represents operation.
    """
    return None

  @abc.abstractmethod
  def GetResult(self, operation):
    """Given operation message retrieves result it represents.

    Args:
      operation: object, representing operation returned by Poll method.
    Returns:
      some object created by given operation.
    """
    return None


class CloudOperationPoller(OperationPoller):
  """Manages a longrunning Operations.

  See https://cloud.google.com/speech/reference/rpc/google.longrunning
  """

  def __init__(self, result_service, operation_service):
    """Sets up poller for cloud operations.

    Args:
      result_service: apitools.base.py.base_api.BaseApiService, api service for
        retrieving created result of initiated operation.
      operation_service: apitools.base.py.base_api.BaseApiService, api service
        for retrieving information about ongoing operation.

      Note that result_service and operation_service Get request must have
      single attribute called 'name'.
    """
    self.result_service = result_service
    self.operation_service = operation_service

  def IsDone(self, operation):
    """Overrides."""
    if operation.done:
      if operation.error:
        raise OperationError(operation.error.message)
      return True
    return False

  def Poll(self, operation_ref):
    """Overrides.

    Args:
      operation_ref: googlecloudsdk.core.resources.Resource.

    Returns:
      fetched operation message.
    """
    request_type = self.operation_service.GetRequestType('Get')
    return self.operation_service.Get(
        request_type(name=operation_ref.RelativeName()))

  def GetResult(self, operation):
    """Overrides.

    Args:
      operation: api_name_messages.Operation.

    Returns:
      result of result_service.Get request.
    """
    request_type = self.result_service.GetRequestType('Get')
    response_dict = encoding.MessageToPyValue(operation.response)
    return self.result_service.Get(request_type(name=response_dict['name']))


class CloudOperationPollerNoResources(OperationPoller):
  """Manages longrunning Operations for Cloud API that creates no resources.

  See https://cloud.google.com/speech/reference/rpc/google.longrunning
  """

  # TODO(b/62478975): Remove get_name_func when ML API operation names
  # are compatible with gcloud parsing, and use RelativeName instead.
  def __init__(self, operation_service, get_name_func=None):
    """Sets up poller for cloud operations.

    Args:
      operation_service: apitools.base.py.base_api.BaseApiService, api service
        for retrieving information about ongoing operation.

        Note that the operation_service Get request must have a
        single attribute called 'name'.
      get_name_func: the function to use to get the name from the operation_ref.
        This is to allow polling with non-traditional operation resource names.
        If the resource name is compatible with gcloud parsing, use
        `lambda x: x.RelativeName()`.
    """
    self.operation_service = operation_service
    self.get_name = get_name_func or (lambda x: x.RelativeName())

  def IsDone(self, operation):
    """Overrides."""
    if operation.done:
      if operation.error:
        raise OperationError(operation.error.message)
      return True
    return False

  def Poll(self, operation_ref):
    """Overrides.

    Args:
      operation_ref: googlecloudsdk.core.resources.Resource.

    Returns:
      fetched operation message.
    """
    request_type = self.operation_service.GetRequestType('Get')
    return self.operation_service.Get(
        request_type(name=self.get_name(operation_ref)))

  def GetResult(self, operation):
    """Overrides to get the response from the completed operation.

    Args:
      operation: api_name_messages.Operation.

    Returns:
      the 'response' field of the Operation.
    """
    return operation.response


def WaitFor(poller,
            operation_ref,
            message=None,
            custom_tracker=None,
            tracker_update_func=None,
            pre_start_sleep_ms=1000,
            max_retrials=None,
            max_wait_ms=1800000,
            exponential_sleep_multiplier=1.4,
            jitter_ms=1000,
            wait_ceiling_ms=180000,
            sleep_ms=2000):
  """Waits for poller.Poll and displays pending operation spinner.

  Args:
    poller: OperationPoller, poller to use during retrials.
    operation_ref: object, passed to operation poller poll method.
    message: str, string to display for default progress_tracker.
    custom_tracker: ProgressTracker, progress_tracker to use for display.
    tracker_update_func: func(tracker, result, status), tracker update function.
    pre_start_sleep_ms: int, Time to wait before making first poll request.
    max_retrials: int, max number of retrials before raising RetryException.
    max_wait_ms: int, number of ms to wait before raising WaitException.
    exponential_sleep_multiplier: float, factor to use on subsequent retries.
    jitter_ms: int, random (up to the value) additional sleep between retries.
    wait_ceiling_ms: int, Maximum wait between retries.
    sleep_ms: int or iterable: for how long to wait between trials.

  Returns:
    poller.GetResult(operation).

  Raises:
    AbortWaitError: if ctrl-c was pressed.
    TimeoutError: if retryer has finished without being done.
  """
  aborted_message = 'Aborting wait for operation {0}.\n'.format(operation_ref)
  try:
    with progress_tracker.ProgressTracker(
        message, aborted_message=aborted_message
    ) if not custom_tracker else custom_tracker as tracker:

      if pre_start_sleep_ms:
        _SleepMs(pre_start_sleep_ms)

      def _StatusUpdate(result, status):
        if tracker_update_func:
          tracker_update_func(tracker, result, status)
        else:
          tracker.Tick()

      operation = PollUntilDone(
          poller, operation_ref, max_retrials, max_wait_ms,
          exponential_sleep_multiplier, jitter_ms, wait_ceiling_ms,
          sleep_ms, _StatusUpdate)

  except retry.WaitException:
    raise TimeoutError(
        'Operation {0} has not finished in {1} seconds. {2}'
        .format(operation_ref, max_wait_ms // 1000, _TIMEOUT_MESSAGE))
  except retry.MaxRetrialsException as e:
    raise TimeoutError(
        'Operation {0} has not finished in {1} seconds '
        'after max {2} retrials. {3}'
        .format(operation_ref,
                e.state.time_passed_ms // 1000,
                e.state.retrial,
                _TIMEOUT_MESSAGE))

  return poller.GetResult(operation)


def PollUntilDone(poller, operation_ref,
                  max_retrials=None,
                  max_wait_ms=1800000,
                  exponential_sleep_multiplier=1.4,
                  jitter_ms=1000,
                  wait_ceiling_ms=180000,
                  sleep_ms=2000,
                  status_update=None):
  """Waits for poller.Poll to complete.

  Note that this *does not* print nice messages to stderr for the user; most
  callers should use WaitFor instead for the best UX unless there's a good
  reason not to print.

  Args:
    poller: OperationPoller, poller to use during retrials.
    operation_ref: object, passed to operation poller poll method.
    max_retrials: int, max number of retrials before raising RetryException.
    max_wait_ms: int, number of ms to wait before raising WaitException.
    exponential_sleep_multiplier: float, factor to use on subsequent retries.
    jitter_ms: int, random (up to the value) additional sleep between retries.
    wait_ceiling_ms: int, Maximum wait between retries.
    sleep_ms: int or iterable: for how long to wait between trials.
    status_update: func(result, state) called right after each trial.

  Returns:
    The return value from poller.Poll.
  """

  retryer = retry.Retryer(
      max_retrials=max_retrials,
      max_wait_ms=max_wait_ms,
      exponential_sleep_multiplier=exponential_sleep_multiplier,
      jitter_ms=jitter_ms,
      wait_ceiling_ms=wait_ceiling_ms,
      status_update_func=status_update)

  def _IsNotDone(operation, unused_state):
    return not poller.IsDone(operation)

  operation = retryer.RetryOnResult(
      func=poller.Poll,
      args=(operation_ref,),
      should_retry_if=_IsNotDone,
      sleep_ms=sleep_ms)

  return operation


def _SleepMs(miliseconds):
  time.sleep(miliseconds / 1000)
