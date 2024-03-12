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
"""Helpers for flags in commands for Anthos GKE On-Prem clusters."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import resources


def GetAdminClusterMembershipResource(membership_name):
  return resources.REGISTRY.ParseRelativeName(
      membership_name, collection='gkehub.projects.locations.memberships'
  )


def AdminClusterMembershipAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='admin_cluster_membership',
      help_text=(
          'admin cluster membership of the {resource}, in the form of'
          ' projects/PROJECT/locations/global/memberships/MEMBERSHIP. '
      ),
  )


def LocationAttributeConfig():
  """Gets Google Cloud location resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='Google Cloud location for the {resource}.',
  )


def GetAdminClusterMembershipResourceSpec():
  return concepts.ResourceSpec(
      'gkehub.projects.locations.memberships',
      resource_name='admin_cluster_membership',
      membershipsId=AdminClusterMembershipAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def AddAdminClusterMembershipResourceArg(
    parser: parser_arguments.ArgumentInterceptor, positional=True, required=True
):
  """Adds a resource argument for a VMware admin cluster membership.

  Args:
    parser: The argparse parser to add the resource arg to.
    positional: bool, whether the argument is positional or not.
    required: bool, whether the argument is required or not.
  """
  name = (
      'admin_cluster_membership' if positional else '--admin-cluster-membership'
  )
  # TODO(b/227667209): Add fallthrough from cluster location when regional
  # membership is implemented.
  concept_parsers.ConceptParser.ForResource(
      name,
      GetAdminClusterMembershipResourceSpec(),
      'membership of the admin cluster. Membership can be the membership ID or'
      ' the full resource name.',
      required=required,
      flag_name_overrides={
          'location': '--admin-cluster-membership-location',
      },
  ).AddToParser(parser)

  parser.set_defaults(admin_cluster_membership_location='global')


def AddBinauthzEvaluationMode(parser):
  parser.add_argument(
      '--binauthz-evaluation-mode',
      choices=['DISABLED', 'PROJECT_SINGLETON_POLICY_ENFORCE'],
      default=None,
      help='Set Binary Authorization evaluation mode for this cluster.',
  )
