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
"""'vmware private-clouds create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.privateclouds import PrivateCloudsClient
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.command_lib.vmware.clusters import util
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION': """
          Create a VMware Engine private cloud. Private cloud creation is considered finished when the private cloud is in READY state. Check the progress of a private cloud using `{parent_command} list`.
        """,
    'EXAMPLES': """
          To create a private cloud in the `us-west2-a` zone using `standard-72` nodes that connects to the `my-network` VMware Engine network, run:


          $ {command} my-private-cloud --location=us-west2-a --project=my-project --cluster=my-management-cluster --node-type-config=type=standard-72,count=3 --management-range=192.168.0.0/24 --vmware-engine-network=my-network

          Or:

          $ {command} my-private-cloud --cluster=my-management-cluster --node-type-config=type=standard-72,count=3 --management-range=192.168.0.0/24 --vmware-engine-network=my-network

          In the second example, the project and location are taken from gcloud properties core/project and compute/zone.


          To create a stretched private cloud in the `us-west2` region using `us-west2-a` zone as preferred and `us-west2-b` zone as secondary

          $ {command} my-private-cloud --project=sample-project --location=us-west2 --cluster=my-management-cluster --node-type-config=type=standard-72,count=6 --management-range=192.168.0.0/24 --vmware-engine-network=my-network --type=STRETCHED --preferred-zone=us-west2-a --secondary-zone=us-west2-b

          The project is taken from gcloud properties core/project.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a VMware Engine private cloud."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivatecloudArgToParser(parser, positional=True)
    flags.AddClusterArgToParser(
        parser, positional=False, hide_resource_argument_flags=True
    )
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--description',
        help="""\
        Text describing the private cloud.
        """,
    )
    parser.add_argument(
        '--management-range',
        required=True,
        help="""\
         IP address range in the private cloud to use for management appliances, in CIDR format. Use an IP address range that meets the [VMware Engine networking requirements](https://cloud.google.com/vmware-engine/docs/quickstart-networking-requirements).
        """,
    )
    parser.add_argument(
        '--vmware-engine-network',
        required=True,
        help="""\
        Resource ID of the VMware Engine network attached to the private cloud.
        """,
    )
    parser.add_argument(
        '--node-type-config',
        required=True,
        type=arg_parsers.ArgDict(
            spec={'type': str, 'count': int, 'custom-core-count': int},
            required_keys=('type', 'count'),
        ),
        action='append',
        help="""\
        Information about the type and number of nodes associated with the cluster.

        type (required): canonical identifier of the node type.

        count (required): number of nodes of this type in the cluster.

        custom-core-count (optional): customized number of cores available to each node of the type.
        To get a list of valid values for your node type,
        run the gcloud vmware node-types describe command and reference the
        availableCustomCoreCounts field in the output.
        """,
    )
    parser.add_argument(
        '--type',
        required=False,
        default='STANDARD',
        choices={
            'STANDARD': """Standard private is a zonal resource, with 3 or more nodes nodes. Default type.""",
            'TIME_LIMITED': """Time limited private cloud is a zonal resource, can have only 1 node and
            has limited life span. Will be deleted after defined period of time,
            can be converted into standard private cloud by expanding it up to 3
            or more nodes.""",
            'STRETCHED': """Stretched private cloud is a regional resource with redundancy,
            with a minimum of 6 nodes, nodes count has to be even.""",
        },
        help='Type of the private cloud',
    )
    parser.add_argument(
        '--preferred-zone',
        required=False,
        help="""\
        Zone that will remain operational when connection between the two zones is
        lost. Specify the resource name of a zone that belongs to the region of the
        private cloud.
        """,
    )
    parser.add_argument(
        '--secondary-zone',
        required=False,
        help="""\
        Additional zone for a higher level of availability and load balancing.
        Specify the resource name of a zone that belongs to the region of the
        private cloud.
        """,
    )
    flags.AddAutoscalingSettingsFlagsToParser(parser)

  def Run(self, args):
    privatecloud = args.CONCEPTS.private_cloud.Parse()
    client = PrivateCloudsClient()
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

    operation = client.Create(
        privatecloud,
        cluster_id=args.cluster,
        nodes_configs=nodes_configs,
        network_cidr=args.management_range,
        vmware_engine_network_id=args.vmware_engine_network,
        description=args.description,
        private_cloud_type=args.type,
        preferred_zone=args.preferred_zone,
        secondary_zone=args.secondary_zone,
        autoscaling_settings=autoscaling_settings,
    )
    if is_async:
      log.CreatedResource(operation.name, kind='private cloud', is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for private cloud [{}] to be created'.format(
            privatecloud.RelativeName()
        ),
    )
    log.CreatedResource(privatecloud.RelativeName(), kind='private cloud')
    return resource
