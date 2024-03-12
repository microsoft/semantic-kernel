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
"""Utilities for Cloud Monitoring Snoozes API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis


def GetClientInstance(no_http=False):
  return apis.GetClientInstance('monitoring', 'v3', no_http=no_http)


def GetMessagesModule(client=None):
  client = client or GetClientInstance()
  return client.MESSAGES_MODULE


class SnoozeClient(object):
  """Client for the Snooze service in the Stackdriver Monitoring API."""

  def __init__(self, client=None, messages=None):
    self.client = client or GetClientInstance()
    self.messages = messages or GetMessagesModule(client)
    self._service = self.client.projects_snoozes

  def Create(self, project_ref, snooze):
    """Creates a Stackdriver snooze."""
    req = self.messages.MonitoringProjectsSnoozesCreateRequest(
        parent=project_ref.RelativeName(),
        snooze=snooze)
    return self._service.Create(req)

  def Get(self, snooze_ref):
    """Gets an Monitoring Snooze."""
    request = self.messages.MonitoringProjectsSnoozesGetRequest(
        name=snooze_ref.RelativeName())
    return self._service.Get(request)

  def Update(self, snooze_ref, snooze, fields=None):
    """Updates a Monitoring Snooze.

    If fields is not specified, then the snooze is replaced entirely. If
    fields are specified, then only the fields are replaced.

    Args:
      snooze_ref: resources.Resource, Resource reference to the snooze to be
          updated.
      snooze: Snooze, The snooze message to be sent with the request.
      fields: str, Comma separated list of field masks.
    Returns:
      Snooze, The updated Snooze.
    """
    request = self.messages.MonitoringProjectsSnoozesPatchRequest(
        name=snooze_ref.RelativeName(),
        snooze=snooze,
        updateMask=fields)
    return self._service.Patch(request)
