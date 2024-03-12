# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Utilities for validating parameters."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.ai import constants


def ValidateDisplayName(display_name):
  """Validates the display name."""
  if display_name is not None and not display_name:
    raise exceptions.InvalidArgumentException(
        '--display-name',
        'Display name can not be empty.')


def ValidateRegion(region, available_regions=constants.SUPPORTED_REGION):
  """Validates whether a given region is among the available ones."""
  if region not in available_regions:
    raise exceptions.InvalidArgumentException(
        'region', 'Available values are [{}], but found [{}].'.format(
            ', '.join(available_regions), region))


def GetAndValidateKmsKey(args):
  """Parse CMEK resource arg, and check if the arg was partially specified."""
  if hasattr(args.CONCEPTS, 'kms_key'):
    kms_ref = args.CONCEPTS.kms_key.Parse()
    if kms_ref:
      return kms_ref.RelativeName()
    else:
      for keyword in ['kms_key', 'kms_keyring', 'kms_location', 'kms_project']:
        if getattr(args, keyword, None):
          raise exceptions.InvalidArgumentException(
              '--kms-key', 'Encryption key not fully specified.')


def ValidateAutoscalingMetricSpecs(specs):
  """Value validation for autoscaling metric specs target name and value."""
  if specs is None:
    return

  for key, value in specs.items():
    if key not in constants.OP_AUTOSCALING_METRIC_NAME_MAPPER:
      raise exceptions.InvalidArgumentException(
          '--autoscaling-metric-specs',
          """Autoscaling metric name can only be one of the following: {}."""
          .format(', '.join([
              "'{}'".format(c) for c in sorted(
                  constants.OP_AUTOSCALING_METRIC_NAME_MAPPER.keys())
          ])))

    if value <= 0 or value > 100:
      raise exceptions.InvalidArgumentException(
          '--autoscaling-metric-specs',
          'Metric target value %s is not between 0 and 100.' % value)


def ValidateSharedResourceArgs(shared_resources_ref=None,
                               machine_type=None,
                               accelerator_dict=None,
                               min_replica_count=None,
                               max_replica_count=None,
                               autoscaling_metric_specs=None):
  """Value validation for dedicated resource args while making a shared resource command call.

  Args:
      shared_resources_ref: str or None, the shared deployment resource pool
      full name the model should use, formatted as the full URI
      machine_type: str or None, the type of the machine to serve the model.
      accelerator_dict: dict or None, the accelerator attached to the deployed
        model from args.
      min_replica_count: int or None, the minimum number of replicas the
        deployed model will be always deployed on.
      max_replica_count: int or None, the maximum number of replicas the
        deployed model may be deployed on.
      autoscaling_metric_specs: dict or None, the metric specification that
        defines the target resource utilization for calculating the desired
        replica count.
  """
  if shared_resources_ref is None:
    return

  if machine_type is not None:
    raise exceptions.InvalidArgumentException('--machine-type', """Cannot use
    machine type and shared resources in the same command.""")
  if accelerator_dict is not None:
    raise exceptions.InvalidArgumentException('--accelerator', """Cannot
    use accelerator and shared resources in the same command.""")
  if min_replica_count is not None:
    raise exceptions.InvalidArgumentException('--max-replica-count', """Cannot
    use max replica count and shared resources in the same command.""")
  if max_replica_count is not None:
    raise exceptions.InvalidArgumentException('--min-replica-count', """Cannot
    use min replica count and shared resources in the same command.""")
  if autoscaling_metric_specs is not None:
    raise exceptions.InvalidArgumentException(
        '--autoscaling-metric-specs', """Cannot use autoscaling metric specs
        and shared resources in the same command.""")


def ValidateEndpointArgs(network=None, public_endpoint_enabled=None):
  """Validates the network and public_endpoint_enabled."""
  if network is not None and public_endpoint_enabled:
    raise exceptions.InvalidArgumentException(
        'Please either set --network for private endpoint, or set'
        ' --public-endpoint-enabled',
        'for public enpdoint.',
    )
