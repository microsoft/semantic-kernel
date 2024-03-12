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
"""Flags for data-catalog commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def AddPrivatecloudArgToParser(parser, positional=False):
  """Sets up an argument for the privatecloud resource."""
  if positional:
    name = 'privatecloud'
  else:
    name = '--privatecloud'
  privatecloud_data = yaml_data.ResourceYAMLData.FromPath(
      'vmware.sddc.privatecloud')
  resource_spec = concepts.ResourceSpec.FromYaml(privatecloud_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='privatecloud.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddIPArgToParser(parser):
  ip_address_id = yaml_data.ResourceYAMLData.FromPath('vmware.sddc.ip_address')
  resource_spec = concepts.ResourceSpec.FromYaml(ip_address_id.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name='name',
      concept_spec=resource_spec,
      required=True,
      group_help='ip_address.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddClusterArgToParser(parser):
  cluster_data = yaml_data.ResourceYAMLData.FromPath('vmware.sddc.cluster')
  resource_spec = concepts.ResourceSpec.FromYaml(cluster_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name='cluster',
      concept_spec=resource_spec,
      required=True,
      group_help='cluster.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddRegionArgToParser(parser, positional=False):
  """Parses region flag."""
  region_data = yaml_data.ResourceYAMLData.FromPath('vmware.sddc.region')
  resource_spec = concepts.ResourceSpec.FromYaml(region_data.GetData())
  if positional:
    name = 'region'
  else:
    name = '--region'
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='region.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddLabelsToMessage(labels, message):
  """Parses labels into a specific message."""

  # set up for call to ParseCreateArgs, which expects labels as an
  # attribute on an object.
  class LabelHolder(object):

    def __init__(self, labels):
      self.labels = labels

  message.labels = labels_util.ParseCreateArgs(
      LabelHolder(labels),
      type(message).LabelsValue)
