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
"""Shared resource args for the Dataplex surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


def GetProjectSpec():
  """Gets Project spec."""
  return concepts.ResourceSpec(
      'dataplex.projects',
      resource_name='projects',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def GetLakeResourceSpec():
  """Gets Lake resource spec."""
  return concepts.ResourceSpec(
      'dataplex.projects.locations.lakes',
      resource_name='lakes',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      lakesId=LakeAttributeConfig())


def GetZoneResourceSpec():
  """Gets Zone resource spec."""
  return concepts.ResourceSpec(
      'dataplex.projects.locations.lakes.zones',
      resource_name='zones',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      lakesId=LakeAttributeConfig(),
      zonesId=ZoneAttributeConfig())


def GetAssetResourceSpec():
  """Gets Asset resource spec."""
  return concepts.ResourceSpec(
      'dataplex.projects.locations.lakes.zones.assets',
      resource_name='assets',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      lakesId=LakeAttributeConfig(),
      zonesId=ZoneAttributeConfig(),
      assetsId=AssetAttributeConfig())


def GetContentitemResourceSpec():
  """Gets Content resource spec."""
  return concepts.ResourceSpec(
      'dataplex.projects.locations.lakes.contentitems',
      resource_name='content',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      lakesId=LakeAttributeConfig(),
      contentitemsId=ContentAttributeConfig())


def GetTaskResourceSpec():
  """Gets Task resource spec."""
  return concepts.ResourceSpec(
      'dataplex.projects.locations.lakes.tasks',
      resource_name='tasks',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      lakesId=LakeAttributeConfig(),
      tasksId=TaskAttributeConfig())


def GetEnvironmentResourceSpec():
  """Gets Environment resource spec."""
  return concepts.ResourceSpec(
      'dataplex.projects.locations.lakes.environments',
      resource_name='environments',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      lakesId=LakeAttributeConfig(),
      environmentsId=EnvironmentAttributeConfig())


def GetDatascanResourceSpec():
  """Gets Datascan resource spec."""
  return concepts.ResourceSpec(
      'dataplex.projects.locations.dataScans',
      resource_name='datascan',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      dataScansId=DatascanAttributeConfig())


def GetDataTaxonomyResourceSpec():
  """Gets DataTaxonomy resource spec."""
  return concepts.ResourceSpec(
      'dataplex.projects.locations.dataTaxonomies',
      resource_name='data taxonomy',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      dataTaxonomiesId=DataTaxonomyAttributeConfig())


def GetDataAttributeBindingResourceSpec():
  """Gets DataAttributeBinding resource spec."""
  return concepts.ResourceSpec(
      'dataplex.projects.locations.dataAttributeBindings',
      resource_name='data attribute binding',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      dataAttributeBindingsId=DataAttributeBindingAttributeConfig())


def GetDataAttributeResourceSpec():
  """Gets Data Attribute resource spec."""
  return concepts.ResourceSpec(
      'dataplex.projects.locations.dataTaxonomies.attributes',
      resource_name='data attribute',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      dataTaxonomiesId=DataTaxonomyAttributeConfig(),
      attributesId=DataAttributeConfig())


def LocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      fallthroughs=[
          deps.PropertyFallthrough(properties.FromString('dataplex/location'))
      ],
      help_text='The location of the Dataplex resource.')


def LakeAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='lake', help_text='The identifier of the Dataplex lake resource.')


def ZoneAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='zone', help_text='The identifier of the Dataplex zone resource.')


def AssetAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='asset', help_text='The identifier of the Dataplex asset resource.')


def ContentAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='content', help_text='The name of the {resource} to use.')


def EnvironmentAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='environment', help_text='The name of {resource} to use.')


def DataTaxonomyAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='data_taxonomy', help_text='The name of {resource} to use.')


def DataAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='data_attribute', help_text='The name of {resource} to use.')


def DataAttributeBindingAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='data_attribute_binding', help_text='The name of {resource} to use.')


def DatascanAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='dataScans', help_text='The name of {resource} to use.')


def AddDatascanResourceArg(parser, verb, positional=True):
  """Adds a resource argument for a Dataplex Datascan."""
  name = 'datascan' if positional else '--datascan'
  return concept_parsers.ConceptParser.ForResource(
      name,
      GetDatascanResourceSpec(),
      'Arguments and flags that define the Dataplex datascan you want {}'
      .format(verb),
      required=True).AddToParser(parser)


def AddProjectArg(parser, verb, positional=True):
  """Adds a resource argument for a project."""
  name = 'project' if positional else '--project'
  return concept_parsers.ConceptParser.ForResource(
      name,
      GetProjectSpec(),
      'Arguments and flags that define the project you want {}'.format(verb),
      required=True).AddToParser(parser)


def TaskAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='task', help_text='The identifier of the Dataplex task resource.')


def AddLakeResourceArg(parser, verb, positional=True):
  """Adds a resource argument for a Dataplex Lake."""
  name = 'lake' if positional else '--lake'
  return concept_parsers.ConceptParser.ForResource(
      name,
      GetLakeResourceSpec(),
      'Arguments and flags that define the Dataplex lake you want {}'.format(
          verb),
      required=True).AddToParser(parser)


def AddZoneResourceArg(parser, verb, positional=True):
  """Adds a resource argument for a Dataplex Zone."""
  name = 'zone' if positional else '--zone'
  return concept_parsers.ConceptParser.ForResource(
      name,
      GetZoneResourceSpec(),
      'Arguments and flags that define the Dataplex zone you want {}'.format(
          verb),
      required=True).AddToParser(parser)


def AddAssetResourceArg(parser, verb, positional=True):
  """Adds a resource argument for a Dataplex Asset."""
  name = 'asset' if positional else '--asset'
  return concept_parsers.ConceptParser.ForResource(
      name,
      GetAssetResourceSpec(),
      'Arguments and flags that define the Dataplex asset you want {}'.format(
          verb),
      required=True).AddToParser(parser)


def AddContentitemResourceArg(parser, verb, positional=True):
  """Adds a resource argument for a Dataplex Content."""
  name = 'content' if positional else '--content'
  return concept_parsers.ConceptParser.ForResource(
      name,
      GetContentitemResourceSpec(),
      'The Content {}'.format(verb),
      required=True).AddToParser(parser)


def AddTaskResourceArg(parser, verb, positional=True):
  """Adds a resource argument for a Dataplex Task."""
  name = 'task' if positional else '--task'
  return concept_parsers.ConceptParser.ForResource(
      name,
      GetTaskResourceSpec(),
      'Arguments and flags that define the Dataplex task you want {}'.format(
          verb),
      required=True).AddToParser(parser)


def AddEnvironmentResourceArg(parser, verb, positional=True):
  """Adds a resource argument for a Dataplex Environment."""
  name = 'environment' if positional else '--environment'
  return concept_parsers.ConceptParser.ForResource(
      name,
      GetEnvironmentResourceSpec(),
      'The Environment {}'.format(verb),
      required=True).AddToParser(parser)


def AddDataTaxonomyResourceArg(parser, verb, positional=True):
  """Adds a resource argument for a Dataplex Data Taxonomy."""
  name = 'data_taxonomy' if positional else '--data_taxonomy'
  return concept_parsers.ConceptParser.ForResource(
      name,
      GetDataTaxonomyResourceSpec(),
      'The DataTaxonomy {}'.format(verb),
      required=True).AddToParser(parser)


def AddAttributeResourceArg(parser, verb, positional=True):
  """Adds a resource argument for a Dataplex Attribute."""
  name = 'data_attribute' if positional else '--data_attribute'
  return concept_parsers.ConceptParser.ForResource(
      name,
      GetDataAttributeResourceSpec(),
      'The DataAttribute {}'.format(verb),
      required=True).AddToParser(parser)


def AddDataAttributeBindingResourceArg(parser, verb, positional=True):
  """Adds a resource argument for a Dataplex DataAttributeBinding."""
  name = 'data_attribute_binding' if positional else '--data_attribute_binding'
  return concept_parsers.ConceptParser.ForResource(
      name,
      GetDataAttributeBindingResourceSpec(),
      'The DataAttributeBinding {}'.format(verb),
      required=True).AddToParser(parser)
