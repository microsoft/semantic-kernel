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
"""Command to create a node pool in an Anthos standalone cluster on bare metal."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkeonprem import operations
from googlecloudsdk.api_lib.container.gkeonprem import standalone_node_pools
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.container.bare_metal import constants as bare_metal_constants
from googlecloudsdk.command_lib.container.bare_metal import node_pool_flags
from googlecloudsdk.command_lib.container.bare_metal import standalone_node_pool_flags
from googlecloudsdk.command_lib.container.gkeonprem import constants
from googlecloudsdk.core import log

_EXAMPLES = """
To create a node pool named ``my-node-pool'' in a cluster named
``my-cluster'' managed in location ``us-west1'', run:

$ {command} my-node-pool --cluster=my-cluster --location=us-west1
"""


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a node pool in an Anthos standalone cluster on bare metal."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    """Gathers command line arguments for the create command.

    Args:
      parser: The argparse parser to add the flag to.
    """
    parser.display_info.AddFormat(
        bare_metal_constants.BARE_METAL_NODE_POOLS_FORMAT)
    standalone_node_pool_flags.AddNodePoolResourceArg(parser, 'to create')
    node_pool_flags.AddValidationOnly(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    standalone_node_pool_flags.AddNodePoolAnnotations(parser)
    standalone_node_pool_flags.AddNodePoolDisplayName(parser)
    standalone_node_pool_flags.AddNodePoolConfig(parser)

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
    node_pool_ref = args.CONCEPTS.node_pool.Parse()
    client = standalone_node_pools.StandaloneNodePoolsClient()
    operation = client.Create(args)

    if args.async_ and not args.IsSpecified('format'):
      args.format = constants.OPERATIONS_FORMAT

    if args.async_:
      return operation

    operation_client = operations.OperationsClient()
    operation_response = operation_client.Wait(operation)

    if not args.validate_only:
      log.CreatedResource(
          node_pool_ref,
          'node pool in Anthos standalone cluster on bare metal',
          args.async_,
      )
    return operation_response
