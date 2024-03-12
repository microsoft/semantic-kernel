# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Cloud vmware hcx activation keys client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.vmware import util


class HcxActivationKeysClient(util.VmwareClientBase):
  """cloud vmware hcx activation keys client."""

  def __init__(self):
    super(HcxActivationKeysClient, self).__init__()
    self.service = self.client.projects_locations_privateClouds_hcxActivationKeys

  def Create(self, hcx_activation_key):
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsHcxActivationKeysCreateRequest(
        parent=hcx_activation_key.Parent().RelativeName(),
        hcxActivationKeyId=hcx_activation_key.Name())
    return self.service.Create(request)

  def Get(self, resource):
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsHcxActivationKeysGetRequest(
        name=resource.RelativeName())
    return self.service.Get(request)

  def List(self, private_cloud_resource):
    request = self.messages.VmwareengineProjectsLocationsPrivateCloudsHcxActivationKeysListRequest(
        parent=private_cloud_resource.RelativeName())
    return list_pager.YieldFromList(
        self.service,
        request,
        batch_size_attribute='pageSize',
        field='hcxActivationKeys')
