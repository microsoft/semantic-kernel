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
"""Resize cluster command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_io


class Resize(base.Command):
  """Resizes an existing cluster for running containers."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument('name', help='The name of this cluster.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--size',
        type=int,
        dest='num_nodes',
        action=actions.DeprecationAction('--size',
                                         warn='The {flag_name} flag is now '
                                         'deprecated. Please use `--num-nodes` '
                                         'instead.'),
        help='Target number of nodes in the cluster.')
    group.add_argument(
        '--num-nodes',
        type=int,
        help='Target number of nodes in the cluster.')
    parser.add_argument('--node-pool', help='The node pool to resize.')
    flags.AddAsyncFlag(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.
    """
    adapter = self.context['api_adapter']
    location_get = self.context['location_get']
    location = location_get(args)
    cluster_ref = adapter.ParseCluster(args.name, location)
    cluster = None
    cluster_name = args.name
    pool_name = args.node_pool if args.node_pool else 'default-pool'
    try:
      # Attempt to get cluster for better prompts and to validate args.
      # Error is a warning but not fatal. Should only exit with a failure on
      # ResizeNodePool(...) below.
      cluster = adapter.GetCluster(cluster_ref)
      cluster_name = cluster.name
    except (exceptions.HttpException, apitools_exceptions.HttpForbiddenError,
            util.Error) as error:
      log.warning(('Problem loading details of cluster to resize:\n\n{}\n\n'
                   'You can still attempt to resize the cluster.\n').format(
                       console_attr.SafeText(error)))

    if cluster is not None:
      pool_name = adapter.FindNodePool(cluster, args.node_pool).name

    console_io.PromptContinue(
        message=('Pool [{pool}] for [{cluster_name}] will be resized to '
                 '{new_size} node(s) in each zone it spans.').format(
                     pool=pool_name,
                     cluster_name=cluster_name,
                     new_size=args.num_nodes),
        throw_if_unattended=True,
        cancel_on_no=True)

    op_ref = adapter.ResizeNodePool(cluster_ref, pool_name, args.num_nodes)

    if not args.async_:
      adapter.WaitForOperation(op_ref,
                               'Resizing {0}'.format(cluster_ref.clusterId))
    log.UpdatedResource(cluster_ref)


Resize.detailed_help = {
    'brief':
        'Resizes an existing cluster for running containers.',
    'DESCRIPTION':
        """
        Resize an existing cluster to a provided size.

If you have multiple node pools, you must specify which node pool to resize by
using the --node-pool flag. You are not required to use the flag if you have
a single node pool.

When increasing the size of a container cluster, the new instances are created
with the same configuration as the existing instances.
Existing pods are not moved onto the new instances,
but new pods (such as those created by resizing a replication controller)
will be scheduled onto the new instances.

When decreasing a cluster, the nodes are drained. As a result, the pods running
on these nodes are gracefully terminated. If your pods are being managed by a
workload controller, the controller will attempt to reschedule them onto the
remaining instances. If your pods are not managed by a workload controller,
they will not be restarted.
Note that when resizing down, instances running pods and instances without pods
are not differentiated. Resize will pick instances to remove at random.

When you resize a node pool that spans multiple zones, the new size represents
the number of nodes in the node pool per zone. For example, if you have a node
pool of size 2 spanning two zones, the total node count is 4. If you resize the
node pool with `--num-nodes=4`, the total node count becomes 8.
""",
    'EXAMPLES':
        """\
        To resize the default node pool of an existing cluster, run:

          $ {command} sample-cluster --num-nodes=2
        """,
}
