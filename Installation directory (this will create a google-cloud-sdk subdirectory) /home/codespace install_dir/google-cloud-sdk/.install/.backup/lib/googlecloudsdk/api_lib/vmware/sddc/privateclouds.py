# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Cloud vmware sddc Privateclouds client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.vmware.sddc import util
from googlecloudsdk.command_lib.vmware.sddc import flags


class PrivatecloudsClient(util.VmwareClientBase):
  """cloud vmware privateclouds client."""

  def __init__(self):
    super(PrivatecloudsClient, self).__init__()
    self.service = self.client.projects_locations_clusterGroups

  def Get(self, resource):
    request = self.messages.SddcProjectsLocationsClusterGroupsGetRequest(
        name=resource.RelativeName())
    return self.service.Get(request)

  def Create(
      self,
      resource,
      vpc_network,
      management_ip_range,
      workload_ip_range,
      labels=None,
      description=None,
  ):
    parent = resource.Parent().RelativeName()
    cluster_group_id = resource.Name()
    cluster_group = self.messages.ClusterGroup(description=description)
    flags.AddLabelsToMessage(labels, cluster_group)
    network_config = self.messages.NetworkConfig(
        network=vpc_network,
        managementCidr=management_ip_range,
        workloadCidr=workload_ip_range)
    cluster_group.networkConfig = network_config
    request = self.messages.SddcProjectsLocationsClusterGroupsCreateRequest(
        parent=parent,
        clusterGroup=cluster_group,
        clusterGroupId=cluster_group_id)
    return self.service.Create(request)

  def Update(self,
             resource,
             labels=None,
             description=None,
             external_ip_access=None):
    cluster_group = self.Get(resource)
    update_mask = ['labels']
    if labels is not None:
      flags.AddLabelsToMessage(labels, cluster_group)
    if description is not None:
      cluster_group.description = description
      update_mask.append('description')
    if external_ip_access is not None:
      cluster_group.networkConfig.externalIpAccess = external_ip_access
      update_mask.append('network_config.external_ip_access')
    request = self.messages.SddcProjectsLocationsClusterGroupsPatchRequest(
        clusterGroup=cluster_group,
        name=resource.RelativeName(),
        updateMask=','.join(update_mask))
    return self.service.Patch(request)

  def Delete(self, resource):
    request = self.messages.SddcProjectsLocationsClusterGroupsDeleteRequest(
        name=resource.RelativeName())
    return self.service.Delete(request)

  def List(self, location_resource):
    location = location_resource.RelativeName()
    request = self.messages.SddcProjectsLocationsClusterGroupsListRequest(
        parent=location
    )
    return list_pager.YieldFromList(
        self.service,
        request,
        batch_size_attribute='pageSize',
        field='clusterGroups')
