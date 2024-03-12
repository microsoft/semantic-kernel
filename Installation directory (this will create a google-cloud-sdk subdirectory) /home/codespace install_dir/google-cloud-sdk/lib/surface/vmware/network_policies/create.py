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
"""'vmware network-policies create' command."""
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
          Create a VMware Engine network policy. Only one network policy applies to a VMware Engine network per region. Check the progress of a network policy creation using `{parent_command} list`.
        """,
    'EXAMPLES':
        """
          To create a network policy called `my-network-policy` which connects to the VMware Engine network `my-vmware-engine-network` using the edge services address range `192.168.0.0/26` with the internet access service enabled and the external IP access service disabled, run:

            $ {command} my-network-policy --location=us-west2 --project=my-project --vmware-engine-network=my-vmware-engine-network --edge-services-cidr=192.168.0.0/26 --internet-access --no-external-ip-access

          Or:

            $ {command} my-network-policy --vmware-engine-network=my-vmware-engine-network --edge-services-cidr=192.168.0.0/26 --internet-access

          In the second example, the project and the location are taken from gcloud properties core/project and compute/region respectively. If the `--external-ip-access` flag is not specified, it is taken as `False`.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a VMware Engine network policy."""
  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddNetworkPolicyToParser(parser, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--vmware-engine-network',
        required=True,
        help="""\
        Resource ID of the VMware Engine network to attach the new policy to.
        """)
    parser.add_argument(
        '--description',
        help="""\
        User-provided description of the network policy.
        """)
    parser.add_argument(
        '--edge-services-cidr',
        required=True,
        help="""\
        IP address range to use for internet access and external IP access gateways, in CIDR notation. An RFC 1918 CIDR block with a "/26" prefix is required.
        """)
    parser.add_argument(
        '--internet-access',
        action='store_true',
        default=False,
        help="""\
        Enable or disable network service that allows VMware workloads to access the internet. Use `--no-internet-access` to disable. If the flag is not provided, internet access is disabled.
        """)
    parser.add_argument(
        '--external-ip-access',
        action='store_true',
        default=False,
        help="""\
        Enable or disable network service that allows external IP addresses to be assigned to VMware workloads. To enable this service, `internet-access` must also be enabled. Use `--no-external-ip-access` to disable. If the flag is not provided, access to VMware workloads through external IP addresses is disabled.
        """)

  def Run(self, args):
    network_policy = args.CONCEPTS.network_policy.Parse()
    client = NetworkPoliciesClient()
    is_async = args.async_
    operation = client.Create(
        network_policy,
        vmware_engine_network_id=args.vmware_engine_network,
        edge_services_cidr=args.edge_services_cidr,
        description=args.description,
        internet_access=args.internet_access,
        external_ip_access=args.external_ip_access,
    )
    if is_async:
      log.CreatedResource(
          operation.name, kind='VMware Engine network policy', is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for network policy [{}] to be created'.format(
            network_policy.RelativeName()
        ),
    )
    log.CreatedResource(
        network_policy.RelativeName(), kind='VMware Engine network policy'
    )
    return resource
