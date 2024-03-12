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
"""Shared resource flags for Cloud SDK attach and detach disk command.

resource_args adds the TPU resource argument to
the attach-disk and detach-disk command.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts


def TPUAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='TPU', help_text='The TPU Name for the {resource}.')


def ZoneAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='zone', help_text='The Cloud zone for the {resource}.')


def GetTPUResourceSpec(resource_name='TPU'):
  return concepts.ResourceSpec(
      'tpu.projects.locations.nodes',
      resource_name=resource_name,
      locationsId=ZoneAttributeConfig(),
      nodesId=TPUAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)
