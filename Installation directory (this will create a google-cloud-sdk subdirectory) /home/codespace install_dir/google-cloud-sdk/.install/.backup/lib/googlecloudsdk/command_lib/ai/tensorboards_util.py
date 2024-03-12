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
"""Utilities for AI Platform Tensorboard commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.tensorboard_time_series import client
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import resources


def ParseTensorboardOperation(operation_name):
  """Parse operation relative resource name to the operation reference object.

  Args:
    operation_name: The operation resource name

  Returns:
    The operation reference object
  """
  collection = 'aiplatform.projects.locations'
  if '/tensorboards/' in operation_name:
    collection += '.tensorboards'
  if '/experiments/' in operation_name:
    collection += '.experiments'
  if '/runs/' in operation_name:
    collection += '.runs'
  collection += '.operations'
  try:
    return resources.REGISTRY.ParseRelativeName(
        operation_name, collection=collection)
  except resources.WrongResourceCollectionException:
    return resources.REGISTRY.ParseRelativeName(
        operation_name, collection='aiplatform.projects.locations.operations')


_TYPE_CHOICES = {
    'SCALAR': (
        'scalar',
        'Used for tensorboard-time-series that is a list of scalars. E.g. '
        'accuracy of a model over epochs/time.'
    ),
    'TENSOR': (
        'tensor',
        'Used for tensorboard-time-series that is a list of tensors. E.g. '
        'histograms of weights of layer in a model over epoch/time.'
    ),
    'BLOB_SEQUENCE': (
        'blob-sequence',
        'Used for tensorboard-time-series that is a list of blob sequences. '
        'E.g. set of sample images with labels over epochs/time.'
    ),
}


def GetTensorboardTimeSeriesTypeArg(noun):
  return arg_utils.ChoiceEnumMapper(
      '--type',
      client.GetMessagesModule(
      ).GoogleCloudAiplatformV1beta1TensorboardTimeSeries
      .ValueTypeValueValuesEnum,
      required=True,
      custom_mappings=_TYPE_CHOICES,
      help_str='Value type of the {noun}.'.format(noun=noun),
      default=None)
