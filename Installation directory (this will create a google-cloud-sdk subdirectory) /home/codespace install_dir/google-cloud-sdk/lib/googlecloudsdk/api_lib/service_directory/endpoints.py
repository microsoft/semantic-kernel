# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Utilities Service Directory endpoints API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.service_directory import base as sd_base
from googlecloudsdk.calliope import base


class EndpointsClient(sd_base.ServiceDirectoryApiLibBase):
  """Client for endpoints in the Service Directory API."""

  def __init__(self, release_track=base.ReleaseTrack.GA):
    super(EndpointsClient, self).__init__(release_track)
    self.service = self.client.projects_locations_namespaces_services_endpoints

  def Create(self,
             endpoint_ref,
             address=None,
             port=None,
             annotations=None,
             network=None):
    """Endpoints create request."""
    endpoint = self.msgs.Endpoint(
        address=address, port=port, annotations=annotations, network=network)
    create_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesEndpointsCreateRequest(
        parent=endpoint_ref.Parent().RelativeName(),
        endpoint=endpoint,
        endpointId=endpoint_ref.endpointsId)
    return self.service.Create(create_req)

  def Delete(self, endpoint_ref):
    """Endpoints delete request."""
    delete_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesEndpointsDeleteRequest(
        name=endpoint_ref.RelativeName())
    return self.service.Delete(delete_req)

  def Describe(self, endpoint_ref):
    """Endpoints describe request."""
    describe_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesEndpointsGetRequest(
        name=endpoint_ref.RelativeName())
    return self.service.Get(describe_req)

  def List(self, service_ref, filter_=None, order_by=None, page_size=None):
    """Endpoints list request."""
    list_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesEndpointsListRequest(
        parent=service_ref.RelativeName(),
        filter=filter_,
        orderBy=order_by,
        pageSize=page_size)
    return list_pager.YieldFromList(
        self.service,
        list_req,
        batch_size=page_size,
        field='endpoints',
        batch_size_attribute='pageSize')

  def Update(self, endpoint_ref, address=None, port=None, annotations=None):
    """Endpoints update request."""
    mask_parts = []
    if address is not None:
      mask_parts.append('address')
    if port is not None:
      mask_parts.append('port')
    if annotations is not None:
      mask_parts.append('annotations')

    endpoint = self.msgs.Endpoint(
        address=address, port=port, annotations=annotations)
    update_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesEndpointsPatchRequest(
        name=endpoint_ref.RelativeName(),
        endpoint=endpoint,
        updateMask=','.join(mask_parts))
    return self.service.Patch(update_req)


class EndpointsClientBeta(EndpointsClient):
  """Client for endpoints in the v1beta1 Service Directory API."""

  def __init__(self):
    super(EndpointsClientBeta, self).__init__(base.ReleaseTrack.BETA)

  def Create(self,
             endpoint_ref,
             address=None,
             port=None,
             metadata=None,
             network=None):
    """Endpoints create request."""
    endpoint = self.msgs.Endpoint(
        address=address, port=port, metadata=metadata, network=network)
    create_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesEndpointsCreateRequest(
        parent=endpoint_ref.Parent().RelativeName(),
        endpoint=endpoint,
        endpointId=endpoint_ref.endpointsId)
    return self.service.Create(create_req)

  def Update(self, endpoint_ref, address=None, port=None, metadata=None):
    """Endpoints update request."""
    mask_parts = []
    if address is not None:
      mask_parts.append('address')
    if port is not None:
      mask_parts.append('port')
    if metadata is not None:
      mask_parts.append('metadata')

    endpoint = self.msgs.Endpoint(address=address, port=port, metadata=metadata)
    update_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesEndpointsPatchRequest(
        name=endpoint_ref.RelativeName(),
        endpoint=endpoint,
        updateMask=','.join(mask_parts))
    return self.service.Patch(update_req)
