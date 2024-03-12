# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Cloud vmware sddc API utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import resources

_DEFAULT_API_VERSION = 'v1alpha1'


class VmwareClientBase(object):
  """Base class for vwmare API client wrappers."""

  def __init__(self, api_version=_DEFAULT_API_VERSION):
    self._client = apis.GetClientInstance('sddc', api_version)
    self._messages = apis.GetMessagesModule('sddc', api_version)
    self.service = None
    self.operations_service = self.client.projects_locations_operations

  @property
  def client(self):
    return self._client

  @property
  def messages(self):
    return self._messages

  def WaitForOperation(self, operation, message, is_delete=False):
    operation_ref = resources.REGISTRY.Parse(
        operation.name, collection='sddc.projects.locations.operations')
    if is_delete:
      poller = waiter.CloudOperationPollerNoResources(self.operations_service)
    else:
      poller = waiter.CloudOperationPoller(self.service,
                                           self.operations_service)
    return waiter.WaitFor(poller, operation_ref, message)
