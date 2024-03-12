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
"""VMware Engine VPC network peering update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware import networkpeering
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware.network_peerings import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Update a VMware Engine VPC network peering description.
        """,
    'EXAMPLES':
        """

          To update only the description of a VPC network peering named `my-peering` to `Example description`, run:

            $ {command} my-peering --description="Example description"

          In this example, the project is taken from gcloud properties core/project and location is taken as `global`.

    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Google Cloud VMware Engine VPC network peering."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddNetworkPeeringToParser(parser, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--description',
        required=False,
        help="""\
        Updated description for this VPC network peering.
        """)

  def Run(self, args):
    peering = args.CONCEPTS.network_peering.Parse()
    client = networkpeering.NetworkPeeringClient()
    is_async = args.async_
    operation = client.Update(peering, description=args.description)
    if is_async:
      log.UpdatedResource(
          operation.name, kind='VPC network peering', is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for vpc peering [{}] to be updated'.format(
            peering.RelativeName()))
    log.UpdatedResource(peering.RelativeName(), kind='VPC network peering')
    return resource
