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
"""Shared resource args for insights inventory-reports command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def location_attribute_config():
  return concepts.ResourceParameterAttributeConfig(
      name='location', help_text='Google Cloud location for the {resource}.')


def report_config_attribute_config():
  return concepts.ResourceParameterAttributeConfig(
      name='report-config', help_text='Report Config ID for the {resource}.')


def report_detail_attribute_config():
  return concepts.ResourceParameterAttributeConfig(
      name='report-detail', help_text='Report Detail ID for the {resource}.')


def get_report_config_resource_spec():
  return concepts.ResourceSpec(
      'storageinsights.projects.locations.reportConfigs',
      resource_name='report-config',
      reportConfigsId=report_config_attribute_config(),
      locationsId=location_attribute_config(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def get_report_detail_resource_spec():
  return concepts.ResourceSpec(
      'storageinsights.projects.locations.reportConfigs.reportDetails',
      resource_name='report-detail',
      reportDetailsId=report_detail_attribute_config(),
      reportConfigsId=report_config_attribute_config(),
      locationsId=location_attribute_config(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def add_report_config_resource_arg(parser, verb):
  """Adds a resource argument for storage insights report config.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'report_config',
      get_report_config_resource_spec(),
      'The Report config {}.'.format(verb),
      required=True).AddToParser(parser)


def add_report_detail_resource_arg(parser, verb):
  """Adds a resource argument for storage insights report detail.

  Args:
    parser: The argparse  parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'report_detail',
      get_report_detail_resource_spec(),
      'The report detail {}.'.format(verb),
      required=True).AddToParser(parser)
