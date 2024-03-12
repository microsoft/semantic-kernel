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
"""Utilities Service Directory namespaces API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.service_directory import base as sd_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util


class NamespacesClient(sd_base.ServiceDirectoryApiLibBase):
  """Client for namespaces in the Service Directory API."""

  def __init__(self, release_track=base.ReleaseTrack.GA):
    super(NamespacesClient, self).__init__(release_track)
    self.service = self.client.projects_locations_namespaces

  def Create(self, namespace_ref, labels=None):
    """Namespaces create request."""
    namespace = self.msgs.Namespace(labels=labels)
    create_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesCreateRequest(
        parent=namespace_ref.Parent().RelativeName(),
        namespace=namespace,
        namespaceId=namespace_ref.namespacesId)
    return self.service.Create(create_req)

  def Delete(self, namespace_ref):
    """Namespaces delete request."""
    delete_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesDeleteRequest(
        name=namespace_ref.RelativeName())
    return self.service.Delete(delete_req)

  def Describe(self, namespace_ref):
    """Namespaces describe request."""
    describe_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesGetRequest(
        name=namespace_ref.RelativeName())
    return self.service.Get(describe_req)

  def List(self, location_ref, filter_=None, order_by=None, page_size=None):
    """Namespaces list request."""
    list_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesListRequest(
        parent=location_ref.RelativeName(),
        filter=filter_,
        orderBy=order_by,
        pageSize=page_size)
    return list_pager.YieldFromList(
        self.service,
        list_req,
        batch_size=page_size,
        field='namespaces',
        batch_size_attribute='pageSize')

  def Update(self, namespace_ref, labels=None):
    """Namespaces update request."""
    mask_parts = []
    if labels:
      mask_parts.append('labels')

    namespace = self.msgs.Namespace(labels=labels)
    update_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesPatchRequest(
        name=namespace_ref.RelativeName(),
        namespace=namespace,
        updateMask=','.join(mask_parts))
    return self.service.Patch(update_req)

  def AddIamPolicyBinding(self, namespace_ref, member, role):
    """Namespaces add iam policy binding request."""
    policy = self.GetIamPolicy(namespace_ref)
    iam_util.AddBindingToIamPolicy(self.msgs.Binding, policy, member, role)
    return self.SetIamPolicy(namespace_ref, policy)

  def GetIamPolicy(self, namespace_ref):
    """Namespaces get iam policy request."""
    get_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesGetIamPolicyRequest(
        resource=namespace_ref.RelativeName())
    return self.service.GetIamPolicy(get_req)

  def RemoveIamPolicyBinding(self, namespace_ref, member, role):
    """Namespaces remove iam policy binding request."""
    policy = self.GetIamPolicy(namespace_ref)
    iam_util.RemoveBindingFromIamPolicy(policy, member, role)
    return self.SetIamPolicy(namespace_ref, policy)

  def SetIamPolicy(self, namespace_ref, policy):
    """Namespaces set iam policy request."""
    set_req = self.msgs.ServicedirectoryProjectsLocationsNamespacesSetIamPolicyRequest(
        resource=namespace_ref.RelativeName(),
        setIamPolicyRequest=self.msgs.SetIamPolicyRequest(policy=policy))
    return self.service.SetIamPolicy(set_req)
