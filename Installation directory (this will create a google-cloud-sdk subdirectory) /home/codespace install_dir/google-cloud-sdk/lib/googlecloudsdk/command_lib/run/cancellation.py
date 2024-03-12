# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Wrapper around serverless_operations CancelFoo for surfaces."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
from googlecloudsdk.core.console import progress_tracker


class CancellationPoller(waiter.OperationPoller):
  """Polls for cancellation of a resource."""

  def __init__(self, getter):
    """Supply getter as the resource getter."""
    self._getter = getter
    self._ret = None

  def IsDone(self, obj):
    return obj is None or obj.conditions.IsTerminal()

  def Poll(self, ref):
    self._ret = self._getter(ref)
    return self._ret

  def GetMessage(self):
    if self._ret and self._ret.conditions:
      return self._ret.conditions.DescriptiveMessage() or ''
    return ''

  def GetResult(self, obj):
    return obj


def Cancel(ref, getter, canceller, async_):
  """Cancels a resource for a surface, including a pretty progress tracker."""
  if async_:
    canceller(ref)
    return
  poller = CancellationPoller(getter)
  with progress_tracker.ProgressTracker(
      message='Cancelling [{}]'.format(ref.Name()),
      detail_message_callback=poller.GetMessage,
  ):
    canceller(ref)
    res = waiter.PollUntilDone(poller, ref)
    if not res:
      raise serverless_exceptions.CancellationFailedError(
          'Failed to cancel [{}].'.format(ref.Name())
      )
    if res.conditions.IsReady():
      raise serverless_exceptions.CancellationFailedError(
          '[{}] has completed successfully before it could be cancelled.'
          .format(ref.Name())
      )
    if res.conditions.TerminalConditionReason() != 'Cancelled':
      if poller.GetMessage():
        raise serverless_exceptions.CancellationFailedError(
            'Failed to cancel [{}]: {}'.format(ref.Name(), poller.GetMessage())
        )
      else:
        raise serverless_exceptions.CancellationFailedError(
            'Failed to cancel [{}].'.format(ref.Name())
        )
