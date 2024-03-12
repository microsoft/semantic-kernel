# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Base class for gkemulticloud API clients for operations."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.container.gkemulticloud import client
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.core import log
from googlecloudsdk.core.console import progress_tracker


class OperationsClient(client.ClientBase):
  """Client for managing LROs."""

  def __init__(self, **kwargs):
    super(OperationsClient, self).__init__(**kwargs)
    self._service = self._client.projects_locations_operations
    self._list_result_field = 'operations'

  def Wait(self, operation_ref, message):
    """Waits for an LRO to complete.

    Args:
      operation_ref: object, passed to operation poller poll method.
      message: str, string to display for the progress tracker.
    """
    poller = _Poller(self._service)
    waiter.WaitFor(
        poller=poller,
        operation_ref=operation_ref,
        custom_tracker=progress_tracker.ProgressTracker(
            message=message,
            detail_message_callback=poller.GetDetailMessage,
            aborted_message='Aborting wait for operation {}.\n'.format(
                operation_ref
            ),
        ),
        wait_ceiling_ms=constants.MAX_LRO_POLL_INTERVAL_MS,
        max_wait_ms=constants.MAX_LRO_WAIT_MS,
    )

  def Cancel(self, operation_ref):
    """Cancels an ongoing LRO.

    Args:
      operation_ref: object, operation resource to be canceled.
    """
    request_type = self._service.GetRequestType('Cancel')
    self._service.Cancel(request_type(name=operation_ref.RelativeName()))


class _Poller(waiter.CloudOperationPollerNoResources):
  """Poller for Anthos Multi-cloud operations.

  The poller stores the status detail from the operation message to update
  the progress tracker.
  """

  def __init__(self, operation_service):
    """See base class."""
    self.operation_service = operation_service
    self.status_detail = None
    self.last_error_detail = None

  def Poll(self, operation_ref):
    """See base class."""
    request_type = self.operation_service.GetRequestType('Get')
    operation = self.operation_service.Get(
        request_type(name=operation_ref.RelativeName())
    )
    if operation.metadata is not None:
      metadata = encoding.MessageToPyValue(operation.metadata)
      if 'statusDetail' in metadata:
        self.status_detail = metadata['statusDetail']
      if 'errorDetail' in metadata:
        error_detail = metadata['errorDetail']
        if error_detail != self.last_error_detail:
          log.error(error_detail)
        self.last_error_detail = error_detail
    return operation

  def GetDetailMessage(self):
    return self.status_detail
