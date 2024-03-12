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
"""Utilities Assured Workloads API, Workloads Endpoints."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.assured import message_util
from googlecloudsdk.api_lib.assured import util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import resources


WORKLOAD_CREATION_IN_PROGRESS_MESSAGE = 'Creating Assured Workloads environment'


def GetWorkloadURI(resource):
  workload = resources.REGISTRY.ParseRelativeName(
      resource.name,
      collection='assuredworkloads.organizations.locations.workloads',
  )
  return workload.SelfLink()


class WorkloadsClient(object):
  """Client for Workloads in Assured Workloads API."""

  def __init__(self, release_track, no_http=False):
    self.client = util.GetClientInstance(release_track, no_http)
    self.messages = util.GetMessagesModule(release_track)
    self._release_track = release_track
    self._service = self.client.organizations_locations_workloads

  def List(self, parent, limit=None, page_size=100):
    """List all Assured Workloads environments belonging to a given parent organization.

    Args:
      parent: str, the parent organization of the Assured Workloads environment
        to be listed, in the form: organizations/{ORG_ID}/locations/{LOCATION}.
      limit: int or None, the total number of results to return.
      page_size: int, the number of entries in each batch (affects requests
        made, but not the yielded results).

    Returns:
      A list of all Assured Workloads environments belonging to a given parent
      organization.
    """
    list_req = self.messages.AssuredworkloadsOrganizationsLocationsWorkloadsListRequest(
        parent=parent, pageSize=page_size
    )
    return list_pager.YieldFromList(
        self._service,
        list_req,
        field='workloads',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute=None,
    )

  def Create(self, parent, external_id, workload):
    """Create a new Assured Workloads environment in the parent organization.

    Args:
      parent: str, the parent organization of the Assured Workloads environment
        to be created, in the form: organizations/{ORG_ID}/locations/{LOCATION}.
      external_id: str, the identifier that identifies this Assured Workloads
        environment externally.
      workload: Workload, new Assured Workloads environment containing the
        values to be used.

    Returns:
      The created Assured Workloads environment resource.
    """
    create_req = message_util.CreateCreateRequest(
        external_id, parent, workload, self._release_track
    )
    op = self.client.organizations_locations_workloads.Create(create_req)
    return self.WaitForOperation(op, WORKLOAD_CREATION_IN_PROGRESS_MESSAGE)

  def Delete(self, name, etag):
    """Delete an existing Assured Workloads environment.

    Args:
      name: str, name of the Assured Workloads environtment to be deleted, in
        the form:
        organization/{ORG_ID}/locations/{LOCATION}/workloads/{WORKLOAD_ID}
      etag: str, the etag string acquired by reading the Workload.

    Returns:
      Empty response message.
    """
    delete_req = self.messages.AssuredworkloadsOrganizationsLocationsWorkloadsDeleteRequest(
        name=name, etag=etag
    )
    return self.client.organizations_locations_workloads.Delete(delete_req)

  def Describe(self, name):
    """Describe an existing Assured Workloads environment.

    Args:
      name: str, the name for the Assured Workloads environment being described
        in the form:
        organizations/{ORG_ID}/locations/{LOCATION}/workloads/{WORKLOAD_ID}.

    Returns:
      Specified Assured Workloads resource.
    """
    describe_req = (
        self.messages.AssuredworkloadsOrganizationsLocationsWorkloadsGetRequest(
            name=name
        )
    )
    return self.client.organizations_locations_workloads.Get(describe_req)

  def Update(self, workload, name, update_mask):
    """Update the configuration values of an existing Assured Workloads environment.

    Args:
      workload: googleCloudAssuredworkloadsV1beta1Workload, new Assured
        Workloads environment containing the new configuration values to be
        used.
      name: str, the name for the Assured Workloads environment being updated in
        the form:
        organizations/{ORG_ID}/locations/{LOCATION}/workloads/{WORKLOAD_ID}.
      update_mask: str, list of the fields to be updated, for example,
        workload.display_name,workload.labels,workload.violation_notifications_enabled

    Returns:
      Updated Assured Workloads environment resource.
    """

    update_req = message_util.CreateUpdateRequest(
        workload, name, update_mask, self._release_track
    )
    return self.client.organizations_locations_workloads.Patch(update_req)

  def EnableResourceMonitoring(self, name):
    """Enable resource violation monitoring for a workload.

    Args:
      name: str, name of the Assured Workloads for which Resource Monitoring is
        enabled, in the form:
        organization/{ORG_ID}/locations/{LOCATION}/workloads/{WORKLOAD_ID}

    Returns:
      Empty response message.
    """
    enable_req = self.messages.AssuredworkloadsOrganizationsLocationsWorkloadsEnableResourceMonitoringRequest(
        name=name
    )
    return (
        self.client.organizations_locations_workloads.EnableResourceMonitoring(
            enable_req
        )
    )

  def WaitForOperation(self, operation, progress_message):
    """Waits for the given google.longrunning.Operation to complete.

    Args:
      operation: The operation to poll.
      progress_message: String to display for default progress_tracker.

    Raises:
      apitools.base.py.HttpError: if the request returns an HTTP error

    Returns:
      The created Environment resource.
    """
    operation_ref = self.GetOperationResource(operation.name)
    poller = waiter.CloudOperationPoller(
        self.client.organizations_locations_workloads,
        self.client.organizations_locations_operations,
    )
    return waiter.WaitFor(poller, operation_ref, progress_message)

  def GetOperationResource(self, name):
    return resources.REGISTRY.ParseRelativeName(
        name, collection='assuredworkloads.organizations.locations.operations'
    )
