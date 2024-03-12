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
"""Utilities for AI Platform model deployment monitoring jobs commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io

from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import errors
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io


def ParseJobName(name):
  return resources.REGISTRY.Parse(
      name, collection=constants.MODEL_MONITORING_JOBS_COLLECTION).Name()


def ReadInstanceFromArgs(path):
  """Reads the instance from the given file path ('-' for stdin).

  Args:
    path: str or None, a path to a file ('-' for stdin) containing the JSON
      body.

  Returns:
    A instance.

  Raises:
    InvalidInstancesFileError: If the input file is invalid (invalid format or
        contains too many/zero instances), or an improper combination of input
        files was given.
  """
  data = console_io.ReadFromFileOrStdin(path, binary=True)
  with io.BytesIO(data) as f:
    try:
      instance = yaml.load(f)
    except ValueError:
      raise errors.InvalidInstancesFileError(
          'Input instance are not in JSON format. '
          'See `gcloud ai model-monitoring-jobs create --help` for details.')

    if not isinstance(instance, dict):
      raise errors.InvalidInstancesFileError(
          'Input instance are not in JSON format. '
          'See `gcloud ai model-monitoring-jobs create --help` for details.')

    return instance


def ParseMonitoringJobOperation(operation_name):
  """Parse operation relative resource name to the operation reference object.

  Args:
    operation_name: The operation resource name

  Returns:
    The operation reference object
  """
  if '/modelDeploymentMonitoringJobs/' in operation_name:
    try:
      return resources.REGISTRY.ParseRelativeName(
          operation_name,
          collection='aiplatform.projects.locations.modelDeploymentMonitoringJobs.operations'
      )
    except resources.WrongResourceCollectionException:
      pass
  return resources.REGISTRY.ParseRelativeName(
      operation_name, collection='aiplatform.projects.locations.operations')
