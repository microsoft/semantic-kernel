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
"""'vmware external-addresses update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware import externaladdresses
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION': """
          Updates an external IP address in a VMware Engine private cloud. Only description and internal-ip can be updated.
        """,
    'EXAMPLES': """
          To update an external IP address called `myip` that belongs to the private cloud `my-private-cloud` in project `my-project` and location `us-west1-a` by changing its description to `"Updated description for the external IP address"` and internal-ip to `165.87.54.14`, run:

            $ {command} myip --project=my-project --private-cloud=my-private-cloud --location=us-west1-a --internal-ip=165.87.54.14 --description="Updated description for the external IP address"

          Or:

            $ {command} myip --private-cloud=my-private-cloud --internal-ip=165.87.54.14 --description="Updated description for the external IP address"

          In the second example, the project and region are taken from gcloud properties core/project and vmware/region.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update an external IP address in a VMware Engine private cloud."""

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
        help="""\
        Updated internal ip address for this external address
        """,
    )
    parser.add_argument(
        '--description',
        help="""\
        Updated description for this external address
        """,
    )

  def Run(self, args):
    external_address = args.CONCEPTS.external_address.Parse()
    client = externaladdresses.ExternalAddressesClient()
    is_async = args.async_
    operation = client.Update(
        external_address, args.internal_ip, args.description
    )
    if is_async:
      log.UpdatedResource(
          operation.name, kind='external address', is_async=True
      )
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for external address [{}] to be updated'.format(
            external_address.RelativeName()
        ),
    )
    log.UpdatedResource(
        external_address.RelativeName(), kind='external address'
    )
    return resource
