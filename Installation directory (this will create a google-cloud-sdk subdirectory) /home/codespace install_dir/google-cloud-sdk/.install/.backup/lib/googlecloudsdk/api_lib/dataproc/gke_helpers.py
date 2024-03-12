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
"""Helpers for interacting with the GKE API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container import api_adapter as gke_api_adapter
from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.core import log


def GetGkeClusterIsWorkloadIdentityEnabled(project, location, cluster):
  """Determines if the GKE cluster is Workload Identity enabled."""
  gke_cluster = _GetGkeCluster(project, location, cluster)
  workload_identity_config = gke_cluster.workloadIdentityConfig
  if not workload_identity_config:
    log.debug('GKE cluster does not have a workloadIdentityConfig.')
    return False
  workload_pool = workload_identity_config.workloadPool
  if not workload_pool:
    log.debug('GKE cluster\'s workloadPool is the empty string.')
    return False
  return True


def _GetGkeCluster(project, location, cluster):
  """Gets the GKE cluster."""
  gke_client = gke_api_adapter.NewV1APIAdapter()

  try:
    return gke_client.GetCluster(
        gke_client.ParseCluster(
            name=cluster, location=location, project=project))
  except Exception as e:
    raise exceptions.GkeClusterGetError(e)
