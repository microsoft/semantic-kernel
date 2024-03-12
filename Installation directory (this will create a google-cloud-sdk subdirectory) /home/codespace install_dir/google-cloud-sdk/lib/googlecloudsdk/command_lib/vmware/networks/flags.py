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
"""Flags for VMware Engine networks commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def AddNetworkToParser(parser, positional=False):
  """Sets up an argument for the VMware Engine network resource."""
  name = '--vmware-engine-network'
  if positional:
    name = 'vmware_engine_network'
  network_data = yaml_data.ResourceYAMLData.FromPath(
      'vmware.networks.vmware_engine_network')
  resource_spec = concepts.ResourceSpec.FromYaml(network_data.GetData())
  if positional:
    presentation_spec = presentation_specs.ResourcePresentationSpec(
        name=name,
        concept_spec=resource_spec,
        required=True,
        group_help='vmware_engine_network.'
        )
  else:
    presentation_spec = presentation_specs.ResourcePresentationSpec(
        name=name,
        concept_spec=resource_spec,
        required=True,
        group_help='vmware_engine_network.',
        flag_name_overrides={'location': '--network-location'}
        )
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddLocationArgToParser(parser, positional=False):
  """Parses location flag."""
  location_data = yaml_data.ResourceYAMLData.FromPath(
      'vmware.networks.location')
  resource_spec = concepts.ResourceSpec.FromYaml(location_data.GetData())
  name = '--location'
  if positional:
    name = 'location'
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='location.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)
