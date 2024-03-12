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
"""API wrapper for `gcloud network-actions wasm-plugin` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_actions import util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import resources


class Client:
  """API client for WasmPlugin commands.

  Attributes:
    messages: API messages class, The Networkservices API messages.
  """

  def __init__(self, release_track):
    self._client = util.GetClientInstance(release_track)
    self._wasm_plugin_client = self._client.projects_locations_wasmPlugins
    self._operations_client = self._client.projects_locations_operations
    self.messages = self._client.MESSAGES_MODULE
    self._resource_parser = resources.Registry()
    self._resource_parser.RegisterApiByName(
        'networkservices', util.API_VERSION_FOR_TRACK.get(release_track)
    )

  def CreateWasmPlugin(
      self, name, parent, description=None, labels=None, log_config=None
  ):
    """Calls the CreateWasmPlugin API."""
    request = (
        self.messages.NetworkservicesProjectsLocationsWasmPluginsCreateRequest(
            parent=parent,
            wasmPluginId=name,
            wasmPlugin=self.messages.WasmPlugin(
                description=description,
                labels=labels,
                logConfig=log_config,
            ),
        )
    )
    return self._wasm_plugin_client.Create(request)

  def UpdateWasmPlugin(
      self,
      name,
      main_version,
      update_mask=None,
      description=None,
      labels=None,
      log_config=None,
  ):
    """Calls the UpdateWasmPlugin API."""
    request = (
        self.messages.NetworkservicesProjectsLocationsWasmPluginsPatchRequest(
            name=name,
            updateMask=update_mask,
            wasmPlugin=self.messages.WasmPlugin(
                mainVersionId=main_version,
                description=description,
                labels=labels,
                logConfig=log_config,
            ),
        )
    )
    return self._wasm_plugin_client.Patch(request)

  def WaitForOperation(
      self,
      operation_ref,
      message,
  ):
    """Waits for the opration to complete and returns the result of the operation.

    Args:
      operation_ref: A Resource describing the Operation.
      message: The message to display to the user while they wait.

    Returns:
      result of result_service.Get request for the provided operation.
    """

    op_resource = resources.REGISTRY.ParseRelativeName(
        operation_ref.name,
        collection='networkservices.projects.locations.operations',
    )
    poller = waiter.CloudOperationPoller(
        self._wasm_plugin_client, self._operations_client
    )
    return waiter.WaitFor(
        poller,
        op_resource,
        message,
    )
