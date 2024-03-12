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
"""Utilities for Edge ML API long-running operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.edgeml import util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import resources


_MAX_WAIT_TIME_MS = 10 * 60 * 1000  # 10 minutes.

_WAITING_MESSAGE = {
    'analyze': 'Analyzing Edge machine learning model. [{}]',
    'compile': 'Optimizing Edge machine learning model for Edge TPU. [{}]',
    'convert': 'Converting SavedModel to TF Lite model. [{}]',
}


class OperationsClient(object):
  """Client for the Edge ML operations API.

  Attributes:
    client: Generated Edge ML API client.
    messages: Generated Edge ML API messages.
  """

  def __init__(self, client=None, messages=None):
    self.client = client or util.GetClientInstance()
    self.messages = messages or util.GetMessagesModule(client)
    self._service = self.client.operations

  def Get(self, operation_ref):
    """Calls get method for long-running operations.

    Args:
      operation_ref: Ref to long-running operation.

    Returns:
      edgeml.Operation message.
    """
    return self.client.projects_operations.Get(
        self.messages.EdgemlOperationsGetRequest(
            name=operation_ref.RelativeName()))

  def WaitForOperation(self, operation):
    """Wait until the operation is complete or times out.

    Args:
      operation: The operation resource to wait on.

    Returns:
      The operation resource when it has completed.

    Raises:
      OperationTimeoutError: When the operation polling times out.
      OperationError: When the operation completed with an error.
    """
    poller = waiter.CloudOperationPollerNoResources(self._service)
    operation_ref = resources.REGISTRY.Parse(
        operation.name, collection='edgeml.operations')
    operation_type = operation_ref.Name().split('/')[0]
    message = _WAITING_MESSAGE.get(operation_type, 'Waiting for operation [{}]')
    return waiter.WaitFor(
        poller,
        operation_ref,
        message,
        pre_start_sleep_ms=1000,
        max_wait_ms=_MAX_WAIT_TIME_MS,
        exponential_sleep_multiplier=None,
        jitter_ms=None,
        wait_ceiling_ms=None,
        sleep_ms=5000)
