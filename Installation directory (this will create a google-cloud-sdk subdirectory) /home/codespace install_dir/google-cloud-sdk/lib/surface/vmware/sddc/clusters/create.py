# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""'vmware sddc clusters create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.sddc.clusters import ClustersClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.vmware.sddc import flags
from googlecloudsdk.core import properties

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Create a cluster in a VMware Engine private cloud. Successful creation
          of a cluster results in a cluster in READY state. Check the progress
          of a cluster using `gcloud alpha vmware sddc clusters list`.

          For more examples, refer to the EXAMPLES section below.
        """,
    'EXAMPLES':
        """
          To create a cluster called ``my-cluster'' in private cloud
          ``my-privatecloud'', with three initial nodes created in zone
          ``us-central1-a'', run:

            $ {command} my-cluster --privatecloud=my-privatecloud --region=us-central1 --project=my-project --zone=us-central1-a --node-count=3

          Or:

            $ {command} my-cluster --privatecloud=my-privatecloud -zone=us-central1-a --node-count=3

          In the second example, the project and region are taken from gcloud properties core/project and vmware/region.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a cluster in a VMware Engine private cloud."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddClusterArgToParser(parser)
    parser.add_argument(
        '--node-count',
        required=True,
        type=int,
        help="""\
        Initial number of nodes in the cluster
        """)
    parser.add_argument(
        '--zone',
        required=True,
        help="""\
        Zone in which to create nodes in the cluster
        """)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    cluster = args.CONCEPTS.cluster.Parse()
    client = ClustersClient()
    node_type = properties.VALUES.vmware.node_type.Get()
    node_count = args.node_count
    zone = args.zone
    operation = client.Create(cluster, node_count, node_type, zone, args.labels)
    return client.WaitForOperation(
        operation, 'waiting for cluster [{}] to be created'.format(cluster))


Create.detailed_help = DETAILED_HELP
