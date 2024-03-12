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
"""Access approval requests API helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis


def Approve(name):
  """Approve an approval request."""
  client = apis.GetClientInstance('accessapproval', 'v1')
  msgs = apis.GetMessagesModule('accessapproval', 'v1')

  if 'organizations/' in name:
    req = msgs.AccessapprovalOrganizationsApprovalRequestsApproveRequest(
        name=name)
    return client.organizations_approvalRequests.Approve(req)
  if 'folders/' in name:
    req = msgs.AccessapprovalFoldersApprovalRequestsApproveRequest(name=name)
    return client.folders_approvalRequests.Approve(req)

  req = msgs.AccessapprovalProjectsApprovalRequestsApproveRequest(name=name)
  return client.projects_approvalRequests.Approve(req)


def Dismiss(name):
  """Dismiss an approval request."""
  client = apis.GetClientInstance('accessapproval', 'v1')
  msgs = apis.GetMessagesModule('accessapproval', 'v1')

  if 'organizations/' in name:
    req = msgs.AccessapprovalOrganizationsApprovalRequestsDismissRequest(
        name=name)
    return client.organizations_approvalRequests.Dismiss(req)
  if 'folders/' in name:
    req = msgs.AccessapprovalFoldersApprovalRequestsDismissRequest(name=name)
    return client.folders_approvalRequests.Dismiss(req)

  req = msgs.AccessapprovalProjectsApprovalRequestsDismissRequest(name=name)
  return client.projects_approvalRequests.Dismiss(req)


def Invalidate(name):
  """Invalidate an approval request."""
  client = apis.GetClientInstance('accessapproval', 'v1')
  msgs = apis.GetMessagesModule('accessapproval', 'v1')

  if 'organizations/' in name:
    req = msgs.AccessapprovalOrganizationsApprovalRequestsInvalidateRequest(
        name=name)
    return client.organizations_approvalRequests.Invalidate(req)
  if 'folders/' in name:
    req = msgs.AccessapprovalFoldersApprovalRequestsInvalidateRequest(name=name)
    return client.folders_approvalRequests.Invalidate(req)

  req = msgs.AccessapprovalProjectsApprovalRequestsInvalidateRequest(name=name)
  return client.projects_approvalRequests.Invalidate(req)


def Get(name):
  """Get an approval request by name."""
  client = apis.GetClientInstance('accessapproval', 'v1')
  msgs = apis.GetMessagesModule('accessapproval', 'v1')

  if 'organizations/' in name:
    req = msgs.AccessapprovalOrganizationsApprovalRequestsGetRequest(name=name)
    return client.organizations_approvalRequests.Get(req)
  if 'folders/' in name:
    req = msgs.AccessapprovalFoldersApprovalRequestsGetRequest(name=name)
    return client.folders_approvalRequests.Get(req)

  req = msgs.AccessapprovalProjectsApprovalRequestsGetRequest(name=name)
  return client.projects_approvalRequests.Get(req)


def List(parent, filter=None):
  """List approval requests for the parent resource."""
  client = apis.GetClientInstance('accessapproval', 'v1')
  msgs = apis.GetMessagesModule('accessapproval', 'v1')
  req = None
  svc = None

  if 'organizations/' in parent:
    req = msgs.AccessapprovalOrganizationsApprovalRequestsListRequest(
        parent=parent)
    svc = client.organizations_approvalRequests
  elif 'folders/' in parent:
    req = msgs.AccessapprovalFoldersApprovalRequestsListRequest(parent=parent)
    svc = client.folders_approvalRequests
  else:
    req = msgs.AccessapprovalProjectsApprovalRequestsListRequest(parent=parent)
    svc = client.projects_approvalRequests

  if filter:
    req.filter = filter
  else:
    req.filter = 'PENDING'

  return list_pager.YieldFromList(
      svc, req, field='approvalRequests', batch_size_attribute='pageSize')
