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
"""Command to enroll a cluster in an Anthos cluster on bare metal."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkeonprem import bare_metal_clusters as apis
from googlecloudsdk.api_lib.container.gkeonprem import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.container.bare_metal import cluster_flags as bare_metal_flags
from googlecloudsdk.command_lib.container.bare_metal import constants as bare_metal_constants
from googlecloudsdk.command_lib.container.gkeonprem import constants

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
  """Enroll an Anthos cluster on bare metal."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    parser.display_info.AddFormat(
        bare_metal_constants.BARE_METAL_CLUSTERS_FORMAT
    )
    bare_metal_flags.AddAdminClusterMembershipResourceArg(
        parser, positional=False
    )
    bare_metal_flags.AddClusterResourceArg(parser, verb='to enroll')
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    cluster_client = apis.ClustersClient()
    cluster_ref = args.CONCEPTS.cluster.Parse()
    operation = cluster_client.Enroll(args)

    if args.async_ and not args.IsSpecified('format'):
      args.format = constants.OPERATIONS_FORMAT

    if args.async_:
      operations.log_enroll(cluster_ref, args.async_)
      return operation
    else:
      operation_client = operations.OperationsClient()
      operation_response = operation_client.Wait(operation)
      operations.log_enroll(cluster_ref, args.async_)
      return operation_response
