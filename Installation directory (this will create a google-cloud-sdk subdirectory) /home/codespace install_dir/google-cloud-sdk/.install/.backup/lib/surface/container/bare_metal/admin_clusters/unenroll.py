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
"""Command to unenroll an Anthos on bare metal admin cluster."""

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

_EXAMPLES = """
To unenroll an admin cluster named `my-cluster` managed in location `us-west1`,
run:

$ {command} my-cluster --location=us-west1
"""


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Unenroll(base.Command):
  """Unenroll an Anthos on bare metal admin cluster so that it is no longer managed by the Anthos On-Prem API."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    """Registers flags for this command."""
    parser.display_info.AddFormat(
        bare_metal_constants.BARE_METAL_ADMIN_CLUSTERS_FORMAT
    )
    cluster_flags.AddAdminClusterResourceArg(parser, 'to unenroll')
    cluster_flags.AddAllowMissingCluster(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    cluster_flags.AddValidationOnly(parser)
    cluster_flags.AddIgnoreErrors(parser)

  def Run(self, args):
    """Runs the unenroll command."""
    cluster_client = apis.AdminClustersClient()
    cluster_ref = args.CONCEPTS.admin_cluster.Parse()
    operation = cluster_client.Unenroll(args)

    if args.async_ and not args.IsSpecified('format'):
      args.format = constants.OPERATIONS_FORMAT

    if args.validate_only:
      return

    # If a resource does not exist, --allow-missing returns an
    # operation with an empty name. Early return to avoid polling error.
    if operation.name is None:
      return

    if args.async_:
      operations.log_unenroll(cluster_ref, args.async_)
      return operation
    else:
      operation_client = operations.OperationsClient()
      operation_response = operation_client.Wait(operation)
      operations.log_unenroll(cluster_ref, args.async_)
      return operation_response
