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
"""Command to create an Anthos on bare metal admin cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkeonprem import bare_metal_admin_clusters as apis
from googlecloudsdk.api_lib.container.gkeonprem import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.container.bare_metal import admin_cluster_flags as bare_metal_flags
from googlecloudsdk.command_lib.container.bare_metal import constants as bare_metal_constants
from googlecloudsdk.command_lib.container.gkeonprem import constants
from googlecloudsdk.command_lib.container.gkeonprem import flags
from googlecloudsdk.core import log

_EXAMPLES = """
To create a cluster named ``my-cluster'' managed in location ``us-west1'', run:

$ {command} my-cluster --location=us-west1
"""


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Create(base.CreateCommand):
  """Create an Anthos on bare metal admin cluster."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    """Gathers command line arguments for the create command.

    Args:
      parser: The argparse parser to add the flag to.
    """
    parser.display_info.AddFormat(
        bare_metal_constants.BARE_METAL_ADMIN_CLUSTERS_FORMAT
    )
    bare_metal_flags.AddAdminClusterResourceArg(parser, 'to create', True)
    base.ASYNC_FLAG.AddToParser(parser)
    bare_metal_flags.AddValidationOnly(parser)
    bare_metal_flags.AddDescription(parser)
    bare_metal_flags.AddAnnotations(parser)
    bare_metal_flags.AddVersion(parser)
    bare_metal_flags.AddNetworkConfig(parser)
    bare_metal_flags.AddAdminLoadBalancerConfig(parser)
    bare_metal_flags.AddStorageConfig(parser)
    bare_metal_flags.AddControlPlaneConfig(parser)
    bare_metal_flags.AddProxyConfig(parser)
    bare_metal_flags.AddClusterOperationsConfig(parser)
    bare_metal_flags.AddMaintenanceConfig(parser)
    bare_metal_flags.AddAdminWorkloadNodeConfig(parser)
    bare_metal_flags.AddNodeAccessConfig(parser)
    bare_metal_flags.AddSecurityConfig(parser)
    flags.AddBinauthzEvaluationMode(parser)

  def Run(self, args):
    """Runs the create command.

    Args:
      args: The arguments received from command line.

    Returns:
      The return value depends on the command arguments. If `--async` is
      specified, it returns an operation; otherwise, it returns the created
      resource. If `--validate-only` is specified, it returns None or any
      possible error.
    """
    cluster_ref = args.CONCEPTS.admin_cluster.Parse()
    cluster_client = apis.AdminClustersClient()
    operation = cluster_client.Create(args)

    if args.async_ and not args.IsSpecified('format'):
      args.format = constants.OPERATIONS_FORMAT

    if args.async_:
      log.CreatedResource(
          cluster_ref, 'Anthos on bare metal Admin Cluster', args.async_
      )
      return operation

    operation_client = operations.OperationsClient()
    operation_response = operation_client.Wait(operation)

    if not args.validate_only:
      log.CreatedResource(
          cluster_ref, 'Anthos on bare metal Admin Cluster', args.async_
      )
    return operation_response
