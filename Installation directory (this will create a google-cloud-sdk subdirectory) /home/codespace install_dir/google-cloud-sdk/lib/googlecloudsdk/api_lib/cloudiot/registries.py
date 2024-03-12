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

"""Utilities Cloud IoT registries API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions


class NoFieldsSpecifiedError(exceptions.Error):
  """Error when no fields were specified for a Patch operation."""


def GetClientInstance(no_http=False):
  return apis.GetClientInstance('cloudiot', 'v1', no_http=no_http)


def GetMessagesModule(client=None):
  client = client or GetClientInstance()
  return client.MESSAGES_MODULE


class _DeviceRegistryUpdateSetting(object):
  """Small value class holding data for updating a device registry."""

  def __init__(self, field_name, update_mask, value):
    self.field_name = field_name
    self.update_mask = update_mask
    self.value = value


class RegistriesClient(object):
  """Client for registries service in the Cloud IoT API."""

  def __init__(self, client=None, messages=None):
    self.client = client or GetClientInstance()
    self.messages = messages or GetMessagesModule(client)
    self._service = self.client.projects_locations_registries

  @property
  def mqtt_config_enum(self):
    return self.messages.MqttConfig.MqttEnabledStateValueValuesEnum

  @property
  def http_config_enum(self):
    return self.messages.HttpConfig.HttpEnabledStateValueValuesEnum

  def Create(self, parent_ref, registry_id, credentials=None,
             event_notification_configs=None, state_pubsub_topic=None,
             mqtt_enabled_state=None, http_enabled_state=None):
    """Creates a DeviceRegistry.

    Args:
      parent_ref: a Resource reference to a cloudiot.projects.locations
        resource for the parent of this registry.
      registry_id: str, the name of the resource to create.
      credentials: List of RegistryCredentials or None, credentials for the
        DeviceRegistry.
      event_notification_configs: List of EventNotificationConfigs or None,
        configs for forwarding telemetry events for the Registry.
      state_pubsub_topic: an optional Resource reference to a
        pubsub.projects.topics. The pubsub topic for state notifications on this
        device registry.
      mqtt_enabled_state: MqttEnabledStateValueValuesEnum, the state of MQTT for
        the registry.
      http_enabled_state: HttpEnabledStateValueValuesEnum, the state of HTTP for
        the registry.

    Returns:
      DeviceRegistry: the created registry.
    """
    if state_pubsub_topic:
      # This is a repeated field, only the first entry is used though.
      state_notification_config = self.messages.StateNotificationConfig(
          pubsubTopicName=state_pubsub_topic.RelativeName())
    else:
      state_notification_config = None

    if mqtt_enabled_state:
      mqtt_config = self.messages.MqttConfig(
          mqttEnabledState=mqtt_enabled_state)
    else:
      mqtt_config = None

    if http_enabled_state:
      http_config = self.messages.HttpConfig(
          httpEnabledState=http_enabled_state)
    else:
      http_config = None

    create_req = self.messages.CloudiotProjectsLocationsRegistriesCreateRequest(
        parent=parent_ref.RelativeName(),
        deviceRegistry=self.messages.DeviceRegistry(
            id=registry_id,
            credentials=credentials or [],
            eventNotificationConfigs=event_notification_configs or [],
            stateNotificationConfig=state_notification_config,
            mqttConfig=mqtt_config,
            httpConfig=http_config))

    return self._service.Create(create_req)

  def Delete(self, registry_ref):
    delete_req = self.messages.CloudiotProjectsLocationsRegistriesDeleteRequest(
        name=registry_ref.RelativeName())
    return self._service.Delete(delete_req)

  def Get(self, registry_ref):
    get_req = self.messages.CloudiotProjectsLocationsRegistriesGetRequest(
        name=registry_ref.RelativeName())
    return self._service.Get(get_req)

  def List(self, parent_ref, limit=None, page_size=100):
    """List the device registries in a given location.

    Args:
      parent_ref: a Resource reference to a cloudiot.projects.locations
        resource to list devices for.
      limit: int, the total number of results to return from the API.
      page_size: int, the number of results in each batch from the API.

    Returns:
      A generator of the device registries in the location.
    """
    list_req = self.messages.CloudiotProjectsLocationsRegistriesListRequest(
        parent=parent_ref.RelativeName())
    return list_pager.YieldFromList(
        self._service, list_req, batch_size=page_size, limit=limit,
        field='deviceRegistries', batch_size_attribute='pageSize')

  def Patch(self,
            registry_ref,
            credentials=None,
            event_notification_configs=None,
            state_pubsub_topic=None,
            mqtt_enabled_state=None,
            http_enabled_state=None,
            log_level=None):
    """Updates a DeviceRegistry.

    Any fields not specified will not be updated; at least one field must be
    specified.

    Args:
      registry_ref: a Resource reference to a
        cloudiot.projects.locations.registries resource.
      credentials: List of RegistryCredentials or None, credentials for the
        DeviceRegistry.
      event_notification_configs: List of EventNotificationConfigs or None,
        configs for forwarding telemetry events for the Registry.
      state_pubsub_topic: an optional Resource reference to a
        pubsub.projects.topics. The pubsub topic for state notifications on this
        device registry.
      mqtt_enabled_state: MqttEnabledStateValueValuesEnum, the state of MQTT for
        the registry.
      http_enabled_state: HttpConfigStateValuEnabledsEnum, the state of HTTP for
        the registry.
      log_level: LogLevelValueValuesEnum, the default logging verbosity for the
        devices in the registry.

    Returns:
      DeviceRegistry: the created registry.

    Raises:
      NoFieldsSpecifiedError: if no fields were specified.
    """
    registry = self.messages.DeviceRegistry()

    if state_pubsub_topic:
      # This is a repeated field, only the first entry is used though.
      state_notification_config = self.messages.StateNotificationConfig(
          pubsubTopicName=state_pubsub_topic.RelativeName())
    else:
      state_notification_config = None

    if mqtt_enabled_state:
      mqtt_config = self.messages.MqttConfig(
          mqttEnabledState=mqtt_enabled_state)
    else:
      mqtt_config = None

    if http_enabled_state:
      http_config = self.messages.HttpConfig(
          httpEnabledState=http_enabled_state)
    else:
      http_config = None

    device_registry_update_settings = [
        _DeviceRegistryUpdateSetting('credentials', 'credentials', credentials),
        _DeviceRegistryUpdateSetting('eventNotificationConfigs',
                                     'event_notification_configs',
                                     event_notification_configs),
        _DeviceRegistryUpdateSetting(
            'stateNotificationConfig',
            'state_notification_config.pubsub_topic_name',
            state_notification_config),
        _DeviceRegistryUpdateSetting(
            'mqttConfig', 'mqtt_config.mqtt_enabled_state', mqtt_config),
        _DeviceRegistryUpdateSetting(
            'httpConfig', 'http_config.http_enabled_state', http_config),
        _DeviceRegistryUpdateSetting('logLevel', 'logLevel', log_level)
    ]
    update_mask = []
    for update_setting in device_registry_update_settings:
      if update_setting.value is not None:
        setattr(registry, update_setting.field_name, update_setting.value)
        update_mask.append(update_setting.update_mask)
    if not update_mask:
      raise NoFieldsSpecifiedError('Must specify at least one field to update.')
    patch_req = self.messages.CloudiotProjectsLocationsRegistriesPatchRequest(
        deviceRegistry=registry,
        name=registry_ref.RelativeName(),
        updateMask=','.join(update_mask))

    return self._service.Patch(patch_req)

  def SetIamPolicy(self, registry_ref, set_iam_policy_request):
    """Sets an IAM policy on a DeviceRegistry.

    Args:
      registry_ref: a Resource reference to a
        cloudiot.projects.locations.registries resource.
      set_iam_policy_request: A SetIamPolicyRequest which contains the Policy to
        add.

    Returns:
      Policy: the added policy.
    """
    set_req = (
        self.messages.CloudiotProjectsLocationsRegistriesSetIamPolicyRequest(
            resource=registry_ref.RelativeName(),
            setIamPolicyRequest=set_iam_policy_request))
    return self._service.SetIamPolicy(set_req)

  def GetIamPolicy(self, registry_ref):
    """Gets the IAM policy for a DeviceRegistry.

    Args:
      registry_ref: a Resource reference to a
        cloudiot.projects.locations.registries resource.

    Returns:
      Policy: the policy for the device registry.
    """
    get_req = (
        self.messages.CloudiotProjectsLocationsRegistriesGetIamPolicyRequest(
            resource=registry_ref.RelativeName()))
    return self._service.GetIamPolicy(get_req)
