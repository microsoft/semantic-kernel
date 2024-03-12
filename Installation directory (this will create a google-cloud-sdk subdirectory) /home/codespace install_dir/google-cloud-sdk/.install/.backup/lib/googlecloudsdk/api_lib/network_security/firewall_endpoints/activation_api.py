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
"""API wrapper for `gcloud network-security firewall-endpoints` commands."""

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
  """API client for FWP activation commands.

  Attributes:
    messages: API messages class, The Firewall Plus API messages.
  """

  def __init__(self, release_track):
    self._client = GetClientInstance(release_track)
    self._endpoint_client = (
        self._client.organizations_locations_firewallEndpoints
    )
    self._operations_client = self._client.organizations_locations_operations
    self.messages = GetMessagesModule(release_track)
    self._resource_parser = resources.Registry()
    self._resource_parser.RegisterApiByName(
        'networksecurity', _API_VERSION_FOR_TRACK.get(release_track)
    )

  def _ParseEndpointType(self, endpoint_type):
    if endpoint_type is None:
      return None
    return self.messages.FirewallEndpoint.TypeValueValuesEnum.lookup_by_name(
        endpoint_type
    )

  def _ParseThirdPartyEndpointSettings(self, target_firewall_attachment):
    if target_firewall_attachment is None:
      return None
    return self.messages.ThirdPartyEndpointSettings(
        targetFirewallAttachment=target_firewall_attachment,
    )

  def CreateEndpoint(
      self,
      name,
      parent,
      description,
      billing_project_id,
      endpoint_type=None,
      target_firewall_attachment=None,
      labels=None,
  ):
    """Calls the CreateEndpoint API."""

    third_party_endpoint_settings = self._ParseThirdPartyEndpointSettings(
        target_firewall_attachment
    )
    if endpoint_type is not None:
      endpoint = self.messages.FirewallEndpoint(
          labels=labels,
          type=self._ParseEndpointType(endpoint_type),
          thirdPartyEndpointSettings=third_party_endpoint_settings,
          description=description,
          billingProjectId=billing_project_id,
      )
    else:
      endpoint = self.messages.FirewallEndpoint(
          labels=labels,
          description=description,
          billingProjectId=billing_project_id,
      )
    create_request = self.messages.NetworksecurityOrganizationsLocationsFirewallEndpointsCreateRequest(
        firewallEndpoint=endpoint, firewallEndpointId=name, parent=parent
    )
    return self._endpoint_client.Create(create_request)

  def UpdateEndpoint(
      self, name, description, update_mask, labels=None, billing_project_id=None
  ):
    """Calls the UpdateEndpoint API.

    Args:
      name: str, full name of the firewall endpoint.
      description: str, description of the firewall endpoint.
      update_mask: str, comma separated list of fields to update.
      labels: LabelsValue, labels for the firewall endpoint.
      billing_project_id: str, billing project ID.
    Returns:
      Operation ref to track the long-running process.
    """
    endpoint = self.messages.FirewallEndpoint(
        labels=labels,
        description=description,
        billingProjectId=billing_project_id,
    )
    update_request = self.messages.NetworksecurityOrganizationsLocationsFirewallEndpointsPatchRequest(
        name=name,
        firewallEndpoint=endpoint,
        updateMask=update_mask,
    )
    return self._endpoint_client.Patch(update_request)

  def DeleteEndpoint(self, name):
    """Calls the DeleteEndpoint API."""
    delete_request = self.messages.NetworksecurityOrganizationsLocationsFirewallEndpointsDeleteRequest(
        name=name
    )
    return self._endpoint_client.Delete(delete_request)

  def DescribeEndpoint(self, name):
    """Calls the GetEndpoint API."""
    get_request = self.messages.NetworksecurityOrganizationsLocationsFirewallEndpointsGetRequest(
        name=name
    )
    return self._endpoint_client.Get(get_request)

  def ListEndpoints(self, parent, limit=None, page_size=None, list_filter=None):
    """Calls the ListEndpoints API."""
    list_request = self.messages.NetworksecurityOrganizationsLocationsFirewallEndpointsListRequest(
        parent=parent, filter=list_filter
    )
    return list_pager.YieldFromList(
        self._endpoint_client,
        list_request,
        batch_size=page_size,
        limit=limit,
        field='firewallEndpoints',
        batch_size_attribute='pageSize',
    )

  def GetOperationRef(self, operation):
    """Converts an Operation to a Resource that can be used with `waiter.WaitFor`."""
    return self._resource_parser.ParseRelativeName(
        operation.name, 'networksecurity.organizations.locations.operations'
    )

  def WaitForOperation(
      self,
      operation_ref,
      message,
      has_result=True,
      max_wait=datetime.timedelta(seconds=600),
  ):
    """Waits for an operation to complete.

    Polls the Firewall Plus Operation service until the operation completes,
    fails, or max_wait_seconds elapses.

    Args:
      operation_ref: A Resource created by GetOperationRef describing the
        Operation.
      message: The message to display to the user while they wait.
      has_result: If True, the function will return the target of the operation
        (the Firewall Plus Endpoint) when it completes. If False, nothing will
        be returned (useful for Delete operations)
      max_wait: The time to wait for the operation to succeed before timing out.

    Returns:
      if has_result = True, an Endpoint entity.
      Otherwise, None.
    """
    if has_result:
      poller = waiter.CloudOperationPoller(
          self._endpoint_client, self._operations_client
      )
    else:
      poller = waiter.CloudOperationPollerNoResources(self._operations_client)

    return waiter.WaitFor(
        poller,
        operation_ref,
        message,
        max_wait_ms=int(max_wait.total_seconds()) * 1000,
    )
