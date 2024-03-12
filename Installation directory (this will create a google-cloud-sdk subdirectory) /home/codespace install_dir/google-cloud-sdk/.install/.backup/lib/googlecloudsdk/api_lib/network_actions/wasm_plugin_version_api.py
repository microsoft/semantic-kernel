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
"""API wrapper for `gcloud network-actions wasm-plugin-versions` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_actions import util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import resources
import six


class Client:
  """API client for WasmPluginVersion commands.

  Attributes:
    messages: API messages class, The Networkservices API messages.
  """

  def __init__(self, release_track):
    self._client = util.GetClientInstance(release_track)
    self._wasm_plugin_version_client = (
        self._client.projects_locations_wasmPlugins_versions
    )
    self._operations_client = self._client.projects_locations_operations
    self.messages = self._client.MESSAGES_MODULE
    self._resource_parser = resources.Registry()
    self._resource_parser.RegisterApiByName(
        'networkservices', util.API_VERSION_FOR_TRACK.get(release_track)
    )

  def CreateWasmPluginVersion(
      self,
      name,
      parent,
      image,
      plugin_config_data=None,
      plugin_config_uri=None,
      description=None,
      labels=None,
  ):
    """Calls the CreateWasmPluginVersion API.

    Args:
      name: string, wasmPluginVersion's name.
      parent: string, wasmPluginVersion's parent relative name.
      image: string, URI of the container image containing the Wasm module,
        stored in the Artifact Registry.
      plugin_config_data: string or bytes, WasmPlugin configuration in the
        textual or binary format.
      plugin_config_uri: string, URI of the container image containing the
        plugin configuration, stored in the Artifact Registry.
      description: string, human-readable description of the service.
      labels: set of label tags.

    Returns:
      (Operation) The response message.
    """
    plugin_config_data_binary = None
    if plugin_config_data:
      # Converts string --plugin-config flag into bytes for the string-type
      # argument and returns the unchanged argument value for bytes-type
      # --plugin-config-file flag.
      plugin_config_data_binary = six.ensure_binary(plugin_config_data)
    request = (
        self.messages.NetworkservicesProjectsLocationsWasmPluginsVersionsCreateRequest(
            parent=parent,
            wasmPluginVersionId=name,
            wasmPluginVersion=self.messages.WasmPluginVersion(
                imageUri=image,
                description=description,
                labels=labels,
                pluginConfigData=plugin_config_data_binary,
                pluginConfigUri=plugin_config_uri,
            ),
        )
    )
    return self._wasm_plugin_version_client.Create(request)

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
        self._wasm_plugin_version_client, self._operations_client
    )
    return waiter.WaitFor(
        poller,
        op_resource,
        message,
    )
