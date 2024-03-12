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
"""Shared resource flags for Secure Source Manager commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def RegionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='region',
      help_text='Secure Source Manager location.')


def InstanceAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(name='instance')


def RepositoryAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(name='repository')


def GetRegionResourceSpec():
  return concepts.ResourceSpec(
      'securesourcemanager.projects.locations',
      resource_name='location',
      locationsId=RegionAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False,
  )


def GetInstanceResourceSpec():
  return concepts.ResourceSpec(
      'securesourcemanager.projects.locations.instances',
      resource_name='instance',
      instancesId=InstanceAttributeConfig(),
      locationsId=RegionAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetRepositoryResourceSpec():
  return concepts.ResourceSpec(
      'securesourcemanager.projects.locations.repositories',
      resource_name='repository',
      repositoriesId=RepositoryAttributeConfig(),
      locationsId=RegionAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False,
  )


def AddRegionResourceArg(parser, verb):
  """Add a resource argument for a Secure Source Manager location.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      '--region',
      GetRegionResourceSpec(),
      'The Secure Source Manager location {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddInstanceResourceArg(parser, verb):
  """Add a resource argument for a Secure Source Manager instance.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'instance',
      GetInstanceResourceSpec(),
      'The Secure Source Manager instance {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddRepositoryResourceArg(parser, verb):
  """Add a resource argument for a Secure Source Manager repository.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'repository',
      GetRepositoryResourceSpec(),
      'The Secure Source Manager repository {}.'.format(verb),
      required=True,
  ).AddToParser(parser)
