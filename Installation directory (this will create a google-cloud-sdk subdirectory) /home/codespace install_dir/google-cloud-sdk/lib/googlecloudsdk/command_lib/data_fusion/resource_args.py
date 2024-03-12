# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Shared resource flags for datafusion commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


def LocationAttributeConfig():
  fallthroughs = [
      deps.PropertyFallthrough(properties.VALUES.datafusion.location)
  ]
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='Compute Engine region in which to create the {resource}.',
      fallthroughs=fallthroughs)


def InstanceAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='instance',
      help_text='Cloud Data Fusion instance for the {resource}.')


def OperationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='operation',
      help_text='Cloud Data Fusion operation for the {resource}.')


def GetLocationResourceSpec():
  return concepts.ResourceSpec(
      'datafusion.projects.locations',
      resource_name='location',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig())


def GetInstanceResourceSpec():
  return concepts.ResourceSpec(
      'datafusion.projects.locations.instances',
      resource_name='instance',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      instancesId=InstanceAttributeConfig())


def GetOperationResourceSpec():
  return concepts.ResourceSpec(
      'datafusion.projects.locations.operations',
      resource_name='operation',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      operationsId=OperationAttributeConfig())


def AddLocationResourceArg(parser, description):
  concept_parsers.ConceptParser.ForResource(
      '--location', GetLocationResourceSpec(), description,
      required=True).AddToParser(parser)


def AddInstanceResourceArg(parser, description):
  concept_parsers.ConceptParser.ForResource(
      'instance',
      GetInstanceResourceSpec(),
      description,
      required=True,
      plural=False).AddToParser(parser)


def AddOperationResourceArg(parser, description):
  concept_parsers.ConceptParser.ForResource(
      'operation', GetOperationResourceSpec(), description,
      required=True).AddToParser(parser)
