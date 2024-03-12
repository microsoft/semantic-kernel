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
"""Handles the updating of PolicyControllerPolicyControllerDeploymentConfig.

Each function updates a single value, diving to the appropriate depth, updating
and returning the updated object. Note that while client-side validation could
occur here, it is deferred to the API layer.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions

# List of supported values to set/remove, with mapping from external to
# internal representations.
SUPPORTED_PROPERTIES = [
    'cpu-limit',
    'cpu-request',
    'memory-limit',
    'memory-request',
    'toleration',
    'replica-count',
    'pod-affinity',
]

K8S_SCHEDULING_OPTIONS = [
    'NoSchedule',
    'PreferNoSchedule',
    'NoExecute',
]


G8R_COMPONENTS = [
    'admission',
    'audit',
    'mutation',
]


def get_configurations(spec):
  """Extracts a dictionary of deployment configuration by component name.

  Args:
    spec: A hub membership spec.

  Returns:
    A dictionary mapping component name to configuration object.
  """
  return {
      cfg.key: cfg.value
      for cfg in spec.policycontroller.policyControllerHubConfig.deploymentConfigs.additionalProperties
  }


def update_replica_count(current, value):
  """Configures a replica count for the current deployment configuration."""
  if value is None:
    current.replicaCount = None
  else:
    current.replicaCount = int(value)
  return current


def update_cpu_limit(messages, current, value):
  """Configures a cpu limit for the current deployment configuration.

  Args:
    messages: the set of proto messages for this feature.
    current: the deployment configuration object being modified.
    value: The value to set the cpu limit to. If None, the limit will be
      removed. If this is the only limit, limit requirements will be removed. If
      this is the only requirement, requirements will be removed.

  Returns:
    The modified deployment configuration object.
  """
  requirements = messages.PolicyControllerResourceRequirements()
  if current.containerResources is not None:
    requirements = current.containerResources
  resource_list = messages.PolicyControllerResourceList()
  if requirements.limits is not None:
    resource_list = requirements.limits
  resource_list.cpu = value
  if resource_list.cpu is None and resource_list.memory is None:
    resource_list = None
  requirements.limits = resource_list
  if requirements.limits is None and requirements.requests is None:
    requirements = None
  current.containerResources = requirements
  return current


def update_mem_limit(messages, current, value):
  """Configures a memory limit for the current deployment configuration.

  Args:
    messages: the set of proto messages for this feature.
    current: the deployment configuration object being modified.
    value: The value to set the memory limit to. If None, the limit will be
      removed. If this is the only limit, limit requirements will be removed. If
      this is the only requirement, requirements will be removed.

  Returns:
    The modified deployment configuration object.
  """
  if current.containerResources is not None:
    requirements = current.containerResources
  else:
    requirements = messages.PolicyControllerResourceRequirements()
  resource_list = messages.PolicyControllerResourceList()
  if requirements.limits is not None:
    resource_list = requirements.limits
  resource_list.memory = value
  if resource_list.cpu is None and resource_list.memory is None:
    resource_list = None
  requirements.limits = resource_list
  if requirements.limits is None and requirements.requests is None:
    requirements = None
  current.containerResources = requirements
  return current


def update_cpu_request(messages, current, value):
  """Configures a cpu request for the current deployment configuration.

  Args:
    messages: the set of proto messages for this feature.
    current: the deployment configuration object being modified.
    value: The value to set the cpu request to. If None, the request will be
      removed. If this is the only request, request requirements will be
      removed. If this is the only requirement, requirements will be removed.

  Returns:
    The modified deployment configuration object.
  """
  if current.containerResources is not None:
    requirements = current.containerResources
  else:
    requirements = messages.PolicyControllerResourceRequirements()
  resource_list = messages.PolicyControllerResourceList()
  if requirements.requests is not None:
    resource_list = requirements.requests
  resource_list.cpu = value
  if resource_list.cpu is None and resource_list.memory is None:
    resource_list = None
  requirements.requests = resource_list
  if requirements.limits is None and requirements.requests is None:
    requirements = None
  current.containerResources = requirements
  return current


def update_mem_request(messages, current, value):
  """Configures a memory request for the current deployment configuration.

  Args:
    messages: the set of proto messages for this feature.
    current: the deployment configuration object being modified.
    value: The value to set the memory request to. If None, the request will be
      removed. If this is the only request, request requirements will be
      removed. If this is the only requirement, requirements will be removed.

  Returns:
    The modified deployment configuration object.
  """
  if current.containerResources is not None:
    requirements = current.containerResources
  else:
    requirements = messages.PolicyControllerResourceRequirements()
  resource_list = messages.PolicyControllerResourceList()
  if requirements.requests is not None:
    resource_list = requirements.requests
  resource_list.memory = value
  if resource_list.cpu is None and resource_list.memory is None:
    resource_list = None
  requirements.requests = resource_list
  if requirements.limits is None and requirements.requests is None:
    requirements = None
  current.containerResources = requirements
  return current


def _parse_key_value(key_value):
  split_key_value = key_value.split('=')
  if len(split_key_value) > 2:
    raise exceptions.Error(
        'Illegal value for toleration key-value={}'.format(key_value)
    )
  key = split_key_value[0]
  value = split_key_value[1] if len(split_key_value) == 2 else None
  operator = 'Exists' if len(split_key_value) == 1 else 'Equal'
  return key, value, operator


def add_toleration(messages, current, key_value, effect):
  """Adds a toleration to the current deployment configuration.

  Args:
    messages: the set of proto messages for this feature.
    current: the deployment configuration object being modified.
    key_value: the key-and-optional-value string specifying the toleration key
      and value.
    effect: Optional. If included, will set the effect value on the toleration.

  Returns:
    The modified deployment configuration object.
  """
  toleration = messages.PolicyControllerToleration()
  key, value, operator = _parse_key_value(key_value)

  toleration.operator = operator
  toleration.key = key
  if value is not None:
    toleration.value = value
  if effect is not None:
    toleration.effect = effect

  tolerations = []
  if current.podTolerations is not None:
    tolerations = current.podTolerations
  tolerations.append(toleration)
  current.podTolerations = tolerations
  return current


def remove_toleration(current, key_value, effect):
  """Removes a toleration from the current deployment configuration.

  A toleration must match exactly to be removed - it is not enough to match the
  key, or even key-value. The effect must also match the toleration being
  removed.

  Args:
    current: the deployment configuration object being modified.
    key_value: the key-and-optional-value string specifying the toleration key
      and value.
    effect: Optional. If included, will set the effect value on the toleration.

  Returns:
    The modified deployment configuration object.
  """
  current_tolerations = current.podTolerations
  key, value, operator = _parse_key_value(key_value)

  def match(toleration):
    return (
        (toleration.key == key)
        and (toleration.value == value)
        and (toleration.operator == operator)
        and (toleration.effect == effect)
    )

  # TODO(b/290215626) If empty, set cleared_fields value, ensure it's updated.
  current.podTolerations = [t for t in current_tolerations if not match(t)]
  return current


def update_pod_affinity(messages, current, value):
  """Configures the pod affinity for the current deployment configuration.

  Args:
    messages: the set of proto messages for this feature.
    current: the deployment configuration object being modified.
    value: The value to set the pod affinity to. If the value is the string
      "none" or value `None`, the pod affinity will be NO_AFFINITY.

  Returns:
    The modified deployment configuration object.
  """
  if value == 'anti':
    current.podAffinity = (
        messages.PolicyControllerPolicyControllerDeploymentConfig.PodAffinityValueValuesEnum.ANTI_AFFINITY
    )
  elif value is None or value == 'none':
    current.podAffinity = (
        messages.PolicyControllerPolicyControllerDeploymentConfig.PodAffinityValueValuesEnum.NO_AFFINITY
    )
  else:
    raise exceptions.Error(
        'invalid pod affinity option {} specified.'.format(value)
    )
  return current
