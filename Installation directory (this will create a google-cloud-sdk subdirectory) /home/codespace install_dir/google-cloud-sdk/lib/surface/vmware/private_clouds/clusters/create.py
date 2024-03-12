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
"""'vmware clusters create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.clusters import ClustersClient
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.command_lib.vmware.clusters import util
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Create a cluster in a VMware Engine private cloud. Successful creation of a cluster results in a cluster in READY state. Check the progress of a cluster using `{parent_command} list`.
        """,
    'EXAMPLES':
        """
          To create a cluster called `my-cluster` in private cloud `my-private-cloud`, with 3 initial `standard-72` nodes in zone `us-west2-a`, run:

            $ {command} my-cluster --location=us-west2-a --project=my-project --private-cloud=my-private-cloud --node-type-config=type=standard-72,count=3

            Or:

            $ {command} my-cluster --private-cloud=my-private-cloud --node-type-config=type=standard-72,count=3

            In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Google Cloud VMware Engine cluster."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddClusterArgToParser(parser, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--node-type-config',
        required=True,
        type=arg_parsers.ArgDict(
            spec={
                'type': str,
                'count': int,
                'custom-core-count': int
            },
            required_keys=('type', 'count')),
        action='append',
        help="""\
        Information about the type and number of nodes associated with the cluster.

        type (required): canonical identifier of the node type.

        count (required): number of nodes of this type in the cluster.

        custom-core-count (optional): customized number of cores available to each node of the type.
        To get a list of valid values for your node type,
        run the gcloud vmware node-types describe command and reference the
        availableCustomCoreCounts field in the output.
        """)
    flags.AddAutoscalingSettingsFlagsToParser(parser)

  def Run(self, args):
    cluster = args.CONCEPTS.cluster.Parse()
    client = ClustersClient()
    is_async = args.async_

    nodes_configs = util.ParseNodesConfigsParameters(args.node_type_config)
    autoscaling_settings = None
    if args.autoscaling_settings_from_file:
      autoscaling_settings = util.ParseAutoscalingSettingsFromFileFormat(
          args.autoscaling_settings_from_file
      )
    if (
        args.autoscaling_min_cluster_node_count
        or args.autoscaling_max_cluster_node_count
        or args.autoscaling_cool_down_period
        or args.autoscaling_policy
    ):
      autoscaling_settings = util.ParseAutoscalingSettingsFromInlinedFormat(
          args.autoscaling_min_cluster_node_count,
          args.autoscaling_max_cluster_node_count,
          args.autoscaling_cool_down_period,
          args.autoscaling_policy,
      )
    operation = client.Create(cluster, nodes_configs, autoscaling_settings)

    if is_async:
      log.CreatedResource(operation.name, kind='cluster', is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for cluster [{}] to be created'.format(
            cluster.RelativeName()))
    log.CreatedResource(cluster.RelativeName(), kind='cluster')
    return resource
