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
"""Command to unenroll an Anthos cluster on bare metal."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkeonprem import bare_metal_clusters as apis
from googlecloudsdk.api_lib.container.gkeonprem import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.container.bare_metal import cluster_flags as flags
from googlecloudsdk.command_lib.container.bare_metal import constants as bare_metal_constants
from googlecloudsdk.command_lib.container.gkeonprem import constants

_EXAMPLES = """
To unenroll a cluster named `my-cluster` managed in location `us-west1`,
run:

$ {command} my-cluster --location=us-west1
"""


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Unenroll(base.Command):
  """Unenroll an Anthos cluster on bare metal."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    """Registers flags for this command."""
    parser.display_info.AddFormat(
        bare_metal_constants.BARE_METAL_CLUSTERS_FORMAT
    )
    flags.AddClusterResourceArg(parser, verb='to unenroll')
    flags.AddForceCluster(parser)
    flags.AddAllowMissingCluster(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Runs the unenroll command."""
    cluster_client = apis.ClustersClient()
    cluster_ref = args.CONCEPTS.cluster.Parse()
    operation = cluster_client.Unenroll(args)

    # if a resource does not exist, --allow-missing returns an
    # operation with an empty name. Early return to avoid polling error.
    if operation.name is None:
      return

    if args.async_ and not args.IsSpecified('format'):
      args.format = constants.OPERATIONS_FORMAT

    if args.async_:
      operations.log_unenroll(cluster_ref, args.async_)
      return operation
    else:
      operation_client = operations.OperationsClient()
      operation_response = operation_client.Wait(operation)
      operations.log_unenroll(cluster_ref, args.async_)
      return operation_response
