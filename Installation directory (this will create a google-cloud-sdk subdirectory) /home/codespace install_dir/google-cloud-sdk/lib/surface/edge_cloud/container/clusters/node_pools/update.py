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
"""Command to update an Edge Container node pool."""

from googlecloudsdk.api_lib.edge_cloud.container import nodepool
from googlecloudsdk.api_lib.edge_cloud.container import util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.edge_cloud.container import flags as container_flags
from googlecloudsdk.command_lib.edge_cloud.container import print_warning
from googlecloudsdk.command_lib.edge_cloud.container import resource_args
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.resource import resource_printer

_EXAMPLES = """
To update the number of nodes in a node pool called `my-node-pool` in region `us-central1`,
run:

  $ {command} my-node-pool --location=us-central1 --cluster=<my-cluster> \
      --node-count=<new-count>
"""

_API_REFERENCE_ = """
  This command uses the edgecontainer/{API} API. The full documentation for this
  API can be found at: https://cloud.google.com/edge-cloud
"""

_LRO_MAXIMUM_TIMEOUT_ = 68400000  # 19 hours


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Updates an Edge Container node pool."""

  detailed_help = {
      'EXAMPLES': _EXAMPLES,
      'API REFERENCE': _API_REFERENCE_.format(
          API=util.VERSION_MAP.get(base.ReleaseTrack.GA)
      ),
  }

  @staticmethod
  def Args(parser):
    resource_args.AddNodePoolResourceArg(parser, 'to update')
    container_flags.AddNodeCount(parser, required=False)
    container_flags.AddMachineFilter(parser)
    container_flags.AddLROMaximumTimeout(parser)
    container_flags.AddNodeLabels(parser)
    labels_util.AddUpdateLabelsFlags(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    node_pool_ref = nodepool.GetNodePoolReference(args)
    client = util.GetClientInstance(self.ReleaseTrack())
    get_req = nodepool.GetNodePoolGetRequest(args, self.ReleaseTrack())
    existing_node_pool = client.projects_locations_clusters_nodePools.Get(
        get_req
    )
    update_req = nodepool.GetNodePoolUpdateRequest(
        args, self.ReleaseTrack(), existing_node_pool
    )
    op = client.projects_locations_clusters_nodePools.Patch(update_req)
    op_ref = resources.REGISTRY.ParseRelativeName(
        op.name, collection='edgecontainer.projects.locations.operations'
    )

    log.status.Print(
        'Update request issued for: [{nodePool}]'.format(
            nodePool=node_pool_ref.nodePoolsId
        )
    )
    if not flags.FlagIsExplicitlySet(args, 'async_'):
      progress_string = (
          'Waiting for operation [{operation}] to complete'.format(
              operation=op_ref.RelativeName()
          )
      )
      operation_poller = util.OperationPoller(
          client.projects_locations_clusters_nodePools,
          client.projects_locations_operations,
      )
      lro_maximum_timeout = _LRO_MAXIMUM_TIMEOUT_
      if flags.FlagIsExplicitlySet(args, 'lro_timeout'):
        lro_maximum_timeout = int(args.lro_timeout)
      response = waiter.WaitFor(
          operation_poller,
          op_ref,
          progress_string,
          max_wait_ms=lro_maximum_timeout,
      )
      updated_node_pool = client.projects_locations_clusters_nodePools.Get(
          get_req
      )
      log.status.Print(
          'Updated node pool [{nodePool}].'.format(
              nodePool=node_pool_ref.nodePoolsId
          )
      )
      resource_printer.Print(updated_node_pool, 'json', out=log.status)
      return print_warning.PrintWarning(response, None)

    log.status.Print(
        'Check operation [{operation}] for status.'.format(
            operation=op_ref.RelativeName()
        )
    )
    return print_warning.PrintWarning(op, None)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  """Updates an Edge Container node pool."""

  @staticmethod
  def Args(parser, track=base.ReleaseTrack.ALPHA):
    """Registers alpha track flags for this command."""
    Update.detailed_help['API REFERENCE'] = _API_REFERENCE_.format(
        API=util.VERSION_MAP.get(track)
    )
    Update.Args(parser)
