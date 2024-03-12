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
"""Shared resource flags for `gcloud service-directory` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties

_PROJECT = properties.VALUES.core.project


def ProjectAttributeConfig():
  """Gets project resource attribute with default value."""
  return concepts.ResourceParameterAttributeConfig(
      name='project',
      help_text='The name of the project for the {resource}.',
      fallthroughs=[deps.PropertyFallthrough(_PROJECT)])


def LocationAttributeConfig():
  """Gets location resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='location', help_text='The name of the region for the {resource}.')


def NamespaceAttributeConfig():
  """Gets namespace resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='namespace',
      help_text='The name of the namespace for the {resource}.')


def ServiceAttributeConfig():
  """Gets service resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='service', help_text='The name of the service for the {resource}.')


def EndpointAttributeConfig():
  """Gets endpoint resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='endpoint', help_text='The name of the endpoint for the {resource}.')


def GetProjectResourceSpec():
  """Gets project resource spec."""
  return concepts.ResourceSpec(
      'servicedirectory.projects',
      resource_name='project',
      projectsId=ProjectAttributeConfig())


def GetLocationResourceSpec():
  """Gets location resource spec."""
  return concepts.ResourceSpec(
      'servicedirectory.projects.locations',
      resource_name='location',
      locationsId=LocationAttributeConfig(),
      projectsId=ProjectAttributeConfig())


def GetNamespaceResourceSpec():
  """Gets namespace resource spec."""
  return concepts.ResourceSpec(
      'servicedirectory.projects.locations.namespaces',
      resource_name='namespace',
      namespacesId=NamespaceAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=ProjectAttributeConfig())


def GetServiceResourceSpec():
  """Gets service resource spec."""
  return concepts.ResourceSpec(
      'servicedirectory.projects.locations.namespaces.services',
      resource_name='service',
      servicesId=ServiceAttributeConfig(),
      namespacesId=NamespaceAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=ProjectAttributeConfig())


def GetEndpointResourceSpec():
  """Gets endpoint resource spec."""
  return concepts.ResourceSpec(
      'servicedirectory.projects.locations.namespaces.services.endpoints',
      resource_name='endpoint',
      endpointsId=EndpointAttributeConfig(),
      servicesId=ServiceAttributeConfig(),
      namespacesId=NamespaceAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=ProjectAttributeConfig())


def AddProjectResourceArg(parser, verb, positional=True):
  """Adds a resource argument for a Service Directory project."""
  name = 'project' if positional else '--project'
  return concept_parsers.ConceptParser.ForResource(
      name,
      GetProjectResourceSpec(),
      'The Service Directory project {}'.format(verb),
      required=True).AddToParser(parser)


def AddLocationResourceArg(parser, verb, positional=True):
  """Adds a resource argument for a Service Directory location."""
  name = 'location' if positional else '--location'
  return concept_parsers.ConceptParser.ForResource(
      name,
      GetLocationResourceSpec(),
      'The Service Directory location {}'.format(verb),
      required=True).AddToParser(parser)


def AddNamespaceResourceArg(parser, verb, positional=True):
  """Adds a resource argument for a Service Directory namespace."""
  name = 'namespace' if positional else '--namespace'
  return concept_parsers.ConceptParser.ForResource(
      name,
      GetNamespaceResourceSpec(),
      'The Service Directory namespace {}'.format(verb),
      required=True).AddToParser(parser)


def AddServiceResourceArg(parser, verb, positional=True):
  """Adds a resource argument for a Service Directory service."""
  name = 'service' if positional else '--service'
  return concept_parsers.ConceptParser.ForResource(
      name,
      GetServiceResourceSpec(),
      'The Service Directory service {}'.format(verb),
      required=True).AddToParser(parser)


def AddEndpointResourceArg(parser, verb, positional=True):
  """Adds a resource argument for a Service Directory endpoint."""
  name = 'endpoint' if positional else '--endpoint'
  return concept_parsers.ConceptParser.ForResource(
      name,
      GetEndpointResourceSpec(),
      'The Service Directory endpoint {}'.format(verb),
      required=True).AddToParser(parser)
