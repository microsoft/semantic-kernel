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
"""Shared resource flags for Edgenetwork commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def LocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location', help_text='The Cloud location for the {resource}.')


def ZoneAttributeConfig(name='zone'):
  return concepts.ResourceParameterAttributeConfig(
      name=name,
      help_text='The zone of the {resource}.',
      completion_request_params={'fieldMask': 'name'},
      completion_id_field='id')


def SubnetAttributeConfig(name='subnet'):
  return concepts.ResourceParameterAttributeConfig(
      name=name,
      help_text='The subnet of the {resource}.',
      completion_request_params={'fieldMask': 'name'},
      completion_id_field='id')


def RouterAttributeConfig(name='router'):
  return concepts.ResourceParameterAttributeConfig(
      name=name,
      help_text='The router of the {resource}.',
      completion_request_params={'fieldMask': 'name'},
      completion_id_field='id')


def NetworkAttributeConfig(name='network'):
  return concepts.ResourceParameterAttributeConfig(
      name=name,
      help_text='The network of the {resource}.',
      completion_request_params={'fieldMask': 'name'},
      completion_id_field='id')


def InterconnectAttributeConfig(name='interconnect'):
  return concepts.ResourceParameterAttributeConfig(
      name=name,
      help_text='The interconnect of the {resource}.',
      completion_request_params={'fieldMask': 'name'},
      completion_id_field='id')


def GetZoneResourceSpec(resource_name='zone'):
  return concepts.ResourceSpec(
      'edgenetwork.projects.locations.zones',
      resource_name=resource_name,
      zonesId=ZoneAttributeConfig(name=resource_name),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetRouterResourceSpec(resource_name='router'):
  return concepts.ResourceSpec(
      'edgenetwork.projects.locations.zones.routers',
      resource_name=resource_name,
      routersId=RouterAttributeConfig(name=resource_name),
      zonesId=ZoneAttributeConfig('zone'),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetNetworkResourceSpec(resource_name='network'):
  return concepts.ResourceSpec(
      'edgenetwork.projects.locations.zones.networks',
      resource_name=resource_name,
      networksId=NetworkAttributeConfig(name=resource_name),
      zonesId=ZoneAttributeConfig('zone'),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetInterconnectResourceSpec(resource_name='interconnect'):
  return concepts.ResourceSpec(
      'edgenetwork.projects.locations.zones.interconnects',
      resource_name=resource_name,
      interconnectsId=InterconnectAttributeConfig(name=resource_name),
      zonesId=ZoneAttributeConfig('zone'),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def AddZoneResourceArg(parser, verb, positional=False):
  """Add a resource argument for a GDCE router.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to create'.
    positional: bool, if True, means that the resource is a positional rather
      than a flag.
  """
  if positional:
    name = 'zone'
  else:
    name = '--zone'

  resource_specs = [
      presentation_specs.ResourcePresentationSpec(
          name,
          GetZoneResourceSpec(),
          'The zone {}.'.format(verb),
          required=True)
  ]
  concept_parsers.ConceptParser(resource_specs).AddToParser(parser)


def AddRouterResourceArg(parser, verb, positional=False):
  """Add a resource argument for a GDCE router.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to create'.
    positional: bool, if True, means that the resource is a positional rather
      than a flag.
  """
  if positional:
    name = 'router'
  else:
    name = '--router'

  resource_specs = [
      presentation_specs.ResourcePresentationSpec(
          name,
          GetRouterResourceSpec(),
          'The router {}.'.format(verb),
          required=True)
  ]
  concept_parsers.ConceptParser(resource_specs).AddToParser(parser)


def AddNetworkResourceArg(parser, verb, positional=False):
  """Add a resource argument for a GDCE network.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to create'.
    positional: bool, if True, means that the resource is a positional rather
      than a flag.
  """
  if positional:
    name = 'network'
  else:
    name = '--network'

  resource_specs = [
      presentation_specs.ResourcePresentationSpec(
          name,
          GetNetworkResourceSpec(),
          'The network {}.'.format(verb),
          required=True)
  ]
  concept_parsers.ConceptParser(resource_specs).AddToParser(parser)


def AddInterconnectResourceArg(parser, verb, positional=False):
  """Add a resource argument for a GDCE interconnect.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to create'.
    positional: bool, if True, means that the resource is a positional rather
      than a flag.
  """
  if positional:
    name = 'interconnect'
  else:
    name = '--interconnect'

  resource_specs = [
      presentation_specs.ResourcePresentationSpec(
          name,
          GetInterconnectResourceSpec(),
          'The interconnect {}.'.format(verb),
          required=True)
  ]
  concept_parsers.ConceptParser(resource_specs).AddToParser(parser)
