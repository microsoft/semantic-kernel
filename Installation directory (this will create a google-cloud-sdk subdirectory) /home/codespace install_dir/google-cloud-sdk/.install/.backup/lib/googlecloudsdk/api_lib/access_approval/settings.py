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
"""Access approval settings API helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis


def Delete(name):
  """Delete the access approval settings for a resource."""
  client = apis.GetClientInstance('accessapproval', 'v1')
  msgs = apis.GetMessagesModule('accessapproval', 'v1')

  if 'organizations/' in name:
    req = msgs.AccessapprovalOrganizationsDeleteAccessApprovalSettingsRequest(
        name=name)
    return client.organizations.DeleteAccessApprovalSettings(req)
  if 'folders/' in name:
    req = msgs.AccessapprovalFoldersDeleteAccessApprovalSettingsRequest(
        name=name)
    return client.folders.DeleteAccessApprovalSettings(req)

  req = msgs.AccessapprovalProjectsDeleteAccessApprovalSettingsRequest(
      name=name)
  return client.projects.DeleteAccessApprovalSettings(req)


def Get(name):
  """Get the access approval settings for a resource."""
  client = apis.GetClientInstance('accessapproval', 'v1')
  msgs = apis.GetMessagesModule('accessapproval', 'v1')

  if 'organizations/' in name:
    req = msgs.AccessapprovalOrganizationsGetAccessApprovalSettingsRequest(
        name=name)
    return client.organizations.GetAccessApprovalSettings(req)
  if 'folders/' in name:
    req = msgs.AccessapprovalFoldersGetAccessApprovalSettingsRequest(
        name=name)
    return client.folders.GetAccessApprovalSettings(req)

  req = msgs.AccessapprovalProjectsGetAccessApprovalSettingsRequest(
      name=name)
  return client.projects.GetAccessApprovalSettings(req)


def Update(name, notification_emails, enrolled_services, active_key_version,
           update_mask):
  """Get the access approval settings for a resource.

  Args:
    name: the settings resource name (e.g. projects/123/accessApprovalSettings)
    notification_emails: list of email addresses
    enrolled_services: list of services
    active_key_version: KMS signing key version resource name
    update_mask: which fields to update

  Returns: updated settings
  """
  client = apis.GetClientInstance('accessapproval', 'v1')
  msgs = apis.GetMessagesModule('accessapproval', 'v1')

  settings = None
  services_protos = [msgs.EnrolledService(cloudProduct=s) for s in enrolled_services]
  if len(services_protos) > 0:
    settings = msgs.AccessApprovalSettings(
        name=name,
        enrolledServices=services_protos,
        notificationEmails=notification_emails,
        activeKeyVersion=active_key_version)
  else:
    settings = msgs.AccessApprovalSettings(
        name=name,
        notificationEmails=notification_emails,
        activeKeyVersion=active_key_version)

  if 'organizations/' in name:
    req = msgs.AccessapprovalOrganizationsUpdateAccessApprovalSettingsRequest(
        name=name,
        accessApprovalSettings=settings,
        updateMask=update_mask)
    return client.organizations.UpdateAccessApprovalSettings(req)
  if 'folders/' in name:
    req = msgs.AccessapprovalFoldersUpdateAccessApprovalSettingsRequest(
        name=name,
        accessApprovalSettings=settings,
        updateMask=update_mask)
    return client.folders.UpdateAccessApprovalSettings(req)

  req = msgs.AccessapprovalProjectsUpdateAccessApprovalSettingsRequest(
      name=name,
      accessApprovalSettings=settings,
      updateMask=update_mask)
  return client.projects.UpdateAccessApprovalSettings(req)
