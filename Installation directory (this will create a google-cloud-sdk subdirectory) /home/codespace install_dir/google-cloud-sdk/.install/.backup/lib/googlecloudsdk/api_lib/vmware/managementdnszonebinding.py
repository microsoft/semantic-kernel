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
# pylint: disable=locally-disabled, line-too-long
"""Cloud vmware Management DNS zone binding client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.vmware import util


class ManagementDNSZoneBindingClient(util.VmwareClientBase):
  """cloud vmware management dns zone binding client."""

  def __init__(self):
    super(ManagementDNSZoneBindingClient, self).__init__()
    self.service = self.client.projects_locations_privateClouds_managementDnsZoneBindings

  def Create(self, resource,
             vpc_network=None,
             vmware_engine_network=None,
             description=None):
    mgmt_dns_zone_binding = self.messages.ManagementDnsZoneBinding()
    if vpc_network is not None:
      mgmt_dns_zone_binding.vpcNetwork = vpc_network
    else:
      mgmt_dns_zone_binding.vmwareEngineNetwork = vmware_engine_network
    if description is not None:
      mgmt_dns_zone_binding.description = description

    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsManagementDnsZoneBindingsCreateRequest(
        managementDnsZoneBinding=mgmt_dns_zone_binding,
        managementDnsZoneBindingId=resource.Name(),
        parent=resource.Parent().RelativeName())

    return self.service.Create(request)

  def Update(self, resource,
             description):
    mgmt_dns_zone_binding = self.Get(resource)
    update_mask = []
    mgmt_dns_zone_binding.description = description
    update_mask.append('description')

    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsManagementDnsZoneBindingsPatchRequest(
        managementDnsZoneBinding=mgmt_dns_zone_binding,
        name=resource.RelativeName(),
        updateMask=','.join(update_mask))

    return self.service.Patch(request)

  def Delete(self, resource):
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsManagementDnsZoneBindingsDeleteRequest(
        name=resource.RelativeName())
    return self.service.Delete(request)

  def Get(self, resource):
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsManagementDnsZoneBindingsGetRequest(
        name=resource.RelativeName())
    return self.service.Get(request)

  def List(self, resource, filter_expression=None,
           limit=None, page_size=None):
    address_name = resource.RelativeName()
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsManagementDnsZoneBindingsListRequest(
        parent=address_name, filter=filter_expression)
    if page_size:
      request.page_size = page_size
    return list_pager.YieldFromList(
        self.service,
        request,
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=page_size,
        field='managementDnsZoneBindings')

  def Repair(self, resource):
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsManagementDnsZoneBindingsRepairRequest(
        name=resource.RelativeName()
    )
    return self.service.Repair(request)
