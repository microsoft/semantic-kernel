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
"""Utilities for Eventarc Channels API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.eventarc import common
from googlecloudsdk.api_lib.eventarc.base import EventarcClientBase
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties


class NoFieldsSpecifiedError(exceptions.Error):
  """Error when no fields were specified for a Patch operation."""


def GetProject(args):
  """Gets project resource from either argument flag or attribute."""
  return args.project or properties.VALUES.core.project.GetOrFail()


def GetLocation(args):
  """Gets location resource from either argument flag or attribute."""
  return args.location or properties.VALUES.eventarc.location.GetOrFail()


class GoogleChannelConfigClientV1(EventarcClientBase):
  """Google Channel Client for interaction with v1 of Eventarc Channels API."""

  def __init__(self):
    super(GoogleChannelConfigClientV1,
          self).__init__(common.API_NAME, common.API_VERSION_1,
                         'GoogleChannelConfig')

    # Eventarc Client
    client = apis.GetClientInstance(common.API_NAME, common.API_VERSION_1)

    self._messages = client.MESSAGES_MODULE
    self._service = client.projects_locations

  def Get(self, google_channel_config_name):
    """Gets the requested GoogleChannelConfig.

    Args:
      google_channel_config_name: str, the name of GoogleChannelConfig to get.

    Returns:
      The GoogleChannelConfig message.
    """
    get_req = self._messages.EventarcProjectsLocationsGetGoogleChannelConfigRequest(
        name=google_channel_config_name)
    return self._service.GetGoogleChannelConfig(get_req)

  def Update(self, google_channel_config_name, google_channel_config_message,
             update_mask):
    """Updates the specified Channel.

    Args:
      google_channel_config_name: str, the name of GoogleChannelConfig to
        update.
      google_channel_config_message: GoogleChannelConfig, the config message
        that holds KMS encryption info.
      update_mask: str, a comma-separated list of GoogleChannelConfig fields to
        update.

    Returns:
      Response for update.
    """
    update_req = self._messages.EventarcProjectsLocationsUpdateGoogleChannelConfigRequest(
        name=google_channel_config_name,
        googleChannelConfig=google_channel_config_message,
        updateMask=update_mask)
    return self._service.UpdateGoogleChannelConfig(update_req)

  def BuildGoogleChannelConfig(self, google_channel_config_name,
                               crypto_key_name):
    return self._messages.GoogleChannelConfig(
        name=google_channel_config_name, cryptoKeyName=crypto_key_name)

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
