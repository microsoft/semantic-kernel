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
"""Utils for Distributed Cloud Edge Network commands."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import resources


def SetResourcesPathForSubnet(ref, args, request):
  """Sets the subnet.network field with a relative resource path.

  Args:
    ref: reference to the subnet object.
    args: command line arguments.
    request: API request to be issued

  Returns:
    modified request
  """

  # Skips if full path of the network resource is provided.
  if 'projects/' in args.network:
    return request

  network = resources.REGISTRY.Create(
      'edgenetwork.projects.locations.zones.networks',
      projectsId=ref.projectsId,
      locationsId=ref.locationsId,
      zonesId=ref.zonesId,
      networksId=args.network)
  request.subnet.network = network.RelativeName()
  return request


def SetResourcesPathForRouter(ref, args, request):
  """Sets the router.network field with a relative resource path.

  Args:
    ref: reference to the router object.
    args: command line arguments.
    request: API request to be issued

  Returns:
    modified request
  """

  # Skips if full path of the network resource is provided.
  if 'projects/' in args.network:
    return request

  network = resources.REGISTRY.Create(
      'edgenetwork.projects.locations.zones.networks',
      projectsId=ref.projectsId,
      locationsId=ref.locationsId,
      zonesId=ref.zonesId,
      networksId=args.network)
  request.router.network = network.RelativeName()
  return request


def SetResourcesPathForRoute(ref, args, request):
  """Sets the route.network field with a relative resource path.

  Args:
    ref: reference to the route object.
    args: command line arguments.
    request: API request to be issued

  Returns:
    modified request
  """

  # Skips if full path of the network resource is provided.
  if 'projects/' in args.network:
    return request

  network = resources.REGISTRY.Create(
      'edgenetwork.projects.locations.zones.networks',
      projectsId=ref.projectsId,
      locationsId=ref.locationsId,
      zonesId=ref.zonesId,
      networksId=args.network)
  request.route.network = network.RelativeName()
  return request


def SetResourcesPathForAttachment(ref, args, request):
  """Sets the interconnectAttachment.router and interconnectAttachment.interconnect field with a relative resource path.

  Args:
    ref: reference to the interconnectAttachment object.
    args: command line arguments.
    request: API request to be issued

  Returns:
    modified request
  """

  if 'projects/' not in args.interconnect:
    interconnect = resources.REGISTRY.Create(
        'edgenetwork.projects.locations.zones.interconnects',
        projectsId=ref.projectsId,
        locationsId=ref.locationsId,
        zonesId=ref.zonesId,
        interconnectsId=args.interconnect)
    request.interconnectAttachment.interconnect = interconnect.RelativeName()

  if args.network and 'projects/' not in args.network:
    network = resources.REGISTRY.Create(
        'edgenetwork.projects.locations.zones.networks',
        projectsId=ref.projectsId,
        locationsId=ref.locationsId,
        zonesId=ref.zonesId,
        networksId=args.network)
    request.interconnectAttachment.network = network.RelativeName()

  return request
