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
"""Access approval service account API helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis


def Get(name):
  """Get the access approval service account for a resource."""
  client = apis.GetClientInstance('accessapproval', 'v1')
  msgs = apis.GetMessagesModule('accessapproval', 'v1')

  if 'organizations/' in name:
    req = msgs.AccessapprovalOrganizationsGetServiceAccountRequest(name=name)
    return client.organizations.GetServiceAccount(req)
  if 'folders/' in name:
    req = msgs.AccessapprovalFoldersGetServiceAccountRequest(name=name)
    return client.folders.GetServiceAccount(req)

  req = msgs.AccessapprovalProjectsGetServiceAccountRequest(name=name)
  return client.projects.GetServiceAccount(req)
