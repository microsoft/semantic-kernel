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
"""'vmware networks update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.networks import NetworksClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware.networks import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Update a VMware Engine network.
        """,
    'EXAMPLES':
        """
          To update a network named `my-network` of type `STANDARD` by changing its description to `Example description`, run:

            $ {command} my-network --location=global --project=my-project --description='Example description'

          Or:

            $ {command} my-network --description='Example description'

          In the second example, the project is taken from gcloud properties core/project and the location is taken as `global`.

          To update a network named `my-network` of type `LEGACY` by changing its description to `Example description`, run:

            $ {command} my-network --location=us-west2 --project=my-project --description='Example description'

          Or:

            $ {command} my-network --location=us-west2 --description='Example description'

          In the last example, the project is taken from gcloud properties core/project. For VMware Engine networks of type `LEGACY`, you must always specify a region as the location.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Google Cloud VMware Engine network."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddNetworkToParser(parser, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--description',
        help="""\
        Text describing the VMware Engine network
        """)

  def Run(self, args):
    network = args.CONCEPTS.vmware_engine_network.Parse()
    client = NetworksClient()
    is_async = args.async_
    operation = client.Update(network, description=args.description)
    if is_async:
      log.UpdatedResource(
          operation.name, kind='VMware Engine network', is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for VMware Engine network [{}] to be updated'.format(
            network.RelativeName()
        ),
    )
    log.UpdatedResource(network.RelativeName(), kind='VMware Engine network')
    return resource
