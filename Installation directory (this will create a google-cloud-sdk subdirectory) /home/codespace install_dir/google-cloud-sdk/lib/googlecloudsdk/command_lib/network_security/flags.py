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
"""Flags for network_security commands."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys
from googlecloudsdk.api_lib.network_security import API_VERSION_FOR_TRACK
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def AddProjectAddressGroupToParser(release_track, parser):
  """Add project address group argument."""
  AddAddressGroupToParser(parser, release_track,
                          'network_security.addressGroup')


def AddOrganizationAddressGroupToParser(release_track, parser):
  """Add organization address group argument."""
  AddAddressGroupToParser(parser, release_track,
                          'network_security.orgAddressGroup')


def AddAddressGroupToParser(parser, release_track, resource_path):
  """Add project or organization address group argument."""
  address_group_data = yaml_data.ResourceYAMLData.FromPath(resource_path)
  resource_spec = concepts.ResourceSpec.FromYaml(
      address_group_data.GetData(),
      api_version=API_VERSION_FOR_TRACK[release_track])
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name='ADDRESS_GROUP',
      concept_spec=resource_spec,
      required=True,
      group_help='address group group help.')
  concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddListReferencesFormat(parser):
  """Add default list reference format to ListReferences command."""
  parser.display_info.AddFormat("""
        table(
          firewallPolicy,
          rulePriority
        )
    """)
