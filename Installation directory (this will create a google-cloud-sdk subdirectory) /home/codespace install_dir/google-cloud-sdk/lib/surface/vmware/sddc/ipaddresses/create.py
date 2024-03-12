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
"""'vmware sddc ip create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.sddc.ipaddresses import IPAddressesClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.vmware.sddc import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Linking external ip address to VMware Engine private cloud.
        """,
    'EXAMPLES':
        """
          To link external ip address for internal ip ``165.87.54.14'' called ``myip'' to private cloud
          ``myprivatecloud'', in region ``us-east2'', run:

            $ {command} myip --project=my project --privatecloud=myprivatecloud --region=us-east2 --internal-ip=165.87.54.14

          Or:

            $ {command} myip --privatecloud=myprivatecloud --internal-ip=165.87.54.14

          In the second example, the project and region are taken from gcloud properties core/project and vmware/region.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Link external ip address to VMware Engine private cloud."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddIPArgToParser(parser)
    parser.add_argument(
        '--internal-ip',
        required=True,
        help="""\
        internal ip address to which will be linked external ip
        """)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    resource = args.CONCEPTS.name.Parse()
    client = IPAddressesClient()
    operation = client.Create(
        resource,
        args.internal_ip,
        args.labels,
    )
    resource_path = client.GetResourcePath(
        resource, resource_path=resource, encoded_cluster_groups_id=True)
    return client.WaitForOperation(
        operation, 'waiting for external ip address [{}] to be linked'.format(
            resource_path))


Create.detailed_help = DETAILED_HELP
