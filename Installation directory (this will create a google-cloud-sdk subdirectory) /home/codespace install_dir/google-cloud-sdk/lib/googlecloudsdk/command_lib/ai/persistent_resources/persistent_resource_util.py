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
"""Utilities for AI Platform persistent resource commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.apis import arg_utils

PERSISTENT_RESOURCE_COLLECTION = 'aiplatform.projects.locations.persistentResources'


def _ConstructSingleResourcePoolSpec(aiplatform_client,
                                     spec):
  """Constructs a single resource pool spec.

  Args:
    aiplatform_client: The AI Platform API client used.
    spec: A dict whose fields represent a resource pool spec.

  Returns:
    A ResourcePoolSpec message instance for setting a resource pool in a
    Persistent Resource
  """
  resource_pool = aiplatform_client.GetMessage('ResourcePool')()

  machine_spec_msg = aiplatform_client.GetMessage('MachineSpec')
  machine_spec = machine_spec_msg(machineType=spec.get('machine-type'))
  accelerator_type = spec.get('accelerator-type')
  if accelerator_type:
    machine_spec.acceleratorType = arg_utils.ChoiceToEnum(
        accelerator_type, machine_spec_msg.AcceleratorTypeValueValuesEnum)
    machine_spec.acceleratorCount = int(spec.get('accelerator-count', 1))
  resource_pool.machineSpec = machine_spec

  replica_count = spec.get('replica-count')
  if replica_count:
    resource_pool.replicaCount = int(replica_count)
  min_replica_count = spec.get('min-replica-count')
  max_replica_count = spec.get('max-replica-count')
  if min_replica_count or max_replica_count:
    autoscaling_spec = (
        aiplatform_client.GetMessage('ResourcePoolAutoscalingSpec')())
    autoscaling_spec.minReplicaCount = int(min_replica_count)
    autoscaling_spec.maxReplicaCount = int(max_replica_count)
    resource_pool.autoscalingSpec = autoscaling_spec

  disk_type = spec.get('disk-type')
  disk_size = spec.get('disk-size')
  if disk_type:
    disk_spec_msg = aiplatform_client.GetMessage('DiskSpec')
    disk_spec = disk_spec_msg(bootDiskType=disk_type, bootDiskSizeGb=disk_size)
    resource_pool.diskSpec = disk_spec

  return resource_pool


def _ConstructResourcePoolSpecs(aiplatform_client, specs, **kwargs):
  """Constructs the resource pool specs for a persistent resource.

  Args:
    aiplatform_client: The AI Platform API client used.
    specs: A list of dict of resource pool specs, supposedly derived from
      the gcloud command flags.
    **kwargs: The keyword args to pass down to construct each worker pool spec.

  Returns:
    A list of ResourcePool message instances for creating a Persistent Resource.
  """
  resource_pool_specs = []

  for spec in specs:
    if spec:
      resource_pool_specs.append(
          _ConstructSingleResourcePoolSpec(aiplatform_client, spec, **kwargs))
    else:
      resource_pool_specs.append(
          aiplatform_client.GetMessage('ResourcePoolSpec')())

  return resource_pool_specs


def ConstructResourcePools(
    aiplatform_client,
    persistent_resource_config=None,
    resource_pool_specs=None,
    **kwargs
):
  """Constructs the resource pools to be used to create a Persistent Resource.

  Resource pools from the config file and arguments will be combined.

  Args:
    aiplatform_client: The AI Platform API client used.
    persistent_resource_config: A Persistent Resource configuration imported
      from a YAML config.
    resource_pool_specs: A dict of worker pool specification, usually derived
      from the gcloud command argument values.
    **kwargs: The keyword args to pass to construct the worker pool specs.

  Returns:
    An array of ResourcePool messages for creating a Persistent Resource.
  """

  resource_pools = []
  if isinstance(persistent_resource_config.resourcePools, list):
    resource_pools = persistent_resource_config.resourcePools
  if resource_pool_specs:
    resource_pools = resource_pools + _ConstructResourcePoolSpecs(
        aiplatform_client, resource_pool_specs, **kwargs)

  return resource_pools


def _IsKwargsDefined(key, **kwargs):
  return key in kwargs and bool(kwargs.get(key))
