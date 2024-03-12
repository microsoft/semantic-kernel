# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Shared resource flags for Cloud Domains commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def RegistrationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='registration',
      help_text='The domain registration for the {resource}.')


def LocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='The Cloud location for the {resource}.',
      fallthroughs=[
          deps.Fallthrough(lambda: 'global', 'location is always global')
      ])


def OperationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='registration',
      help_text='Cloud Domains operation for the {resource}.')


def GetRegistrationResourceSpec():
  return concepts.ResourceSpec(
      'domains.projects.locations.registrations',
      resource_name='registration',
      registrationsId=RegistrationAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetLocationResourceSpec():
  return concepts.ResourceSpec(
      'domains.projects.locations',
      resource_name='location',
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def GetOperationResourceSpec():
  return concepts.ResourceSpec(
      'domains.projects.locations.operations',
      resource_name='operation',
      operationsId=OperationAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def AddRegistrationResourceArg(parser, verb, noun=None, positional=True):
  """Add a resource argument for a Cloud Domains registration.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    noun: str, the resource; default: 'The domain registration'.
    positional: bool, if True, means that the registration ID is a positional
      arg rather than a flag.
  """
  noun = noun or 'The domain registration'
  concept_parsers.ConceptParser.ForResource(
      'registration' if positional else '--registration',
      GetRegistrationResourceSpec(),
      '{} {}.'.format(noun, verb),
      required=True,
      flag_name_overrides={
          'location': ''  # location is always global so don't create a flag.
      }).AddToParser(parser)


def AddLocationResourceArg(parser, verb=''):
  """Add a resource argument for a cloud location.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      '--location',
      GetLocationResourceSpec(),
      'The Cloud location {}.'.format(verb),
      required=True,
      flag_name_overrides={
          'location': ''  # location is always global so don't create a flag.
      }).AddToParser(parser)


def AddOperationResourceArg(parser, verb, positional=True):
  """Add a resource argument for a Cloud Domains registration.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the registration ID is a positional
      arg rather than a flag.
  """
  concept_parsers.ConceptParser.ForResource(
      'operation' if positional else '--operation',
      GetOperationResourceSpec(),
      'The operation {}.'.format(verb),
      required=True,
      flag_name_overrides={
          'location': ''  # location is always global so don't create a flag.
      }).AddToParser(parser)
