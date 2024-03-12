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
"""API wrapper for `gcloud network-security security-profile-groups` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

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


def GetMessagesModule(release_track=base.ReleaseTrack.BETA):
  api_version = _API_VERSION_FOR_TRACK.get(release_track)
  return apis.GetMessagesModule(_API_NAME, api_version)


def GetClientInstance(release_track=base.ReleaseTrack.BETA):
  api_version = _API_VERSION_FOR_TRACK.get(release_track)
  return apis.GetClientInstance(_API_NAME, api_version)


def GetApiBaseUrl(release_track=base.ReleaseTrack.BETA):
  api_version = _API_VERSION_FOR_TRACK.get(release_track)
  return resources.GetApiBaseUrlOrThrow(_API_NAME, api_version)


def GetApiVersion(release_track=base.ReleaseTrack.BETA):
  return _API_VERSION_FOR_TRACK.get(release_track)


class Client:
  """API client for security profile group commands."""

  def __init__(self, release_track):
    self._client = GetClientInstance(release_track)
    self._security_profile_group_client = (
        self._client.organizations_locations_securityProfileGroups
    )
    self._operations_client = self._client.organizations_locations_operations
    self._locations_client = self._client.organizations_locations
    self.messages = GetMessagesModule(release_track)
    self._resource_parser = resources.Registry()
    self.api_version = _API_VERSION_FOR_TRACK.get(release_track)
    self._resource_parser.RegisterApiByName(
        _API_NAME, _API_VERSION_FOR_TRACK.get(release_track)
    )

  def WaitForOperation(
      self,
      operation_ref,
      message,
      has_result=False,
      max_wait=datetime.timedelta(seconds=600),
  ):
    """Waits for an operation to complete.

    Polls the Network Security Operation service until the operation completes,
    fails, or max_wait_seconds elapses.

    Args:
      operation_ref: A Resource created by GetOperationRef describing the
        Operation.
      message: The message to display to the user while they wait.
      has_result: If True, the function will return the target of the operation
        when it completes. If False, nothing will be returned.
      max_wait: The time to wait for the operation to succeed before timing out.

    Returns:
      if has_result = True, a Security Profile Group entity.
      Otherwise, None.
    """
    if has_result:
      poller = waiter.CloudOperationPoller(
          self._security_profile_group_client, self._operations_client
      )
    else:
      poller = waiter.CloudOperationPollerNoResources(self._operations_client)

    response = waiter.WaitFor(
        poller, operation_ref, message, max_wait_ms=max_wait.seconds * 1000
    )

    return response

  def GetOperationsRef(self, operation):
    """Operations to Resource used for `waiter.WaitFor`."""
    return self._resource_parser.ParseRelativeName(
        operation.name,
        'networksecurity.organizations.locations.operations',
        False,
        self.api_version,
    )

  def GetSecurityProfileGroup(self, security_profile_group_name):
    """Calls the Security Profile Group Get API.

    Args:
      security_profile_group_name: Fully specified Security Profile Group.

    Returns:
      Security Profile Group object.
    """
    api_request = self.messages.NetworksecurityOrganizationsLocationsSecurityProfileGroupsGetRequest(
        name=security_profile_group_name
    )
    return self._security_profile_group_client.Get(api_request)

  def CreateSecurityProfileGroup(
      self,
      security_profile_group_name,
      security_profile_group_id,
      parent,
      description,
      threat_prevention_profile,
      labels=None,
  ):
    """Calls the Create Security Profile Group API."""
    security_profile_group = self.messages.SecurityProfileGroup(
        name=security_profile_group_name,
        description=description,
        threatPreventionProfile=threat_prevention_profile,
        labels=labels,
    )

    api_request = self.messages.NetworksecurityOrganizationsLocationsSecurityProfileGroupsCreateRequest(
        parent=parent,
        securityProfileGroup=security_profile_group,
        securityProfileGroupId=security_profile_group_id,
    )
    return self._security_profile_group_client.Create(api_request)

  def UpdateSecurityProfileGroup(
      self,
      security_profile_group_name,
      description,
      threat_prevention_profile,
      update_mask,
      labels=None,
  ):
    """Calls the Patch Security Profile Group API."""
    security_profile_group = self.messages.SecurityProfileGroup(
        name=security_profile_group_name,
        description=description,
        threatPreventionProfile=threat_prevention_profile,
        labels=labels,
    )

    api_request = self.messages.NetworksecurityOrganizationsLocationsSecurityProfileGroupsPatchRequest(
        name=security_profile_group_name,
        securityProfileGroup=security_profile_group,
        updateMask=update_mask,
    )
    return self._security_profile_group_client.Patch(api_request)
