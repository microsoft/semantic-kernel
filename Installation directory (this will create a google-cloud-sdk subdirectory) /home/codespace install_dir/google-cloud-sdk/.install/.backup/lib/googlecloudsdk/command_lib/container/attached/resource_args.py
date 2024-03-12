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
"""Shared resource flags for `gcloud container attached` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def AttachedClusterAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='cluster', help_text='cluster of the {resource}.'
  )


def LocationAttributeConfig():
  """Gets Google Cloud location resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='Google Cloud location for the {resource}.',
      fallthroughs=[
          deps.PropertyFallthrough(
              properties.VALUES.container_attached.location
          ),
      ],
  )


def GetAttachedClusterResourceSpec():
  return concepts.ResourceSpec(
      'gkemulticloud.projects.locations.attachedClusters',
      resource_name='cluster',
      attachedClustersId=AttachedClusterAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
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
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def AddAttachedClusterResourceArg(parser, verb, positional=True):
  """Adds a resource argument for an Attached cluster.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, whether the argument is positional or not.
  """
  name = 'cluster' if positional else '--cluster'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetAttachedClusterResourceSpec(),
      'cluster {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddLocationResourceArg(parser, verb):
  """Adds a resource argument for Google Cloud location.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      '--location',
      GetLocationResourceSpec(),
      'Google Cloud location {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def ParseAttachedClusterResourceArg(args):
  return resources.REGISTRY.ParseRelativeName(
      args.CONCEPTS.cluster.Parse().RelativeName(),
      collection='gkemulticloud.projects.locations.attachedClusters',
  )


def FleetMembershipAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='fleet_membership',
      help_text=(
          'attached cluster membership of the {resource}, in the form of'
          ' projects/PROJECT/locations/global/memberships/MEMBERSHIP. '
      ),
  )


def GetFleetMembershipResourceSpec():
  return concepts.ResourceSpec(
      'gkehub.projects.locations.memberships',
      resource_name='fleet_membership',
      locationsId=LocationAttributeConfig(),
      membershipsId=FleetMembershipAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def AddFleetMembershipResourceArg(parser):
  """Adds a resource argument for Fleet Membership.

  Args:
    parser: The argparse parser to add the resource arg to.
  """
  concept_parsers.ConceptParser.ForResource(
      '--fleet-membership',
      GetFleetMembershipResourceSpec(),
      'Membership of the registered cluster. Membership can be the membership'
      ' ID or the full resource name.',
      required=True,
      flag_name_overrides={
          'location': '--fleet-membership-location',
      },
  ).AddToParser(parser)

  parser.set_defaults(fleet_membership_location='global')


def AddOperationResourceArg(parser, verb):
  """Adds a resource argument for operation on Attached clusters.

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


def ParseOperationResourceArg(args):
  return resources.REGISTRY.ParseRelativeName(
      args.CONCEPTS.operation_id.Parse().RelativeName(),
      collection='gkemulticloud.projects.locations.operations',
  )
