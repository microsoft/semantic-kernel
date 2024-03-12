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
"""Wrapper around serverless_operations DeleteFoo for surfaces."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
from googlecloudsdk.command_lib.run import platforms
from googlecloudsdk.core.console import progress_tracker


class DeletionPoller(waiter.OperationPoller):
  """Polls for deletion of a resource."""

  def __init__(self, getter):
    """Supply getter as the resource getter."""
    self._getter = getter
    self._ret = None

  def IsDone(self, obj):
    return obj is None or obj.conditions.IsFailed()

  def Poll(self, ref):
    try:
      self._ret = self._getter(ref)
    except api_exceptions.HttpNotFoundError:  # Some getters let this through.
      self._ret = None
    return self._ret

  def GetMessage(self):
    if (self._ret and self._ret.conditions and
        not self._ret.conditions.IsReady()):
      return self._ret.conditions.DescriptiveMessage() or ''
    return ''

  def GetResult(self, obj):
    return obj


def Delete(ref, getter, deleter, async_):
  """Deletes a resource for a surface, including a pretty progress tracker."""
  if AsyncOrDefault(async_):
    deleter(ref)
    return
  poller = DeletionPoller(getter)
  with progress_tracker.ProgressTracker(
      message='Deleting [{}]'.format(ref.Name()),
      detail_message_callback=poller.GetMessage):
    deleter(ref)
    res = waiter.PollUntilDone(poller, ref)
    if res:
      if poller.GetMessage():
        raise serverless_exceptions.DeletionFailedError(
            'Failed to delete [{}]: {}.'.format(ref.Name(),
                                                poller.GetMessage()))
      else:
        raise serverless_exceptions.DeletionFailedError(
            'Failed to delete [{}].'.format(ref.Name()))


def AsyncOrDefault(async_):
  if async_ is None:
    return platforms.GetPlatform() != platforms.PLATFORM_MANAGED
  return async_
