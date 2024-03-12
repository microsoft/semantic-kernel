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
"""Shared resource flags for edge-cloud container commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.edge_cloud.container import util
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers

GDCE_SYS_ADDONS_CONFIG = 'systemAddonsConfig'


def ClusterAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='cluster', help_text='Cluster of the {resource}.')


def LocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location', help_text='Google Cloud location for the {resource}.')


def GetClusterResourceSpec():
  return concepts.ResourceSpec(
      'edgecontainer.projects.locations.clusters',
      resource_name='cluster',
      clustersId=ClusterAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def AddClusterResourceArg(parser, verb, positional=True):
  """Adds a resource argument for an Edge Container cluster.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, whether the argument is positional or not.
  """
  name = 'cluster' if positional else '--cluster'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetClusterResourceSpec(),
      'Edge Container cluster {}.'.format(verb),
      required=True).AddToParser(parser)


def NodePoolAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='nodePool', help_text='Node pool of the {resource}.')


def GetNodePoolResourceSpec():
  return concepts.ResourceSpec(
      'edgecontainer.projects.locations.clusters.nodePools',
      resource_name='node pool',
      clustersId=ClusterAttributeConfig(),
      nodePoolsId=NodePoolAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def AddNodePoolResourceArg(parser, verb):
  """Adds a resource argument for an Edge Container node pool.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  name = 'node_pool'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetNodePoolResourceSpec(),
      'Edge Container node pool {}.'.format(verb),
      required=True).AddToParser(parser)


def ProcessSystemAddonsConfig(args, req):
  """Processes the cluster.system_addons_config.

  Args:
    args: command line arguments.
    req: API request to be issued
  """

  release_track = args.calliope_command.ReleaseTrack()
  msgs = util.GetMessagesModule(release_track)

  data = args.system_addons_config
  try:
    system_addons_config = messages_util.DictToMessageWithErrorCheck(
        data[GDCE_SYS_ADDONS_CONFIG], msgs.SystemAddonsConfig)
  except (messages_util.DecodeError, AttributeError, KeyError) as err:
    raise exceptions.InvalidArgumentException(
        '--system-addons-config',
        '\'{}\''.format(err.args[0] if err.args else err))
  req.cluster.systemAddonsConfig = system_addons_config


def SetSystemAddonsConfig(args, request):
  """Sets the cluster.system_addons_config if specified.

  Args:
    args: command line arguments.
    request: API request to be issued
  """

  if args.IsKnownAndSpecified('system_addons_config'):
    ProcessSystemAddonsConfig(args, request)
