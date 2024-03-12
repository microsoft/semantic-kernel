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
"""Utilities Service Directory services API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.service_directory import base as sd_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util


class ServicesClient(sd_base.ServiceDirectoryApiLibBase):
  """Client for service in the Service Directory API."""

  def __init__(self, release_track=base.ReleaseTrack.GA):
    super(ServicesClient, self).__init__(release_track)
    self.service = self.client.projects_locations_namespaces_services

  def Create(self, service_ref, annotations=None):
    """Services create request."""
    service = self.msgs.Service(annotations=annotations)
    create_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesCreateRequest(
        parent=service_ref.Parent().RelativeName(),
        service=service,
        serviceId=service_ref.servicesId)
    return self.service.Create(create_req)

  def Delete(self, service_ref):
    """Services delete request."""
    delete_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesDeleteRequest(
        name=service_ref.RelativeName())
    return self.service.Delete(delete_req)

  def Describe(self, service_ref):
    """Services describe request."""
    describe_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesGetRequest(
        name=service_ref.RelativeName())
    return self.service.Get(describe_req)

  def List(self, namespace_ref, filter_=None, order_by=None, page_size=None):
    """Services list request."""
    list_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesListRequest(
        parent=namespace_ref.RelativeName(),
        filter=filter_,
        orderBy=order_by,
        pageSize=page_size)
    return list_pager.YieldFromList(
        self.service,
        list_req,
        batch_size=page_size,
        field='services',
        batch_size_attribute='pageSize')

  def Update(self, service_ref, annotations=None):
    """Services update request."""
    mask_parts = []
    if annotations:
      mask_parts.append('annotations')

    service = self.msgs.Service(annotations=annotations)
    update_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesPatchRequest(
        name=service_ref.RelativeName(),
        service=service,
        updateMask=','.join(mask_parts))
    return self.service.Patch(update_req)

  def Resolve(self, service_ref, max_endpoints=None, endpoint_filter=None):
    """Services resolve request."""
    resolve_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesResolveRequest(
        name=service_ref.RelativeName(),
        resolveServiceRequest=self.msgs.ResolveServiceRequest(
            maxEndpoints=max_endpoints, endpointFilter=endpoint_filter))
    return self.service.Resolve(resolve_req)

  def AddIamPolicyBinding(self, service_ref, member, role):
    """Services add iam policy binding request."""
    policy = self.GetIamPolicy(service_ref)
    iam_util.AddBindingToIamPolicy(self.msgs.Binding, policy, member, role)
    return self.SetIamPolicy(service_ref, policy)

  def GetIamPolicy(self, service_ref):
    """Services get iam policy request."""
    get_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesGetIamPolicyRequest(
        resource=service_ref.RelativeName())
    return self.service.GetIamPolicy(get_req)

  def RemoveIamPolicyBinding(self, service_ref, member, role):
    """Services remove iam policy binding request."""
    policy = self.GetIamPolicy(service_ref)
    iam_util.RemoveBindingFromIamPolicy(policy, member, role)
    return self.SetIamPolicy(service_ref, policy)

  def SetIamPolicy(self, service_ref, policy):
    """Services set iam policy request."""
    set_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesSetIamPolicyRequest(
        resource=service_ref.RelativeName(),
        setIamPolicyRequest=self.msgs.SetIamPolicyRequest(policy=policy))
    return self.service.SetIamPolicy(set_req)


class ServicesClientBeta(ServicesClient):
  """Client for service in the Service Directory API."""

  def __init__(self):
    super(ServicesClientBeta, self).__init__(base.ReleaseTrack.BETA)

  def Create(self, service_ref, metadata=None):
    """Services create request."""
    service = self.msgs.Service(metadata=metadata)
    create_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesCreateRequest(
        parent=service_ref.Parent().RelativeName(),
        service=service,
        serviceId=service_ref.servicesId)
    return self.service.Create(create_req)

  def Update(self, service_ref, metadata=None):
    """Services update request."""
    mask_parts = []
    if metadata:
      mask_parts.append('metadata')

    service = self.msgs.Service(metadata=metadata)
    update_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesServicesPatchRequest(
        name=service_ref.RelativeName(),
        service=service,
        updateMask=','.join(mask_parts))
    return self.service.Patch(update_req)
