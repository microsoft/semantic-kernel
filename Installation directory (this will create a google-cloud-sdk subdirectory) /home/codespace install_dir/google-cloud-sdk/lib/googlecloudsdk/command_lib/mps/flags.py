# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def AddInstanceArgToParser(parser, positional=False):
  """Sets up an argument for the instance resource."""
  if positional:
    name = 'instance'
  else:
    name = '--instance'
  instance_data = yaml_data.ResourceYAMLData.FromPath('mps.power_instance')
  resource_spec = concepts.ResourceSpec.FromYaml(instance_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='instance.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddInstanceSystemTypeArgToParse(parser):
  """Adds system type argument for Instance."""
  parser.add_argument(
      '--system-type',
      help='IBM Power system type of the instance',
      type=str,
      required=True)


def AddInstanceBootImageNameArgToParse(parser):
  """Adds name of boot image to create Instance."""
  parser.add_argument(
      '--boot-image-name',
      help='Name of the boot image used to create this instance',
      type=str,
      required=True)


def AddInstanceMemoryGibArgToParse(parser, required=True):
  """Adds memory size to create Instance."""
  parser.add_argument(
      '--memory-gib',
      help='The memory size used to create instance in Gib',
      type=int,
      required=required)


def AddInstanceVirtualCpuCoresArgToParse(parser, required=True):
  """Adds virtual CPU Cores argument for Instance."""
  parser.add_argument(
      '--virtual-cpu-cores',
      help='Processor for the instance',
      type=float,
      required=required)


def AddInstanceVirtualCpuTypeArgToParse(parser):
  """Adds virtual CPU Cores argument for Instance."""
  parser.add_argument(
      '--virtual-cpu-type',
      choices={
          'UNSPECIFIED':
          'Unspecified',
          'DEDICATED':
          'Dedicated processors. ',
          'UNCAPPED_SHARED':
          'Uncapped shared processors',
          'CAPPED_SHARED':
          'Capped shared processors'
      },
      help='Processor type for the instance',
      type=arg_utils.ChoiceToEnumName,
      required=True)


def AddInstanceNetworkAttachmentNameArgToParse(parser):
  parser.add_argument(
      '--network-attachment-name',
      type=str,
      required=True,
      action='append',
      help='Name of network attached to the instance created',
      )


def AddImageArgToParser(parser, positional=False):
  """Sets up an argument for the image resource."""
  if positional:
    name = 'image'
  else:
    name = '--image'
  image_data = yaml_data.ResourceYAMLData.FromPath('mps.power_image')
  resource_spec = concepts.ResourceSpec.FromYaml(image_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='image.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddNetworkArgToParser(parser, positional=False):
  """Sets up an argument for the network resource."""
  if positional:
    name = 'network'
  else:
    name = '--network'
  network_data = yaml_data.ResourceYAMLData.FromPath('mps.power_network')
  resource_spec = concepts.ResourceSpec.FromYaml(network_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='network.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddVolumeArgToParser(parser, positional=False):
  """Sets up an argument for the volume resource."""
  if positional:
    name = 'volume'
  else:
    name = '--volume'
  volume_data = yaml_data.ResourceYAMLData.FromPath('mps.power_volume')
  resource_spec = concepts.ResourceSpec.FromYaml(volume_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='volume.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddSSHKeyArgToParser(parser, positional=False):
  """Sets up an argument for the image resource."""
  if positional:
    name = 'ssh_key'
  else:
    name = '--ssh_key'
  ssh_key_data = yaml_data.ResourceYAMLData.FromPath('mps.power_ssh_key')
  resource_spec = concepts.ResourceSpec.FromYaml(ssh_key_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help='ssh-key.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddRegionArgToParser(parser, positional=False):
  """Parses region flag."""
  region_data = yaml_data.ResourceYAMLData.FromPath('mps.region')
  resource_spec = concepts.ResourceSpec.FromYaml(region_data.GetData())
  if positional:
    name = 'region'
  else:
    name = '--region'
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=False,
      group_help='region.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)
