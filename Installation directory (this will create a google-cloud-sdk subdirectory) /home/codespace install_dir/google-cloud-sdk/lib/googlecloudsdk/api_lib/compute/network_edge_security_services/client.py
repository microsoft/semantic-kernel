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
"""Network edge security service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


class NetworkEdgeSecurityService(object):
  """Abstracts NetworkEdgeSecurityService resource."""

  def __init__(self, ref, compute_client=None):
    self.ref = ref
    self._compute_client = compute_client

  @property
  def _client(self):
    return self._compute_client.apitools_client

  @property
  def _messages(self):
    return self._compute_client.messages

  def _MakeDeleteRequestTuple(self):
    region = getattr(self.ref, 'region', None)
    return (self._client.networkEdgeSecurityServices, 'Delete',
            self._messages.ComputeNetworkEdgeSecurityServicesDeleteRequest(
                project=self.ref.project,
                region=region,
                networkEdgeSecurityService=self.ref.Name()))

  def _MakeDescribeRequestTuple(self):
    region = getattr(self.ref, 'region', None)
    return (self._client.networkEdgeSecurityServices, 'Get',
            self._messages.ComputeNetworkEdgeSecurityServicesGetRequest(
                project=self.ref.project,
                region=region,
                networkEdgeSecurityService=self.ref.Name()))

  def _MakeCreateRequestTuple(self, network_edge_security_service):
    region = getattr(self.ref, 'region', None)
    return (self._client.networkEdgeSecurityServices, 'Insert',
            self._messages.ComputeNetworkEdgeSecurityServicesInsertRequest(
                project=self.ref.project,
                region=region,
                networkEdgeSecurityService=network_edge_security_service))

  def _MakePatchRequestTuple(self, network_edge_security_service, update_mask):
    region = getattr(self.ref, 'region', None)
    return (
        self._client.networkEdgeSecurityServices, 'Patch',
        self._messages.ComputeNetworkEdgeSecurityServicesPatchRequest(
            project=self.ref.project,
            region=region,
            paths=update_mask,
            networkEdgeSecurityService=self.ref.Name(),
            networkEdgeSecurityServiceResource=network_edge_security_service))

  def Delete(self):
    requests = [self._MakeDeleteRequestTuple()]
    return self._compute_client.MakeRequests(requests)

  def Describe(self):
    requests = [self._MakeDescribeRequestTuple()]
    return self._compute_client.MakeRequests(requests)

  def Create(self, network_edge_security_service=None):
    requests = [self._MakeCreateRequestTuple(network_edge_security_service)]
    return self._compute_client.MakeRequests(requests)

  def Patch(self, network_edge_security_service=None, update_mask=None):
    requests = [
        self._MakePatchRequestTuple(network_edge_security_service, update_mask)
    ]
    return self._compute_client.MakeRequests(requests)
