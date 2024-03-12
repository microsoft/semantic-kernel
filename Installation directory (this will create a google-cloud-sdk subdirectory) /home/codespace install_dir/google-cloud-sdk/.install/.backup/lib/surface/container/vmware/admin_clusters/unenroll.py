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
"""Command to unenroll an Anthos on VMware admin cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkeonprem import operations
from googlecloudsdk.api_lib.container.gkeonprem import vmware_admin_clusters as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.container.gkeonprem import constants
from googlecloudsdk.command_lib.container.vmware import constants as vmware_constants
from googlecloudsdk.command_lib.container.vmware import flags

_EXAMPLES = """
To unenroll an admin cluster named `my-cluster` managed in location `us-west1`,
run:

$ {command} my-cluster --location=us-west1
"""


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Unenroll(base.Command):
  """Unenroll an Anthos on VMware admin cluster."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    """Registers flags for this command."""
    parser.display_info.AddFormat(vmware_constants.VMWARE_CLUSTERS_FORMAT)
    flags.AddAdminClusterResourceArg(parser, 'to unenroll')
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddValidationOnly(parser)
    flags.AddAllowMissingUnenrollCluster(parser)

  def Run(self, args):
    """Runs the unenroll command."""
    cluster_client = apis.AdminClustersClient()
    admin_cluster_ref = args.CONCEPTS.admin_cluster.Parse()
    operation = cluster_client.Unenroll(args)

    if args.async_ and not args.IsSpecified('format'):
      args.format = constants.OPERATIONS_FORMAT

    if args.validate_only:
      return None

    # when using --allow-missing without --async on a non-existing resource,
    # it would return an operation object with an empty name.
    # return early to avoid potential polling error.
    if operation.name is None:
      return None

    if args.async_:
      operations.log_unenroll(admin_cluster_ref, args.async_)
      return operation
    else:
      operation_client = operations.OperationsClient()
      operation_response = operation_client.Wait(operation)
      operations.log_unenroll(admin_cluster_ref, args.async_)
      return operation_response
