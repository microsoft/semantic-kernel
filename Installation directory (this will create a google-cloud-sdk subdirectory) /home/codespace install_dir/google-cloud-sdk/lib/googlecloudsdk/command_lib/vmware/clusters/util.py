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
"""Utils for VMware Engine private-clouds clusters commands.

Provides helpers for parsing the autoscaling settings and node type configs and
for combining settings from many sources together.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import dataclasses
from typing import Any, Dict, List, Union

from googlecloudsdk.core import exceptions


@dataclasses.dataclass(frozen=True)
class ScalingThresholds:
  """Scaling thresholds for a single condition. Uses None for empty values.

  Attributes:
    scale_in: The threshold for scaling in.
    scale_out: The threshold for scaling out.
  """

  scale_in: int
  scale_out: int


def _MergeFields(left, right):
  """Merges two fields, favoring right one.

  Args:
    left: First field.
    right: Second field.

  Returns:
    Merged field.
  """
  return right if right is not None else left


def _MergeScalingThresholds(
    left: ScalingThresholds, right: ScalingThresholds
) -> ScalingThresholds:
  """Merges two ScalingThresholds objects, favoring right one.

  Args:
    left: First ScalingThresholds object.
    right: Second ScalingThresholds object.

  Returns:
    Merged ScalingThresholds.
  """
  if left is None:
    return right
  if right is None:
    return left

  return ScalingThresholds(
      scale_in=_MergeFields(left.scale_in, right.scale_in),
      scale_out=_MergeFields(left.scale_out, right.scale_out),
  )


@dataclasses.dataclass(frozen=True)
class AutoscalingPolicy:
  """Represents the autoscaling policy for a single node type.

  Uses None for empty settings.

  Attributes:
    node_type_id: The node type id.
    scale_out_size: The size of a single scale out operation.
    min_node_count: The minimum number of nodes of this type in the cluster.
    max_node_count: The maximum number of nodes of this type in the cluster.
    cpu_thresholds: The CPU thresholds.
    granted_memory_thresholds: The granted memory thresholds.
    consumed_memory_thresholds: The consumed memory thresholds.
    storage_thresholds: The storage thresholds.
  """

  node_type_id: str
  scale_out_size: int
  min_node_count: int
  max_node_count: int
  cpu_thresholds: ScalingThresholds
  granted_memory_thresholds: ScalingThresholds
  consumed_memory_thresholds: ScalingThresholds
  storage_thresholds: ScalingThresholds


def _MergeAutoscalingPolicies(
    left: AutoscalingPolicy,
    right: AutoscalingPolicy,
) -> AutoscalingPolicy:
  """Merges two AutoscalingPolicy objects, favoring right one.

  Args:
    left: First AutoscalingPolicy object.
    right: Second AutoscalingPolicy object.

  Returns:
    Merged AutoscalingPolicy.
  """
  if left is None:
    return right
  if right is None:
    return left

  return AutoscalingPolicy(
      node_type_id=_MergeFields(left.node_type_id, right.node_type_id),
      scale_out_size=_MergeFields(left.scale_out_size, right.scale_out_size),
      min_node_count=_MergeFields(left.min_node_count, right.min_node_count),
      max_node_count=_MergeFields(left.max_node_count, right.max_node_count),
      cpu_thresholds=_MergeScalingThresholds(
          left.cpu_thresholds, right.cpu_thresholds
      ),
      granted_memory_thresholds=_MergeScalingThresholds(
          left.granted_memory_thresholds, right.granted_memory_thresholds
      ),
      consumed_memory_thresholds=_MergeScalingThresholds(
          left.consumed_memory_thresholds, right.consumed_memory_thresholds
      ),
      storage_thresholds=_MergeScalingThresholds(
          left.storage_thresholds, right.storage_thresholds
      ),
  )


@dataclasses.dataclass(frozen=True)
class AutoscalingSettings:
  """Represents the autoscaling settings for a private-cloud cluster.

  Uses None for empty settings.

  Attributes:
    min_cluster_node_count: The minimum number of nodes in the cluster.
    max_cluster_node_count: The maximum number of nodes in the cluster.
    cool_down_period: The cool down period for autoscaling.
    autoscaling_policies: The autoscaling policies for each node type.
  """

  min_cluster_node_count: int
  max_cluster_node_count: int
  cool_down_period: str
  autoscaling_policies: Dict[str, AutoscalingPolicy]


def MergeAutoscalingSettings(
    left: AutoscalingSettings, right: AutoscalingSettings
) -> AutoscalingSettings:
  """Merges two AutoscalingSettings objects, favoring right one.

  Args:
    left: First AutoscalingSettings object.
    right: Second AutoscalingSettings object.

  Returns:
    Merged AutoscalingSettings.
  """
  if left is None:
    return right
  if right is None:
    return left

  policies = {}
  for policy_name, policy in left.autoscaling_policies.items():
    if policy_name in right.autoscaling_policies:
      policies[policy_name] = _MergeAutoscalingPolicies(
          policy, right.autoscaling_policies[policy_name]
      )
    else:
      policies[policy_name] = policy

  for policy_name, policy in right.autoscaling_policies.items():
    if policy_name not in left.autoscaling_policies:
      policies[policy_name] = policy

  return AutoscalingSettings(
      min_cluster_node_count=_MergeFields(
          left.min_cluster_node_count, right.min_cluster_node_count
      ),
      max_cluster_node_count=_MergeFields(
          left.max_cluster_node_count, right.max_cluster_node_count
      ),
      cool_down_period=_MergeFields(
          left.cool_down_period, right.cool_down_period
      ),
      autoscaling_policies=policies,
  )


class InvalidNodeConfigsProvidedError(exceptions.Error):

  def __init__(self, details):
    super(InvalidNodeConfigsProvidedError, self).__init__(
        f'INVALID_ARGUMENT: {details}'
    )


class InvalidAutoscalingSettingsProvidedError(exceptions.Error):

  def __init__(self, details):
    super(InvalidAutoscalingSettingsProvidedError, self).__init__(
        f'INVALID_ARGUMENT: {details}'
    )


NodeTypeConfig = collections.namedtuple(
    typename='NodeTypeConfig',
    field_names=['type', 'count', 'custom_core_count'],
)


def FindDuplicatedTypes(types):
  type_counts = collections.Counter(types)
  return [node_type for node_type, count in type_counts.items() if count > 1]


def ParseNodesConfigsParameters(nodes_configs):
  requested_node_types = [config['type'] for config in nodes_configs]

  duplicated_types = FindDuplicatedTypes(requested_node_types)
  if duplicated_types:
    raise InvalidNodeConfigsProvidedError(
        'types: {} provided more than once.'.format(duplicated_types)
    )

  return [
      NodeTypeConfig(
          config['type'], config['count'], config.get('custom-core-count', 0)
      )
      for config in nodes_configs
  ]


def ParseAutoscalingSettingsFromInlinedFormat(
    min_cluster_node_count: int,
    max_cluster_node_count: int,
    cool_down_period: str,
    autoscaling_policies: List[Dict[str, Union[str, int]]],
) -> AutoscalingSettings:
  """Parses inlined autoscaling settings (passed as CLI arguments).

  The resulting object can later be passed to
  googlecloudsdk.api_lib.vmware.util.ConstructAutoscalingSettingsMessage.

  Args:
    min_cluster_node_count: autoscaling-min-cluster-node-count CLI argument.
    max_cluster_node_count: autoscaling-max-cluster-node-count CLI argument.
    cool_down_period: autoscaling-cool-down-period CLI argument.
    autoscaling_policies: list of update-autoscaling-policy CLI arguments.

  Returns:
    Equivalent AutoscalingSettings instance.
  """
  parsed_settings = AutoscalingSettings(
      min_cluster_node_count=min_cluster_node_count,
      max_cluster_node_count=max_cluster_node_count,
      cool_down_period=cool_down_period,
      autoscaling_policies={},
  )

  for policy in autoscaling_policies:
    parsed_policy = AutoscalingPolicy(
        node_type_id=policy.get('node-type-id'),
        scale_out_size=policy.get('scale-out-size'),
        min_node_count=policy.get('min-node-count'),
        max_node_count=policy.get('max-node-count'),
        cpu_thresholds=_AutoscalingThresholdsFromPolicy(
            policy, 'cpu-thresholds'
        ),
        granted_memory_thresholds=_AutoscalingThresholdsFromPolicy(
            policy, 'granted-memory-thresholds'
        ),
        consumed_memory_thresholds=_AutoscalingThresholdsFromPolicy(
            policy, 'consumed-memory-thresholds'
        ),
        storage_thresholds=_AutoscalingThresholdsFromPolicy(
            policy, 'storage-thresholds'
        ),
    )

    parsed_settings.autoscaling_policies[policy['name']] = parsed_policy

  return parsed_settings


def _AutoscalingThresholdsFromPolicy(
    policy: Dict[str, Union[str, int]], threshold: str
) -> ScalingThresholds:
  scale_in = policy.get(f'{threshold}-scale-in')
  scale_out = policy.get(f'{threshold}-scale-out')
  if scale_in is None and scale_out is None:
    return None
  return ScalingThresholds(scale_in=scale_in, scale_out=scale_out)


def _ValidateIfOnlySupportedKeysArePassed(
    keys: List[str], supported_keys: List[str]
):
  for key in keys:
    if key not in supported_keys:
      raise InvalidAutoscalingSettingsProvidedError(
          'unsupported key: {key}, supported keys are: {supported_keys}'.format(
              key=key, supported_keys=supported_keys
          )
      )


def ParseAutoscalingSettingsFromFileFormat(
    cluster: Dict[str, Any]
) -> AutoscalingSettings:
  """Parses the autoscaling settings from the format returned by  the describe command.

  The resulting object can later be passed to
  googlecloudsdk.api_lib.vmware.util.ConstructAutoscalingSettingsMessage.

  Args:
    cluster: dictionary with the settings. Parsed from a file provided by user.

  Returns:
    Equivalent AutoscalingSettings instance.

  Raises:
    InvalidAutoscalingSettingsProvidedError: if the file format was wrong.
  """

  def _ParseThresholds(thresholds_dict):
    if thresholds_dict is None:
      return None

    _ValidateIfOnlySupportedKeysArePassed(
        thresholds_dict.keys(), ['scaleIn', 'scaleOut']
    )

    return ScalingThresholds(
        scale_in=thresholds_dict.get('scaleIn'),
        scale_out=thresholds_dict.get('scaleOut'),
    )

  _ValidateIfOnlySupportedKeysArePassed(cluster.keys(), ['autoscalingSettings'])
  if 'autoscalingSettings' not in cluster:
    raise InvalidAutoscalingSettingsProvidedError(
        'autoscalingSettings not provided in the file'
    )
  autoscaling_settings = cluster['autoscalingSettings']

  _ValidateIfOnlySupportedKeysArePassed(
      autoscaling_settings.keys(),
      [
          'minClusterNodeCount',
          'maxClusterNodeCount',
          'coolDownPeriod',
          'autoscalingPolicies',
      ],
  )
  parsed_settings = AutoscalingSettings(
      min_cluster_node_count=autoscaling_settings.get('minClusterNodeCount'),
      max_cluster_node_count=autoscaling_settings.get('maxClusterNodeCount'),
      cool_down_period=autoscaling_settings.get('coolDownPeriod'),
      autoscaling_policies={},
  )

  if 'autoscalingPolicies' not in autoscaling_settings:
    return parsed_settings

  for policy_name, policy_settings in autoscaling_settings[
      'autoscalingPolicies'
  ].items():
    _ValidateIfOnlySupportedKeysArePassed(
        policy_settings.keys(),
        [
            'nodeTypeId',
            'scaleOutSize',
            'minNodeCount',
            'maxNodeCount',
            'cpuThresholds',
            'grantedMemoryThresholds',
            'consumedMemoryThresholds',
            'storageThresholds',
        ],
    )
    parsed_policy = AutoscalingPolicy(
        node_type_id=policy_settings.get('nodeTypeId'),
        scale_out_size=policy_settings.get('scaleOutSize'),
        min_node_count=policy_settings.get('minNodeCount'),
        max_node_count=policy_settings.get('maxNodeCount'),
        cpu_thresholds=_ParseThresholds(policy_settings.get('cpuThresholds')),
        granted_memory_thresholds=_ParseThresholds(
            policy_settings.get('grantedMemoryThresholds')
        ),
        consumed_memory_thresholds=_ParseThresholds(
            policy_settings.get('consumedMemoryThresholds')
        ),
        storage_thresholds=_ParseThresholds(
            policy_settings.get('storageThresholds')
        ),
    )
    parsed_settings.autoscaling_policies[policy_name] = parsed_policy

  return parsed_settings


def ParseAutoscalingSettingsFromApiFormat(
    cluster_message,
) -> AutoscalingSettings:
  """Parses the autoscaling settings from the format returned by the describe command.

  The resulting object can later be passed to
  googlecloudsdk.api_lib.vmware.util.ConstructAutoscalingSettingsMessage.

  Args:
    cluster_message: cluster object with the autoscaling settings.

  Returns:
    Equivalent AutoscalingSettings istance.
  """
  if cluster_message.autoscalingSettings is None:
    return None

  autoscaling_settings = cluster_message.autoscalingSettings

  parsed_settings = AutoscalingSettings(
      min_cluster_node_count=autoscaling_settings.minClusterNodeCount,
      max_cluster_node_count=autoscaling_settings.maxClusterNodeCount,
      cool_down_period=autoscaling_settings.coolDownPeriod,
      autoscaling_policies={},
  )

  for item in autoscaling_settings.autoscalingPolicies.additionalProperties:
    policy_name, policy_settings = item.key, item.value

    def _ParseThresholds(thresholds):
      if thresholds is None:
        return None
      return ScalingThresholds(
          scale_in=thresholds.scaleIn,
          scale_out=thresholds.scaleOut,
      )

    parsed_policy = AutoscalingPolicy(
        node_type_id=policy_settings.nodeTypeId,
        scale_out_size=policy_settings.scaleOutSize,
        min_node_count=policy_settings.minNodeCount,
        max_node_count=policy_settings.maxNodeCount,
        cpu_thresholds=_ParseThresholds(policy_settings.cpuThresholds),
        granted_memory_thresholds=_ParseThresholds(
            policy_settings.grantedMemoryThresholds
        ),
        consumed_memory_thresholds=_ParseThresholds(
            policy_settings.consumedMemoryThresholds
        ),
        storage_thresholds=_ParseThresholds(policy_settings.storageThresholds),
    )
    parsed_settings.autoscaling_policies[policy_name] = parsed_policy

  return parsed_settings
