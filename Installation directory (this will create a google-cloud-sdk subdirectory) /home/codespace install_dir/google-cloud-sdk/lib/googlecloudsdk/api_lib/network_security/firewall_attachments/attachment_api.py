# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""API wrapper for `gcloud network-security firewall-attachment` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources


_API_VERSION_FOR_TRACK = {
    base.ReleaseTrack.ALPHA: 'v1alpha1',
    base.ReleaseTrack.BETA: 'v1beta1',
    base.ReleaseTrack.GA: 'v1',
}
_API_NAME = 'networksecurity'


def GetMessagesModule(release_track=base.ReleaseTrack.ALPHA):
  api_version = _API_VERSION_FOR_TRACK.get(release_track)
  return apis.GetMessagesModule(_API_NAME, api_version)


def GetClientInstance(release_track=base.ReleaseTrack.ALPHA):
  api_version = _API_VERSION_FOR_TRACK.get(release_track)
  return apis.GetClientInstance(_API_NAME, api_version)


def GetEffectiveApiEndpoint(release_track=base.ReleaseTrack.ALPHA):
  api_version = _API_VERSION_FOR_TRACK.get(release_track)
  return apis.GetEffectiveApiEndpoint(_API_NAME, api_version)


def GetApiBaseUrl(release_track=base.ReleaseTrack.ALPHA):
  api_version = _API_VERSION_FOR_TRACK.get(release_track)
  return resources.GetApiBaseUrlOrThrow(_API_NAME, api_version)


def GetApiVersion(release_track=base.ReleaseTrack.ALPHA):
  return _API_VERSION_FOR_TRACK.get(release_track)


class Client:
  """API client for Firewall Attachment commands.

  Attributes:
    messages: API messages class, The Firewall Plus API messages.
  """

  def __init__(self, release_track):
    self._client = GetClientInstance(release_track)
    self._attachment_client = (
        self._client.projects_locations_firewallAttachments
    )
    self._operations_client = self._client.projects_locations_operations
    self.messages = GetMessagesModule(release_track)
    self._resource_parser = resources.Registry()
    self._resource_parser.RegisterApiByName(
        'networksecurity', _API_VERSION_FOR_TRACK.get(release_track)
    )

  def CreateAttachment(
      self,
      attachment_id,
      parent,
      producer_forwarding_rule_name,
      labels=None,
  ):
    """Calls the CreateAttachment API."""

    attachment = self.messages.FirewallAttachment(
        producerForwardingRuleName=producer_forwarding_rule_name,
        labels=labels,
    )

    create_request = self.messages.NetworksecurityProjectsLocationsFirewallAttachmentsCreateRequest(
        firewallAttachment=attachment,
        firewallAttachmentId=attachment_id,
        parent=parent,
    )
    return self._attachment_client.Create(create_request)

  def DeleteAttachment(self, name):
    """Calls the DeleteAttachment API."""
    delete_request = self.messages.NetworksecurityProjectsLocationsFirewallAttachmentsDeleteRequest(
        name=name
    )
    return self._attachment_client.Delete(delete_request)

  def DescribeAttachment(self, name):
    """Calls the GetAttachment API."""
    get_request = self.messages.NetworksecurityProjectsLocationsFirewallAttachmentsGetRequest(
        name=name
    )
    return self._attachment_client.Get(get_request)

  def ListAttachments(
      self, parent, limit=None, page_size=None
  ):
    """Calls the ListAttachments API."""
    list_request = self.messages.NetworksecurityProjectsLocationsFirewallAttachmentsListRequest(
        parent=parent
    )
    return list_pager.YieldFromList(
        self._attachment_client,
        list_request,
        batch_size=page_size,
        limit=limit,
        field='firewallAttachments',
        batch_size_attribute='pageSize',
    )

  def GetOperationRef(self, operation):
    """Converts an Operation to a Resource to use with `waiter.WaitFor`."""
    return self._resource_parser.ParseRelativeName(
        operation.name, 'networksecurity.projects.locations.operations'
    )

  def WaitForOperation(
      self,
      operation_ref,
      message,
      has_result=True,
      max_wait=datetime.timedelta(seconds=600),
  ):
    """Waits for an operation to complete.

    Polls the Firewall Attachment Operation service until the operation
    completes, fails, or max_wait_seconds elapses.

    Args:
      operation_ref: A Resource created by GetOperationRef describing the
        Operation.
      message: The message to display to the user while they wait.
      has_result: If True, the function will return the target of the operation
        (the Firewall Attachment) when it completes. If False, nothing will
        be returned (useful for Delete operations)
      max_wait: The time to wait for the operation to succeed before timing out.

    Returns:
      If has_result = True, an Attachment entity.
      Otherwise, None.
    """
    if has_result:
      poller = waiter.CloudOperationPoller(
          self._attachment_client, self._operations_client
      )
    else:
      poller = waiter.CloudOperationPollerNoResources(self._operations_client)

    return waiter.WaitFor(
        poller,
        operation_ref,
        message,
        max_wait_ms=int(max_wait.total_seconds()) * 1000,
    )
