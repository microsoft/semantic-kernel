# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Rollback node pool command."""

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


def _Args(parser):
  """Register flags for this command.

  Args:
    parser: an argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.
  """

  flags.AddAsyncFlag(parser)
  flags.AddNodePoolNameArg(parser, 'The name of the node pool to rollback.')
  flags.AddNodePoolClusterFlag(
      parser, 'The cluster from which to rollback the node pool.')
  flags.AddRespectPodDisruptionBudgetFlag(parser)
  parser.add_argument(
      '--timeout',
      type=int,
      default=1800,  # Seconds
      hidden=True,
      help='THIS ARGUMENT NEEDS HELP TEXT.')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Rollback(base.Command):
  """Rollback a node-pool upgrade."""

  @staticmethod
  def Args(parser):
    _Args(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.

    Raises:
      util.Error, if rollback failed.
    """
    adapter = self.context['api_adapter']
    location_get = self.context['location_get']
    location = location_get(args)

    pool_ref = adapter.ParseNodePool(args.name, location)

    console_io.PromptContinue(
        message='Node Pool: [{node_pool_id}], of Cluster: [{cluster_name}] '
        'will be rolled back to previous configuration. This operation is '
        'long-running and will block other operations on the cluster '
        '(including delete) until it has run to completion.'.format(
            node_pool_id=pool_ref.nodePoolId, cluster_name=pool_ref.clusterId),
        throw_if_unattended=True,
        cancel_on_no=True)

    try:
      # Make sure it exists (will raise appropriate error if not)
      adapter.GetNodePool(pool_ref)

      op_ref = adapter.RollbackUpgrade(pool_ref, respect_pdb=args.respect_pdb)

      if not args.async_:
        adapter.WaitForOperation(
            op_ref,
            'Rolling back {0}'.format(pool_ref.nodePoolId),
            timeout_s=args.timeout)

    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)

    log.UpdatedResource(pool_ref)
    return op_ref


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class RollbackBeta(Rollback):
  """Rollback a node-pool upgrade."""

  @staticmethod
  def Args(parser):
    _Args(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RollbackAlpha(Rollback):
  """Rollback a node-pool upgrade."""

  @staticmethod
  def Args(parser):
    _Args(parser)

Rollback.detailed_help = {
    'brief':
        'Rollback a node-pool upgrade.',
    'DESCRIPTION':
        """
        Rollback a node-pool upgrade.

Rollback is a method used after a canceled or failed node-pool upgrade. It
makes a best-effort attempt to revert the pool back to its original state.
""",
    'EXAMPLES':
        """\
        To roll back a canceled or failed upgrade in "node-pool-1" in the
        cluster "sample-cluster", run:

          $ {command} node-pool-1 --cluster=sample-cluster
        """,
}
