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
"""Common Flags for Overwatch commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def organization_attribute_config():
  return concepts.ResourceParameterAttributeConfig(
      name='organization', help_text='Organization ID of the {resource}.')


def location_attribute_config():
  return concepts.ResourceParameterAttributeConfig(
      name='location', help_text='Location of the {resource}.')


def overwatch_attribute_config():
  return concepts.ResourceParameterAttributeConfig(
      name='overwatch', help_text='Overwatch ID of the {resource}.')


def operation_attribute_config():
  return concepts.ResourceParameterAttributeConfig(
      name='operation', help_text='Operation ID of the {resource}.')


def get_parent_resource_specs():
  return concepts.ResourceSpec(
      'securedlandingzone.organizations.locations',
      resource_name='parent',
      organizationsId=organization_attribute_config(),
      locationsId=location_attribute_config())


def get_overwatch_resource_specs():
  return concepts.ResourceSpec(
      'securedlandingzone.organizations.locations.overwatches',
      resource_name='overwatch',
      organizationsId=organization_attribute_config(),
      locationsId=location_attribute_config(),
      overwatchesId=overwatch_attribute_config())


def get_operation_resource_specs():
  return concepts.ResourceSpec(
      'securedlandingzone.organizations.locations.operations',
      resource_name='operation',
      organizationsId=organization_attribute_config(),
      locationsId=location_attribute_config(),
      operationsId=operation_attribute_config())


def add_parent_flag(parser):
  concept_parsers.ConceptParser.ForResource(
      'PARENT',
      get_parent_resource_specs(),
      'Parent of the overwatch instances.',
      required=True).AddToParser(parser)


def get_size_flag():
  return base.Argument(
      '--size', required=False, help='Page size of overwatch list.')


def get_page_token_flag():
  return base.Argument(
      '--page-token', required=False, help='Page token to retrieve next page.')


def add_overwatch_path_flag(parser):
  concept_parsers.ConceptParser.ForResource(
      'OVERWATCH',
      get_overwatch_resource_specs(),
      'Name of the overwatch instance.',
      required=True).AddToParser(parser)


def get_blueprint_plan_flag():
  return base.Argument(
      '--blueprint-plan-file',
      required=True,
      help='Path of the JSON file containing the blueprint plan.')


def get_update_mask_flag():
  return base.Argument(
      '--update-mask',
      help='Update mask providing the fields that are required to be updated.')


def add_operation_flag(parser):
  concept_parsers.ConceptParser.ForResource(
      'OPERATION',
      get_operation_resource_specs(),
      'Name of the longrunning operation.',
      required=True).AddToParser(parser)
