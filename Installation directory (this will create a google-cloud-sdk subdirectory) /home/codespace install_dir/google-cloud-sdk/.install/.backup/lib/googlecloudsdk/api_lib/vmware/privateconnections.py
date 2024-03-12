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
"""Google Cloud Private Connections client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.vmware import util
from googlecloudsdk.api_lib.vmware.networks import NetworksClient
from googlecloudsdk.command_lib.util.apis import arg_utils


class PrivateConnectionsClient(util.VmwareClientBase):
  """Private Connections client."""

  def __init__(self):
    super(PrivateConnectionsClient, self).__init__()
    self.service = self.client.projects_locations_privateConnections
    self.networks_client = NetworksClient()

  def Get(self, resource):
    request = self.messages.VmwareengineProjectsLocationsPrivateConnectionsGetRequest(
        name=resource.RelativeName())
    response = self.service.Get(request)
    return response

  def Create(self,
             resource,
             vmware_engine_network,
             service_project,
             private_connection_type,
             routing_mode=None,
             description=None,
             service_network=None):
    parent = resource.Parent().RelativeName()
    project = resource.Parent().Parent().Name()
    private_connection_id = resource.Name()
    private_connection = self.messages.PrivateConnection(
        description=description)
    if routing_mode is not None:
      private_connection.routingMode = self.GetRoutingMode(routing_mode)
    ven = self.networks_client.GetByID(project, vmware_engine_network)
    private_connection.vmwareEngineNetwork = ven.name
    type_enum = arg_utils.ChoiceEnumMapper(
        arg_name='type',
        message_enum=self.messages.PrivateConnection.TypeValueValuesEnum,
        include_filter=lambda x: 'TYPE_UNSPECIFIED' not in x).GetEnumForChoice(
            arg_utils.EnumNameToChoice(private_connection_type))
    private_connection.type = type_enum
    service_network = self.GetServiceNetwork(type_enum, service_network)
    private_connection.serviceNetwork = 'projects/{project}/global/networks/{network_id}'.format(
        project=service_project, network_id=service_network)
    request = self.messages.VmwareengineProjectsLocationsPrivateConnectionsCreateRequest(
        parent=parent,
        privateConnection=private_connection,
        privateConnectionId=private_connection_id)
    return self.service.Create(request)

  def Update(self, resource, description=None, routing_mode=None):
    private_connection = self.Get(resource)
    update_mask = []
    if description is not None:
      private_connection.description = description
      update_mask.append('description')
    if routing_mode is not None:
      private_connection.routingMode = self.GetRoutingMode(routing_mode)
      update_mask.append('routing_mode')
    request = self.messages.VmwareengineProjectsLocationsPrivateConnectionsPatchRequest(
        privateConnection=private_connection,
        name=resource.RelativeName(),
        updateMask=','.join(update_mask))
    return self.service.Patch(request)

  def Delete(self, resource):
    request = self.messages.VmwareengineProjectsLocationsPrivateConnectionsDeleteRequest(
        name=resource.RelativeName())
    return self.service.Delete(request)

  def List(self, location_resource):
    location = location_resource.RelativeName()
    request = self.messages.VmwareengineProjectsLocationsPrivateConnectionsListRequest(
        parent=location)
    return list_pager.YieldFromList(
        self.service,
        request,
        field='privateConnections',
        batch_size_attribute='pageSize')

  def GetServiceNetwork(self, type_enum, service_network=None):
    if service_network:
      return service_network
    if type_enum == self.messages.PrivateConnection.TypeValueValuesEnum.PRIVATE_SERVICE_ACCESS:
      return 'servicenetworking'
    if type_enum == self.messages.PrivateConnection.TypeValueValuesEnum.DELL_POWERSCALE:
      return 'dell-tenant-vpc'
    if type_enum == self.messages.PrivateConnection.TypeValueValuesEnum.NETAPP_CLOUD_VOLUMES:
      return 'netapp-tenant-vpc'

  def GetRoutingMode(self, routing_mode):
    routing_mode_enum = arg_utils.ChoiceEnumMapper(
        arg_name='routing_mode',
        message_enum=self.messages.PrivateConnection.RoutingModeValueValuesEnum,
        include_filter=lambda x: 'ROUTING_MODE_UNSPECIFIED' not in x
    ).GetEnumForChoice(arg_utils.EnumNameToChoice(routing_mode))
    return routing_mode_enum
