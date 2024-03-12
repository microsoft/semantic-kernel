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
"""Util package for memberships debug API."""
import re
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib import network_services
from googlecloudsdk.api_lib.container import util as container_util
from googlecloudsdk.api_lib.container.fleet import util as fleet_util
from googlecloudsdk.command_lib.container.fleet import api_util as hubapi_util
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties


def ContextGenerator(args):
  """Generate k8s context from membership, location and project."""
  membership_resource_name = base.ParseMembership(
      args, prompt=True, autoselect=True, search=True
  )
  membership_id = fleet_util.MembershipShortname(membership_resource_name)
  project_id = args.project
  location = args.location
  if project_id is None:
    # read the default projectId from local configuration file
    project_id = properties.VALUES.core.project.Get()

  # fetch clusterName from fleet API

  try:
    membership_resource = hubapi_util.GetMembership(membership_resource_name)
  except apitools_exceptions.HttpNotFoundError:
    raise exceptions.Error(
        'Failed finding membership. Please verify the membership, and location'
        ' passed is valid.  membership={}, location={}, project={}'.format(
            membership_id, location, project_id
        )
    )

  if membership_resource is None:
    print('Membership resource is none')
    return

  if not membership_resource.endpoint.gkeCluster:
    raise exceptions.Error(
        'The cluster to the input membership does not belong to gke.'
        ' Please verify the membership and location'
        ' passed is valid.  membership={}, location={}, project={}.'.format(
            membership_id, location, project_id
        )
    )
  cluster_resourcelink = membership_resource.endpoint.gkeCluster.resourceLink
  cluster_location = cluster_resourcelink.split('/')[-3]
  cluster_name = cluster_resourcelink.split('/')[-1]
  print('Found cluster=' + cluster_name)

  cluster_context = container_util.ClusterConfig.KubeContext(
      cluster_name, cluster_location, project_id
  )
  return cluster_context


def ListMeshes():
  client = network_services.GetClientInstance()
  return client.projects_locations_meshes.List(
      client.MESSAGES_MODULE.NetworkservicesProjectsLocationsMeshesListRequest(
          parent='projects/{}/locations/global'.format(
              properties.VALUES.core.project.Get()
          )
      )
  )


# Return meshName, projectNumber
def MeshInfoGenerator(args):
  """Generate meshName from membership, location and project."""
  target_mesh_name = ''
  target_project_number = ''
  meshes = ListMeshes()
  for mesh_info in meshes.meshes:
    matcher = re.match(
        r'.*projects/(.*)/locations/(.*)/memberships/(.*): ',
        mesh_info.description,
    )
    if matcher is None:
      continue
    if matcher.group(2) != args.location or matcher.group(3) != args.membership:
      continue
    else:
      matcher_new = re.match(r'.+/meshes/(.*)', mesh_info.name)
      if matcher_new is None: continue
      target_mesh_name = matcher_new.group(1)
      target_project_number = matcher.group(1)
      break

  # it's possible the targetMeshName does not exist.
  # Return '' as meshName if meshName not exists.
  return target_mesh_name, target_project_number
