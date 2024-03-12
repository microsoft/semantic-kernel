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
"""Cloud vmware API utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import resources


_DEFAULT_API_VERSION = 'v1'


class VmwareClientBase(object):
  """Base class for vwmare API client wrappers."""

  def __init__(self, api_version=_DEFAULT_API_VERSION):
    self._client = apis.GetClientInstance('vmwareengine', api_version)
    self._messages = apis.GetMessagesModule('vmwareengine', api_version)
    self.service = None
    self.operations_service = self.client.projects_locations_operations

  @property
  def client(self):
    return self._client

  @property
  def messages(self):
    return self._messages

  def GetOperationRef(self, operation):
    """Converts an Operation to a Resource that can be used with `waiter.WaitFor`.
    """
    return resources.REGISTRY.ParseRelativeName(
        operation.name, collection='vmwareengine.projects.locations.operations')

  def WaitForOperation(self,
                       operation_ref,
                       message,
                       has_result=True,
                       max_wait=datetime.timedelta(seconds=3600)):
    """Waits for an operation to complete.

    Polls the IDS Operation service until the operation completes, fails, or
    max_wait_seconds elapses.

    Args:
      operation_ref: a Resource created by GetOperationRef describing the
        operation.
      message: the message to display to the user while they wait.
      has_result: if True, the function will return the target of the operation
        when it completes. If False, nothing will be returned (useful for Delete
        operations)
      max_wait: The time to wait for the operation to succeed before returning.

    Returns:
      if has_result = True, an Endpoint entity.
      Otherwise, None.
    """
    if has_result:
      poller = waiter.CloudOperationPoller(self.service,
                                           self.operations_service)
    else:
      poller = waiter.CloudOperationPollerNoResources(self.operations_service)

    return waiter.WaitFor(
        poller, operation_ref, message, max_wait_ms=max_wait.seconds * 1000)

  def GetResponse(self, operation):
    poller = waiter.CloudOperationPoller(self.service, self.operations_service)
    return poller.GetResult(operation)


def GetResourceId(resource_name):
  return resource_name.split('/')[-1]


def ConstructNodeParameterConfigMessage(map_class, config_class, nodes_configs):
  """Constructs a node configs API message.

  Args:
    map_class: The map message class.
    config_class: The config (map-entry) message class.
    nodes_configs: The list of nodes configurations.

  Returns:
    The constructed message.
  """
  properties = []
  for nodes_config in nodes_configs:
    if nodes_config.count == 0:
      continue

    node_type_config = config_class(nodeCount=nodes_config.count)
    if nodes_config.custom_core_count > 0:
      node_type_config.customCoreCount = nodes_config.custom_core_count

    prop = map_class.AdditionalProperty(
        key=nodes_config.type, value=node_type_config
    )
    properties.append(prop)
  return map_class(additionalProperties=properties)


def ConstructAutoscalingSettingsMessage(
    settings_message_class,
    policy_message_class,
    thresholds_message_class,
    autoscaling_settings,
):
  """Constructs autoscaling settings API message.

  Args:
    settings_message_class: Top-level autoscaling settings message class.
    policy_message_class: Autoscaling policy message class.
    thresholds_message_class: Autoscaling policy thresholds message class.
    autoscaling_settings: Desired autoscaling settings.

  Returns:
    The constructed message.
  """
  if not autoscaling_settings:
    return None

  settings_message = settings_message_class()
  settings_message.minClusterNodeCount = (
      autoscaling_settings.min_cluster_node_count
  )
  settings_message.maxClusterNodeCount = (
      autoscaling_settings.max_cluster_node_count
  )
  settings_message.coolDownPeriod = autoscaling_settings.cool_down_period

  policy_messages = {}
  for name, policy in autoscaling_settings.autoscaling_policies.items():
    policy_message = policy_message_class()
    policy_message.nodeTypeId = policy.node_type_id
    policy_message.scaleOutSize = policy.scale_out_size
    policy_message.minNodeCount = policy.min_node_count
    policy_message.maxNodeCount = policy.max_node_count

    policy_message.cpuThresholds = _ConstructThresholdsMessage(
        policy.cpu_thresholds, thresholds_message_class
    )
    policy_message.grantedMemoryThresholds = _ConstructThresholdsMessage(
        policy.granted_memory_thresholds, thresholds_message_class
    )
    policy_message.consumedMemoryThresholds = _ConstructThresholdsMessage(
        policy.consumed_memory_thresholds, thresholds_message_class
    )
    policy_message.storageThresholds = _ConstructThresholdsMessage(
        policy.storage_thresholds, thresholds_message_class
    )

    policy_messages[name] = policy_message

  settings_message.autoscalingPolicies = settings_message_class.AutoscalingPoliciesValue(
      additionalProperties=[
          settings_message_class.AutoscalingPoliciesValue.AdditionalProperty(
              key=name, value=policy_message
          ) for name, policy_message in policy_messages.items()
      ]
  )
  return settings_message


def _ConstructThresholdsMessage(thresholds, thresholds_message_class):
  thresholds_message = thresholds_message_class()
  if thresholds is None:
    return None
  thresholds_message.scaleIn = thresholds.scale_in
  thresholds_message.scaleOut = thresholds.scale_out
  return thresholds_message
