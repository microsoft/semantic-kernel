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
"""Command to delete an Anthos cluster on bare metal."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkeonprem import bare_metal_clusters as apis
from googlecloudsdk.api_lib.container.gkeonprem import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.container.bare_metal import cluster_flags as flags
from googlecloudsdk.core import log

_EXAMPLES = """
To delete a cluster named ``my-cluster'' managed in location ``us-west1'', run:

$ {command} my-cluster --location=us-west1
"""


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Delete(base.DeleteCommand):
  """Delete an Anthos cluster on bare metal."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    flags.AddClusterResourceArg(parser, verb='to delete')
    flags.AddValidationOnly(parser)
    flags.AddForceCluster(parser)
    flags.AddAllowMissingCluster(parser)
    flags.AddIgnoreErrors(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Runs the delete command."""
    cluster_ref = args.CONCEPTS.cluster.Parse()

    client = apis.ClustersClient()
    operation = client.Delete(args)

    if args.validate_only:
      return

    if operation.name is None:
      return operation

    if args.async_:
      log.DeletedResource(cluster_ref, 'Anthos Cluster on bare metal',
                          args.async_)
      return operation
    else:
      operation_client = operations.OperationsClient()
      response = operation_client.Wait(operation)
      log.DeletedResource(cluster_ref, 'Anthos Cluster on bare metal',
                          args.async_)
      return response
