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
"""Utilities for Eventarc channel connections API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.eventarc import common
from googlecloudsdk.api_lib.eventarc import common_publishing
from googlecloudsdk.api_lib.eventarc.base import EventarcClientBase
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import resources


def GetChannelConnectionsURI(resource):
  channel_connections = resources.REGISTRY.ParseRelativeName(
      resource.name,
      collection='eventarc.projects.locations.channelConnections')
  return channel_connections.SelfLink()


class ChannelConnectionClientV1(EventarcClientBase):
  """Channel connections client for Eventarc API V1."""

  def __init__(self):
    super(ChannelConnectionClientV1,
          self).__init__(common.API_NAME, common.API_VERSION_1,
                         'Channel Connection')

    # Eventarc Client
    client = apis.GetClientInstance(common.API_NAME, common.API_VERSION_1)
    self._messages = client.MESSAGES_MODULE
    self._service = client.projects_locations_channelConnections

    # Eventarc Publishing client
    publishing_client = apis.GetClientInstance(common_publishing.API_NAME,
                                               common_publishing.API_VERSION_1)
    self._publishing_messages = publishing_client.MESSAGES_MODULE
    self._publishing_service = publishing_client.projects_locations_channelConnections

  def Create(self, channel_connection_ref, channel_connection_message):
    """Creates a new Channel Connection.

    Args:
      channel_connection_ref: Resource, the Channel connection to create.
      channel_connection_message: Channel connection, the channel connection
        message that holds channel's reference, activation token, etc.

    Returns:
      A long-running operation for create.
    """
    create_req = self._messages.EventarcProjectsLocationsChannelConnectionsCreateRequest(
        parent=channel_connection_ref.Parent().RelativeName(),
        channelConnection=channel_connection_message,
        channelConnectionId=channel_connection_ref.Name())
    return self._service.Create(create_req)

  def Delete(self, channel_connection_ref):
    """Deletes the specified Channel Connection.

    Args:
      channel_connection_ref: Resource, the Channel Connection to delete.

    Returns:
      A long-running operation for delete.
    """
    delete_req = self._messages.EventarcProjectsLocationsChannelConnectionsDeleteRequest(
        name=channel_connection_ref.RelativeName())
    return self._service.Delete(delete_req)

  def Get(self, channel_connection_ref):
    """Gets the requested Channel Connection.

    Args:
      channel_connection_ref: Resource, the Channel Connection to get.

    Returns:
      The Channel Connection message.
    """
    get_req = self._messages.EventarcProjectsLocationsChannelConnectionsGetRequest(
        name=channel_connection_ref.RelativeName())
    return self._service.Get(get_req)

  def List(self, location_ref, limit, page_size):
    """List available channel connections in location.

    Args:
      location_ref: Resource, the location to list Channel Connections in.
      limit: int or None, the total number of results to return.
      page_size: int, the number of entries in each batch (affects requests
        made, but not the yielded results).

    Returns:
      A generator of Channel Connections in the location.
    """
    list_req = self._messages.EventarcProjectsLocationsChannelConnectionsListRequest(
        parent=location_ref.RelativeName(), pageSize=page_size)
    return list_pager.YieldFromList(
        service=self._service,
        request=list_req,
        field='channelConnections',
        limit=limit,
        batch_size=page_size,
        batch_size_attribute='pageSize')

  def Publish(self, channel_connection_ref, cloud_event):
    """Publish to a Channel Conenction.

    Args:
      channel_connection_ref: Resource, the channel connection to publish from.
      cloud_event: A CloudEvent representation to be passed as the request body.
    """

    # Format to CloudEvents v1.0
    events_value_list_entry = common_publishing.TransformEventsForPublishing(
        self._publishing_messages
        .GoogleCloudEventarcPublishingV1PublishChannelConnectionEventsRequest
        .EventsValueListEntry, cloud_event)

    publish_events_request = self._publishing_messages.GoogleCloudEventarcPublishingV1PublishChannelConnectionEventsRequest(
        events=[events_value_list_entry]
    )
    publish_req = self._publishing_messages.EventarcpublishingProjectsLocationsChannelConnectionsPublishEventsRequest(
        channelConnection=channel_connection_ref.RelativeName(),
        googleCloudEventarcPublishingV1PublishChannelConnectionEventsRequest=publish_events_request
    )

    self._publishing_service.PublishEvents(publish_req)

  def BuildChannelConnection(self, channel_connection_ref, channel,
                             activation_token):
    return self._messages.ChannelConnection(
        name=channel_connection_ref.RelativeName(),
        channel=channel,
        activationToken=activation_token)
