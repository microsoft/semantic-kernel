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
"""'vmware clusters describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.clusters import ClustersClient
from googlecloudsdk.api_lib.vmware.nodetypes import NodeTypesClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core.resource import resource_projector

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Display data associated with a VMware Engine cluster, such as its node count, node type, and status.
        """,
    'EXAMPLES':
        """
          To describe a cluster called `my-cluster` in private cloud `my-private-cloud` and zone `us-west2-a`, run:

            $ {command} my-cluster --location=us-west2-a --project=my-project --private-cloud=my-private-cloud

            Or:

            $ {command} my-cluster --private-cloud=my-private-cloud

           In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe a Google Cloud VMware Engine cluster."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddClusterArgToParser(parser, positional=True)

  def Run(self, args):
    cluster = args.CONCEPTS.cluster.Parse()
    location = cluster.Parent().Parent()
    clusters_client = ClustersClient()
    node_types_client = NodeTypesClient()

    existing_cluster = resource_projector.MakeSerializable(
        clusters_client.Get(cluster)
    )
    node_types = node_types_client.List(location)
    id_to_node_type = {
        node_type.nodeTypeId: node_type for node_type in node_types
    }

    cluster_memory, cluster_storage, cluster_vcpu, cluster_cores = 0, 0, 0, 0
    for node_type_id, node_type_config in existing_cluster[
        'nodeTypeConfigs'
    ].items():
      if node_type_id not in id_to_node_type:
        continue
      node_type = id_to_node_type[node_type_id]
      node_count = node_type_config['nodeCount']
      custom_core_count = node_type_config.get('customCoreCount') or 0
      cores_count = custom_core_count or node_type.totalCoreCount or 0
      vcpu_ratio = (
          node_type.virtualCpuCount // node_type.totalCoreCount
          if node_type.totalCoreCount
          else 0
      )

      cluster_memory += (node_type.memoryGb or 0) * node_count
      cluster_storage += (node_type.diskSizeGb or 0) * node_count
      cluster_vcpu += cores_count * vcpu_ratio * node_count
      cluster_cores += cores_count * node_count
    existing_cluster['clusterMemoryGb'] = cluster_memory
    existing_cluster['clusterStorageGb'] = cluster_storage
    existing_cluster['clusterVirtualCpuCount'] = cluster_vcpu
    existing_cluster['clusterCoreCount'] = cluster_cores
    return existing_cluster
