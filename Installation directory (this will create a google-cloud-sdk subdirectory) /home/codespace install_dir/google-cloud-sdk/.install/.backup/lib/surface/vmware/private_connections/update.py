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
"""'vmware private-connections update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.privateconnections import PrivateConnectionsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Updates a VMware Engine private connection. Only description and routing-mode can be updated.
        """,
    'EXAMPLES':
        """
        To update a private connection named `my-private-connection` in project `my-project` and region `us-west1` by changing its description to `Updated description for the private connection` and routing-mode to `GLOBAL`, run:

          $ {command} my-private-connection --location=us-west1 --project=my-project --description="Updated description for the private connection" --routing-mode=GLOBAL

        Or:

          $ {command} my-private-connection --description="Updated description for the private connection" --routing-mode=GLOBAL

        In the second example, the project and location are taken from gcloud properties core/project and compute/regions, respectively.
        """
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Google Cloud Private Connection."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivateConnectionToParser(parser, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--description',
        help="""\
        Updated description for this Private Connection.
        """)
    parser.add_argument(
        '--routing-mode',
        choices=['GLOBAL', 'REGIONAL'],
        help="""\
        Updated routing mode for this Private Connection.
        """)

  def Run(self, args):
    private_connection = args.CONCEPTS.private_connection.Parse()
    client = PrivateConnectionsClient()
    is_async = args.async_
    operation = client.Update(private_connection, args.description,
                              args.routing_mode)
    if is_async:
      log.UpdatedResource(
          operation.name, kind='Private Connection', is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for private connection [{}] to be updated'.format(
            private_connection.RelativeName()
        ),
    )
    log.UpdatedResource(
        private_connection.RelativeName(), kind='Private Connection'
    )
    return resource
