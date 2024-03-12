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
"""Google Cloud private connections peering routes client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.vmware import util


class PrivateConnectionPeeringRoutesClient(util.VmwareClientBase):
  """Google Cloud private connections peering routes client."""

  def __init__(self):
    super(PrivateConnectionPeeringRoutesClient, self).__init__()
    self.service = self.client.projects_locations_privateConnections_peeringRoutes

  def List(self, private_connection):
    private_connection = private_connection.RelativeName()
    request = self.messages.VmwareengineProjectsLocationsPrivateConnectionsPeeringRoutesListRequest(
        parent=private_connection)
    return list_pager.YieldFromList(
        self.service,
        request,
        field='peeringRoutes',
        batch_size_attribute='pageSize')
