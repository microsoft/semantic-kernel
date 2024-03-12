# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""API Wrapper lib for Cloud IDS."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources

_VERSION_MAP = {
    base.ReleaseTrack.ALPHA: 'v1',
    base.ReleaseTrack.BETA: 'v1',
    base.ReleaseTrack.GA: 'v1'
}


def GetMessagesModule(release_track=base.ReleaseTrack.GA):
  api_version = _VERSION_MAP.get(release_track)
  return apis.GetMessagesModule('ids', api_version)


def GetClientInstance(release_track=base.ReleaseTrack.GA):
  api_version = _VERSION_MAP.get(release_track)
  return apis.GetClientInstance('ids', api_version)


def GetEffectiveApiEndpoint(release_track=base.ReleaseTrack.GA):
  api_version = _VERSION_MAP.get(release_track)
  return apis.GetEffectiveApiEndpoint('ids', api_version)


class Client:
  """API client for IDS commands."""

  def __init__(self, release_track):
    self._client = GetClientInstance(release_track)
    self._endpoint_client = self._client.projects_locations_endpoints
    self._operations_client = self._client.projects_locations_operations
    self._locations_client = self._client.projects_locations
    self.messages = GetMessagesModule(release_track)
    self._resource_parser = resources.Registry()
    self._resource_parser.RegisterApiByName('ids',
                                            _VERSION_MAP.get(release_track))

  def _ParseSeverityLevel(self, severity_name):
    return self.messages.Endpoint.SeverityValueValuesEnum.lookup_by_name(
        severity_name.upper())

  def CreateEndpoint(self,
                     name,
                     parent,
                     network,
                     severity,
                     threat_exceptions=(),
                     description='',
                     enable_traffic_logs=False,
                     labels=None):
    """Calls the CreateEndpoint API."""
    endpoint = self.messages.Endpoint(
        network=network,
        description=description,
        severity=self._ParseSeverityLevel(severity),
        threatExceptions=threat_exceptions,
        trafficLogs=enable_traffic_logs,
        labels=labels)
    req = self.messages.IdsProjectsLocationsEndpointsCreateRequest(
        endpointId=name, parent=parent, endpoint=endpoint)
    return self._endpoint_client.Create(req)

  def UpdateEndpoint(self,
                     name,
                     threat_exceptions,
                     update_mask):
    """Calls the UpdateEndpoint API."""
    endpoint = self.messages.Endpoint(
        name=name,
        threatExceptions=threat_exceptions)
    req = self.messages.IdsProjectsLocationsEndpointsPatchRequest(
        name=name, endpoint=endpoint, updateMask=','.join(update_mask))
    return self._endpoint_client.Patch(req)

  def DeleteEndpoint(self, name):
    """Calls the DeleteEndpoint API."""
    req = self.messages.IdsProjectsLocationsEndpointsDeleteRequest(name=name)
    return self._endpoint_client.Delete(req)

  def DescribeEndpoint(self, name):
    """Calls the GetEndpoint API."""
    req = self.messages.IdsProjectsLocationsEndpointsGetRequest(name=name)
    return self._endpoint_client.Get(req)

  def ListEndpoints(self, parent, limit=None, page_size=None, list_filter=None):
    """Calls the ListEndpoints API."""
    req = self.messages.IdsProjectsLocationsEndpointsListRequest(
        parent=parent, filter=list_filter)
    return list_pager.YieldFromList(
        self._endpoint_client,
        req,
        batch_size=page_size,
        limit=limit,
        field='endpoints',
        batch_size_attribute='pageSize')

  def GetSupportedLocations(self, project):
    """Calls the ListLocations API."""
    req = self.messages.IdsProjectsLocationsListRequest(name='projects/' +
                                                        project)
    return self._locations_client.List(req)

  def GetOperationRef(self, operation):
    """Converts an Operation to a Resource that can be used with `waiter.WaitFor`."""
    return self._resource_parser.ParseRelativeName(
        operation.name, 'ids.projects.locations.operations')

  def WaitForOperation(self,
                       operation_ref,
                       message,
                       has_result=True,
                       max_wait=datetime.timedelta(seconds=600)):
    """Waits for an operation to complete.

    Polls the IDS Operation service until the operation completes, fails, or
      max_wait_seconds elapses.

    Args:
      operation_ref:
        A Resource created by GetOperationRef describing the Operation.
      message:
        The message to display to the user while they wait.
      has_result:
        If True, the function will return the target of the
        operation (the IDS Endpoint) when it completes. If False, nothing will
        be returned (useful for Delete operations)
      max_wait:
        The time to wait for the operation to succeed before timing out.

    Returns:
      if has_result = True, an Endpoint entity.
      Otherwise, None.
    """
    if has_result:
      poller = waiter.CloudOperationPoller(self._endpoint_client,
                                           self._operations_client)
    else:
      poller = waiter.CloudOperationPollerNoResources(self._operations_client)

    return waiter.WaitFor(
        poller, operation_ref, message, max_wait_ms=max_wait.seconds * 1000)

  def CancelOperations(self, name):
    """Calls the CancelOperation API."""
    req = self.messages.IdsProjectsLocationsOperationsCancelRequest(name=name)
    return self._operations_client.Cancel(req)

  def DescribeOperation(self, name):
    """Calls the Operations API."""
    req = self.messages.IdsProjectsLocationsOperationsGetRequest(name=name)
    return self._operations_client.Get(req)

  def ListOperations(self, name, limit=None, page_size=None, list_filter=None):
    """Calls the ListOperations API."""
    req = self.messages.IdsProjectsLocationsOperationsListRequest(
        name=name, filter=list_filter)
    return list_pager.YieldFromList(
        self._operations_client,
        req,
        batch_size=page_size,
        limit=limit,
        field='operations',
        batch_size_attribute='pageSize')
