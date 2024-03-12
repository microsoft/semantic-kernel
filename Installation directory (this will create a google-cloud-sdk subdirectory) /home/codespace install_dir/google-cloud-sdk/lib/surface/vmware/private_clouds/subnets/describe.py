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
"""'vmware private-clouds subnets describe' command."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.private_clouds.subnets import SubnetsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Describe a Subnet by its resource name. It contains details of the subnet, such as ip_cidr_range, gateway_ip, state, and type.
        """,
    'EXAMPLES':
        """
          To get the information about a subnet resource called `my-subnet`, that belongs to the private cloud `my-private-cloud` in project `my-project` and zone `us-west1-a`, run:

            $ {command} my-subnet --private-cloud=my-private-cloud --location=us-west1-a --project=my-project

          Or:

            $ {command} my-subnet --private-cloud=my-private-cloud

          In the second example, the project and location are taken from gcloud properties `core/project` and `compute/zone`, respectively.
        """
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe a subnet in a VMware Engine private cloud."""
  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddSubnetArgToParser(parser)

  def Run(self, args):
    subnet = args.CONCEPTS.subnet.Parse()
    client = SubnetsClient()
    return client.Get(subnet)
