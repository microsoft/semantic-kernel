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
"""'vmware network-policies update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.networkpolicies import NetworkPoliciesClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware.network_policies import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Update a VMware Engine network policy.
        """,
    'EXAMPLES':
        """
          To update a network policy named `my-network-policy` so that it disables the external IP access service, run:

            $ {command} my-network-policy --location=us-west2 --project=my-project --no-external-ip-access

          Or:

            $ {command} my-network-policy --no-external-ip-access

          In the second example, the project and the location are taken from gcloud properties core/project and compute/regions respectively.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a VMware Engine network policy."""
  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddNetworkPolicyToParser(parser, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--description',
        help="""\
        Updated description for the network policy.
        """)
    parser.add_argument(
        '--edge-services-cidr',
        help="""\
        Updated IP address range to use for internet access and external IP access gateways, in CIDR notation.
        """)
    parser.add_argument(
        '--internet-access',
        action='store_true',
        default=None,
        help="""\
        Enable or disable network service that allows VMware workloads to access the internet. Use `--no-internet-access` to disable.
        """)
    parser.add_argument(
        '--external-ip-access',
        action='store_true',
        default=None,
        help="""\
        Enable or disable network service that allows external IP addresses to be assigned to VMware workloads. To enable this service, `internet-access` must also be enabled. Use `--no-external-ip-access` to disable.
        """)

  def Run(self, args):
    network_policy = args.CONCEPTS.network_policy.Parse()
    client = NetworkPoliciesClient()
    is_async = args.async_
    operation = client.Update(network_policy, args.description,
                              args.edge_services_cidr, args.internet_access,
                              args.external_ip_access)
    if is_async:
      log.UpdatedResource(
          operation.name, kind='VMware Engine network policy', is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for network policy [{}] to be updated'.format(
            network_policy.RelativeName()
        ),
    )
    log.UpdatedResource(
        network_policy.RelativeName(), kind='VMware Engine network policy'
    )
    return resource
