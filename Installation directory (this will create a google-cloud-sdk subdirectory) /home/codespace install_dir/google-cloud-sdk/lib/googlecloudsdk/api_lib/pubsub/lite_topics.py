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

"""Utilities for Pub/Sub Lite topics."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from google.cloud.pubsublite import cloudpubsub
from google.cloud.pubsublite import types
from google.cloud.pubsublite.cloudpubsub import message_transforms
from googlecloudsdk.api_lib.pubsub import topics
from googlecloudsdk.command_lib.pubsub import lite_util
from googlecloudsdk.core import gapic_util
from googlecloudsdk.core.util import http_encoding


def GetDefaultPublisherClient():
  return cloudpubsub.PublisherClient(
      credentials=gapic_util.GetGapicCredentials())


class PublisherClient(object):
  """Wrapper client for a Pub/Sub Lite publisher."""

  def __init__(self, client=None):
    self._client = client or GetDefaultPublisherClient()

  def __enter__(self):
    self._client.__enter__()
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self._client.__exit__(exc_type, exc_value, traceback)

  def _TopicResourceToPath(self, resource):
    return types.TopicPath(
        project=lite_util.ProjectIdToProjectNumber(resource.projectsId),
        location=lite_util.LocationToZoneOrRegion(resource.locationsId),
        name=resource.topicsId)

  def Publish(self,
              topic_resource,
              message=None,
              ordering_key=None,
              attributes=None,
              event_time=None):
    """Publishes a message to the specified Pub/Sub Lite topic.

    Args:
      topic_resource: The pubsub.lite_topic resource to publish to.
      message: The string message to publish.
      ordering_key: The key for ordering delivery to subscribers.
      attributes: A dict of attributes to attach to the message.
      event_time: A user-specified event timestamp.

    Raises:
      EmptyMessageException: if the message is empty.
      PublishOperationException: if the publish operation is not successful.

    Returns:
      The messageId of the published message, containing the Partition and
      Offset.
    """
    if not message and not attributes:
      raise topics.EmptyMessageException(
          'You cannot send an empty message. You must specify either a '
          'MESSAGE, one or more ATTRIBUTE, or both.')
    topic_path = self._TopicResourceToPath(topic_resource)
    attributes = attributes or {}
    if event_time:
      attributes[message_transforms.PUBSUB_LITE_EVENT_TIME] = (
          message_transforms.encode_attribute_event_time(event_time))
    try:
      return types.MessageMetadata.decode(
          self._client.publish(topic_path, http_encoding.Encode(message),
                               ordering_key, **attributes).result())
    except Exception as e:
      raise topics.PublishOperationException(
          'Publish operation failed with error: {error}'.format(error=e))
