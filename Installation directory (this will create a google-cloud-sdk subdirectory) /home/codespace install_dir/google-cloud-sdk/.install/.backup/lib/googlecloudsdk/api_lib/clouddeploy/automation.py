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
"""Support library to handle the automation subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.clouddeploy import client_util

AUTOMATION_UPDATE_MASK = '*,labels'


class AutomationsClient(object):
  """Client for automation service in the Cloud Deploy API."""

  def __init__(self, client=None, messages=None):
    """Initialize an automation.AutomationsClient.

    Args:
      client: base_api.BaseApiClient, the client class for Cloud Deploy.
      messages: module containing the definitions of messages for Cloud Deploy.
    """
    self.client = client or client_util.GetClientInstance()
    self.messages = messages or client_util.GetMessagesModule(client)
    self._service = self.client.projects_locations_deliveryPipelines_automations

  def Patch(self, obj):
    """Patches a target resource.

    Args:
      obj: apitools.base.protorpclite.messages.Message, automation message.

    Returns:
      The operation message.
    """
    return self._service.Patch(
        self.messages.ClouddeployProjectsLocationsDeliveryPipelinesAutomationsPatchRequest(
            automation=obj,
            allowMissing=True,
            name=obj.name,
            updateMask=AUTOMATION_UPDATE_MASK,
        )
    )

  def Get(self, name):
    """Gets the automation object by calling the automation get API.

    Args:
      name: automation name.

    Returns:
      an automation object.
    """
    request = self.messages.ClouddeployProjectsLocationsDeliveryPipelinesAutomationsGetRequest(
        name=name
    )
    return self._service.Get(request)

  def Delete(self, name):
    """Deletes an automation resource.

    Args:
      name: str, automation name.

    Returns:
      The operation message. It could be none if the resource doesn't exist.
    """
    return self._service.Delete(
        self.messages.ClouddeployProjectsLocationsDeliveryPipelinesAutomationsDeleteRequest(
            allowMissing=True, name=name
        )
    )
