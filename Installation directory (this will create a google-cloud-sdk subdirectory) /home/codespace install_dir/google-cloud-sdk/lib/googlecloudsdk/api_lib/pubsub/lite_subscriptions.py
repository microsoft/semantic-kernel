# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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

"""Utilities for Pub/Sub Lite subscriptions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from concurrent import futures
import time
from typing import Optional

from google.cloud.pubsublite import cloudpubsub
from google.cloud.pubsublite import types
from google.pubsub_v1 import PubsubMessage
from googlecloudsdk.command_lib.pubsub import lite_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import gapic_util
from googlecloudsdk.core import log
from six.moves import queue

_MAX_INT64 = 0x7FFFFFFFFFFFFFFF


class SubscribeOperationException(exceptions.Error):
  """Error when something went wrong while subscribing."""


def GetDefaultSubscriberClient():
  return cloudpubsub.SubscriberClient(
      credentials=gapic_util.GetGapicCredentials())


class SubscriberClient(object):
  """GCloud wrapper client for a Pub/Sub Lite subscriber."""

  def __init__(self,
               subscription_resource,
               partitions,
               max_messages,
               auto_ack,
               client=None):
    self._client = client or GetDefaultSubscriberClient()
    self._messages = queue.Queue()
    self._subscription = self._SubscriptionResourceToPath(subscription_resource)
    self._partitions = {types.Partition(partition) for partition in partitions}
    self._flow_control_settings = types.FlowControlSettings(
        messages_outstanding=max_messages,
        bytes_outstanding=_MAX_INT64,
    )
    self._auto_ack = auto_ack
    self._pull_future = None

  def __enter__(self):
    self._client.__enter__()
    self._pull_future = self._client.subscribe(
        self._subscription,
        callback=self._messages.put,
        per_partition_flow_control_settings=self._flow_control_settings,
        fixed_partitions=self._partitions)
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    time.sleep(1)  # Wait 1 second to ensure all acks have been processed
    if not self._pull_future.done():
      try:
        # Cancel the streaming pull future and get the result to prevent
        # logging an abandoned future.
        self._pull_future.cancel()
        self._pull_future.result()
      except futures.CancelledError:
        pass
    self._client.__exit__(exc_type, exc_value, traceback)

  def _SubscriptionResourceToPath(self, resource):
    return types.SubscriptionPath(
        project=lite_util.ProjectIdToProjectNumber(resource.projectsId),
        location=lite_util.LocationToZoneOrRegion(resource.locationsId),
        name=resource.subscriptionsId)

  def _RaiseIfFailed(self):
    if self._pull_future.done():
      e = self._pull_future.exception()
      if e:
        raise SubscribeOperationException(
            'Subscribe operation failed with error: {error}'.format(error=e))
      log.debug('The streaming pull future completed unexpectedly without '
                'raising an exception.')
      raise exceptions.InternalError(
          'The subscribe stream terminated unexpectedly.')

  def Pull(self) -> Optional[PubsubMessage]:
    """Pulls and optionally acks a message from the provided subscription.

    Returns:
      A PubsubMessage pulled from the subscription.
    """
    self._RaiseIfFailed()
    try:
      message = self._messages.get(timeout=1)
      if self._auto_ack:
        message.ack()
      return message
    except queue.Empty:
      return None
