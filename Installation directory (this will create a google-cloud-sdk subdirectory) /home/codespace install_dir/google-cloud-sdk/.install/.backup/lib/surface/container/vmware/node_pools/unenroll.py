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
"""Command to unenroll a node pool in an Anthos cluster on VMware."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkeonprem import operations
from googlecloudsdk.api_lib.container.gkeonprem import vmware_node_pools as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.container.gkeonprem import constants
from googlecloudsdk.command_lib.container.vmware import constants as vmware_constants
from googlecloudsdk.command_lib.container.vmware import flags

_EXAMPLES = """
To unenroll a node pool named ``my-node-pool'' in a cluster named
``my-cluster'' managed in location ``us-west1'', run:

$ {command} my-node-pool --cluster=my-cluster --location=us-west1
"""


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Unenroll(base.Command):
  """Unenroll a node pool in an Anthos cluster on VMware."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    parser.display_info.AddFormat(vmware_constants.VMWARE_NODEPOOLS_FORMAT)
    flags.AddNodePoolResourceArg(parser, 'to unenroll')
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddAllowMissingUnenrollNodePool(parser)
    flags.AddValidationOnly(parser)

  def Run(self, args):
    """Runs the unenroll command."""
    node_pool_ref = args.CONCEPTS.node_pool.Parse()
    client = apis.NodePoolsClient()
    operation = client.Unenroll(args)

    if args.async_ and not args.IsSpecified('format'):
      args.format = constants.OPERATIONS_FORMAT

    if args.validate_only:
      return

    # when using --allow-missing without --async on a non-existing resource,
    # it would return an operation object with an empty name.
    # return early to avoid potential polling error.
    if operation.name is None:
      return None

    if args.async_:
      operations.log_unenroll(node_pool_ref, args.async_)
      return operation
    else:
      operation_client = operations.OperationsClient()
      response = operation_client.Wait(operation)
      operations.log_unenroll(node_pool_ref, args.async_)
      return response
