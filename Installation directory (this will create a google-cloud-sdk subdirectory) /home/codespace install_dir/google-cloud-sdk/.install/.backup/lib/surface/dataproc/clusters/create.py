# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Create cluster command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import compute_helpers
from googlecloudsdk.api_lib.dataproc import constants
from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.dataproc import clusters
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.kms import resource_args as kms_resource_args
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a cluster."""

  # DEPRECATED Beta release track should no longer be used, Google Cloud
  # no longer supports it.
  BETA = False

  detailed_help = {
      'EXAMPLES': """\
          To create a cluster, run:

            $ {command} my-cluster --region=us-central1
      """
  }

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddClusterResourceArg(parser, 'create', dataproc.api_version)
    clusters.ArgsForClusterRef(
        parser,
        dataproc,
        cls.BETA,
        cls.ReleaseTrack() == base.ReleaseTrack.ALPHA,
        include_ttl_config=True,
        include_gke_platform_args=cls.BETA,
        include_driver_pool_args=True)
    # Add arguments for failure action for primary workers
    if not cls.BETA:
      parser.add_argument(
          '--action-on-failed-primary-workers',
          choices={
              'NO_ACTION': 'take no action',
              'DELETE': 'delete the failed primary workers',
              'FAILURE_ACTION_UNSPECIFIED': 'failure action is not specified'
          },
          type=arg_utils.ChoiceToEnumName,
          help="""
        Failure action to take when primary workers fail during cluster creation
        """)
    # Add gce-pd-kms-key args
    kms_flag_overrides = {
        'kms-key': '--gce-pd-kms-key',
        'kms-keyring': '--gce-pd-kms-key-keyring',
        'kms-location': '--gce-pd-kms-key-location',
        'kms-project': '--gce-pd-kms-key-project'
    }
    kms_resource_args.AddKmsKeyResourceArg(
        parser,
        'cluster',
        flag_overrides=kms_flag_overrides,
        name='--gce-pd-kms-key')

  @staticmethod
  def ValidateArgs(args):
    if constants.ALLOW_ZERO_WORKERS_PROPERTY in args.properties:
      raise exceptions.InvalidArgumentException(
          '--properties',
          'Instead of %s, use gcloud beta dataproc clusters create '
          '--single-node to deploy single node clusters' %
          constants.ALLOW_ZERO_WORKERS_PROPERTY)

    clusters.ValidateReservationAffinityGroup(args)

  def Run(self, args):
    self.ValidateArgs(args)

    dataproc = dp.Dataproc(self.ReleaseTrack())

    cluster_ref = args.CONCEPTS.cluster.Parse()

    compute_resources = compute_helpers.GetComputeResources(
        self.ReleaseTrack(), cluster_ref.clusterName, cluster_ref.region)

    cluster_config = clusters.GetClusterConfig(
        args,
        dataproc,
        cluster_ref.projectId,
        compute_resources,
        self.BETA,
        self.ReleaseTrack() == base.ReleaseTrack.ALPHA,
        include_ttl_config=True,
        include_gke_platform_args=self.BETA)

    action_on_failed_primary_workers = None
    if not self.BETA:
      action_on_failed_primary_workers = arg_utils.ChoiceToEnum(
          args.action_on_failed_primary_workers,
          dataproc.messages.DataprocProjectsRegionsClustersCreateRequest
          .ActionOnFailedPrimaryWorkersValueValuesEnum)

    cluster = dataproc.messages.Cluster(
        config=cluster_config,
        clusterName=cluster_ref.clusterName,
        projectId=cluster_ref.projectId)

    self.ConfigureCluster(dataproc.messages, args, cluster)

    return clusters.CreateCluster(
        dataproc,
        cluster_ref,
        cluster,
        args.async_,
        args.timeout,
        enable_create_on_gke=self.BETA,
        action_on_failed_primary_workers=action_on_failed_primary_workers)

  @staticmethod
  def ConfigureCluster(messages, args, cluster):
    """Performs any additional configuration of the cluster."""
    cluster.labels = labels_util.ParseCreateArgs(args,
                                                 messages.Cluster.LabelsValue)


# DEPRECATED Beta & Alpha release tracks should no longer be used, Google Cloud
# no longer supports them.
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a cluster."""
  BETA = True

  @classmethod
  def Args(cls, parser):
    super(CreateBeta, cls).Args(parser)
    clusters.BetaArgsForClusterRef(parser)

  @staticmethod
  def ValidateArgs(args):
    super(CreateBeta, CreateBeta).ValidateArgs(args)
    if args.master_accelerator and 'type' not in args.master_accelerator:
      raise exceptions.InvalidArgumentException(
          '--master-accelerator', 'accelerator type must be specified. '
          'e.g. --master-accelerator type=nvidia-tesla-k80,count=2')
    if args.worker_accelerator and 'type' not in args.worker_accelerator:
      raise exceptions.InvalidArgumentException(
          '--worker-accelerator', 'accelerator type must be specified. '
          'e.g. --worker-accelerator type=nvidia-tesla-k80,count=2')
