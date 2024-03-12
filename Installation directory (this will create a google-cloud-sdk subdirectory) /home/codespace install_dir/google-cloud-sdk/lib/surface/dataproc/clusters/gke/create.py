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
"""Create GKE-based virtual cluster command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from apitools.base.py import encoding

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.api_lib.dataproc import gke_helpers
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import clusters
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.dataproc import gke_clusters
from googlecloudsdk.command_lib.dataproc import gke_workload_identity
from googlecloudsdk.command_lib.dataproc.gke_clusters import GkeNodePoolTargetsParser
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Create(base.CreateCommand):
  """Create a GKE-based virtual cluster."""

  detailed_help = {
      'EXAMPLES':
          """\
          Create a Dataproc on GKE cluster in us-central1 on a GKE cluster in
          the same project and region with default values:

            $ {command} my-cluster --region=us-central1 --gke-cluster=my-gke-cluster --spark-engine-version=latest --pools='name=dp,roles=default'

          Create a Dataproc on GKE cluster in us-central1 on a GKE cluster in
          the same project and zone us-central1-f with default values:

            $ {command} my-cluster --region=us-central1 --gke-cluster=my-gke-cluster --gke-cluster-location=us-central1-f --spark-engine-version=3.1 --pools='name=dp,roles=default'

          Create a Dataproc on GKE cluster in us-central1 with machine type
          'e2-standard-4', autoscaling 5-15 nodes per zone.

            $ {command} my-cluster --region='us-central1' --gke-cluster='projects/my-project/locations/us-central1/clusters/my-gke-cluster' --spark-engine-version=dataproc-1.5 --pools='name=dp-default,roles=default,machineType=e2-standard-4,min=5,max=15'

          Create a Dataproc on GKE cluster in us-central1 with two distinct
          node pools.

            $ {command} my-cluster --region='us-central1' --gke-cluster='my-gke-cluster' --spark-engine-version='dataproc-2.0' --pools='name=dp-default,roles=default,machineType=e2-standard-4' --pools='name=workers,roles=spark-drivers;spark-executors,machineType=n2-standard-8
          """
  }

  _support_shuffle_service = False

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddClusterResourceArg(parser, 'create', dataproc.api_version)

    # 30m is backend timeout + 5m for safety buffer.
    flags.AddTimeoutFlag(parser, default='35m')

    parser.add_argument(
        '--spark-engine-version',
        required=True,
        help="""\
        The version of the Spark engine to run on this cluster.
        """)

    parser.add_argument(
        '--staging-bucket',
        help="""\
        The Cloud Storage bucket to use to stage job dependencies, miscellaneous
        config files, and job driver console output when using this cluster.
        """)

    parser.add_argument(
        '--properties',
        type=arg_parsers.ArgDict(),
        action=arg_parsers.UpdateAction,
        default={},
        metavar='PREFIX:PROPERTY=VALUE',
        help="""\
        Specifies configuration properties for installed packages, such as
        Spark. Properties are mapped to configuration files by specifying a
        prefix, such as "core:io.serializations".
        """)

    flags.AddGkeClusterResourceArg(parser)
    parser.add_argument(
        '--namespace',
        help="""\
            The name of the Kubernetes namespace to deploy Dataproc system
            components in. This namespace does not need to exist.
            """)
    if cls._support_shuffle_service:
      gke_clusters.AddPoolsAlphaArg(parser)
    else:
      gke_clusters.AddPoolsArg(parser)

    parser.add_argument(
        '--setup-workload-identity',
        action='store_true',
        help="""\
            Sets up the GKE Workload Identity for your Dataproc on GKE cluster.
            Note that running this requires elevated permissions as it will
            manipulate IAM policies on the Google Service Accounts that will be
            used by your Dataproc on GKE cluster.
            """)
    flags.AddMetastoreServiceResourceArg(parser)
    flags.AddHistoryServerClusterResourceArg(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())
    cluster_ref = args.CONCEPTS.cluster.Parse()
    gke_cluster_ref = args.CONCEPTS.gke_cluster.Parse()
    metastore_service_ref = args.CONCEPTS.metastore_service.Parse()
    history_server_cluster_ref = args.CONCEPTS.history_server_cluster.Parse()
    virtual_cluster_config = Create._GetVirtualClusterConfig(
        dataproc, gke_cluster_ref, args, metastore_service_ref,
        history_server_cluster_ref)

    Create._VerifyGkeClusterIsWorkloadIdentityEnabled(gke_cluster_ref)

    if args.setup_workload_identity:
      Create._SetupWorkloadIdentity(args, cluster_ref, gke_cluster_ref)

    cluster = dataproc.messages.Cluster(
        virtualClusterConfig=virtual_cluster_config,
        clusterName=cluster_ref.clusterName,
        projectId=cluster_ref.projectId)

    return clusters.CreateCluster(
        dataproc,
        cluster_ref,
        cluster,
        args.async_,
        args.timeout,
        # This refers to the old GKE beta.
        enable_create_on_gke=False,
        action_on_failed_primary_workers=None)

  @staticmethod
  def _GetVirtualClusterConfig(dataproc, gke_cluster_ref, args,
                               metastore_service_ref,
                               history_server_cluster_ref):
    """Get dataproc virtual cluster configuration for GKE based clusters.

    Args:
      dataproc: Dataproc object that contains client, messages, and resources
      gke_cluster_ref: GKE cluster reference.
      args: Arguments parsed from argparse.ArgParser.
      metastore_service_ref: Reference to a Dataproc Metastore Service.
      history_server_cluster_ref: Reference to a Dataproc history cluster.

    Returns:
      virtual_cluster_config: Dataproc virtual cluster configuration
    """

    kubernetes_software_config = dataproc.messages.KubernetesSoftwareConfig(
        componentVersion=encoding.DictToAdditionalPropertyMessage(
            {'SPARK': args.spark_engine_version},
            dataproc.messages.KubernetesSoftwareConfig.ComponentVersionValue,
            sort_items=True))

    if args.properties:
      kubernetes_software_config.properties = encoding.DictToAdditionalPropertyMessage(
          args.properties,
          dataproc.messages.KubernetesSoftwareConfig.PropertiesValue,
          sort_items=True)

    pools = GkeNodePoolTargetsParser.Parse(dataproc,
                                           gke_cluster_ref.RelativeName(),
                                           args.pools)

    gke_cluster_config = dataproc.messages.GkeClusterConfig(
        gkeClusterTarget=gke_cluster_ref.RelativeName(), nodePoolTarget=pools)

    kubernetes_cluster_config = dataproc.messages.KubernetesClusterConfig(
        kubernetesNamespace=args.namespace,
        gkeClusterConfig=gke_cluster_config,
        kubernetesSoftwareConfig=kubernetes_software_config)

    metastore_config = None
    if metastore_service_ref:
      metastore_config = dataproc.messages.MetastoreConfig(
          dataprocMetastoreService=metastore_service_ref.RelativeName())
    spark_history_server_config = None
    if history_server_cluster_ref:
      spark_history_server_config = dataproc.messages.SparkHistoryServerConfig(
          dataprocCluster=history_server_cluster_ref.RelativeName())

    auxiliary_services_config = None
    if metastore_config or spark_history_server_config:
      auxiliary_services_config = dataproc.messages.AuxiliaryServicesConfig(
          metastoreConfig=metastore_config,
          sparkHistoryServerConfig=spark_history_server_config)

    virtual_cluster_config = dataproc.messages.VirtualClusterConfig(
        stagingBucket=args.staging_bucket,
        kubernetesClusterConfig=kubernetes_cluster_config,
        auxiliaryServicesConfig=auxiliary_services_config)

    return virtual_cluster_config

  @staticmethod
  def _VerifyGkeClusterIsWorkloadIdentityEnabled(gke_cluster_ref):
    workload_identity_enabled = gke_helpers.GetGkeClusterIsWorkloadIdentityEnabled(
        project=gke_cluster_ref.projectsId,
        location=gke_cluster_ref.locationsId,
        cluster=gke_cluster_ref.clustersId)
    if not workload_identity_enabled:
      raise exceptions.GkeClusterMissingWorkloadIdentityError(gke_cluster_ref)

  @staticmethod
  def _SetupWorkloadIdentity(args, cluster_ref, gke_cluster_ref):
    default_gsa_sentinel = None

    gsa_to_ksas = collections.OrderedDict()
    agent_gsa = args.properties.get(
        'dataproc:dataproc.gke.agent.google-service-account',
        default_gsa_sentinel)
    gsa_to_ksas.setdefault(agent_gsa, []).append('agent')
    spark_driver_gsa = args.properties.get(
        'dataproc:dataproc.gke.spark.driver.google-service-account',
        default_gsa_sentinel)
    gsa_to_ksas.setdefault(spark_driver_gsa, []).append('spark-driver')
    spark_executor_gsa = args.properties.get(
        'dataproc:dataproc.gke.spark.executor.google-service-account',
        default_gsa_sentinel)
    gsa_to_ksas.setdefault(spark_executor_gsa, []).append('spark-executor')

    if default_gsa_sentinel in gsa_to_ksas:
      ksas = gsa_to_ksas.pop(default_gsa_sentinel)
      default_gsa = (
          gke_workload_identity.DefaultDataprocDataPlaneServiceAccount.Get(
              gke_cluster_ref.projectsId))
      if default_gsa in gsa_to_ksas:
        gsa_to_ksas[default_gsa].extend(ksas)
      else:
        gsa_to_ksas[default_gsa] = ksas

    k8s_namespace = args.namespace or cluster_ref.clusterName
    log.debug(
        'Setting up Workload Identity for the following GSA to KSAs %s in the "%s" namespace.',
        gsa_to_ksas, k8s_namespace)
    for gsa, ksas in gsa_to_ksas.items():
      gke_workload_identity.GkeWorkloadIdentity.UpdateGsaIamPolicy(
          project_id=gke_cluster_ref.projectsId,
          gsa_email=gsa,
          k8s_namespace=k8s_namespace,
          k8s_service_accounts=ksas)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  _support_shuffle_service = True
  __doc__ = Create.__doc__
