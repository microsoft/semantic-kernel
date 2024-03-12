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
"""Google Cloud VMware Engine network client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.vmware import util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core.exceptions import Error
from googlecloudsdk.core.resources import REGISTRY


class NetworkNotFoundError(Error):

  def __init__(self, network_id):
    super(NetworkNotFoundError, self).__init__(
        'FAILED_PRECONDITION: The VMware Engine network `{network_id}` doesn\'t exist. Operation on the resource can\'t be fulfilled.'
        .format(network_id=network_id))


class MultipleNetworksFoundError(Error):

  def __init__(self, network_id):
    super(MultipleNetworksFoundError, self).__init__(
        'Multiple VMware Engine networks `{network_id}` exist. Operation on the resource can\'t be fulfilled.'
        .format(network_id=network_id))


class NetworksClient(util.VmwareClientBase):
  """Google Cloud VMware Engine network client."""

  def __init__(self):
    super(NetworksClient, self).__init__()
    self.service = self.client.projects_locations_vmwareEngineNetworks

  def Get(self, resource):
    request = self.messages.VmwareengineProjectsLocationsVmwareEngineNetworksGetRequest(
        name=resource.RelativeName())

    response = self.service.Get(request)
    return response

  def GetByID(self, project, network_id):
    parent_location = REGISTRY.Create(
        'vmwareengine.projects.locations', projectsId=project, locationsId='-')

    networks = list(
        network for network in self.List(parent_location)
        if util.GetResourceId(network.name) == network_id)

    if len(networks) > 1:
      raise MultipleNetworksFoundError(network_id)

    if not networks:
      raise NetworkNotFoundError(network_id)

    return networks[0]

  def Create(self, resource, network_type, description=None):
    parent = resource.Parent().RelativeName()
    network_id = resource.Name()
    network = self.messages.VmwareEngineNetwork(description=description)
    type_enum = arg_utils.ChoiceEnumMapper(
        arg_name='type',
        message_enum=self.messages.VmwareEngineNetwork.TypeValueValuesEnum,
        include_filter=lambda x: 'TYPE_UNSPECIFIED' not in x).GetEnumForChoice(
            arg_utils.EnumNameToChoice(network_type))
    network.type = type_enum
    request = self.messages.VmwareengineProjectsLocationsVmwareEngineNetworksCreateRequest(
        parent=parent,
        vmwareEngineNetwork=network,
        vmwareEngineNetworkId=network_id,
    )
    return self.service.Create(request)

  def Update(self, resource, description):
    network = self.Get(resource)
    update_mask = []
    if description is not None:
      network.description = description
      update_mask.append('description')
    request = self.messages.VmwareengineProjectsLocationsVmwareEngineNetworksPatchRequest(
        vmwareEngineNetwork=network,
        name=resource.RelativeName(),
        updateMask=','.join(update_mask),
    )
    return self.service.Patch(request)

  def Delete(self, resource, delay_hours=None):
    return self.service.Delete(
        self.messages.VmwareengineProjectsLocationsVmwareEngineNetworksDeleteRequest(
            name=resource.RelativeName()
        )
    )

  def List(self, location_resource):
    location = location_resource.RelativeName()
    request = self.messages.VmwareengineProjectsLocationsVmwareEngineNetworksListRequest(
        parent=location
    )
    return list_pager.YieldFromList(
        self.service,
        request,
        batch_size_attribute='pageSize',
        field='vmwareEngineNetworks')
