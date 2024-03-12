# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""API Client for Cloud Monitoring Notification Channels."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis


def GetClientInstance(no_http=False):
  return apis.GetClientInstance('monitoring', 'v3', no_http=no_http)


def GetMessagesModule(client=None):
  client = client or GetClientInstance()
  return client.MESSAGES_MODULE


class NotificationChannelsClient(object):
  """Client for Notification Channels service in the Cloud Monitoring."""

  def __init__(self, client=None, messages=None):
    self.client = client or GetClientInstance()
    self.messages = messages or GetMessagesModule(client)
    self._service = self.client.projects_notificationChannels

  def Create(self, project_ref, channel):
    """Creates an Monitoring Alert Policy."""
    req = self.messages.MonitoringProjectsNotificationChannelsCreateRequest(
        name=project_ref.RelativeName(),
        notificationChannel=channel)
    return self._service.Create(req)

  def Get(self, channel_ref):
    req = self.messages.MonitoringProjectsNotificationChannelsGetRequest(
        name=channel_ref.RelativeName())
    return self._service.Get(req)

  def Update(self, channel_ref, channel, fields=None):
    req = self.messages.MonitoringProjectsNotificationChannelsPatchRequest(
        name=channel_ref.RelativeName(),
        notificationChannel=channel,
        updateMask=fields)
    return self._service.Patch(req)

