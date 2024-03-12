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

"""Shared resource args for Cloud API Gateway surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def LocationAttributeConfig(default=None):
  """Creates location attribute config."""
  default_keyword = default
  if default == '-':
    default_keyword = 'a wildcard'

  fallthroughs = []
  if default:
    fallthroughs.append(
        deps.Fallthrough(
            lambda: default,
            'Location for API and API Configs. Defaults to {}'.format(
                default_keyword)))

  return concepts.ResourceParameterAttributeConfig(
      name='location',
      fallthroughs=fallthroughs,
      help_text='Cloud location for {resource}.')


def GatewayAttributeConfig(name='gateway'):
  return concepts.ResourceParameterAttributeConfig(
      name=name,
      help_text='Name for API Gateway')


def ApiAttributeConfig(name='api', wildcard=False):
  fallthroughs = []
  if wildcard:
    fallthroughs.append(
        deps.Fallthrough(
            lambda: '-',
            'Defaults to wildcard for all APIs'))

  return concepts.ResourceParameterAttributeConfig(
      name=name,
      fallthroughs=fallthroughs,
      help_text='API ID.')


def ApiConfigAttributeConfig(name='api-config'):
  return concepts.ResourceParameterAttributeConfig(
      name=name,
      help_text='API Config ID.')


def OperationAttributeConfig(name='operation'):
  return concepts.ResourceParameterAttributeConfig(
      name=name,
      help_text='The name for the API Gateway operation')


def GetLocationResourceSpec(resource_name='location', default=None):
  return concepts.ResourceSpec(
      'apigateway.projects.locations',
      resource_name=resource_name,
      locationsId=LocationAttributeConfig(default=default),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def GetGatewayResourceSpec(resource_name='gateway'):
  return concepts.ResourceSpec(
      'apigateway.projects.locations.gateways',
      resource_name=resource_name,
      gatewaysId=GatewayAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def GetApiResourceSpec(resource_name='api', wildcard=False):
  return concepts.ResourceSpec(
      'apigateway.projects.locations.apis',
      resource_name=resource_name,
      apisId=ApiAttributeConfig(wildcard=wildcard),
      locationsId=LocationAttributeConfig(default='global'),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def GetApiConfigResourceSpec(resource_name='api-config'):
  return concepts.ResourceSpec(
      'apigateway.projects.locations.apis.configs',
      resource_name=resource_name,
      configsId=ApiConfigAttributeConfig(),
      apisId=ApiAttributeConfig(),
      locationsId=LocationAttributeConfig(default='global'),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def GetOperationResourceSpec(resource_name='operation'):
  return concepts.ResourceSpec(
      'apigateway.projects.locations.operations',
      resource_name=resource_name,
      operationsId=OperationAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def AddGatewayResourceArg(parser, verb, positional=False, required=True):
  """Adds Gateway resource argument to parser.

  Args:
    parser: parser to add arg to
    verb: action being taken with the Gateway
    positional: Boolean indicating if argument is positional, default False
    required: Boolean for if this is required, default is True

  Returns: None
  """

  if positional:
    name = 'gateway'
  else:
    name = '--gateway'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetGatewayResourceSpec(),
      'Name for gateway which will be {}.'.format(verb),
      required=required).AddToParser(parser)


def AddGatewayApiConfigResourceArgs(parser, verb, gateway_required=True,
                                    api_config_required=True):
  """Adds Gateway and API Config resource arguments to parser.

  Args:
    parser: parser to add arg to
    verb: action being taken with the Gateway
    gateway_required: Boolean for if Gateway is required, default is True
    api_config_required: Boolean for if API Config is required, default is True

  Returns: None
  """

  concept_parsers.ConceptParser(
      [
          presentation_specs.ResourcePresentationSpec(
              'gateway',
              GetGatewayResourceSpec(),
              'Name for gateway which will be {}.'.format(verb),
              required=gateway_required),
          presentation_specs.ResourcePresentationSpec(
              '--api-config',
              GetApiConfigResourceSpec(),
              'Resource name for API config the gateway will use.',
              flag_name_overrides={'location': ''},
              required=api_config_required)
      ]).AddToParser(parser)


def AddLocationResourceArg(parser, verb, positional=False, default=None,
                           required=True):
  """Adds location resource argument to parser.

  Args:
    parser: parser to add arg to
    verb: action being taken with the location
    positional: Optional boolean indiicating if argument is positional
    default: Optional default value for the arg
    required: Boolean for if this is required, default is True

  Returns: None
  """

  if positional:
    name = 'location'
  else:
    name = '--location'

  override = None
  if default == 'global':
    override = {'location': ''}

  concept_parsers.ConceptParser.ForResource(
      name,
      GetLocationResourceSpec(default=default),
      'Parent location which {}.'.format(verb),
      flag_name_overrides=override,
      required=required).AddToParser(parser)


def AddApiResourceArg(parser, verb, positional=False, required=True,
                      wildcard=False):
  """Adds API resource argument to parser.

  Args:
    parser: parser to add arg to
    verb: action being taken with the API
    positional: Optional boolean indiicating if argument is positional
    required: Boolean for if this is required, default is True
    wildcard: Boolean. Does arg have a default wildcard? default: False

  Returns: None
  """

  if positional:
    name = 'api'
  else:
    name = '--api'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetApiResourceSpec(wildcard=wildcard),
      'Name for API which {}.'.format(verb),
      flag_name_overrides={'location': ''},
      required=required).AddToParser(parser)


def AddApiConfigResourceArg(parser, verb, positional=False, required=True):
  """Adds API Config resource argument to parser.

  Args:
    parser: parser to add arg to
    verb: action being taken with the API Config
    positional: Boolean indicating if argument is positional, default False
    required: Boolean for if this is required, default is True

  Returns: None
  """

  if positional:
    name = 'api_config'
  else:
    name = '--api-config'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetApiConfigResourceSpec(),
      'Name for API Config which will be {}.'.format(verb),
      flag_name_overrides={'location': ''},
      required=required).AddToParser(parser)


def AddOperationResourceArgs(parser, verb):
  concept_parsers.ConceptParser.ForResource(
      'operation',
      GetOperationResourceSpec(),
      'The name of the operation to {}.'.format(verb),
      required=True).AddToParser(parser)
