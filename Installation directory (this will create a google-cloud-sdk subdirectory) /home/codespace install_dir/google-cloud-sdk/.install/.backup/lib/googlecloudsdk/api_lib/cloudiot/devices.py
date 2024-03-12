# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Utilities Cloud IoT devices API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions


class NoFieldsSpecifiedError(exceptions.Error):
  """Error when no fields were specified for a Patch operation."""


def GetClientInstance(no_http=False):
  return apis.GetClientInstance('cloudiot', 'v1', no_http=no_http)


def GetMessagesModule(client=None):
  client = client or GetClientInstance()
  return client.MESSAGES_MODULE


class _DeviceUpdateSetting(object):
  """Small value class holding data for updating a device."""

  def __init__(self, field_name, update_mask, value):
    self.field_name = field_name
    self.update_mask = update_mask
    self.value = value


class DevicesClient(object):
  """Client for devices service in the Cloud IoT API."""

  def __init__(self, client=None, messages=None):
    self.client = client or GetClientInstance()
    self.messages = messages or GetMessagesModule(client)
    self._service = self.client.projects_locations_registries_devices

  def Create(self, parent_ref, device_id,
             blocked=None, credentials=None, metadata=None):
    """Creates a Device.

    Args:
      parent_ref: a Resource reference to a parent
        cloudiot.projects.locations.registries resource for this device.
      device_id: str, the name of the resource to create.
      blocked: bool, whether the device to create should have connections
        blocked or not.
      credentials: list of DeviceCredential, the credentials for the device.
      metadata: MetadataValue, the metadata message for the device.

    Returns:
      Device: the created device.
    """
    credentials = credentials or []

    create_req_type = (
        self.messages.CloudiotProjectsLocationsRegistriesDevicesCreateRequest)
    create_req = create_req_type(
        parent=parent_ref.RelativeName(),
        device=self.messages.Device(
            id=device_id,
            blocked=blocked,
            credentials=credentials,
            metadata=metadata
        ))

    return self._service.Create(create_req)

  def Delete(self, device_ref):
    delete_req_type = (
        self.messages.CloudiotProjectsLocationsRegistriesDevicesDeleteRequest)
    delete_req = delete_req_type(name=device_ref.RelativeName())
    return self._service.Delete(delete_req)

  def Get(self, device_ref):
    get_req_type = (
        self.messages.CloudiotProjectsLocationsRegistriesDevicesGetRequest)
    get_req = get_req_type(name=device_ref.RelativeName())
    return self._service.Get(get_req)

  def List(self, parent_ref, device_ids=None, device_num_ids=None,
           field_mask=None, limit=None, page_size=100):
    """List Devices in a DeviceRegistry.

    Args:
      parent_ref: a Resource reference to a parent
        cloudiot.projects.locations.registries resource to list.
      device_ids: list of strings, the device IDs
      device_num_ids: a list of numerical device IDs
      field_mask: list of str, the fields (in addition to `id` and `num_id`) to
        populate in the listed Devices.
      limit: int or None, the total number of results to return.
      page_size: int, the number of entries in each batch (affects requests
        made, but not the yielded results).

    Returns:
      Generator of matching devices.
    """
    list_req_type = (
        self.messages.CloudiotProjectsLocationsRegistriesDevicesListRequest)
    field_mask = ','.join(field_mask) if field_mask else None
    list_req = list_req_type(
        parent=parent_ref.RelativeName(),
        deviceIds=device_ids or [],
        deviceNumIds=device_num_ids or [],
        fieldMask=field_mask)
    return list_pager.YieldFromList(
        self._service, list_req, batch_size=page_size, limit=limit,
        field='devices', batch_size_attribute='pageSize')

  def Patch(self, device_ref, blocked=None, credentials=None, metadata=None,
            auth_method=None, log_level=None):
    """Updates a Device.

    Any fields not specified will not be updated; at least one field must be
    specified.

    Args:
      device_ref: a Resource reference to a
        cloudiot.projects.locations.registries.devices resource.
      blocked: bool, whether the device to create should have connections
        blocked or not.
      credentials: List of DeviceCredential or None. If given, update the
        credentials for the device.
      metadata: MetadataValue, the metadata message for the device.
      auth_method: GatewayAuthMethodValueValuesEnum, auth method to update on
        a gateway device.
      log_level: LogLevelValueValuesEnum, the default logging verbosity for the
        device.

    Returns:
      Device: the updated device.

    Raises:
      NoFieldsSpecifiedError: if no fields were specified.
    """
    device = self.messages.Device()

    update_settings = [
        _DeviceUpdateSetting(
            'blocked',
            'blocked',
            blocked),
        _DeviceUpdateSetting(
            'credentials',
            'credentials',
            credentials),
        _DeviceUpdateSetting(
            'metadata',
            'metadata',
            metadata),
        _DeviceUpdateSetting(
            'gatewayConfig.gatewayAuthMethod',
            'gatewayConfig.gatewayAuthMethod',
            auth_method),
        _DeviceUpdateSetting(
            'logLevel',
            'logLevel',
            log_level),
    ]
    update_mask = []
    for update_setting in update_settings:
      if update_setting.value is not None:
        arg_utils.SetFieldInMessage(device,
                                    update_setting.field_name,
                                    update_setting.value)
        update_mask.append(update_setting.update_mask)
    if not update_mask:
      raise NoFieldsSpecifiedError('Must specify at least one field to update.')
    patch_req_type = (
        self.messages.CloudiotProjectsLocationsRegistriesDevicesPatchRequest)
    patch_req = patch_req_type(
        device=device,
        name=device_ref.RelativeName(),
        updateMask=','.join(update_mask))

    return self._service.Patch(patch_req)

  def ModifyConfig(self, device_ref, data, version=None):
    """Modify a device configuration.

    Follows the API semantics, notably those regarding the version parameter: If
    0 or None, the latest version is modified. Otherwise, this update will fail
    if the version number provided does not match the latest version on the
    server.

    Args:
      device_ref: a Resource reference to a
        cloudiot.projects.locations.registries.devices resource.
      data: str, the binary data for the configuration
      version: int or None, the version of the configuration to modify.

    Returns:
      DeviceConfig: the modified DeviceConfig for the device
    """
    request_type = getattr(self.messages,
                           'CloudiotProjectsLocationsRegistriesDevices'
                           'ModifyCloudToDeviceConfigRequest')
    modify_request_type = self.messages.ModifyCloudToDeviceConfigRequest
    request = request_type(
        name=device_ref.RelativeName(),
        modifyCloudToDeviceConfigRequest=modify_request_type(
            binaryData=data,
            versionToUpdate=version
        )
    )
    return self._service.ModifyCloudToDeviceConfig(request)


