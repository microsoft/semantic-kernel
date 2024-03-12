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
"""Shared resource args for insights dataset-configs command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def location_attribute_config():
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='Insights supported Google Cloud location for the {resource}.',
  )


def dataset_config_attribute_config():
  return concepts.ResourceParameterAttributeConfig(
      name='dataset-config',
      help_text='Dataset Config ID for the {resource}.',
  )


def get_dataset_config_resource_spec():
  return concepts.ResourceSpec(
      'storageinsights.projects.locations.datasetConfigs',
      resource_name='dataset-config',
      datasetConfigsId=dataset_config_attribute_config(),
      locationsId=location_attribute_config(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def add_dataset_config_resource_arg(parser, verb):
  """Adds a resource argument for storage insights dataset config.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'dataset_config',
      get_dataset_config_resource_spec(),
      'The Dataset config {}.'.format(verb),
      required=True).AddToParser(parser)

