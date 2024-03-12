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
"""Resource parsing helpers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def GetLocation(required=True):
  """Returns the value of the composer/location config property.

  Config properties can be overridden with command line flags. If the --location
  flag was provided, this will return the value provided with the flag.

  Args:
    required: boolean, if True, the absence of the [composer/location] property
        will result in an exception being raised
  """
  return properties.VALUES.composer.location.Get(required=required)


def GetProject():
  """Returns the value of the core/project config property.

  Config properties can be overridden with command line flags. If the --project
  flag was provided, this will return the value provided with the flag.
  """
  return properties.VALUES.core.project.Get(required=True)


def ParseEnvironment(environment_name):
  """Parse out an environment resource using configuration properties.

  Args:
    environment_name: str, the environment's ID, absolute name, or relative name
  Returns:
    Environment: the parsed environment resource
  """
  return resources.REGISTRY.Parse(
      environment_name,
      params={
          'projectsId': GetProject,
          'locationsId': GetLocation
      },
      collection='composer.projects.locations.environments')


def ParseLocation(location_name):
  """Parse out a location resource using configuration properties.

  Args:
    location_name: str, the location's base name, absolute name, or
        relative name

  Returns:
    Location: the parsed Location resource
  """
  return resources.REGISTRY.Parse(
      location_name,
      params={'projectsId': GetProject},
      collection='composer.projects.locations')


def ParseOperation(operation_name):
  """Parse out an operation resource using configuration properties.

  Args:
    operation_name: str, the operation's UUID, absolute name, or relative name

  Returns:
    Operation: the parsed Operation resource
  """
  return resources.REGISTRY.Parse(
      operation_name,
      params={
          'projectsId': GetProject,
          'locationsId': GetLocation
      },
      collection='composer.projects.locations.operations')


def ParseZone(zone):
  """Parses a zone name using configuration properties for fallback.

  Args:
    zone: str, the zone's ID, fully-qualified URL, or relative name

  Returns:
    googlecloudsdk.core.resources.Resource: a resource reference for the zone
  """
  return resources.REGISTRY.Parse(
      zone,
      params={'project': GetProject},
      collection='compute.zones')


def ParseMachineType(machine_type, fallback_zone=None):
  """Parses a machine type name using configuration properties for fallback.

  Args:
    machine_type: str, the machine type's ID, fully-qualified URL, or relative
        name
    fallback_zone: str, the zone to use if `machine_type` does not contain zone
        information. If None, and `machine_type` does not contain zone
        information, parsing will fail.

  Returns:
    googlecloudsdk.core.resources.Resource: a resource reference for the
    machine type
  """
  params = {'project': GetProject}
  if fallback_zone:
    params['zone'] = lambda z=fallback_zone: z
  return resources.REGISTRY.Parse(
      machine_type,
      params=params,
      collection='compute.machineTypes')


def ParseNetworkAttachment(network_attachment, fallback_region=None):
  """Parses a network attachment name using configuration properties for fallback.

  Args:
    network_attachment: str, the network attachment's ID, fully-qualified URL,
      or relative name
    fallback_region: str, the region to use if `networkAttachment` does not
      contain region information. If None, and `networkAttachment` does not
      contain region information, parsing will fail.

  Returns:
    googlecloudsdk.core.resources.Resource: a resource reference for the
    networkAttachment
  """
  params = {'project': GetProject}
  if fallback_region:
    params['region'] = lambda r=fallback_region: r
  return resources.REGISTRY.Parse(
      network_attachment, params=params, collection='compute.networkAttachments'
  )


def ParseNetwork(network):
  """Parses a network name using configuration properties for fallback.

  Args:
    network: str, the network's ID, fully-qualified URL, or relative name

  Returns:
    googlecloudsdk.core.resources.Resource: a resource reference for the network
  """
  return resources.REGISTRY.Parse(
      network,
      params={'project': GetProject},
      collection='compute.networks')


def ParseSubnetwork(subnetwork, fallback_region=None):
  """Parses a subnetwork name using configuration properties for fallback.

  Args:
    subnetwork: str, the subnetwork's ID, fully-qualified URL, or relative name
    fallback_region: str, the region to use if `subnetwork` does not contain
        region information. If None, and `subnetwork` does not contain region
        information, parsing will fail.

  Returns:
    googlecloudsdk.core.resources.Resource: a resource reference for the
    subnetwork
  """
  params = {'project': GetProject}
  if fallback_region:
    params['region'] = lambda r=fallback_region: r
  return resources.REGISTRY.Parse(
      subnetwork,
      params=params,
      collection='compute.subnetworks')
