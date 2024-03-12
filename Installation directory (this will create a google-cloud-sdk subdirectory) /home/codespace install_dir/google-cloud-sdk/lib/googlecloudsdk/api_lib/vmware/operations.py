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
"""Cloud vmware operations client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.vmware import util


class OperationsClient(util.VmwareClientBase):
  """cloud vmware operations client."""

  def __init__(self):
    super(OperationsClient, self).__init__()
    self.service = self.client.projects_locations_operations

  def List(self, location_resource):
    location = location_resource.RelativeName()
    request = self.messages.VmwareengineProjectsLocationsOperationsListRequest(
        name=location
    )
    return list_pager.YieldFromList(
        self.service,
        request,
        batch_size_attribute='pageSize',
        field='operations')

  def Get(self, resource):
    request = self.messages.VmwareengineProjectsLocationsOperationsGetRequest(
        name=resource.RelativeName())
    return self.service.Get(request)
