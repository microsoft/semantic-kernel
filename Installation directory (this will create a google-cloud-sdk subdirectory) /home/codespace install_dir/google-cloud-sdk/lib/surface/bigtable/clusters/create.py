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
"""Command for bigtable clusters create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.bigtable import clusters
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class CreateCluster(base.CreateCommand):
  """Create a bigtable cluster."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
          To add a cluster in zone `us-east1-c` to the instance with id
          `my-instance-id`, run:

            $ {command} my-cluster-id --instance=my-instance-id --zone=us-east1-c

          To add a cluster with `10` nodes, run:

            $ {command} my-cluster-id --instance=my-instance-id --zone=us-east1-c --num-nodes=10

          """),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    arguments.AddClusterResourceArg(parser, 'to describe')
    arguments.ArgAdder(
        parser).AddClusterZone().AddAsync().AddScalingArgsForClusterCreate()
    arguments.AddKmsKeyResourceArg(parser, 'cluster')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """

    cluster = self._Cluster(args)
    cluster_ref = args.CONCEPTS.cluster.Parse()
    operation = clusters.Create(cluster_ref, cluster)
    operation_ref = util.GetOperationRef(operation)
    if args.async_:
      log.CreatedResource(
          operation_ref.RelativeName(),
          kind='bigtable cluster {0}'.format(cluster_ref.Name()),
          is_async=True)
      return
    return util.AwaitCluster(
        operation_ref,
        'Creating bigtable cluster {0}'.format(cluster_ref.Name()))

  def _Cluster(self, args):
    msgs = util.GetAdminMessages()
    storage_type = (
        msgs.Cluster.DefaultStorageTypeValueValuesEnum.STORAGE_TYPE_UNSPECIFIED)
    cluster = msgs.Cluster(
        serveNodes=args.num_nodes,
        location=util.LocationUrl(args.zone),
        defaultStorageType=storage_type)

    kms_key = arguments.GetAndValidateKmsKeyName(args)
    if kms_key:
      cluster.encryptionConfig = msgs.EncryptionConfig(kmsKeyName=kms_key)

    if (args.autoscaling_min_nodes is not None or
        args.autoscaling_max_nodes is not None or
        args.autoscaling_cpu_target is not None or
        args.autoscaling_storage_target is not None):
      cluster.clusterConfig = clusters.BuildClusterConfig(
          autoscaling_min=args.autoscaling_min_nodes,
          autoscaling_max=args.autoscaling_max_nodes,
          autoscaling_cpu_target=args.autoscaling_cpu_target,
          autoscaling_storage_target=args.autoscaling_storage_target)
      # serveNodes must be set to None or 0 to enable Autoscaling.
      # go/cbt-autoscaler-api
      cluster.serveNodes = None

    return cluster
