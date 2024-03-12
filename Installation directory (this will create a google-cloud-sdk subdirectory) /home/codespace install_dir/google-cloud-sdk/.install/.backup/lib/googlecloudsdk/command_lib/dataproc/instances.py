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

"""Utilities for converting Dataproc cluster to instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def ConvertClusterToInstance(cluster):
  """Convert a dataproc cluster to instance object.

  Args:
    cluster: cluster returned from Dataproc service.

  Returns:
    Instance: instance dict represents resources installed on GDCE cluster.
  """

  instance = dict()
  gdce_cluster_config = (
      cluster.virtualClusterConfig.kubernetesClusterConfig.gdceClusterConfig
  )
  instance['instanceName'] = cluster.clusterName
  instance['instanceUuid'] = cluster.clusterUuid
  instance['projectId'] = cluster.projectId
  instance['status'] = cluster.status
  instance['gdcEdgeIdentityProvider'] = (
      gdce_cluster_config.gdcEdgeIdentityProvider
  )
  instance['gdcEdgeMembershipTarget'] = (
      gdce_cluster_config.gdcEdgeMembershipTarget
  )
  instance['gdcEdgeWorkloadIdentityPool'] = (
      gdce_cluster_config.gdcEdgeWorkloadIdentityPool
  )
  return instance
