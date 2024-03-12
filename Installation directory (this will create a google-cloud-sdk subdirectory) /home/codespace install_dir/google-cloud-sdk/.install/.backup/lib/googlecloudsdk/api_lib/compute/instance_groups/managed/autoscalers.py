# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""API library for managing the autoscalers of a managed instance group."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def _IsZonalGroup(ref):
  """Checks if reference to instance group is zonal."""
  return ref.Collection() == 'compute.instanceGroupManagers'


class Client(object):
  """API client class for MIG Autoscalers."""

  def __init__(self, client=None):
    self._client = client

  @property
  def _service(self):
    raise NotImplementedError

  def _ScopeRequest(self, request, igm_ref):
    raise NotImplementedError

  @property
  def message_type(self):
    return self._client.messages.Autoscaler

  def Update(self, igm_ref, autoscaler_resource):
    request = self._service.GetRequestType('Update')(
        project=igm_ref.project,
        autoscaler=autoscaler_resource.name,
        autoscalerResource=autoscaler_resource)
    self._ScopeRequest(request, igm_ref)
    return self._client.MakeRequests([(self._service, 'Update', request)])

  def Patch(self, igm_ref, autoscaler_resource):
    request = self._service.GetRequestType('Patch')(
        project=igm_ref.project,
        autoscaler=autoscaler_resource.name,
        autoscalerResource=autoscaler_resource)
    self._ScopeRequest(request, igm_ref)
    return self._client.MakeRequests([(self._service, 'Patch', request)])

  def Insert(self, igm_ref, autoscaler_resource):
    request = self._service.GetRequestType('Insert')(
        project=igm_ref.project,
        autoscaler=autoscaler_resource,
    )
    self._ScopeRequest(request, igm_ref)
    return self._client.MakeRequests([(self._service, 'Insert', request)])

  def Delete(self, igm_ref, autoscaler_name):
    request = self._service.GetRequestType('Delete')(
        project=igm_ref.project,
        autoscaler=autoscaler_name)
    self._ScopeRequest(request, igm_ref)
    return self._client.MakeRequests([(self._service, 'Delete', request)])


class RegionalClient(Client):

  @property
  def _service(self):
    return self._client.apitools_client.regionAutoscalers

  def _ScopeRequest(self, request, igm_ref):
    request.region = igm_ref.region


class ZonalClient(Client):

  @property
  def _service(self):
    return self._client.apitools_client.autoscalers

  def _ScopeRequest(self, request, igm_ref):
    request.zone = igm_ref.zone


def GetClient(client, igm_ref):
  if _IsZonalGroup(igm_ref):
    return ZonalClient(client)
  else:
    return RegionalClient(client)
