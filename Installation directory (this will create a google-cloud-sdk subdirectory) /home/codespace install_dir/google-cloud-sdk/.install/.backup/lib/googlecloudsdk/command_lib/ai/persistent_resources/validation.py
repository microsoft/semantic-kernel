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
"""Validation of the arguments for the persistent-resources command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai import util as api_util
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import validation


def ValidateRegion(region):
  """Validate whether the given region is allowed for persistent resources."""
  validation.ValidateRegion(
      region, available_regions=constants.SUPPORTED_TRAINING_REGIONS)


def ValidateCreateArgs(args, persistent_resource_config, version):
  """Validate the argument values specified in the `create` command."""
  if args.resource_pool_spec:
    _ValidateResourcePoolSpecArgs(args.resource_pool_spec, version)
  if isinstance(persistent_resource_config.resourcePools, list):
    _ValidateResourcePoolSpecsFromConfig(
        persistent_resource_config.resourcePools, version)

  if (not args.resource_pool_spec and
      not isinstance(persistent_resource_config.resourcePools, list)):
    raise exceptions.InvalidArgumentException(
        '--resource-pool-spec',
        'No resource pools specified. At least one resource pool must be '
        'provided via a YAML config file (--config) or via the '
        '--resource-pool-spec arg.')


def _ValidateResourcePoolSpecArgs(resource_pool_specs, version):
  """Validates the argument values specified via `--resource-pool-spec` flags.

  Args:
    resource_pool_specs: List[dict], a list of resource pool specs specified via
      command line arguments.
    version: str, the API version this command will interact with, either GA or
      BETA.
  """
  if not resource_pool_specs[0]:
    raise exceptions.InvalidArgumentException(
        '--resource-pool-spec',
        'Empty value is not allowed for the first `--resource-pool-spec` flag.')

  _ValidateHardwareInResourcePoolSpecArgs(resource_pool_specs, version)


def _ValidateHardwareInResourcePoolSpecArgs(resource_pool_specs, version):
  """Validates the hardware related fields specified in `--resource-pool-spec` flags.

  Args:
    resource_pool_specs: List[dict], a list of resource pool specs specified via
      command line arguments.
    version: str, the API version this command will interact with, either GA or
      BETA.
  """
  for spec in resource_pool_specs:
    if spec:
      if 'machine-type' not in spec:
        raise exceptions.InvalidArgumentException(
            '--resource-pool-spec',
            'Key [machine-type] required in dict arg but not provided.')

      if ('min-replica-count' in spec) and ('max-replica-count' not in spec):
        raise exceptions.InvalidArgumentException(
            '--resource-pool-spec',
            'Key [max-replica-count] required in dict arg when key '
            '[min-replica-count] is provided.')

      if ('max-replica-count' in spec) and ('min-replica-count' not in spec):
        raise exceptions.InvalidArgumentException(
            '--resource-pool-spec',
            'Key [min-replica-count] required in dict arg when key '
            '[max-replica-count] is provided.')

      # Require replica count if autoscaling is not enabled on the resource pool
      if ('replica-count' not in spec) and ('min-replica-count' not in spec):
        raise exceptions.InvalidArgumentException(
            '--resource-pool-spec',
            'Key [replica-count] required in dict arg but not provided.')

      if ('accelerator-count' in spec) != ('accelerator-type' in spec):
        raise exceptions.InvalidArgumentException(
            '--resource-pool-spec',
            'Key [accelerator-type] and [accelerator-count] are required to ' +
            'use accelerators.')

      accelerator_type = spec.get('accelerator-type', None)
      if accelerator_type:
        type_enum = api_util.GetMessage(
            'MachineSpec', version).AcceleratorTypeValueValuesEnum
        valid_types = [
            type for type in type_enum.names()
            if type.startswith('NVIDIA')
        ]
        if accelerator_type not in valid_types:
          raise exceptions.InvalidArgumentException(
              '--resource-pool-spec',
              ('Found invalid value of [accelerator-type]: {actual}. '
               'Available values are [{expected}].').format(
                   actual=accelerator_type,
                   expected=', '.join(v for v in sorted(valid_types))))


def _ValidateResourcePoolSpecsFromConfig(resource_pools, version):
  """Validate ResourcePoolSpec message instances imported from the config file."""
  if not resource_pools:
    raise exceptions.InvalidArgumentException(
        '--config',
        'At least one [resourcePools] required in but not provided in config.')
  for spec in resource_pools:
    if not spec.machineSpec:
      raise exceptions.InvalidArgumentException(
          '--config',
          'Field [machineSpec] required in but not provided in config.')

    if not spec.machineSpec.machineType:
      raise exceptions.InvalidArgumentException(
          '--config',
          'Field [machineType] required in but not provided in config.')

    if (not spec.replicaCount) and (not spec.autoscalingSpec):
      raise exceptions.InvalidArgumentException(
          '--config',
          'Field [replicaCount] required in but not provided in config.')

    if (spec.autoscalingSpec) and (not spec.autoscalingSpec.minReplicaCount):
      raise exceptions.InvalidArgumentException(
          '--config',
          'Field [minReplicaCount] required when using autoscaling')

    if (spec.autoscalingSpec) and (not spec.autoscalingSpec.maxReplicaCount):
      raise exceptions.InvalidArgumentException(
          '--config',
          'Field [maxReplicaCount] required when using autoscaling')

    if (spec.machineSpec.acceleratorCount and
        not spec.machineSpec.acceleratorType):
      raise exceptions.InvalidArgumentException(
          '--config',
          'Field [acceleratorType] required as [acceleratorCount] is specified'
          'in config.')

    if spec.diskSpec and (spec.diskSpec.bootDiskSizeGb and
                          not spec.diskSpec.bootDiskType):
      raise exceptions.InvalidArgumentException(
          '--config',
          'Field [bootDiskType] required as [bootDiskSizeGb] is specified'
          'in config.')

    if spec.machineSpec.acceleratorType:
      accelerator_type = str(spec.machineSpec.acceleratorType.name)
      type_enum = api_util.GetMessage(
          'MachineSpec', version).AcceleratorTypeValueValuesEnum
      valid_types = [
          type for type in type_enum.names()
          if type.startswith('NVIDIA')
      ]
      if accelerator_type not in valid_types:
        raise exceptions.InvalidArgumentException(
            '--config',
            ('Found invalid value of [acceleratorType]: {actual}. '
             'Available values are [{expected}].').format(
                 actual=accelerator_type,
                 expected=', '.join(v for v in sorted(valid_types))))
