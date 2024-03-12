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

"""Create Dataproc on GDCE cluster command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import api_util
from googlecloudsdk.command_lib.dataproc import clusters
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.dataproc import gke_workload_identity
from googlecloudsdk.command_lib.dataproc import instances
from googlecloudsdk.core import log


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a Dataproc instance on GDCE cluster."""

  detailed_help = {
      'EXAMPLES':
          """\
          Create a Dataproc on GDCE cluster in us-central1 in
          the same project and region with default values:

            $ {command} my-instance --region=us-central1 --gdce-cluster=my-gdce-cluster
          """
  }

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddInstanceResourceArg(parser, 'create', dataproc.api_version)

    # 30m is backend timeout + 5m for safety buffer.
    flags.AddTimeoutFlag(parser, default='35m')

    flags.AddGdceClusterResourceArg(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())
    instance_ref = args.CONCEPTS.instance.Parse()
    gdce_cluster_ref = args.CONCEPTS.gdce_cluster.Parse()
    virtual_cluster_config = Create._GetVirtualClusterConfig(
        dataproc, gdce_cluster_ref, args)

    Create._SetupWorkloadIdentity(args, instance_ref, gdce_cluster_ref)

    cluster = dataproc.messages.Cluster(
        virtualClusterConfig=virtual_cluster_config,
        clusterName=instance_ref.clusterName,
        projectId=instance_ref.projectId)

    cluster = clusters.CreateCluster(
        dataproc,
        instance_ref,
        cluster,
        args.async_,
        args.timeout,
        # This refers to the old GKE beta.
        enable_create_on_gke=False,
        action_on_failed_primary_workers=None)

    return instances.ConvertClusterToInstance(cluster)

  @staticmethod
  def _GetVirtualClusterConfig(dataproc, gdce_cluster_ref, args):
    """Get dataproc virtual cluster configuration for GDCE based clusters.

    Args:
      dataproc: Dataproc object that contains client, messages, and resources
      gdce_cluster_ref: GDCE cluster reference.
      args: Arguments parsed from argparse.ArgParser.

    Returns:
      virtual_cluster_config: Dataproc virtual cluster configuration
    """

    matches = re.search(
        'projects/(.*)/locations/(.*)/clusters/(.*)',
        gdce_cluster_ref.RelativeName(),
    )
    if matches:
      membership_full_name = (
          'projects/{project_id}/locations/global/memberships/{membership}'
          .format(project_id=matches[1], membership=matches[3])
      )
      container_membership = api_util.GetMembership(membership_full_name)

      gdce_cluster_config = dataproc.messages.GdceClusterConfig(
          gdcEdgeMembershipTarget=gdce_cluster_ref.RelativeName(),
          gdcEdgeWorkloadIdentityPool=container_membership.authority.workloadIdentityPool,
          gdcEdgeIdentityProvider=container_membership.authority.identityProvider,
      )

      kubernetes_cluster_config = dataproc.messages.KubernetesClusterConfig(
          gdceClusterConfig=gdce_cluster_config
      )

      virtual_cluster_config = dataproc.messages.VirtualClusterConfig(
          kubernetesClusterConfig=kubernetes_cluster_config
      )

      return virtual_cluster_config
    else:
      raise exceptions.Error(
          'Invalid GDCE cluster: {}'.format(gdce_cluster_ref.RelativeName())
      )

  @staticmethod
  def _SetupWorkloadIdentity(args, cluster_ref, gke_cluster_ref):
    operator_ksa = ['dataproc-operator']
    spark_ksa = ['spark-driver', 'spark-executor']
    operator_namespace = 'dataproc'
    default_job_env_namespace = 'dataproc-environment-default'

    default_gsa = (
        gke_workload_identity.DefaultDataprocDataPlaneServiceAccount.Get(
            gke_cluster_ref.projectsId
        )
    )

    log.debug(
        (
            'Setting up Workload Identity for the following GSA to operator'
            'KSAs %s in the default "%s" namespace.'
        ),
        operator_ksa,
        operator_namespace,
    )

    gke_workload_identity.GkeWorkloadIdentity.UpdateGsaIamPolicy(
        project_id=gke_cluster_ref.projectsId,
        gsa_email=default_gsa,
        k8s_namespace=operator_namespace,
        k8s_service_accounts=operator_ksa,
    )

    log.debug(
        (
            'Setting up Workload Identity for the following GSA to default'
            'spark KSAs %s in the default "%s" namespace.'
        ),
        spark_ksa,
        default_job_env_namespace,
    )

    gke_workload_identity.GkeWorkloadIdentity.UpdateGsaIamPolicy(
        project_id=gke_cluster_ref.projectsId,
        gsa_email=default_gsa,
        k8s_namespace=default_job_env_namespace,
        k8s_service_accounts=spark_ksa,
    )
