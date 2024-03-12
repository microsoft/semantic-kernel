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
"""'vmware external-addresses create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.externaladdresses import ExternalAddressesClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION': """
          Create an external IP address that represents an allocated external IP address and its corresponding internal IP address in the private cloud.
        """,
    'EXAMPLES': """
          To create an external IP address called `myip` that corresponds to the internal IP address `165.87.54.14` that belongs to the private cloud `my-private-cloud` in project `my-project` and location `us-east2-b`, run:

            $ {command} myip --project=my-project --private-cloud=my-private-cloud --location=us-east2-b --internal-ip=165.87.54.14 --description="A short description for the new external address"

          Or:

            $ {command} myip --private-cloud=my-private-cloud --internal-ip=165.87.54.14 --description="A short description for the new external address"

          In the second example, the project and region are taken from gcloud properties core/project and vmware/region.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create an external IP address."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddExternalAddressArgToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--internal-ip',
        required=True,
        help="""\
        internal ip address to which external address will be linked
        """)
    parser.add_argument(
        '--description',
        help="""\
        Text describing the external address
        """,
    )

  def Run(self, args):
    external_address = args.CONCEPTS.external_address.Parse()
    client = ExternalAddressesClient()
    is_async = args.async_
    operation = client.Create(
        external_address, args.internal_ip, args.description
    )
    if is_async:
      log.CreatedResource(
          operation.name, kind='external address', is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for external address [{}] to be created'.format(
            external_address.RelativeName()))
    log.CreatedResource(
        external_address.RelativeName(), kind='external address'
    )
    return resource
