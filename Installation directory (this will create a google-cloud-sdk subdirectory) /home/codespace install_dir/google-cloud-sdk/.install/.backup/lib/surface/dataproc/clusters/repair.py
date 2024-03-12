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

"""Repair cluster command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
import six


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
@base.Hidden
class Repair(base.Command):
  """Repair a cluster."""

  detailed_help = {
      'EXAMPLES':
          """
          To repair a cluster by deleting faulty primary worker nodes, run:

            $ {command} my-cluster --region=us-central1 \
              --node-pool id=PRIMARY_WORKER_POOL,repair-action=delete,instance-names="w-1;w-10"

          To repair a cluster by deleting faulty secondary worker nodes, run:

            $ {command} my-cluster --region=us-central1 \
              --node-pool id=SECONDARY_WORKER_POOL,repair-action=delete,instance-names="sw-1;sw-10"

          To repair a cluster by deleting faulty nodes from different pools, run:

            $ {command} my-cluster --region=us-central1 \
              --node-pool id=PRIMARY_WORKER_POOL,repair-action=delete,instance-names="w-1;w-10" \
              --node-pool id=SECONDARY_WORKER_POOL,repair-action=delete,instance-names="sw-1;sw-10"
          """,
  }

  @classmethod
  def Args(cls, parser):
    """Parse arguments for repair command."""
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddTimeoutFlag(parser)
    flags.AddClusterResourceArg(parser, 'repair', dataproc.api_version)
    parser.add_argument(
        '--node-pool',
        type=arg_parsers.ArgDict(
            required_keys=['id', 'repair-action', 'instance-names'],
            spec={
                'id': str,
                'repair-action': cls._GetParseRepairActionFunc(dataproc),
                'instance-names': arg_parsers.ArgList(custom_delim_char=';')
            }),
        action='append',
        required=True,
        default=[],
        metavar='id=ID,repair-action=REPAIR_ACTION,instance-names="INSTANCE_NAME1[;INSTANCE_NAME2]"',
        help="""
          Each `--node-pool` flag represents either the primary or secondary
          worker pool associated with the cluster and an action on specified
          nodes.
          *id:*::: Valid values : {}.
          *repair-action:*::: Valid values : {}.
          """.format(
              cls._GetValidNodePoolIdChoices(dataproc),
              cls._GetValidRepairActionChoices(dataproc)))
    parser.add_argument(
        '--graceful-decommission-timeout',
        type=arg_parsers.Duration(lower_bound='0s', upper_bound='1d'),
        help="""
              The graceful decommission timeout for decommissioning Node Managers
              in the cluster, used when removing nodes. Graceful decommissioning
              allows removing nodes from the cluster without interrupting jobs in
              progress. Timeout specifies how long to wait for jobs in progress to
              finish before forcefully removing nodes (and potentially
              interrupting jobs). Timeout defaults to 0 if not set (for forceful
              decommission), and the maximum allowed timeout is 1 day.
              See $ gcloud topic datetimes for information on duration formats.
              """)

  @classmethod
  def _GetParseRepairActionFunc(cls, dataproc):
    """Get the function to verify repair-action values."""

    def _ParseRepairActionFunc(repair_action=None):
      return arg_utils.ChoiceToEnum(
          repair_action,
          dataproc.messages.NodePool.RepairActionValueValuesEnum,
          item_type='REPAIR_ACTION',
          valid_choices=cls._GetValidRepairActionChoices(dataproc))

    return _ParseRepairActionFunc

  @classmethod
  def _GetValidNodePoolIdChoices(cls, dataproc):
    """Get list of valid node-pool id values."""
    return ['PRIMARY_WORKER_POOL', 'SECONDARY_WORKER_POOL']

  @classmethod
  def _GetValidRepairActionChoices(cls, dataproc):
    """Get list of valid REPAIR_ACTION values."""
    repair_action_enums = dataproc.messages.NodePool.RepairActionValueValuesEnum
    return [
        arg_utils.ChoiceToEnumName(n)
        for n in repair_action_enums.names()
        if n != 'REPAIR_ACTION_UNSPECIFIED'
    ]

  def _ParseNodePool(self, dataproc, node_pool):
    """Parses a single --node-pool flag into a NodePool message."""
    return dataproc.messages.NodePool(
        id=node_pool['id'],
        repairAction=node_pool['repair-action'],
        instanceNames=node_pool['instance-names'])

  def _ParseNodePools(self, dataproc, args_node_pools):
    """Parses all --node-pool flags into a list of NodePool messages."""
    pools = [
        self._ParseNodePool(dataproc, node_pool)
        for node_pool in args_node_pools
    ]
    self._ValidateNodePoolIds(dataproc, pools)
    return pools

  def _ValidateNodePoolIds(self, dataproc, node_pools):
    """Validates whether node-pools are valid."""
    valid_ids = self._GetValidNodePoolIdChoices(dataproc)
    for node_pool in node_pools:
      node_pool_id = node_pool.id
      if node_pool_id not in valid_ids:
        raise exceptions.InvalidArgumentException(
            '--node-pool',
            'Node pool ID "{}" is not one of {}'.format(node_pool_id,
                                                        valid_ids))

    unique_ids = set()
    for node_pool in node_pools:
      node_pool_id = node_pool.id
      if node_pool_id in unique_ids:
        raise exceptions.InvalidArgumentException(
            '--node-pool',
            'Node pool id "{}" used more than once.'.format(node_pool_id))
      unique_ids.add(node_pool_id)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())
    cluster_ref = args.CONCEPTS.cluster.Parse()

    repair_cluster_request = dataproc.messages.RepairClusterRequest(
        requestId=util.GetUniqueId(),
        nodePools=self._ParseNodePools(dataproc, args.node_pool))

    if args.graceful_decommission_timeout is not None:
      repair_cluster_request.gracefulDecommissionTimeout = (
          six.text_type(args.graceful_decommission_timeout) + 's')

    console_io.PromptContinue(
        message="The specified nodes in cluster '{0}' and all"
        ' attached disks will be deleted.'.format(cluster_ref.clusterName),
        cancel_on_no=True,
        cancel_string='Repair canceled by user.')

    request = dataproc.messages.DataprocProjectsRegionsClustersRepairRequest(
        clusterName=cluster_ref.clusterName,
        region=cluster_ref.region,
        projectId=cluster_ref.projectId,
        repairClusterRequest=repair_cluster_request)

    operation = dataproc.client.projects_regions_clusters.Repair(request)

    if args.async_:
      log.status.write('Repairing [{0}] with operation [{1}].'.format(
          cluster_ref, operation.name))
      return operation

    return util.WaitForOperation(
        dataproc,
        operation,
        message="Waiting for cluster '{0}' repair to finish.".format(
            cluster_ref.clusterName),
        timeout_s=args.timeout)
