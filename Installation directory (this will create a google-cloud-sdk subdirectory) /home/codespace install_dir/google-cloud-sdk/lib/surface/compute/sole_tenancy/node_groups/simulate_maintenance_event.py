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
"""Simulate maintenance event command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.sole_tenancy.node_groups import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class SimulateMaintenanceEvent(base.UpdateCommand):
  """Simulate maintenance of a Compute Engine node group."""

  detailed_help = {
      'brief':
          'Simulate maintenance of a Compute Engine node group.',
      'EXAMPLES':
          """
         To simulate maintenance of a node group, run:

           $ {command} my-node-group --nodes=example-nodes
       """,
  }

  @staticmethod
  def Args(parser):
    flags.MakeNodeGroupArg().AddArgument(parser)
    flags.AddSimulateMaintenanceEventNodesArgToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    messages = holder.client.messages

    node_group_ref = flags.MakeNodeGroupArg().ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    request = messages.ComputeNodeGroupsSimulateMaintenanceEventRequest(
        nodeGroupsSimulateMaintenanceEventRequest=messages
        .NodeGroupsSimulateMaintenanceEventRequest(nodes=args.nodes),
        nodeGroup=node_group_ref.Name(),
        project=node_group_ref.project,
        zone=node_group_ref.zone)

    service = holder.client.apitools_client.nodeGroups
    operation = service.SimulateMaintenanceEvent(request)
    operation_ref = holder.resources.Parse(
        operation.selfLink, collection='compute.zoneOperations')
    if args.async_:
      log.status.Print(
          'Simulation Maintenance Event in progress for node group [{}]: {}'
          .format(node_group_ref.Name(), operation_ref.SelfLink()))
      log.status.Print('Use [gcloud compute operations describe URI] '
                       'to check the status of the operation(s).')
      return operation
    operation_poller = poller.Poller(service)
    nodes_str = ','.join(map(str, args.nodes or []))
    return waiter.WaitFor(
        operation_poller, operation_ref,
        'Simulation Maintenance Event for nodes [{}] in [{}].'.format(
            nodes_str, node_group_ref.Name()))
