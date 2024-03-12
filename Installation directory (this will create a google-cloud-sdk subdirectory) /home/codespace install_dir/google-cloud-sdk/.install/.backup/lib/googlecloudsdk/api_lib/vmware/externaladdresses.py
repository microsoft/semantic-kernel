# -*- coding: utf-8 -*- # # Copyright 2020 Google LLC. All Rights Reserved.
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
"""Cloud vmware External Addresses client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.vmware import util


class ExternalAddressesClient(util.VmwareClientBase):
  """cloud vmware external addresses client."""

  def __init__(self):
    super(ExternalAddressesClient, self).__init__()
    self.service = self.client.projects_locations_privateClouds_externalAddresses

  def Create(self, resource, internal_ip, description=None):
    external_address = self.messages.ExternalAddress(
        internalIp=internal_ip, description=description
    )
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsExternalAddressesCreateRequest(
        externalAddress=external_address,
        externalAddressId=resource.Name(),
        parent=resource.Parent().RelativeName())

    return self.service.Create(request)

  def Update(self, resource, internal_ip=None, description=None):
    external_address = self.Get(resource)
    update_mask = []
    if description is not None:
      external_address.description = description
      update_mask.append('description')
    if internal_ip is not None:
      external_address.internalIp = internal_ip
      update_mask.append('internal_ip')

    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsExternalAddressesPatchRequest(
        externalAddress=external_address,
        name=resource.RelativeName(),
        updateMask=','.join(update_mask),
    )
    return self.service.Patch(request)

  def Delete(self, resource):
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsExternalAddressesDeleteRequest(
        name=resource.RelativeName())
    return self.service.Delete(request)

  def Get(self, resource):
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsExternalAddressesGetRequest(
        name=resource.RelativeName())
    return self.service.Get(request)

  def List(self, resource):
    address_name = resource.RelativeName()
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsExternalAddressesListRequest(
        parent=address_name
    )
    return list_pager.YieldFromList(
        self.service,
        request,
        batch_size_attribute='pageSize',
        field='externalAddresses')
