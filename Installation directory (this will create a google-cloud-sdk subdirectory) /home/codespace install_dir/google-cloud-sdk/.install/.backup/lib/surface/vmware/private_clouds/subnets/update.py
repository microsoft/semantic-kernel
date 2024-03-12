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
"""'vmware private-clouds subnets update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.private_clouds.subnets import SubnetsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Update a Subnet. Only ip-cidr-range can be updated. This is a synchronous command and doesn't support `--async` and `--no-async` flags.
        """,
    'EXAMPLES':
        """
        To update a subnet named `my-subnet`, that belongs to the private cloud `my-private-cloud` in project `my-project` and zone `us-west1-a` by changing its ip-cidr-range to `10.0.0.0/24`, run:

          $ {command} my-subnet --private-cloud=my-private-cloud --location=us-west1 --project=my-project --ip-cidr-range=10.0.0.0/24

        Or:

          $ {command} my-subnet --private-cloud=my-private-cloud --ip-cidr-range=10.0.0.0/24

        In the second example, the project and location are taken from gcloud properties `core/project` and `compute/zone`, respectively.
        """
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a subnet."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddSubnetArgToParser(parser)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--ip-cidr-range',
        required=True,
        help="""\
        Updated IP CIDR range for this subnet.
        """)

  def Run(self, args):
    subnet = args.CONCEPTS.subnet.Parse()
    client = SubnetsClient()
    operation = client.Update(subnet, args.ip_cidr_range)
    # Since this is a passthrough API, it doesn't return a standard operation.
    # It returns an operation with only two fields: `done` and `response`. If
    # `operation.done == true` we extract the resource from `operation.response`
    # field otherwise we wait for the operation to be completed.
    if operation.done:
      resource = client.GetResponse(operation)
    else:
      resource = client.WaitForOperation(
          operation_ref=client.GetOperationRef(operation),
          message='waiting for subnet [{}] to be updated'.format(
              subnet.RelativeName()
          ),
      )
    log.UpdatedResource(subnet.RelativeName(), kind='subnet')
    return resource
