# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Complete node-pool upgrade command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class CompleteUpgrade(base.Command):
  """Complete a node pool upgrade."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: an argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    flags.AddNodePoolNameArg(
        parser,
        'Name of the node pool for which the upgrade is to be completed.')
    flags.AddNodePoolClusterFlag(parser,
                                 'Cluster to which the node pool belongs.')
    parser.add_argument(
        '--timeout',
        type=int,
        default=1800,  # Seconds
        hidden=True,
        help='Duration to wait before command timeout.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.

    Raises:
      util.Error, if complete failed.
    """
    adapter = self.context['api_adapter']
    location_get = self.context['location_get']
    location = location_get(args)

    try:
      pool_ref = adapter.ParseNodePool(args.name, location)
      adapter.CompleteNodePoolUpgrade(pool_ref)

    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)

    log.UpdatedResource(pool_ref)


CompleteUpgrade.detailed_help = {
    'brief':
        'Complete a node pool upgrade.',
    'DESCRIPTION':
        """
        Complete a node pool upgrade.

Complete upgrade is a method used to skip the remaining node pool soaking
phase during blue-green node pool upgrades.
""",
    'EXAMPLES':
        """\
        To complete an active upgrade in ``node-pool-1'' in the
        cluster ``sample-cluster'', run:

          $ {command} node-pool-1 --cluster=sample-cluster
        """,
}
