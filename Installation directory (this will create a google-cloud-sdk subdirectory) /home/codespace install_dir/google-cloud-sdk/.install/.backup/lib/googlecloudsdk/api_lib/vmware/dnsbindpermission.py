# -*- coding: utf-8 -*- #
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
"""Google Cloud DNS Bind Permission client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware import util


class DNSBindPermissionClient(util.VmwareClientBase):
  """cloud vmware dns bind permission client."""

  def __init__(self):
    super(DNSBindPermissionClient, self).__init__()
    self.service = self.client.projects_locations_dnsBindPermission
    self.describe_service = self.client.projects_locations

  def GetPrincipal(self, dns_bind_permission, user=None, service_account=None):
    if user is not None:
      dns_bind_permission.principal = self.messages.Principal(user=user)
    else:
      dns_bind_permission.principal = self.messages.Principal(
          serviceAccount=service_account
      )

  def Grant(self, project_resource, user=None, service_account=None):
    dns_bind_permission = self.messages.GrantDnsBindPermissionRequest()
    self.GetPrincipal(
        dns_bind_permission, user=user, service_account=service_account
    )
    dns_bind_permission_name = (
        '{project}/locations/global/dnsBindPermission'.format(
            project=project_resource.RelativeName()
        )
    )
    request = self.messages.VmwareengineProjectsLocationsDnsBindPermissionGrantRequest(
        grantDnsBindPermissionRequest=dns_bind_permission,
        name=dns_bind_permission_name,
    )
    return self.service.Grant(request)

  def Revoke(self, project_resource, user=None, service_account=None):
    dns_bind_permission = self.messages.RevokeDnsBindPermissionRequest()
    self.GetPrincipal(
        dns_bind_permission, user=user, service_account=service_account
    )
    dns_bind_permission_name = (
        '{project}/locations/global/dnsBindPermission'.format(
            project=project_resource.RelativeName()
        )
    )
    request = self.messages.VmwareengineProjectsLocationsDnsBindPermissionRevokeRequest(
        revokeDnsBindPermissionRequest=dns_bind_permission,
        name=dns_bind_permission_name,
    )
    return self.service.Revoke(request)

  def Get(self, project_resource):
    dns_bind_permission_name = (
        '{project}/locations/global/dnsBindPermission'.format(
            project=project_resource.RelativeName()
        )
    )
    request = (
        self.messages.VmwareengineProjectsLocationsGetDnsBindPermissionRequest(
            name=dns_bind_permission_name
        )
    )
    return self.describe_service.GetDnsBindPermission(request)
