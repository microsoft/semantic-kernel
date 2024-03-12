# -*- coding: utf-8 -*- # # Copyright 2020 Google LLC. All Rights Reserved.
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Google Cloud Identity Sources client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.vmware import util
from googlecloudsdk.command_lib.util.apis import arg_utils


class IdentitySourcesClient(util.VmwareClientBase):
  """Identity Sources client."""

  def __init__(self):
    super(IdentitySourcesClient, self).__init__()
    self.service = self.client.projects_locations_privateClouds_identitySources

  def Create(
      self,
      resource,
      domain,
      base_users_dn,
      base_groups_dn,
      domain_user,
      domain_password,
      protocol,
      primary_server,
      domain_alias=None,
      secondary_server=None,
      ssl_certificates=None,
  ):
    protocol_enum_value = arg_utils.ChoiceEnumMapper(
        arg_name='protocol',
        message_enum=self.messages.IdentitySource.ProtocolValueValuesEnum,
        include_filter=lambda x: 'PROTOCOL_UNSPECIFIED' not in x,
    ).GetEnumForChoice(arg_utils.EnumNameToChoice(protocol))

    source = self.messages.IdentitySource(
        domain=domain,
        baseUsersDn=base_users_dn,
        baseGroupsDn=base_groups_dn,
        domainUser=domain_user,
        domainPassword=domain_password,
        protocol=protocol_enum_value,
        specificDomainControllers=self.messages.SpecificDomainControllers(
            primaryServerUri=primary_server,
            secondaryServerUri=secondary_server,
        ),
        domainAlias=domain_alias,
        sslCertificates=ssl_certificates,
        applianceType=self.messages.IdentitySource.ApplianceTypeValueValuesEnum.VCENTER,
    )

    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsIdentitySourcesCreateRequest(
        identitySource=source,
        identitySourceId=resource.Name(),
        parent=resource.Parent().RelativeName(),
    )

    return self.service.Create(request)

  def Get(self, resource):
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsIdentitySourcesGetRequest(
        name=resource.RelativeName()
    )
    return self.service.Get(request)

  def List(self, resource):
    address_name = resource.RelativeName()
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsIdentitySourcesListRequest(
        parent=address_name
    )

    return list_pager.YieldFromList(
        self.service,
        request,
        batch_size_attribute='pageSize',
        field='identitySources',
    )

  def Update(
      self,
      resource,
      base_users_dn=None,
      base_groups_dn=None,
      domain_user=None,
      domain_password=None,
      ssl_certificates=None,
  ):
    source = self.messages.IdentitySource()
    update_mask = []

    if base_users_dn is not None:
      source.baseUsersDn = base_users_dn
      update_mask.append('base_users_dn')
    if base_groups_dn is not None:
      source.baseGroupsDn = base_groups_dn
      update_mask.append('base_groups_dn')
    if domain_user is not None:
      source.domainUser = domain_user
      update_mask.append('domain_user')
    if domain_password is not None:
      source.domainPassword = domain_password
      update_mask.append('domain_password')
    if ssl_certificates:
      source.sslCertificates = ssl_certificates
      update_mask.append('ssl_certificates')

    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsIdentitySourcesPatchRequest(
        identitySource=source,
        name=resource.RelativeName(),
        updateMask=','.join(update_mask),
    )

    return self.service.Patch(request)

  def Delete(self, resource):
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsIdentitySourcesDeleteRequest(
        name=resource.RelativeName()
    )
    return self.service.Delete(request)
