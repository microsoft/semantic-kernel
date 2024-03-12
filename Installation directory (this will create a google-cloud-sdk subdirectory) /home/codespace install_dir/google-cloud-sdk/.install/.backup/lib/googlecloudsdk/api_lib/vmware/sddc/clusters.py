# -*- coding: utf-8 -*- # # Copyright 2020 Google LLC. All Rights Reserved.
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
"""Cloud vmware sddc Clusters client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.vmware.sddc import util
from googlecloudsdk.command_lib.vmware.sddc import flags


class ClustersClient(util.VmwareClientBase):
  """cloud vmware Clusters client."""

  def __init__(self):
    super(ClustersClient, self).__init__()
    self.service = self.client.projects_locations_clusterGroups_clusters

  def Get(self, resource):
    request = self.messages.SddcProjectsLocationsClusterGroupsClustersGetRequest(
        name=resource.RelativeName())
    return self.service.Get(request)

  def Create(self, resource, node_count, node_type, zone, labels=None):
    parent = resource.Parent().RelativeName()
    cluster_id = resource.Name()
    cluster = self.messages.Cluster(
        nodeCount=node_count, defaultZone=zone, nodeType=node_type)
    flags.AddLabelsToMessage(labels, cluster)

    request = self.messages.SddcProjectsLocationsClusterGroupsClustersCreateRequest(
        parent=parent,
        cluster=cluster,
        clusterId=cluster_id,
        managementCluster=True)

    return self.service.Create(request)

  def Delete(self, resource):
    request = self.messages.SddcProjectsLocationsClusterGroupsClustersDeleteRequest(
        name=resource.RelativeName())
    return self.service.Delete(request)

  def List(self, cluster_group_resource):
    cluster_group = cluster_group_resource.RelativeName()
    request = (
        self.messages.SddcProjectsLocationsClusterGroupsClustersListRequest(
            parent=cluster_group
        )
    )
    return list_pager.YieldFromList(
        self.service,
        request,
        batch_size_attribute='pageSize',
        field='clusters')

  def AddNodes(self, resource, node_count):
    cluster = self.Get(resource)
    request = self.messages.SddcProjectsLocationsClusterGroupsClustersAddNodesRequest(
        cluster=resource.RelativeName(),
        addNodesRequest=self.messages.AddNodesRequest(
            nodeCount=cluster.nodeCount + node_count))
    return self.service.AddNodes(request)

  def RemoveNodes(self, resource, node_count):
    cluster = self.Get(resource)
    request = self.messages.SddcProjectsLocationsClusterGroupsClustersRemoveNodesRequest(
        cluster=resource.RelativeName(),
        removeNodesRequest=self.messages.RemoveNodesRequest(
            nodeCount=cluster.nodeCount - node_count))
    return self.service.RemoveNodes(request)
