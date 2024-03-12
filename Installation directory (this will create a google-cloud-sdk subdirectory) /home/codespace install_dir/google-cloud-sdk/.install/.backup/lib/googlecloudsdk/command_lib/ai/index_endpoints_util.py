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
"""Utilities for AI Platform index endpoints commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import resources


def BuildParentOperation(project_id, location_id, index_endpoint_id,
                         operation_id):
  """Build multi-parent operation."""
  return ParseIndexEndpointOperation(
      'projects/{}/locations/{}/indexEndpoints/{}/operations/{}'.format(
          project_id, location_id, index_endpoint_id, operation_id))


def ParseIndexEndpointOperation(operation_name):
  """Parse operation relative resource name to the operation reference object.

  Args:
    operation_name: The operation resource name

  Returns:
    The operation reference object
  """
  if '/indexEndpoints/' in operation_name:
    try:
      return resources.REGISTRY.ParseRelativeName(
          operation_name,
          collection='aiplatform.projects.locations.indexEndpoints.operations')
    except resources.WrongResourceCollectionException:
      pass
  return resources.REGISTRY.ParseRelativeName(
      operation_name, collection='aiplatform.projects.locations.operations')
