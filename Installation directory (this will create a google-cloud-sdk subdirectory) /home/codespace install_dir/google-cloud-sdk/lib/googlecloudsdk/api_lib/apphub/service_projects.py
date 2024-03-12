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
"""Apphub Service Projects API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.apphub import consts as api_lib_consts
from googlecloudsdk.api_lib.apphub import utils as api_lib_utils
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base


class ServiceProjectsClient(object):
  """Client for service projects in apphub API."""

  def __init__(self, release_track=base.ReleaseTrack.ALPHA):
    self.client = api_lib_utils.GetClientInstance(release_track)
    self.messages = api_lib_utils.GetMessagesModule(release_track)
    self._sp_client = self.client.projects_locations_serviceProjectAttachments
    self._project_locations_client = self.client.projects_locations
    self._poller = waiter.CloudOperationPoller(
        self._sp_client,
        self.client.projects_locations_operations,
    )
    self._remove_poller = waiter.CloudOperationPollerNoResources(
        self.client.projects_locations_operations,
    )

  def Describe(self, service_project):
    """Describe a service project in the Project/location.

    Args:
      service_project: str, the name for the service project being described.

    Returns:
      Described service project Resource.
    """
    describe_req = self.messages.ApphubProjectsLocationsServiceProjectAttachmentsGetRequest(
        name=service_project
    )
    return self._sp_client.Get(describe_req)

  def List(
      self,
      parent,
      limit=None,
      page_size=100,
  ):
    """List service projects in the Projects/Location.

    Args:
      parent: str, projects/{projectId}/locations/{location}
      limit: int or None, the total number of results to return.
        Default value is None
      page_size: int, the number of entries in each batch (affects requests
        made, but not the yielded results). Default value is 100.

    Returns:
      Generator of matching service projects.
    """
    list_req = (
        self.messages.ApphubProjectsLocationsServiceProjectAttachmentsListRequest(
            parent=parent
        )
    )
    return list_pager.YieldFromList(
        self._sp_client,
        list_req,
        field='serviceProjectAttachments',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize',
    )

  def Add(
      self,
      service_project,
      async_flag,
      parent
  ):

    """Add a service project in the Project/location.

    Args:
      service_project: str, the name for the service project being created
      async_flag: Boolean value for async operation. If true the operation will
        be async
      parent: parent for service project resource

    Returns:
      Service Project or Operation based on async flag value.
    """
    service_project_attachment = self.messages.ServiceProjectAttachment(
        serviceProject='projects/' + service_project
    )

    create_req = self.messages.ApphubProjectsLocationsServiceProjectAttachmentsCreateRequest(
        parent=parent,
        serviceProjectAttachment=service_project_attachment,
        serviceProjectAttachmentId=service_project,
    )
    operation = self._sp_client.Create(create_req)

    if async_flag:
      return operation

    create_response = api_lib_utils.WaitForOperation(
        self._poller,
        operation,
        api_lib_consts.AddServiceProject.WAIT_FOR_ADD_MESSAGE,
        api_lib_consts.AddServiceProject.ADD_TIMELIMIT_SEC,
    )

    return create_response

  def Remove(self, service_project, async_flag):
    """Remove a service project in the Project/location.

    Args:
      service_project: str, the name for the service project being deleted
      async_flag: Boolean value for async operation. If true the operation will
        be async

    Returns:
      Empty Response Message or Operation based on async flag value.
    """
    remove_req = self.messages.ApphubProjectsLocationsServiceProjectAttachmentsDeleteRequest(
        name=service_project
    )
    operation = self._sp_client.Delete(remove_req)

    if async_flag:
      return operation

    remove_response = api_lib_utils.WaitForOperation(
        self._remove_poller,
        operation,
        api_lib_consts.RemoveServiceProject.WAIT_FOR_REMOVE_MESSAGE,
        api_lib_consts.RemoveServiceProject.REMOVE_TIMELIMIT_SEC,
    )

    return remove_response

  def Lookup(self, service_project):
    """Lookup a service project in the Project/location.

    Args:
      service_project: Service project id

    Returns:
       Service Project.
    """
    lookup_req = self.messages.ApphubProjectsLocationsLookupServiceProjectAttachmentRequest(
        name='projects/' + service_project + '/locations/global'
    )

    return self._project_locations_client.LookupServiceProjectAttachment(
        lookup_req
    )

  def Detach(self, service_project):
    """Detach a service project in the Project/location.

    Args:
      service_project: Service project id

    Returns:
      None
    """
    detach_req = self.messages.ApphubProjectsLocationsDetachServiceProjectAttachmentRequest(
        name='projects/' + service_project + '/locations/global'
    )
    return self._project_locations_client.DetachServiceProjectAttachment(
        detach_req
    )
