# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Flags and helpers for general Cloud Filestore commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties


LIST_HELP = ('Instances in all locations will be listed if this argument is '
             'not specified.')


def GetZoneAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      # TODO(b/180447280): Switch to use location as the default argument here.
      'zone',
      'The zone of the {resource}.',
      fallthroughs=[
          deps.ArgFallthrough('region'),
          deps.ArgFallthrough('location'),
          deps.PropertyFallthrough(properties.VALUES.filestore.zone),
          deps.PropertyFallthrough(properties.VALUES.filestore.region),
          deps.PropertyFallthrough(properties.VALUES.filestore.location),
      ])


def GetInstanceAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      'instance',
      'The instance of the {resource}.')


def GetOperationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      'operation',
      'The Cloud Filestore operation.')


def GetLocationResourceSpec():
  location_attribute_config = GetZoneAttributeConfig()
  location_attribute_config.fallthroughs = []
  return concepts.ResourceSpec(
      'file.projects.locations',
      'zone',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=location_attribute_config)


def GetListingLocationResourceSpec():
  location_attribute_config = GetZoneAttributeConfig()
  location_attribute_config.fallthroughs.insert(
      0,
      deps.Fallthrough(lambda: '-', hint='uses all locations by default.'))
  return concepts.ResourceSpec(
      'file.projects.locations',
      'zone',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=location_attribute_config)


def GetInstanceResourceSpec():
  return concepts.ResourceSpec(
      'file.projects.locations.instances',
      'instance',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=GetZoneAttributeConfig(),
      instancesId=GetInstanceAttributeConfig())


def GetOperationResourceSpec():
  return concepts.ResourceSpec(
      'file.projects.locations.operations',
      'operation',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=GetZoneAttributeConfig(),
      operationsId=GetOperationAttributeConfig())


def GetLocationPresentationSpec(group_help):
  return presentation_specs.ResourcePresentationSpec(
      'zone',
      GetLocationResourceSpec(),
      group_help,
      required=True)


def GetListingLocationPresentationSpec(group_help):
  return presentation_specs.ResourcePresentationSpec(
      '--zone',
      GetListingLocationResourceSpec(),
      group_help)


def GetInstancePresentationSpec(group_help):
  return presentation_specs.ResourcePresentationSpec(
      'instance',
      GetInstanceResourceSpec(),
      group_help,
      required=True)


def GetOperationPresentationSpec(group_help):
  return presentation_specs.ResourcePresentationSpec(
      'operation',
      GetOperationResourceSpec(),
      group_help,
      required=True)