class DeviceConfigsClient(object):
  """Client for device_configs service in the Cloud IoT API."""

  def __init__(self, client=None, messages=None):
    self.client = client or GetClientInstance()
    self.messages = messages or GetMessagesModule(client)
    # Get around line length limits...
    service = self.client.projects_locations_registries_devices_configVersions
    self._service = service

  def List(self, parent_ref, num_versions=None):
    """List all device configurations available for a device.

    Up to a maximum of 10 (enforced by service). No pagination.

    Args:
      parent_ref: a Resource reference to a
        cloudiot.projects.locations.registries.devices resource.
      num_versions: int, the number of device configurations to list (max 10).

    Returns:
      List of DeviceConfig
    """
    request_type = getattr(self.messages,
                           'CloudiotProjectsLocationsRegistries'
                           'DevicesConfigVersionsListRequest')
    response = self._service.List(
        request_type(name=parent_ref.RelativeName(),
                     numVersions=num_versions))
    return response.deviceConfigs


class DeviceStatesClient(object):
  """Client for device_states service in the Cloud IoT API."""

  def __init__(self, client=None, messages=None):
    self.client = client or GetClientInstance()
    self.messages = messages or GetMessagesModule(client)
    self._service = self.client.projects_locations_registries_devices_states

  def List(self, parent_ref, num_states=None):
    """List all device states available for a device.

    Up to a maximum of 10 (enforced by service). No pagination.

    Args:
      parent_ref: a Resource reference to a
        cloudiot.projects.locations.registries.devices resource.
      num_states: int, the number of device states to list (max 10).

    Returns:
      List of DeviceStates
    """
    request_type = getattr(self.messages,
                           'CloudiotProjectsLocationsRegistries'
                           'DevicesStatesListRequest')
    response = self._service.List(
        request_type(name=parent_ref.RelativeName(),
                     numStates=num_states))
    return response.deviceStates
