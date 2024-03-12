# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Utilities for bms commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def DefaultToGlobal():
  """Returns 'global' to be used as a fallthrough hook in resources.yaml."""
  return 'global'


def NFSNetworkFullName(nfs_share_resource, allowed_client_dict):
  """Returns the full GCP name of the NFS allowed client network."""
  # We default to NFS project ID if network project ID is not specified.
  nfs_region = nfs_share_resource.Parent()
  nfs_project = nfs_region.Parent()
  network_project_id = allowed_client_dict.get('network-project-id',
                                               nfs_project.Name())
  return resources.REGISTRY.Parse(
      allowed_client_dict['network'],
      params={
          'projectsId': network_project_id,
          'locationsId': nfs_region.Name(),
      },
      collection='baremetalsolution.projects.locations.networks').RelativeName()


def RemoveAllowedClients(nfs_share_resource, allowed_clients,
                         remove_key_dicts):
  """Removes the allowed clients specified by remove_key_dicts from allowed_clients."""
  keys_to_remove = set()
  for key_dict in remove_key_dicts:
    key_network_full_name = NFSNetworkFullName(
        nfs_share_resource=nfs_share_resource,
        allowed_client_dict=key_dict,
    )
    keys_to_remove.add((key_network_full_name, key_dict['cidr']))

  out = []
  for allowed_client in allowed_clients:
    curr_key = (allowed_client.network, allowed_client.allowedClientsCidr)
    if curr_key in keys_to_remove:
      keys_to_remove.remove(curr_key)
    else:
      out.append(allowed_client)
  for key in keys_to_remove:
    raise LookupError('Cannot find an existing allowed client for network'
                      ' [{}] and CIDR [{}]'.format(key[0],
                                                   key[1]))
  return out


def FixParentPathWithGlobalRegion(region: str) -> str:
  """Returns projects/$project/location/$location parent path based on region."""
  if region is not None:
    return region.RelativeName()
  project = properties.VALUES.core.project.Get(required=True)
  return 'projects/{}/locations/global'.format(project)
