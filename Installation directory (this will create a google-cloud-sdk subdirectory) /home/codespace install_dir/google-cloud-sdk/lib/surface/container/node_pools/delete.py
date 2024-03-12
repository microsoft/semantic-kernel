# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Delete node pool command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

DETAILED_HELP = {
    'DESCRIPTION':
        """\
        *{command}* deletes a node pool from a Google Kubernetes Engine (GKE)
        cluster. When you delete a node pool, GKE drains all the nodes in the
        node pool. The draining process involves GKE deleting Pods on each node
        in the node pool. Each node in a node pool is drained by deleting Pods
        with an allotted graceful termination period of `MAX_POD`. `MAX_POD` is
        the maximum `terminationGracePeriodSeconds` set on the Pods scheduled to
        the node with a cap of one hour.
        """,
    'EXAMPLES':
        """\
        To delete the "node-pool-1" node pool from the cluster
        "sample-cluster", run:

          $ {command} node-pool-1 --cluster=sample-cluster
        """,
}


class Delete(base.DeleteCommand):
  """Delete an existing node pool in a running cluster."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    # TODO(b/28639250): Support remote completion when the SDK supports it.
    flags.AddNodePoolNameArg(parser, 'The name of the node pool to delete.')
    parser.add_argument(
        '--timeout',
        type=int,
        default=1800,
        hidden=True,
        help='THIS ARGUMENT NEEDS HELP TEXT.')
    flags.AddAsyncFlag(parser)
    flags.AddNodePoolClusterFlag(
        parser, 'The cluster from which to delete the node pool.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    adapter = self.context['api_adapter']
    location_get = self.context['location_get']
    location = location_get(args)

    pool_ref = adapter.ParseNodePool(args.name, location)

    console_io.PromptContinue(
        message=('The following node pool will be deleted.\n'
                 '[{name}] in cluster [{clusterId}] in [{zone}]').format(
                     name=pool_ref.nodePoolId,
                     clusterId=pool_ref.clusterId,
                     zone=adapter.Zone(pool_ref)),
        throw_if_unattended=True,
        cancel_on_no=True)

    try:
      # Make sure it exists (will raise appropriate error if not)
      adapter.GetNodePool(pool_ref)

      op_ref = adapter.DeleteNodePool(pool_ref)
      if args.async_:
        op = adapter.GetOperation(op_ref)
        if not args.IsSpecified('format'):
          args.format = util.OPERATIONS_FORMAT
        return op
      adapter.WaitForOperation(
          op_ref,
          'Deleting node pool {0}'.format(pool_ref.nodePoolId),
          timeout_s=args.timeout)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)

    log.DeletedResource(pool_ref)
    return op_ref


Delete.detailed_help = DETAILED_HELP
