# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Bigtable clusters API helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bigtable import util


def Delete(cluster_ref):
  """Delete a cluster.

  Args:
    cluster_ref: A resource reference to the cluster to delete.
  """
  client = util.GetAdminClient()
  msgs = util.GetAdminMessages()
  msg = msgs.BigtableadminProjectsInstancesClustersDeleteRequest(
      name=cluster_ref.RelativeName())
  client.projects_instances_clusters.Delete(msg)


def Create(cluster_ref, cluster):
  """Create a cluster.

  Args:
    cluster_ref: A resource reference to the cluster to create.
    cluster: A Cluster msg object to create.

  Returns:
    Long running operation.
  """
  client = util.GetAdminClient()
  msgs = util.GetAdminMessages()
  msg = msgs.BigtableadminProjectsInstancesClustersCreateRequest(
      cluster=cluster,
      clusterId=cluster_ref.Name(),
      parent=cluster_ref.Parent().RelativeName())
  return client.projects_instances_clusters.Create(msg)


def BuildClusterAutoscalingConfig(min_nodes=None,
                                  max_nodes=None,
                                  cpu_target=None,
                                  storage_target=None):
  """Build a ClusterAutoscalingConfig field."""
  msgs = util.GetAdminMessages()
  limits = msgs.AutoscalingLimits(
      minServeNodes=min_nodes, maxServeNodes=max_nodes)
  targets = msgs.AutoscalingTargets(
      cpuUtilizationPercent=cpu_target,
      storageUtilizationGibPerNode=storage_target)
  return msgs.ClusterAutoscalingConfig(
      autoscalingLimits=limits, autoscalingTargets=targets)


def BuildClusterConfig(autoscaling_min=None,
                       autoscaling_max=None,
                       autoscaling_cpu_target=None,
                       autoscaling_storage_target=None):
  """Build a ClusterConfig field."""
  msgs = util.GetAdminMessages()
  return msgs.ClusterConfig(
      clusterAutoscalingConfig=BuildClusterAutoscalingConfig(
          min_nodes=autoscaling_min,
          max_nodes=autoscaling_max,
          cpu_target=autoscaling_cpu_target,
          storage_target=autoscaling_storage_target))


def BuildPartialUpdateClusterRequest(msgs,
                                     name=None,
                                     nodes=None,
                                     autoscaling_min=None,
                                     autoscaling_max=None,
                                     autoscaling_cpu_target=None,
                                     autoscaling_storage_target=None,
                                     update_mask=None):
  """Build a PartialUpdateClusterRequest."""
  cluster = msgs.Cluster(name=name, serveNodes=nodes)

  if (autoscaling_min is not None or autoscaling_max is not None or
      autoscaling_cpu_target is not None or
      autoscaling_storage_target is not None):
    cluster.clusterConfig = BuildClusterConfig(
        autoscaling_min=autoscaling_min,
        autoscaling_max=autoscaling_max,
        autoscaling_cpu_target=autoscaling_cpu_target,
        autoscaling_storage_target=autoscaling_storage_target)

  return msgs.BigtableadminProjectsInstancesClustersPartialUpdateClusterRequest(
      cluster=cluster, name=name, updateMask=update_mask)


def PartialUpdate(cluster_ref,
                  nodes=None,
                  autoscaling_min=None,
                  autoscaling_max=None,
                  autoscaling_cpu_target=None,
                  autoscaling_storage_target=None,
                  disable_autoscaling=False):
  """Partially update a cluster.

  Args:
    cluster_ref: A resource reference to the cluster to update.
    nodes: int, the number of nodes in this cluster.
    autoscaling_min: int, the minimum number of nodes for autoscaling.
    autoscaling_max: int, the maximum number of nodes for autoscaling.
    autoscaling_cpu_target: int, the target CPU utilization percent for
      autoscaling.
    autoscaling_storage_target: int, the target storage utilization gibibytes
      per node for autoscaling.
    disable_autoscaling: bool, True means disable autoscaling if it is currently
      enabled. False means change nothing whether it is currently enabled or
      not.

  Returns:
    Long running operation.
  """
  client = util.GetAdminClient()
  msgs = util.GetAdminMessages()

  if disable_autoscaling:
    if (autoscaling_min is not None or autoscaling_max is not None or
        autoscaling_cpu_target is not None or
        autoscaling_storage_target is not None):
      raise ValueError('autoscaling arguments cannot be set together with '
                       'disable_autoscaling')
    return client.projects_instances_clusters.PartialUpdateCluster(
        # To disable autoscaling, set clusterConfig to empty, but include it in
        # update_mask.
        BuildPartialUpdateClusterRequest(
            msgs=msgs,
            name=cluster_ref.RelativeName(),
            nodes=nodes,
            update_mask='serve_nodes,cluster_config.cluster_autoscaling_config'
        ))

  changed_fields = []
  if nodes is not None:
    changed_fields.append('serve_nodes')
  if autoscaling_min is not None:
    changed_fields.append(
        'cluster_config.cluster_autoscaling_config.autoscaling_limits.min_serve_nodes'
    )
  if autoscaling_max is not None:
    changed_fields.append(
        'cluster_config.cluster_autoscaling_config.autoscaling_limits.max_serve_nodes'
    )
  if autoscaling_cpu_target is not None:
    changed_fields.append(
        'cluster_config.cluster_autoscaling_config.autoscaling_targets.cpu_utilization_percent'
    )
  if autoscaling_storage_target is not None:
    changed_fields.append(
        'cluster_config.cluster_autoscaling_config.autoscaling_targets.storage_utilization_gib_per_node'
    )
  update_mask = ','.join(changed_fields)

  return client.projects_instances_clusters.PartialUpdateCluster(
      BuildPartialUpdateClusterRequest(
          msgs=msgs,
          name=cluster_ref.RelativeName(),
          nodes=nodes,
          autoscaling_min=autoscaling_min,
          autoscaling_max=autoscaling_max,
          autoscaling_cpu_target=autoscaling_cpu_target,
          autoscaling_storage_target=autoscaling_storage_target,
          update_mask=update_mask))
