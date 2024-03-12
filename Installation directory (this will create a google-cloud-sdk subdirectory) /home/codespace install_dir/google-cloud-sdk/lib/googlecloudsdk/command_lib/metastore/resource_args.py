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
"""Shared resource flags for Dataproc Metastore commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


def AddServiceResourceArg(parser,
                          verb,
                          positional=True,
                          required=True,
                          plural=False):
  """Add a resource argument for a Dataproc Metastore Service.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command
    verb: str, the verb to describe the resource, for example, 'to update'.
    positional: boolean, if True, means that the resource is a positional rather
      than a flag.
    required: boolean, if True, the arg is required
    plural: boolean, if True, expects a list of resources
  """
  noun = 'service' + ('s' if plural else '')
  name = _BuildArgName(noun, positional)
  concept_parsers.ConceptParser.ForResource(
      name,
      GetServiceResourceSpec(),
      'The {} {}.'.format(noun, verb),
      required=required,
      plural=plural).AddToParser(parser)


def AddOperationResourceArg(parser,
                            verb,
                            positional=True,
                            required=True,
                            plural=False):
  """Add a resource argument for a Dataproc Metastore long-running operation.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command
    verb: str, the verb to describe the resource, for example, 'to update'.
    positional: boolean, if True, means that the resource is a positional rather
      than a flag.
    required: boolean, if True, the arg is required
    plural: boolean, if True, expects a list of resources
  """
  noun = 'operation' + ('s' if plural else '')
  name = _BuildArgName(noun, positional)
  concept_parsers.ConceptParser.ForResource(
      name,
      GetOperationResourceSpec(),
      'The {} {}.'.format(noun, verb),
      required=required,
      plural=plural).AddToParser(parser)


def AddFederationResourceArg(parser,
                             verb,
                             positional=True,
                             required=True,
                             plural=False):
  """Add a resource argument for a Dataproc Metastore Federation.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command
    verb: str, the verb to describe the resource, for example, 'to update'.
    positional: boolean, if True, means that the resource is a positional rather
      than a flag.
    required: boolean, if True, the arg is required
    plural: boolean, if True, expects a list of resources
  """
  noun = 'federation' + ('s' if plural else '')
  name = _BuildArgName(noun, positional)
  concept_parsers.ConceptParser.ForResource(
      name,
      GetFederationResourceSpec(),
      'The {} {}.'.format(noun, verb),
      required=required,
      plural=plural).AddToParser(parser)


def GetServiceResourceSpec():
  return concepts.ResourceSpec(
      'metastore.projects.locations.services',
      resource_name='service',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      servicesId=ServiceAttributeConfig())


def GetOperationResourceSpec():
  return concepts.ResourceSpec(
      'metastore.projects.locations.operations',
      resource_name='operation',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      operationsId=OperationAttributeConfig())


def GetFederationResourceSpec():
  return concepts.ResourceSpec(
      'metastore.projects.locations.federations',
      resource_name='federation',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      federationsId=FederationAttributeConfig())


def ServiceAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='service',
      help_text='Dataproc Metastore service for the {resource}.')


def FederationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='federation',
      help_text='Dataproc Metastore federation for the {resource}.')


def OperationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='operation',
      help_text='Dataproc Metastore operation for the {resource}.')


def LocationAttributeConfig(fallthroughs_enabled=True):
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='Location to which the {resource} belongs.',
      fallthroughs=([
          deps.PropertyFallthrough(properties.VALUES.metastore.location)
      ] if fallthroughs_enabled else []))


def _BuildArgName(name, positional):
  return '{}{}'.format('' if positional else '--', name)
