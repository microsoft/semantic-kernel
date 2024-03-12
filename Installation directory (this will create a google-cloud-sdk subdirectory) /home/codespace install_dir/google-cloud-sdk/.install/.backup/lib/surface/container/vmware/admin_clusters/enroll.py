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
"""Command to enroll an admin cluster in an Anthos cluster on VMware."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkeonprem import operations
from googlecloudsdk.api_lib.container.gkeonprem import vmware_admin_clusters as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.container.gkeonprem import constants
from googlecloudsdk.command_lib.container.gkeonprem import flags
from googlecloudsdk.command_lib.container.vmware import constants as vmware_constants
from googlecloudsdk.command_lib.container.vmware import flags as vmware_flags

_EXAMPLES = """
To enroll a cluster named ``my-cluster'' managed in location ``us-west1''
with admin cluster membership of
``projects/my-project/locations/us-west1/memberships/my-admin-cluster-membership'',
run:

$ {command} my-cluster --location=us-west1 --admin-cluster-membership=projects/my-project/locations/us-west1/memberships/my-admin-cluster-membership
"""


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Enroll(base.Command):
  """Enroll an Anthos on VMware admin cluster."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    parser.display_info.AddFormat(vmware_constants.VMWARE_CLUSTERS_FORMAT)
    flags.AddAdminClusterMembershipResourceArg(parser, positional=False)
    vmware_flags.AddAdminClusterResourceArg(parser, 'to enroll')
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    cluster_client = apis.AdminClustersClient()
    admin_cluster_ref = args.CONCEPTS.admin_cluster.Parse()
    operation = cluster_client.Enroll(args)

    if args.async_ and not args.IsSpecified('format'):
      args.format = constants.OPERATIONS_FORMAT

    if args.async_:
      operations.log_enroll(admin_cluster_ref, args.async_)
      return operation
    else:
      operation_client = operations.OperationsClient()
      operation_response = operation_client.Wait(operation)
      operations.log_enroll(admin_cluster_ref, args.async_)
      return operation_response
