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
"""VMware Engine VPC network peering create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware import networkpeering
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware.network_peerings import flags
from googlecloudsdk.core import log


DETAILED_HELP = {
    'DESCRIPTION':
        """
          Create a VMware Engine VPC network peering. VPC network peering creation is considered finished when the network peering is in ACTIVE state. Check the progress of a VPC network peering using `{parent_command} list`.
        """,
    'EXAMPLES':
        """
          To create a VPC network peering called `new-peering` that connects the VMware Engine network `my-vmware-engine-network` with another VMware Engine network `another-vmware-engine-network` from project `another-project`, run:

          $ {command} new-peering --vmware-engine-network=my-vmware-engine-network --peer-network=another-vmware-engine-network --peer-network-type=VMWARE_ENGINE_NETWORK --peer-project=another-project

          In this example, the project is taken from gcloud properties core/project and location is taken as `global`.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a VMware Engine VPC network peering."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    peer_network_choices = [
        'PEER_NETWORK_TYPE_UNSPECIFIED',
        'STANDARD',
        'VMWARE_ENGINE_NETWORK',
        'PRIVATE_SERVICES_ACCESS',
        'NETAPP_CLOUD_VOLUMES',
        'THIRD_PARTY_SERVICE',
        'DELL_POWERSCALE',
    ]
    flags.AddNetworkPeeringToParser(parser, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--vmware-engine-network',
        required=True,
        help="""\
        ID of the VMware Engine network to attach the new peering to.
        """)
    parser.add_argument(
        '--peer-network',
        required=True,
        help="""\
        ID of the network to peer with the VMware Engine network. The peer network can be a consumer VPC network or another VMware Engine network.
        """)
    parser.add_argument(
        '--peer-network-type',
        required=True,
        choices=peer_network_choices,
        help="""\
        Type of the VPC network to peer with the VMware Engine network. PEER_NETWORK_TYPE must be one of the following:
        * STANDARD: Peering connection used for connecting to another VPC network established by the same user.
          For example, a peering connection to another VPC network in the same project or to an on-premises network.
        * VMWARE_ENGINE_NETWORK: Peering connection used for connecting to another VMware Engine network.
        * PRIVATE_SERVICES_ACCESS: Peering connection used for establishing private services access.
        * NETAPP_CLOUD_VOLUMES: Peering connection used for connecting to NetApp Cloud Volumes.
        * THIRD_PARTY_SERVICE: Peering connection used for connecting to third-party services. Most third-party services require manual setup of reverse peering on the VPC network associated with the third-party service.
        * DELL_POWERSCALE: Peering connection used for connecting to Dell PowerScale Filers.
        """,
    )
    parser.add_argument(
        '--vmware-engine-network-project',
        help="""\
        Project of the VMware Engine network to attach the new peering to. Use this flag when the VMware Engine network is in another project.
        """)
    parser.add_argument(
        '--peer-project',
        help="""\
        Project ID or project number of the peer network. Use this flag when the peer network is in another project.
        """)
    parser.add_argument(
        '--description',
        help="""\
        User-provided description of the VPC network peering.
        """)
    parser.add_argument(
        '--peer-mtu',
        required=False,
        type=arg_parsers.BinarySize(lower_bound='1GB'),
        help="""\
        Maximum transmission unit (MTU) in bytes.
        """)
    parser.add_argument(
        '--export-custom-routes',
        required=False,
        action='store_true',
        default=True,
        help="""\
        True if custom routes are exported to the peered VPC network; false otherwise. The default value is true.
        """)
    parser.add_argument(
        '--import-custom-routes',
        required=False,
        action='store_true',
        default=True,
        help="""\
        True if custom routes are imported to the peered VPC network; false otherwise. The default value is true.
        """)
    parser.add_argument(
        '--import-custom-routes-with-public-ip',
        required=False,
        action='store_true',
        default=True,
        help="""\
        True if all subnet routes with public IP address range are imported; false otherwise. The default value is true.
        """)
    parser.add_argument(
        '--export-custom-routes-with-public-ip',
        required=False,
        action='store_true',
        default=True,
        help="""\
        True if all subnet routes with public IP address range are exported; false otherwise. The default value is true.
        """)
    parser.add_argument(
        '--exchange-subnet-routes',
        required=False,
        action='store_true',
        default=True,
        help="""\
        True if full-mesh connectivity is created and managed automatically between peered VPC networks; false otherwise. This field is always true because Google Compute Engine automatically creates and manages subnetwork routes between two VPC networks when the peering state is ACTIVE.
        """)

  def Run(self, args):
    peering = args.CONCEPTS.network_peering.Parse()
    client = networkpeering.NetworkPeeringClient()
    is_async = args.async_

    operation = client.Create(
        peering,
        vmware_engine_network_id=args.vmware_engine_network,
        peer_network_id=args.peer_network,
        peer_network_type=args.peer_network_type,
        description=args.description,
        vmware_engine_network_project=args.vmware_engine_network_project,
        peer_project=args.peer_project,
        peer_mtu=args.peer_mtu,
        export_custom_routes=args.export_custom_routes,
        import_custom_routes=args.import_custom_routes,
        export_custom_routes_with_public_ip=args.export_custom_routes_with_public_ip,
        import_custom_routes_with_public_ip=args.import_custom_routes_with_public_ip,
        exchange_subnet_routes=args.exchange_subnet_routes
    )
    if is_async:
      log.CreatedResource(
          operation.name, kind='VPC network peering', is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for vpc peering [{}] to be created'.format(
            peering.RelativeName()))
    log.CreatedResource(peering.RelativeName(), kind='VPC network peering')
    return resource
