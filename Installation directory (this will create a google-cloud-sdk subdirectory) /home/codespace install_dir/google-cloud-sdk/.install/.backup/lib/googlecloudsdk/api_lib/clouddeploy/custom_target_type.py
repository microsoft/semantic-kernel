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
"""Support library to handle the custom-target-type subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.clouddeploy import client_util

CUSTOM_TARGET_TYPE_UPDATE_MASK = '*,labels'


class CustomTargetTypesClient(object):
  """Client for custom target type service in the Cloud Deploy API."""

  def __init__(self, client=None, messages=None):
    """Initialize a custom_target_type.CustomTargetTypesClient.

    Args:
      client: base_api.BaseApiClient, the client class for Cloud Deploy.
      messages: module containing the definitions of messages for Cloud Deploy.
    """
    self.client = client or client_util.GetClientInstance()
    self.messages = messages or client_util.GetMessagesModule(client)
    self._service = self.client.projects_locations_customTargetTypes

  def Get(self, name):
    """Gets the custom target type object.

    Args:
      name: custom target type name.

    Returns:
      a custom target type object.
    """
    request = (
        self.messages.ClouddeployProjectsLocationsCustomTargetTypesGetRequest(
            name=name
        )
    )
    return self._service.Get(request)

  def Patch(self, obj):
    """Patches a custom target type resource.

    Args:
      obj: apitools.base.protorpclite.messages.Message, custom target type
        message.

    Returns:
      The operation message.
    """
    return self._service.Patch(
        self.messages.ClouddeployProjectsLocationsCustomTargetTypesPatchRequest(
            customTargetType=obj,
            allowMissing=True,
            name=obj.name,
            updateMask=CUSTOM_TARGET_TYPE_UPDATE_MASK,
        )
    )

  def Delete(self, name):
    """Deletes a custom target type resource.

    Args:
      name: str, custom target type name.

    Returns:
      The operation message.
    """
    return self._service.Delete(
        self.messages.ClouddeployProjectsLocationsCustomTargetTypesDeleteRequest(
            name=name, allowMissing=True))
