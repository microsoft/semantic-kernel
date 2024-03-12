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
"""VMware Engine VPC network peering client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.vmware import util
from googlecloudsdk.api_lib.vmware import networks
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import resources


class NetworkPeeringClient(util.VmwareClientBase):
  """VMware Engine VPC network peering client."""

  def __init__(self):
    super(NetworkPeeringClient, self).__init__()
    self.service = self.client.projects_locations_networkPeerings
    self.networks_client = networks.NetworksClient()

  def Get(self, resource):
    request = (
        self.messages.VmwareengineProjectsLocationsNetworkPeeringsGetRequest(
            name=resource.RelativeName()
        )
    )
    response = self.service.Get(request)
    return response

  def Create(
      self,
      resource,
      vmware_engine_network_id,
      peer_network_id,
      peer_network_type,
      description=None,
      peer_project=None,
      peer_mtu=None,
      export_custom_routes=True,
      import_custom_routes=True,
      export_custom_routes_with_public_ip=True,
      import_custom_routes_with_public_ip=True,
      exchange_subnet_routes=True,
      vmware_engine_network_project=None,
  ):
    project = resource.Parent().Parent().Name()
    if peer_project is None:
      peer_project = project
    parent = resource.Parent().RelativeName()
    peering_id = resource.Name()
    # TODO(b/265135446) : pass the values as arguments into the constructor
    peering = self.messages.NetworkPeering(description=description)
    peer_network_type_enum = arg_utils.ChoiceEnumMapper(
        arg_name='peer-network-type',
        message_enum=self.messages.NetworkPeering
        .PeerNetworkTypeValueValuesEnum,
        include_filter=lambda x: 'UNSPECIFIED' not in x).GetEnumForChoice(
            arg_utils.EnumNameToChoice(peer_network_type))
    peering.peerNetworkType = peer_network_type_enum
    peering.vmwareEngineNetwork = resources.REGISTRY.Parse(
        line=None,
        collection='vmwareengine.projects.locations.vmwareEngineNetworks',
        params={
            'projectsId': (
                vmware_engine_network_project
                if vmware_engine_network_project
                else project
            ),
            'locationsId': 'global',
            'vmwareEngineNetworksId': vmware_engine_network_id,
        },
    ).RelativeName()
    if (
        peer_network_type_enum
        == self.messages.NetworkPeering.PeerNetworkTypeValueValuesEnum.VMWARE_ENGINE_NETWORK
    ):
      peering.peerNetwork = 'projects/{project}/locations/global/vmwareEngineNetworks/{network_id}'.format(
          project=peer_project, network_id=peer_network_id
      )
    else:
      peering.peerNetwork = (
          'projects/{project}/global/networks/{network_id}'.format(
              project=peer_project, network_id=peer_network_id
          )
      )
    if peer_mtu:
      peering.peer_mtu = peer_mtu
    peering.exportCustomRoutes = export_custom_routes
    peering.importCustomRoutes = import_custom_routes
    peering.exportCustomRoutesWithPublicIp = export_custom_routes_with_public_ip
    peering.importCustomRoutesWithPublicIp = import_custom_routes_with_public_ip
    peering.exchangeSubnetRoutes = exchange_subnet_routes
    request = (
        self.messages.VmwareengineProjectsLocationsNetworkPeeringsCreateRequest(
            parent=parent, networkPeering=peering, networkPeeringId=peering_id
        )
    )

    return self.service.Create(request)

  def Update(self, resource, description):
    peering = self.Get(resource)
    update_mask = []
    peering.description = description
    update_mask.append('description')
    request = (
        self.messages.VmwareengineProjectsLocationsNetworkPeeringsPatchRequest(
            networkPeering=peering,
            name=resource.RelativeName(),
            updateMask=','.join(update_mask),
        )
    )
    return self.service.Patch(request)

  def Delete(self, resource):
    return self.service.Delete(
        self.messages.VmwareengineProjectsLocationsNetworkPeeringsDeleteRequest(
            name=resource.RelativeName()
        )
    )

  def List(self, location_resource):
    location = location_resource.RelativeName()
    request = (
        self.messages.VmwareengineProjectsLocationsNetworkPeeringsListRequest(
            parent=location
        )
    )
    return list_pager.YieldFromList(
        self.service,
        request,
        batch_size_attribute='pageSize',
        field='networkPeerings')
