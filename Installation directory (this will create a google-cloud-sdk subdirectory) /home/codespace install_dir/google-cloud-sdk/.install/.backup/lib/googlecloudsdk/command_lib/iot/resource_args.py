# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Shared resource flags for Cloud IoT commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def DeviceAttributeConfig(name='device'):
  return concepts.ResourceParameterAttributeConfig(
      name=name,
      help_text='The device of the {resource}.',
      completion_request_params={'fieldMask': 'name'},
      completion_id_field='id')


def RegistryAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='registry',
      help_text='The device registry for the {resource}.')


def RegionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='region',
      help_text='The Cloud region for the {resource}.')


def GetDeviceResourceSpec(resource_name='device'):
  return concepts.ResourceSpec(
      'cloudiot.projects.locations.registries.devices',
      resource_name=resource_name,
      devicesId=DeviceAttributeConfig(name=resource_name),
      registriesId=RegistryAttributeConfig(),
      locationsId=RegionAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetRegistryResourceSpec():
  return concepts.ResourceSpec(
      'cloudiot.projects.locations.registries',
      resource_name='registry',
      registriesId=RegistryAttributeConfig(),
      locationsId=RegionAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetRegionResourceSpec():
  return concepts.ResourceSpec(
      'cloudiot.projects.locations',
      resource_name='region',
      locationsId=RegionAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def AddDeviceResourceArg(parser, verb, positional=True):
  """Add a resource argument for a cloud IOT device.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the device ID is a positional rather
      than a flag.
  """
  if positional:
    name = 'device'
  else:
    name = '--device'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetDeviceResourceSpec(),
      'The device {}.'.format(verb),
      required=True).AddToParser(parser)


def AddRegistryResourceArg(parser, verb, positional=True):
  """Add a resource argument for a cloud IOT device registry.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the device ID is a positional rather
      than a flag.
  """
  if positional:
    name = 'registry'
  else:
    name = '--registry'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetRegistryResourceSpec(),
      'The device registry {}.'.format(verb),
      required=True).AddToParser(parser)


def AddRegionResourceArg(parser, verb):
  """Add a resource argument for a cloud IOT region.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      '--region',
      GetRegionResourceSpec(),
      'The Cloud region {}.'.format(verb),
      required=True).AddToParser(parser)


def CreateDevicePresentationSpec(verb, help_text='The device {}.',
                                 name='device', required=False,
                                 prefixes=True, positional=False):
  """Build ResourcePresentationSpec for generic device Resource.

  NOTE: Should be used when there are multiple resources args in the command.

  Args:
    verb: string, the verb to describe the resource, such as 'to bind'.
    help_text: string, the help text for the entire resource arg group. Should
      have a format specifier (`{}`) to insert verb.
    name: string, name of resource anchor argument.
    required: bool, whether or not this resource arg is required.
    prefixes: bool, if True the resource name will be used as a prefix for
      the flags in the resource group.
    positional: bool, if True, means that the device ID is a positional rather
      than a flag.
  Returns:
    ResourcePresentationSpec, presentation spec for device.
  """
  arg_name = name if positional else '--' + name
  arg_help = help_text.format(verb)

  return presentation_specs.ResourcePresentationSpec(
      arg_name,
      GetDeviceResourceSpec(name),
      arg_help,
      required=required,
      prefixes=prefixes
  )


def _GetBindResourceConcepts(verb='to bind to'):
  """Build ConceptParser for (un)bind commands resource args."""
  arg_specs = [
      CreateDevicePresentationSpec(  # gateway spec
          verb,
          help_text='The gateway device {}.',
          name='gateway',
          required=True),
      CreateDevicePresentationSpec(  # device spec
          verb,
          help_text='The device {} the gateway.',
          required=True),
  ]

  fallthroughs = {
      '--device.registry': ['--gateway.registry'],
      '--gateway.registry': ['--device.registry']
  }

  return concept_parsers.ConceptParser(arg_specs, fallthroughs)


def AddBindResourceArgsToParser(parser):
  """Add resource args for gateways (un)bind commands to parser."""
  _GetBindResourceConcepts().AddToParser(parser)


def BindAdditionalArgsHook():
  return [_GetBindResourceConcepts()]


def UnBindAdditionalArgsHook():
  return [_GetBindResourceConcepts('to unbind from')]

