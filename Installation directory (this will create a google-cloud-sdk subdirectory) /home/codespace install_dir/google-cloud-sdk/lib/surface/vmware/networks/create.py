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
"""'vmware networks create' command."""

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
          Create a VMware Engine network. VMware Engine network creation is considered finished when the VMware Engine network is in ACTIVE state. Check the progress of a VMware Engine network creation using `{parent_command} list`.
        """,
    'EXAMPLES':
        """
          To create a VMware Engine network of type `STANDARD`, run:

            $ {command} my-network --type=STANDARD --location=global --project=my-project

          Or:

            $ {command} my-network --type=STANDARD

          In the second example, the project is taken from gcloud properties core/project and the location is taken as `global`.

          To create a VMware Engine network of type `LEGACY` in the `us-west2` region, run:

            $ {command} my-network --type=LEGACY --location=us-west2 --project=my-project

          Or:

            $ {command} my-network --type=LEGACY --location=us-west2

          In the last example, the project is taken from gcloud properties core/project. For VMware Engine networks of type `LEGACY`, you must always specify a region as the location.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Google Cloud VMware Engine network."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    type_choices = {
        'STANDARD':
            'Standard network type used for private cloud connectivity. A '
            'VMware Engine network of type STANDARD is a global resource.',
        'LEGACY':
            'Network type used by private clouds created in projects without a'
            ' network of type STANDARD. This network type is only used for new'
            ' PCs in existing projects that continue to use LEGACY network. A '
            'VMware Engine network of type LEGACY is a regional resource.'
    }
    flags.AddNetworkToParser(parser, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--description',
        help="""\
        Text describing the VMware Engine network.
        """)
    parser.add_argument(
        '--type',
        required=True,
        choices=type_choices,
        help="""Type of the VMware Engine network.""")

  def Run(self, args):
    network = args.CONCEPTS.vmware_engine_network.Parse()
    client = NetworksClient()
    is_async = args.async_
    operation = client.Create(network, args.type, args.description)
    if is_async:
      log.CreatedResource(
          operation.name, kind='VMware Engine network', is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for VMware Engine network [{}] to be created'.format(
            network.RelativeName()
        ),
    )
    log.CreatedResource(network.RelativeName(), kind='VMware Engine network')
    return resource
