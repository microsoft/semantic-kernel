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
"""Command to create a GDCE cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.edge_cloud.container import cluster
from googlecloudsdk.api_lib.edge_cloud.container import util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.edge_cloud.container import flags as container_flags
from googlecloudsdk.command_lib.edge_cloud.container import print_warning
from googlecloudsdk.command_lib.edge_cloud.container import resource_args
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

_EXAMPLES = """
To create a cluster called `my-cluster` in region us-central1,
run:

$ {command} my-cluster --location=us-central1
"""

_API_REFERENCE_ = """
  This command uses the edgecontainer/{API} API. The full documentation for this
  API can be found at: https://cloud.google.com/edge-cloud
"""

_RCP_LRO_MAXIMUM_TIMEOUT_ = 1800000  # 30 min
_LCP_LRO_MAXIMUM_TIMEOUT_ = 36000000  # 10 hours


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create an Edge Container cluster."""

  detailed_help = {
      'EXAMPLES': _EXAMPLES,
      'API REFERENCE': _API_REFERENCE_.format(
          API=util.VERSION_MAP.get(base.ReleaseTrack.GA)
      ),
  }

  @staticmethod
  def Args(parser):
    resource_args.AddClusterResourceArg(parser, 'to create')
    container_flags.AddAdminUsers(parser)
    container_flags.AddClusterIPV4CIDR(parser)
    container_flags.AddServicesIPV4CIDR(parser)
    container_flags.AddDefaultMaxPodsPerNode(parser)
    container_flags.AddFleetProject(parser)
    container_flags.AddLabels(parser)
    container_flags.AddMaintenanceWindowRecurrence(parser)
    container_flags.AddMaintenanceWindowEnd(parser)
    container_flags.AddMaintenanceWindowStart(parser)
    container_flags.AddControlPlaneKMSKey(parser)
    container_flags.AddLROMaximumTimeout(parser)
    container_flags.AddSystemAddonsConfig(parser)
    container_flags.AddExternalLbIpv4AddressPools(parser)
    container_flags.AddControlPlaneNodeLocation(parser)
    container_flags.AddControlPlaneNodeCount(parser)
    container_flags.AddControlPlaneMachineFilter(parser)
    container_flags.AddControlPlaneSharedDeploymentPolicy(parser)
    container_flags.AddReleaseChannel(parser)
    container_flags.AddVersion(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    cluster_ref = cluster.GetClusterReference(args)
    req = cluster.GetClusterCreateRequest(args, self.ReleaseTrack())
    error = cluster.ValidateClusterCreateRequest(req, self.ReleaseTrack())
    if error is not None:
      log.error(error)
      return None
    cluster_client = util.GetClientInstance(self.ReleaseTrack())
    op = cluster_client.projects_locations_clusters.Create(req)
    op_ref = resources.REGISTRY.ParseRelativeName(
        op.name, collection='edgecontainer.projects.locations.operations'
    )

    log.status.Print(
        'Create request issued for: [{cluster}]'.format(
            cluster=cluster_ref.clustersId
        )
    )
    if not flags.FlagIsExplicitlySet(args, 'async_'):
      progress_string = (
          'Waiting for operation [{operation}] to complete'.format(
              operation=op_ref.RelativeName()
          )
      )
      operation_poller = util.OperationPoller(
          cluster_client.projects_locations_clusters,
          cluster_client.projects_locations_operations,
      )
      lro_maximum_timeout = _RCP_LRO_MAXIMUM_TIMEOUT_
      if cluster.IsLCPCluster(args):
        lro_maximum_timeout = _LCP_LRO_MAXIMUM_TIMEOUT_
      if flags.FlagIsExplicitlySet(args, 'lro_timeout'):
        lro_maximum_timeout = int(args.lro_timeout)
      response = waiter.WaitFor(
          operation_poller,
          op_ref,
          progress_string,
          max_wait_ms=lro_maximum_timeout,
      )
      log.status.Print(
          'Created cluster [{cluster}].'.format(cluster=cluster_ref.clustersId)
      )
      return print_warning.PrintWarning(response, None)

    log.status.Print(
        'Check operation [{operation}] for status.'.format(
            operation=op_ref.RelativeName()
        )
    )
    return print_warning.PrintWarning(op, None)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create an Edge Container cluster."""

  @staticmethod
  def Args(parser, track=base.ReleaseTrack.ALPHA):
    """Registers alpha track flags for this command."""
    Create.detailed_help['API REFERENCE'] = _API_REFERENCE_.format(
        API=util.VERSION_MAP.get(track)
    )
    Create.Args(parser)
    container_flags.AddClusterIPV6CIDR(parser)
    container_flags.AddServicesIPV6CIDR(parser)
    container_flags.AddExternalLbIpv6AddressPools(parser)
    container_flags.AddOfflineRebootTtL(parser)
