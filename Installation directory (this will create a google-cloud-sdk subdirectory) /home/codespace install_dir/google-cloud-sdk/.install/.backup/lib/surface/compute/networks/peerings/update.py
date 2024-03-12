# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command for updating network peerings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import exceptions
from googlecloudsdk.command_lib.compute.networks.peerings import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Update(base.Command):
  r"""Update a Compute Engine network peering.

  ## EXAMPLES

  To update the peering named peering-name to both export and import custom
  routes, run:

    $ {command} peering-name \
      --export-custom-routes \
      --import-custom-routes


  To update the peering named peering-name to both export and import subnet
  routes with public ip, run:

    $ {command} peering-name \
      --export-subnet-routes-with-public-ip \
      --import-subnet-routes-with-public-ip
  """

  _support_stack_type = False

  @classmethod
  def Args(cls, parser):
    parser.add_argument('name', help='The name of the peering.')
    parser.add_argument(
        '--network',
        required=True,
        help='The name of the network in the current project to be peered '
        'with the peer network.')
    flags.AddImportCustomRoutesFlag(parser)
    flags.AddExportCustomRoutesFlag(parser)

    flags.AddImportSubnetRoutesWithPublicIpFlag(parser)
    flags.AddExportSubnetRoutesWithPublicIpFlag(parser)

    flags.AddStackType(parser)

  def Run(self, args):
    """Issues the request necessary for updating the peering."""
    self.ValidateArgs(args)
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    network_peering = self._CreateNetworkPeeringForRequest(client, args)

    request = client.messages.ComputeNetworksUpdatePeeringRequest(
        network=args.network,
        networksUpdatePeeringRequest=client.messages
        .NetworksUpdatePeeringRequest(networkPeering=network_peering),
        project=properties.VALUES.core.project.GetOrFail())

    return client.MakeRequests([(client.apitools_client.networks,
                                 'UpdatePeering', request)])

  def _CreateNetworkPeeringForRequest(self, client, args):
    network_peering = client.messages.NetworkPeering(
        name=args.name,
        exportCustomRoutes=args.export_custom_routes,
        importCustomRoutes=args.import_custom_routes,
        exportSubnetRoutesWithPublicIp=args.export_subnet_routes_with_public_ip,
        importSubnetRoutesWithPublicIp=args.import_subnet_routes_with_public_ip)

    if getattr(args, 'stack_type'):
      network_peering.stackType = client.messages.NetworkPeering.StackTypeValueValuesEnum(
          args.stack_type)

    return network_peering

  def ValidateArgs(self, args):
    """Validate arguments."""
    check_args = [
        args.export_custom_routes is None, args.import_custom_routes is None
    ]

    check_args.extend([
        args.export_subnet_routes_with_public_ip is None,
        args.import_subnet_routes_with_public_ip is None
    ])

    check_args.append(args.stack_type is None)

    if all(check_args):
      raise exceptions.UpdatePropertyError(
          'At least one property must be modified.')
