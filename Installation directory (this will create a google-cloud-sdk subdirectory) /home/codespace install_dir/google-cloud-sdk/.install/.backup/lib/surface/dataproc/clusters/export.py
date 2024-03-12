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
"""Export cluster command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys
from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import clusters
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.util import files


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Export(base.DescribeCommand):
  """Export a cluster.

  Exports an existing cluster's configuration to a file.
  This configuration can then be used to create new clusters using the import
  command.
  """

  detailed_help = {
      'EXAMPLES': """
To export a cluster to a YAML file, run:

  $ {command} my-cluster --region=us-central1 --destination=cluster.yaml

To export a cluster to standard output, run:

  $ {command} my-cluster --region=us-central1
"""
  }

  @classmethod
  def GetApiVersion(cls):
    """Returns the API version based on the release track."""
    return 'v1'

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddClusterResourceArg(parser, 'export', dataproc.api_version)
    export_util.AddExportFlags(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())

    cluster_ref = args.CONCEPTS.cluster.Parse()

    request = dataproc.messages.DataprocProjectsRegionsClustersGetRequest(
        projectId=cluster_ref.projectId,
        region=cluster_ref.region,
        clusterName=cluster_ref.clusterName)

    cluster = dataproc.client.projects_regions_clusters.Get(request)

    # Filter out Dataproc-generated labels and properties.
    clusters.DeleteGeneratedLabels(cluster, dataproc)
    clusters.DeleteGeneratedProperties(cluster, dataproc)

    RemoveNonImportableFields(cluster)
    if args.destination:
      with files.FileWriter(args.destination) as stream:
        export_util.Export(message=cluster, stream=stream)
    else:
      export_util.Export(message=cluster, stream=sys.stdout)


# Note that this needs to be kept in sync with v1 clusters.proto.
def RemoveNonImportableFields(cluster):
  """Modifies cluster to exclude OUTPUT_ONLY and resource-identifying fields."""

  cluster.projectId = None
  cluster.clusterName = None
  cluster.status = None
  cluster.statusHistory = []
  cluster.clusterUuid = None
  cluster.metrics = None

  if cluster.config is not None:
    config = cluster.config
    if config.lifecycleConfig is not None:
      config.lifecycleConfig.idleStartTime = None

      # This is an absolute time, so exclude it from cluster templates. Due to
      # b/152239418, even if a user specified a TTL (auto_delete_ttl) rather
      # than an absolute time, the API still returns the absolute time and does
      # not return auto_delete_ttl. So TTLs are effectively excluded from
      # templates, at least until that FR is resolved.
      config.lifecycleConfig.autoDeleteTime = None

    instance_group_configs = [
        config.masterConfig, config.workerConfig, config.secondaryWorkerConfig
    ]

    for aux_config in config.auxiliaryNodeGroups:
      instance_group_configs.append(aux_config.nodeGroup.nodeGroupConfig)

    for group in instance_group_configs:
      if group is not None:
        group.instanceNames = []
        group.isPreemptible = None
        group.managedGroupConfig = None
