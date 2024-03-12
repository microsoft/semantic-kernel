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
"""Cloud Backup and DR Management Servers client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.backupdr import util


class ManagementServersClient(util.BackupDrClientBase):
  """Cloud Backup and DR Management client."""

  def __init__(self):
    super(ManagementServersClient, self).__init__()
    self.service = self.client.projects_locations_managementServers

  def Create(self, resource, network):
    networks = [self.messages.NetworkConfig(network=network)]
    parent = resource.Parent().RelativeName()
    management_server_id = resource.Name()
    management_server = self.messages.ManagementServer(
        networks=networks,
        type=self.messages.ManagementServer.TypeValueValuesEnum.BACKUP_RESTORE,
    )
    request = (
        self.messages.BackupdrProjectsLocationsManagementServersCreateRequest(
            parent=parent,
            managementServer=management_server,
            managementServerId=management_server_id,
        )
    )
    return self.service.Create(request)

  def Delete(self, resource):
    request = (
        self.messages.BackupdrProjectsLocationsManagementServersDeleteRequest(
            name=resource.RelativeName()
        )
    )
    return self.service.Delete(request)
