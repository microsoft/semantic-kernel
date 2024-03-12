# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Shared resource flags for `gcloud container azure` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.projects import util as project_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class _ProjectNumberPropertyFallthrough(deps.PropertyFallthrough):
  """A fallthrough for project number from property core/project."""

  def __init__(self):
    """See base class."""
    super(_ProjectNumberPropertyFallthrough, self).__init__(
        prop=properties.VALUES.core.project
    )

  def _Call(self, parsed_args):
    """See base class."""
    return _EnsureProjectNumber(
        super(_ProjectNumberPropertyFallthrough, self)._Call(parsed_args)
    )


class _ProjectNumberArgFallthrough(deps.ArgFallthrough):
  """A fallthrough for project number from the --project argument."""

  def __init__(self):
    """See base class."""
    super(_ProjectNumberArgFallthrough, self).__init__(arg_name='--project')

  def _Call(self, parsed_args):
    """See base class."""
    return _EnsureProjectNumber(
        super(_ProjectNumberArgFallthrough, self)._Call(parsed_args)
    )


def GetOperationResource(op):
  return resources.REGISTRY.ParseRelativeName(
      op.name, collection='gkemulticloud.projects.locations.operations'
  )


def AzureClusterAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='cluster', help_text='cluster of the {resource}.'
  )


def AzureNodePoolAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='nodepool', help_text='node pool of the {resource}.'
  )


def AzureClientAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='client', help_text='Azure client of the {resource}.'
  )


def LocationAttributeConfig():
  """Gets Google Cloud location resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='Google Cloud location for the {resource}.',
      fallthroughs=[
          deps.PropertyFallthrough(properties.VALUES.container_azure.location)
      ],
  )


def ProjectAttributeConfig(use_project_number):
  if not use_project_number:
    return concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG
  return concepts.ResourceParameterAttributeConfig(
      name='project',
      help_text=(
          'Project number of the Google Cloud Platform project for '
          'the {resource}.'
      ),
      fallthroughs=[
          _ProjectNumberArgFallthrough(),
          _ProjectNumberPropertyFallthrough(),
      ],
  )


def OperationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='operation', help_text='Operation for the {resource}.'
  )


def GetLocationResourceSpec():
  return concepts.ResourceSpec(
      'gkemulticloud.projects.locations',
      resource_name='location',
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def GetOperationResourceSpec():
  return concepts.ResourceSpec(
      'gkemulticloud.projects.locations.operations',
      resource_name='operation',
      operationsId=OperationAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def GetAzureClusterResourceSpec():
  return concepts.ResourceSpec(
      'gkemulticloud.projects.locations.azureClusters',
      resource_name='cluster',
      azureClustersId=AzureClusterAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def GetAzureNodePoolResourceSpec():
  return concepts.ResourceSpec(
      'gkemulticloud.projects.locations.azureClusters.azureNodePools',
      resource_name='nodepool',
      azureNodePoolsId=AzureNodePoolAttributeConfig(),
      azureClustersId=AzureClusterAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def GetAzureClientResourceSpec(use_project_number=False):
  """Gets the resource spec for an Azure client.

  Args:
    use_project_number: bool, whether to enforce using project number in the
      resource spec. Project number should always be used when a resource is
      referenced in a field e.g. the client field when creating/updating Azure
      clusters.

  Returns:
    The resource spec for an Azure client.
  """
  return concepts.ResourceSpec(
      'gkemulticloud.projects.locations.azureClients',
      resource_name='client',
      azureClientsId=AzureClientAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=ProjectAttributeConfig(use_project_number),
  )


def AddAzureClusterResourceArg(parser, verb, positional=True):
  """Adds a resource argument for an Azure cluster.

  Args:
    parser: The argparse.parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, whether the argument is positional or not.
  """
  name = 'cluster' if positional else '--cluster'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetAzureClusterResourceSpec(),
      'cluster {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddAzureNodePoolResourceArg(parser, verb, positional=True):
  """Adds a resource argument for an Azure node pool.

  Args:
    parser: The argparse.parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, whether the argument is positional or not.
  """
  name = 'node_pool' if positional else '--node-pool'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetAzureNodePoolResourceSpec(),
      'node pool {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddAzureClientResourceArg(parser, verb, positional=True):
  """Adds a resource argument for an Azure client.

  Args:
    parser: The argparse.parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, whether the argument is positional or not.
  """
  name = 'client' if positional else '--client'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetAzureClientResourceSpec(),
      'Azure client {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddLocationResourceArg(parser, verb):
  """Adds a resource argument for Google Cloud location.

  Args:
    parser: The argparse.parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to list'.
  """
  concept_parsers.ConceptParser.ForResource(
      '--location',
      GetLocationResourceSpec(),
      'Google Cloud location {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddOperationResourceArg(parser, verb):
  """Adds a resource argument for operation in Azure.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'operation_id',
      GetOperationResourceSpec(),
      'operation {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddAzureClusterAndClientResourceArgs(
    parser, auth_config_group, update=False
):
  """Adds resource arguments for both Azure cluster and client.

  This is used for the create and update command.

  Args:
    parser: The argparse.parser to add the resource arg to.
    auth_config_group: The Authentication Configuration argument group.
    update: bool, whether the resources are used in update command.
  """
  arg_parser = concept_parsers.ConceptParser(
      [
          presentation_specs.ResourcePresentationSpec(
              'cluster',
              GetAzureClusterResourceSpec(),
              'Azure cluster to {}.'.format('update' if update else 'create'),
              required=True,
          ),
          presentation_specs.ResourcePresentationSpec(
              '--client',
              GetAzureClientResourceSpec(use_project_number=True),
              'Azure client to use for cluster {}.'.format(
                  'update' if update else 'creation'
              ),
              required=False,
              flag_name_overrides={'location': ''},
              group=auth_config_group,
          ),
      ],
      command_level_fallthroughs={'--client.location': ['cluster.location']},
  )
  arg_parser.AddToParser(parser)


def ParseAzureClientResourceArg(args):
  return resources.REGISTRY.ParseRelativeName(
      args.CONCEPTS.client.Parse().RelativeName(),
      collection='gkemulticloud.projects.locations.azureClients',
  )


def ParseAzureClusterResourceArg(args):
  return resources.REGISTRY.ParseRelativeName(
      args.CONCEPTS.cluster.Parse().RelativeName(),
      collection='gkemulticloud.projects.locations.azureClusters',
  )


def ParseAzureNodePoolResourceArg(args):
  return resources.REGISTRY.ParseRelativeName(
      args.CONCEPTS.node_pool.Parse().RelativeName(),
      collection=(
          'gkemulticloud.projects.locations.azureClusters.azureNodePools'
      ),
  )


def ParseOperationResourceArg(args):
  return resources.REGISTRY.ParseRelativeName(
      args.CONCEPTS.operation_id.Parse().RelativeName(),
      collection='gkemulticloud.projects.locations.operations',
  )


def _EnsureProjectNumber(p):
  if p is None:
    return p
  if p.isdigit():
    return p
  return project_util.GetProjectNumber(p)
