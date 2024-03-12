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
"""CRM API Operations utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import time

from apitools.base.py import encoding
from apitools.base.py import exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import progress_tracker as tracker
from googlecloudsdk.core.util import retry

OPERATIONS_API_V1 = 'v1'
OPERATIONS_API_V3 = 'v3'


class OperationError(exceptions.Error):
  pass


def OperationsClient(version=OPERATIONS_API_V1):
  return apis.GetClientInstance('cloudresourcemanager', version)


def OperationsRegistry(version=OPERATIONS_API_V1):
  registry = resources.REGISTRY.Clone()
  registry.RegisterApiByName('cloudresourcemanager', version)
  return registry


def OperationsService(version=OPERATIONS_API_V1):
  return OperationsClient(version).operations


def OperationsMessages(version=OPERATIONS_API_V1):
  return apis.GetMessagesModule('cloudresourcemanager', version)


def OperationNameToId(operation_name):
  return operation_name[len('operations/'):]


def OperationIdToName(operation_id):
  return 'operations/{0}'.format(operation_id)


def GetOperation(operation_id):
  return OperationsService().Get(
      OperationsMessages().CloudresourcemanagerOperationsGetRequest(
          operationsId=operation_id))


def GetOperationV3(operation_id):
  return OperationsService(OPERATIONS_API_V3).Get(
      OperationsMessages(
          OPERATIONS_API_V3).CloudresourcemanagerOperationsGetRequest(
              name=OperationIdToName(operation_id)))


def WaitForOperation(operation):
  wait_message = 'Waiting for [{0}] to finish'.format(operation.name)
  with tracker.ProgressTracker(wait_message, autotick=False) as pt:
    retryer = OperationRetryer()
    poller = OperationPoller(pt)
    return retryer.RetryPollOperation(poller, operation)


def ExtractOperationResponse(operation, response_message_type):
  raw_dict = encoding.MessageToDict(operation.response)
  return encoding.DictToMessage(raw_dict, response_message_type)


def ToOperationResponse(message):
  raw_dict = encoding.MessageToDict(message)
  return encoding.DictToMessage(raw_dict,
                                OperationsMessages().Operation.ResponseValue)


class OperationRetryer(object):
  """A wrapper around a Retryer that works with CRM operations.

  Uses predefined constants for retry timing, so all CRM operation commands can
  share their retry timing settings.
  """

  def __init__(self,
               pre_start_sleep=lambda: time.sleep(1),
               max_retry_ms=2000,
               max_wait_ms=300000,
               wait_ceiling_ms=20000,
               first_retry_sleep_ms=2000):
    self._pre_start_sleep = pre_start_sleep
    self._max_retry_ms = max_retry_ms
    self._max_wait_ms = max_wait_ms
    self._wait_ceiling_ms = wait_ceiling_ms
    self._first_retry_sleep_ms = first_retry_sleep_ms

  def RetryPollOperation(self, operation_poller, operation):
    self._pre_start_sleep()
    return self._Retryer().RetryOnResult(
        lambda: operation_poller.Poll(operation),
        should_retry_if=self._ShouldRetry,
        sleep_ms=self._first_retry_sleep_ms)

  def _Retryer(self):
    return retry.Retryer(
        exponential_sleep_multiplier=2,
        max_wait_ms=self._max_wait_ms,
        wait_ceiling_ms=self._wait_ceiling_ms)

  def _ShouldRetry(self, result, state):
    if isinstance(result, exceptions.HttpError):
      return self._CheckTimePassedBelowMax(result, state)
    return self._CheckResultNotException(result)

  def _CheckTimePassedBelowMax(self, result, state):
    if state.time_passed_ms > self._max_retry_ms:
      raise result
    return True

  def _CheckResultNotException(self, result):
    if isinstance(result, Exception):
      raise result
    return not result.done


class OperationPoller(object):

  def __init__(self, progress_tracker=None):
    self._progress_tracker = progress_tracker

  def Poll(self, operation):
    if self._progress_tracker:
      self._progress_tracker.Tick()
    latest = GetOperation(OperationNameToId(operation.name))
    if latest.done and latest.error:
      raise OperationFailedException(latest)
    return latest


class OperationFailedException(core_exceptions.Error):

  def __init__(self, operation_with_error):
    op_id = OperationNameToId(operation_with_error.name)
    error_code = operation_with_error.error.code
    error_message = operation_with_error.error.message
    message = 'Operation [{0}] failed: {1}: {2}'.format(op_id, error_code,
                                                        error_message)
    super(OperationFailedException, self).__init__(message)


def GetUri(resource):
  """Returns the uri for resource."""
  operation_id = OperationNameToId(resource.name)
  operation_ref = OperationsRegistry().Parse(
      None,
      params={'operationsId': operation_id},
      collection='cloudresourcemanager.operations')
  return operation_ref.SelfLink()
