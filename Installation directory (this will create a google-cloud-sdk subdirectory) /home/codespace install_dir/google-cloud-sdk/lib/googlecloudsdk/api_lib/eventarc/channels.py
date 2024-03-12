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
"""Utilities for Eventarc Channels API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.eventarc import common
from googlecloudsdk.api_lib.eventarc import common_publishing
from googlecloudsdk.api_lib.eventarc.base import EventarcClientBase
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources


class NoFieldsSpecifiedError(exceptions.Error):
  """Error when no fields were specified for a Patch operation."""


def GetChannelURI(resource):
  channels = resources.REGISTRY.ParseRelativeName(
      resource.name, collection='eventarc.projects.locations.channels')
  return channels.SelfLink()


class ChannelClientV1(EventarcClientBase):
  """Channel Client for interaction with v1 of Eventarc Channels API."""

  def __init__(self):
    super(ChannelClientV1, self).__init__(common.API_NAME, common.API_VERSION_1,
                                          'channel')

    # Eventarc Client
    client = apis.GetClientInstance(common.API_NAME, common.API_VERSION_1)

    self._messages = client.MESSAGES_MODULE
    self._service = client.projects_locations_channels

    # Eventarc Publishing client
    publishing_client = apis.GetClientInstance(common_publishing.API_NAME,
                                               common_publishing.API_VERSION_1)

    self._publishing_messages = publishing_client.MESSAGES_MODULE
    self._publishing_service = publishing_client.projects_locations_channels

  def Create(self, channel_ref, channel_message, dry_run=False):
    """Creates a new Channel.

    Args:
      channel_ref: Resource, the Channel to create.
      channel_message: Channel, the channel message that holds channel's name,
        provider, etc.
      dry_run: If set, the changes will not be commited, only validated

    Returns:
      A long-running operation for create.
    """
    create_req = self._messages.EventarcProjectsLocationsChannelsCreateRequest(
        parent=channel_ref.Parent().RelativeName(),
        channel=channel_message,
        channelId=channel_ref.Name(),
        validateOnly=dry_run)
    return self._service.Create(create_req)

  def Delete(self, channel_ref):
    """Deletes the specified Channel.

    Args:
      channel_ref: Resource, the Channel to delete.

    Returns:
      A long-running operation for delete.
    """
    delete_req = self._messages.EventarcProjectsLocationsChannelsDeleteRequest(
        name=channel_ref.RelativeName())
    return self._service.Delete(delete_req)

  def Get(self, channel_ref):
    """Gets the requested Channel.

    Args:
      channel_ref: Resource, the Channel to get.

    Returns:
      The Channel message.
    """
    get_req = self._messages.EventarcProjectsLocationsChannelsGetRequest(
        name=channel_ref.RelativeName())
    return self._service.Get(get_req)

  def List(self, location_ref, limit, page_size):
    """List available channels in location.

    Args:
      location_ref: Resource, the location to list Channels in.
      limit: int or None, the total number of results to return.
      page_size: int, the number of entries in each batch (affects requests
        made, but not the yielded results).

    Returns:
      A generator of Channels in the location.
    """
    list_req = self._messages.EventarcProjectsLocationsChannelsListRequest(
        parent=location_ref.RelativeName(), pageSize=page_size)
    return list_pager.YieldFromList(
        service=self._service,
        request=list_req,
        field='channels',
        limit=limit,
        batch_size=page_size,
        batch_size_attribute='pageSize')

  def Patch(self, channel_ref, channel_message, update_mask):
    """Updates the specified Channel.

    Args:
      channel_ref: Resource, the Channel to update.
      channel_message: Channel, the channel message that holds channel's name,
        provider, etc.
      update_mask: str, a comma-separated list of Channel fields to update.

    Returns:
      A long-running operation for update.
    """
    patch_req = self._messages.EventarcProjectsLocationsChannelsPatchRequest(
        name=channel_ref.RelativeName(),
        channel=channel_message,
        updateMask=update_mask)
    return self._service.Patch(patch_req)

  def Publish(self, channel_ref, cloud_event):
    """Publish to a Channel.

    Args:
      channel_ref: Resource, the channel to publish to.
      cloud_event: A CloudEvent representation to be passed as the request body.
    """

    # Format to CloudEvents v1.0
    events_value_list_entry = common_publishing.TransformEventsForPublishing(
        self._publishing_messages
        .GoogleCloudEventarcPublishingV1PublishEventsRequest
        .EventsValueListEntry, cloud_event)

    publish_events_request = self._publishing_messages.GoogleCloudEventarcPublishingV1PublishEventsRequest(
        events=[events_value_list_entry])
    publish_req = self._publishing_messages.EventarcpublishingProjectsLocationsChannelsPublishEventsRequest(
        channel=channel_ref.RelativeName(),
        googleCloudEventarcPublishingV1PublishEventsRequest=publish_events_request
    )

    # GoogleCloudEventarcPublishingV1PublishEventsResponse
    self._publishing_service.PublishEvents(publish_req)

  def BuildChannel(self, channel_ref, provider_ref, crypto_key_name):
    return self._messages.Channel(
        name=channel_ref.RelativeName(),
        cryptoKeyName=crypto_key_name,
        provider=provider_ref
        if provider_ref is None else provider_ref.RelativeName())

  def BuildUpdateMask(self, crypto_key, clear_crypto_key):
    """Builds an update mask for updating a channel.

    Args:
      crypto_key: bool, whether to update the crypto key.
      clear_crypto_key: bool, whether to clear the crypto key.

    Returns:
      The update mask as a string.

    Raises:
      NoFieldsSpecifiedError: No fields are being updated.
    """
    update_mask = []
    if crypto_key:
      update_mask.append('cryptoKeyName')
    if clear_crypto_key:
      update_mask.append('cryptoKeyName')

    if not update_mask:
      raise NoFieldsSpecifiedError('Must specify at least one field to update.')
    return ','.join(update_mask)
