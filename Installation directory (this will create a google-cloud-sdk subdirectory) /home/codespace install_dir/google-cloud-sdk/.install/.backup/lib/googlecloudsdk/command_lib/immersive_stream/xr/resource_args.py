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
"""Shared resource flags for edgecontainer commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.immersive_stream.xr import util
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def ContentAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='name',
      help_text='Immersive Stream for XR content resource served by the {resource}.'
  )


def InstanceAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='name',
      help_text='Immersive Stream for XR service instance for the {resource}')


def LocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='Google Cloud location for the {resource}.',
      fallthroughs=[
          deps.Fallthrough(util.DefaultToGlobal, 'location is always global')
      ])


def GetContentResourceSpec():
  return concepts.ResourceSpec(
      resource_collection='stream.projects.locations.streamContents',
      api_version='v1alpha1',
      resource_name='content',
      streamContentsId=ContentAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def GetInstanceResourceSpec():
  return concepts.ResourceSpec(
      resource_collection='stream.projects.locations.streamInstances',
      api_version='v1alpha1',
      resource_name='instance',
      streamInstancesId=InstanceAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def AddContentResourceArg(parser, verb, positional=True):
  """Adds a resource argument for an Immersive Stream for XR content resource.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, whether the argument is positional or not.
  """
  name = 'content' if positional else '--content'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetContentResourceSpec(),
      'Immersive Stream for XR content resource {}.'.format(verb),
      required=True).AddToParser(parser)


def AddInstanceResourceArg(parser, verb, positional=True):
  """Adds a resource argument for an Immersive Stream for XR service instance resource.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, whether the argument is positional or not.
  """
  name = 'instance' if positional else '--instance'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetInstanceResourceSpec(),
      'Immersive Stream for XR service instance {}.'.format(verb),
      required=True).AddToParser(parser)
