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

"""Shared resource flags for Cloud Pub/Sub commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def SubscriptionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='subscription',
      help_text='Name of the subscription.')


def TopicAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='topic',
      help_text='Name of the topic.')


def SchemaAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='schema', help_text='Name of the schema.')


def GetSubscriptionResourceSpec():
  return concepts.ResourceSpec(
      'pubsub.projects.subscriptions',
      resource_name='subscription',
      subscriptionsId=SubscriptionAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def GetTopicResourceSpec(name='topic'):
  return concepts.ResourceSpec(
      'pubsub.projects.topics',
      resource_name=name,
      topicsId=TopicAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def GetSchemaResourceSpec(name='schema'):
  return concepts.ResourceSpec(
      'pubsub.projects.schemas',
      resource_name=name,
      schemasId=SchemaAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def CreateSubscriptionResourceArg(verb, plural=False):
  """Create a resource argument for a Cloud Pub/Sub Subscription.

  Args:
    verb: str, the verb to describe the resource, such as 'to update'.
    plural: bool, if True, use a resource argument that returns a list.

  Returns:
    the PresentationSpec for the resource argument.
  """
  if plural:
    help_stem = 'One or more subscriptions'
  else:
    help_stem = 'Name of the subscription'
  return presentation_specs.ResourcePresentationSpec(
      'subscription',
      GetSubscriptionResourceSpec(),
      '{} {}'.format(help_stem, verb),
      required=True,
      plural=plural,
      prefixes=True)


def AddSubscriptionResourceArg(parser, verb, plural=False):
  """Add a resource argument for a Cloud Pub/Sub Subscription.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    plural: bool, if True, use a resource argument that returns a list.
  """
  concept_parsers.ConceptParser(
      [CreateSubscriptionResourceArg(verb, plural=plural)]
  ).AddToParser(parser)


def AddSchemaResourceArg(parser, verb, plural=False):
  """Add a resource argument for a Cloud Pub/Sub Schema.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    plural: bool, if True, use a resource argument that returns a list.
  """
  concept_parsers.ConceptParser([CreateSchemaResourceArg(verb, plural=plural)
                                ]).AddToParser(parser)


def CreateTopicResourceArg(verb,
                           positional=True,
                           plural=False,
                           required=True,
                           flag_name='topic'):
  """Create a resource argument for a Cloud Pub/Sub Topic.

  Args:
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the topic ID is a positional rather
      than a flag. If not positional, this also creates a '--topic-project' flag
      as subscriptions and topics do not need to be in the same project.
    plural: bool, if True, use a resource argument that returns a list.
    required: bool, if True, create topic resource arg will be required.
    flag_name: str, name of the topic resource arg (singular).

  Returns:
    the PresentationSpec for the resource argument.
  """
  if positional:
    name = flag_name
    flag_name_overrides = {}
  else:
    name = '--' + flag_name if not plural else '--' + flag_name + 's'
    flag_name_overrides = {'project': '--' + flag_name + '-project'}
  help_stem = 'Name of the topic'
  if plural:
    help_stem = 'One or more topics'
  return presentation_specs.ResourcePresentationSpec(
      name,
      GetTopicResourceSpec(flag_name),
      '{} {}'.format(help_stem, verb),
      required=required,
      flag_name_overrides=flag_name_overrides,
      plural=plural,
      prefixes=True)


def AddTopicResourceArg(parser, verb, positional=True, plural=False):
  """Add a resource argument for a Cloud Pub/Sub Topic.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the topic ID is a positional rather
      than a flag. If not positional, this also creates a '--topic-project' flag
      as subscriptions and topics do not need to be in the same project.
    plural: bool, if True, use a resource argument that returns a list.
  """
  concept_parsers.ConceptParser(
      [CreateTopicResourceArg(verb, positional=positional, plural=plural)]
  ).AddToParser(parser)


def CreateSchemaResourceArg(verb,
                            positional=True,
                            plural=False,
                            required=True,
                            flag_name='schema'):
  """Create a resource argument for a Cloud Pub/Sub Schema.

  Args:
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the schema ID is a positional rather
      than a flag. If not positional, this also creates a '--schema-project'
      flag as schemas and topics do not need to be in the same project.
    plural: bool, if True, use a resource argument that returns a list.
    required: bool, if True, schema resource arg will be required.
    flag_name: str, name of the schema resource arg (singular).

  Returns:
    the PresentationSpec for the resource argument.
  """
  if positional:
    name = flag_name
    flag_name_overrides = {}
  else:
    name = '--' + flag_name if not plural else '--' + flag_name + 's'
    flag_name_overrides = {'project': '--' + flag_name + '-project'}
  help_stem = 'Name of the schema'
  if plural:
    help_stem = 'One or more schemas'
  return presentation_specs.ResourcePresentationSpec(
      name,
      GetSchemaResourceSpec(flag_name),
      '{} {}'.format(help_stem, verb),
      required=required,
      flag_name_overrides=flag_name_overrides,
      plural=plural,
      prefixes=True)


def AddResourceArgs(parser, resources):
  """Add resource arguments for commands that have topic and subscriptions.

  Args:
    parser: the parser for the command.
    resources: a list of resource args to add.
  """
  concept_parsers.ConceptParser(resources).AddToParser(parser)
