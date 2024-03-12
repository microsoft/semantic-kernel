# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Utilities for AI Platform deployment resource pools commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import resources


def ParseOperation(operation_name):
  """Parse operation resource to the operation reference object.

  Args:
    operation_name: The operation resource to wait on

  Returns:
    The operation reference object
  """
  if '/deploymentResourcePools/' in operation_name:
    try:
      return resources.REGISTRY.ParseRelativeName(
          operation_name,
          collection=
          'aiplatform.projects.locations.deploymentResourcePools.operations')
    except resources.WrongResourceCollectionException:
      pass
  return resources.REGISTRY.ParseRelativeName(
      operation_name,
      collection='aiplatform.projects.locations.operations')
