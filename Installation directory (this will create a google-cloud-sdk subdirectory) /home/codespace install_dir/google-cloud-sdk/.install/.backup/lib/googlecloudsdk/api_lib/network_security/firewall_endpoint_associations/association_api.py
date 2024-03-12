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
"""API wrapper for `gcloud network-security firewall-endpoint-associations` commands."""

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


class Client:
  """API client for FWP association commands.

  Attributes:
    messages: API messages class, The Firewall Plus API messages.
  """

  def __init__(self, release_track):
    self._release_track = release_track
    self._client = GetClientInstance(release_track)
    self._association_client = (
        self._client.projects_locations_firewallEndpointAssociations
    )
    self._operations_client = self._client.projects_locations_operations
    self.messages = GetMessagesModule(release_track)
    self._resource_parser = resources.Registry()
    self._resource_parser.RegisterApiByName(
        'networksecurity', _API_VERSION_FOR_TRACK.get(release_track)
    )

  def CreateAssociation(
      self,
      parent,
      network,
      firewall_endpoint,
      association_id=None,
      tls_inspection_policy=None,
      labels=None,
  ):
    """Calls the CreateAssociation API.

    Args:
      parent: The parent of the association, e.g.
        "projects/myproj/locations/us-central1-a"
      network: The network of the association, e.g.
        "projects/myproj/networks/global/my-vpc"
      firewall_endpoint: The firewall endpoint of the association, e.g. "
        organizations/123456/locations/us-central1-a/firewallEndpoints/my-ep"
      association_id: The ID of the association, e.g. "my-assoc".
      tls_inspection_policy: The TLS inspection policy of the association, e.g.
        "projects/my-proj/locations/us-central1/tlsInspectionPolicies/my-tls".
      labels: A dictionary with the labels of the association.

    Returns:
      NetworksecurityProjectsLocationsFirewallEndpointAssociationsCreateResponse
    """

    association = self.messages.FirewallEndpointAssociation(
        network=network,
        firewallEndpoint=firewall_endpoint,
        labels=labels,
        tlsInspectionPolicy=tls_inspection_policy,
    )

    create_request = self.messages.NetworksecurityProjectsLocationsFirewallEndpointAssociationsCreateRequest(
        firewallEndpointAssociation=association,
        firewallEndpointAssociationId=association_id,
        parent=parent,
    )
    return self._association_client.Create(create_request)

  def UpdateAssociation(
      self,
      name,
      update_fields,
  ):
    """Calls the UpdateAssociation API to modify an existing association.

    Args:
      name: The resource name of the association.
      update_fields: A dictionary mapping from field names to update, to their
        new values. Supported values: 'labels', 'tls_inspection_policy',
        'disabled'.

    Returns:
      NetworksecurityProjectsLocationsFirewallEndpointAssociationsPatchResponse
    """
    # Only keys that exist in the dictionary are updated. This is done via the
    # updateMask request parameter. Values for keys that do not exist in the
    # dictionary can be anything and will not be updated.
    if (
        self._release_track == base.ReleaseTrack.ALPHA
        or self._release_track == base.ReleaseTrack.BETA
    ):
      association = self.messages.FirewallEndpointAssociation(
          disabled=update_fields.get('disabled', None),
          labels=update_fields.get('labels', None),
          tlsInspectionPolicy=update_fields.get('tls_inspection_policy', None),
      )
    else:  # GA
      association = self.messages.FirewallEndpointAssociation(
          labels=update_fields.get('labels', None),
          tlsInspectionPolicy=update_fields.get('tls_inspection_policy', None),
      )

    update_request = self.messages.NetworksecurityProjectsLocationsFirewallEndpointAssociationsPatchRequest(
        name=name,
        firewallEndpointAssociation=association,
        updateMask=','.join(update_fields.keys()),
    )
    return self._association_client.Patch(update_request)

  def DeleteAssociation(self, name):
    """Calls the DeleteAssociation API."""
    delete_request = self.messages.NetworksecurityProjectsLocationsFirewallEndpointAssociationsDeleteRequest(
        name=name
    )
    return self._association_client.Delete(delete_request)

  def DescribeAssociation(self, name):
    """Calls the GetAssociation API."""
    get_request = self.messages.NetworksecurityProjectsLocationsFirewallEndpointAssociationsGetRequest(
        name=name
    )
    return self._association_client.Get(get_request)

  def ListAssociations(
      self, parent, limit=None, page_size=None, list_filter=None
  ):
    """Calls the ListAssociations API."""
    list_request = self.messages.NetworksecurityProjectsLocationsFirewallEndpointAssociationsListRequest(
        parent=parent, filter=list_filter
    )
    return list_pager.YieldFromList(
        self._association_client,
        list_request,
        batch_size=page_size,
        limit=limit,
        field='firewallEndpointAssociations',
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
      If has_result = True, an Endpoint entity.
      Otherwise, None.
    """
    if has_result:
      poller = waiter.CloudOperationPoller(
          self._association_client, self._operations_client
      )
    else:
      poller = waiter.CloudOperationPollerNoResources(self._operations_client)

    return waiter.WaitFor(
        poller,
        operation_ref,
        message,
        max_wait_ms=int(max_wait.total_seconds()) * 1000,
    )
