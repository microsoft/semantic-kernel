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
"""Interconnect Remote Location."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import path_simplifier


class InterconnectRemoteLocation(object):
  """Abstracts Interconnect Remote Location resource."""

  def __init__(self, ref, compute_client=None):
    self.ref = ref
    self._compute_client = compute_client

  @property
  def _client(self):
    return self._compute_client.apitools_client

  @property
  def _messages(self):
    return self._compute_client.messages

  def _MapInterconnectLocationUrlToName(self, resource):

    def PermittedConnection(permitted_connection):
      return {
          'interconnectLocation':
              path_simplifier.Name(permitted_connection.interconnectLocation)
      }

    return [
        PermittedConnection(permitted_connection)
        for permitted_connection in resource.permittedConnections
    ]

  def _MakeDescribeRequestTuple(self):
    return (self._client.interconnectRemoteLocations, 'Get',
            self._messages.ComputeInterconnectRemoteLocationsGetRequest(
                project=self.ref.project,
                interconnectRemoteLocation=self.ref.Name()))

  def Describe(self, only_generate_request=False):
    requests = [self._MakeDescribeRequestTuple()]
    if not only_generate_request:
      resources = self._compute_client.MakeRequests(requests)
      resource = resources[0]
      if resource.permittedConnections:
        resource.permittedConnections = self._MapInterconnectLocationUrlToName(
            resource)
      return resource
    return requests
