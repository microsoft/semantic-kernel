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
"""Command to update an Anthos cluster on VMware."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkeonprem import bare_metal_admin_clusters as apis
from googlecloudsdk.api_lib.container.gkeonprem import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.container.bare_metal import admin_cluster_flags as cluster_flags
from googlecloudsdk.command_lib.container.bare_metal import constants as bare_metal_constants
from googlecloudsdk.command_lib.container.gkeonprem import constants
from googlecloudsdk.command_lib.container.gkeonprem import flags
from googlecloudsdk.core import log

_EXAMPLES = """
To update a cluster named ``my-cluster'' managed in location ``us-west1'', run:

$ {command} my-cluster --location=us-west1
"""


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Update(base.UpdateCommand):
  """Update an Anthos on bare metal admin cluster."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    """Gathers command line arguments for the update command.

    Args:
      parser: The argparse parser to add the flag to.
    """
    parser.display_info.AddFormat(
        bare_metal_constants.BARE_METAL_ADMIN_CLUSTERS_FORMAT)
    cluster_flags.AddAdminClusterResourceArg(parser, 'to update', True)
    base.ASYNC_FLAG.AddToParser(parser)
    cluster_flags.AddValidationOnly(parser)
    cluster_flags.AddDescription(parser)
    cluster_flags.AddVersion(parser, is_update=True)
    cluster_flags.AddControlPlaneConfig(parser, is_update=True)
    cluster_flags.AddProxyConfig(parser, is_update=True)
    cluster_flags.AddClusterOperationsConfig(parser)
    cluster_flags.AddMaintenanceConfig(parser, is_update=True)
    cluster_flags.AddNetworkConfig(parser, is_update=True)
    cluster_flags.AddAdminWorkloadNodeConfig(parser)
    cluster_flags.AddNodeAccessConfig(parser)
    flags.AddBinauthzEvaluationMode(parser)

  def Run(self, args):
    """Runs the update command.

    Args:
      args: The arguments received from command line.

    Returns:
      The return value depends on the command arguments. If `--async` is
      specified, it returns an operation; otherwise, it returns the updated
      resource.
    """
    cluster_ref = args.CONCEPTS.admin_cluster.Parse()
    cluster_client = apis.AdminClustersClient()
    operation = cluster_client.Update(args)

    if args.async_ and not args.IsSpecified('format'):
      args.format = constants.OPERATIONS_FORMAT

    if args.async_:
      log.UpdatedResource(cluster_ref, 'Anthos on bare metal Admin Cluster',
                          args.async_)
      return operation
    else:
      operation_client = operations.OperationsClient()
      operation_response = operation_client.Wait(operation)
      log.UpdatedResource(cluster_ref, 'Anthos on bare metal Admin Cluster',
                          args.async_)

      return operation_response
