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
"""Command to delete a node pool in an Anthos cluster on VMware."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkeonprem import operations
from googlecloudsdk.api_lib.container.gkeonprem import vmware_node_pools as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.container.vmware import command_util
from googlecloudsdk.command_lib.container.vmware import flags
from googlecloudsdk.core import log

_EXAMPLES = """
To delete a node pool named ``my-node-pool'' in a cluster named
``my-cluster'' managed in location ``us-west1'', run:

$ {command} my-node-pool --cluster=my-cluster --location=us-west1
"""


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Delete(base.DeleteCommand):
  """Delete a node pool in an Anthos cluster on VMware."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    flags.AddNodePoolResourceArg(parser, 'to delete')
    flags.AddAllowMissingDeleteNodePool(parser)
    flags.AddValidationOnly(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddNodePoolIgnoreErrors(parser)

  def Run(self, args):
    """Runs the delete command."""
    node_pool_ref = args.CONCEPTS.node_pool.Parse()
    items = [
        command_util.NodePoolMessage(
            name=node_pool_ref.vmwareNodePoolsId,
            cluster=node_pool_ref.vmwareClustersId)
    ]

    if not args.validate_only:
      command_util.ConfirmationPrompt('node pool', items, 'deleted')

    client = apis.NodePoolsClient()
    operation = client.Delete(args)

    if args.validate_only:
      return

    # when --allow-missing is enabled on a non-existing resource,
    # it would return an operation object with an empty name.
    # return early to avoid potential polling error.
    if operation.name is None:
      return operation

    if args.async_:
      log.DeletedResource(node_pool_ref,
                          'Node Pool in Anthos Cluster on VMware', args.async_)
      return operation
    else:
      operation_client = operations.OperationsClient()
      response = operation_client.Wait(operation)
      log.DeletedResource(node_pool_ref,
                          'Node Pool in Anthos Cluster on VMware', args.async_)
      return response
