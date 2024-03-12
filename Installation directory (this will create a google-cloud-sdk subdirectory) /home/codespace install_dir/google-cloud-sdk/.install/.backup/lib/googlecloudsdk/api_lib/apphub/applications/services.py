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
"""Apphub Application Services API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.apphub import consts as api_lib_consts
from googlecloudsdk.api_lib.apphub import utils as api_lib_utils
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


class ServicesClient(object):
  """Client for Application services in apphub API."""

  def __init__(self, release_track=base.ReleaseTrack.ALPHA):
    self.client = api_lib_utils.GetClientInstance(release_track)
    self.messages = api_lib_utils.GetMessagesModule(release_track)
    self._app_services_client = (
        self.client.projects_locations_applications_services
    )
    self._poller = waiter.CloudOperationPoller(
        self._app_services_client,
        self.client.projects_locations_operations,
    )
    self._delete_poller = waiter.CloudOperationPollerNoResources(
        self.client.projects_locations_operations,
    )

  def Describe(self, service):
    """Describe a Application Service in the Project/location.

    Args:
      service: str, the name for the service being described.

    Returns:
      Described service Resource.
    """
    describe_req = (
        self.messages.ApphubProjectsLocationsApplicationsServicesGetRequest(
            name=service
        )
    )
    return self._app_services_client.Get(describe_req)

  def List(
      self,
      parent,
      limit=None,
      page_size=100,
  ):
    """List application services in the Projects/Location.

    Args:
      parent: str,
        projects/{projectId}/locations/{location}/applications/{application}
      limit: int or None, the total number of results to return. Default value
        is None
      page_size: int, the number of entries in each batch (affects requests
        made, but not the yielded results). Default value is 100.

    Returns:
      Generator of matching application services.
    """
    list_req = (
        self.messages.ApphubProjectsLocationsApplicationsServicesListRequest(
            parent=parent
        )
    )
    return list_pager.YieldFromList(
        self._app_services_client,
        list_req,
        field='services',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize',
    )

  def Delete(self, service, async_flag):
    """Delete a application service in the Project/location.

    Args:
      service: str, the name for the service being deleted
      async_flag: Boolean value for async operation. If true the operation will
        be async

    Returns:
      Empty Response Message or Operation based on async flag value.
    """
    delete_req = (
        self.messages.ApphubProjectsLocationsApplicationsServicesDeleteRequest(
            name=service
        )
    )
    operation = self._app_services_client.Delete(delete_req)

    if async_flag:
      return operation

    delete_response = api_lib_utils.WaitForOperation(
        self._delete_poller,
        operation,
        api_lib_consts.DeleteApplicationService.WAIT_FOR_DELETE_MESSAGE,
        api_lib_consts.DeleteApplicationService.DELETE_TIMELIMIT_SEC,
    )

    return delete_response

  def Create(
      self,
      service_id,
      parent,
      async_flag,
      discovered_service,
      display_name,
      description,
      attributes,
  ):
    """Creates an application in the Project/location.

    Args:
      service_id: str, Service ID
      parent: parent for Application resource
      async_flag: Boolean value for async operation. If true the operation will
        be async
      discovered_service: str, Discovered service name
      display_name: str, Human-friendly display name
      description: str, Description of the Service
      attributes: Attributes, Attributes of the Service

    Returns:
      Service or Operation based on async flag value.
    """
    service = self.messages.Service(
        description=description,
        displayName=display_name,
        discoveredService=discovered_service,
        attributes=attributes,
    )

    create_req = (
        self.messages.ApphubProjectsLocationsApplicationsServicesCreateRequest(
            service=service, serviceId=service_id, parent=parent
        )
    )
    operation = self._app_services_client.Create(create_req)

    if async_flag:
      return operation

    create_response = api_lib_utils.WaitForOperation(
        self._poller,
        operation,
        api_lib_consts.CreateApplicationService.WAIT_FOR_CREATE_MESSAGE,
        api_lib_consts.CreateApplicationService.CREATE_TIMELIMIT_SEC,
    )

    return create_response

  def Update(self, service_id, async_flag, attributes, args):
    """Update application service."""
    service, update_mask = self._UpdateHelper(args, attributes)

    if not update_mask:
      log.status.Print(
          api_lib_consts.UpdateApplicationService.EMPTY_UPDATE_HELP_TEXT
      )
      return

    update_request = (
        self.messages.ApphubProjectsLocationsApplicationsServicesPatchRequest(
            name=service_id,
            service=service,
            updateMask=update_mask,
        )
    )

    operation = self._app_services_client.Patch(update_request)

    if async_flag:
      return operation
    update_response = api_lib_utils.WaitForOperation(
        self._poller,
        operation,
        api_lib_consts.UpdateApplicationService.WAIT_FOR_UPDATE_MESSAGE,
        api_lib_consts.UpdateApplicationService.UPDATE_TIMELIMIT_SEC,
    )

    return update_response

  def _UpdateHelper(self, args, attributes):
    """Helper to generate service and update_mask fields for update_request."""
    service = self.messages.Service()
    update_mask = ''

    if args.display_name:
      update_mask = api_lib_utils.AddToUpdateMask(
          update_mask,
          api_lib_consts.UpdateApplicationService.UPDATE_MASK_DISPLAY_NAME_FIELD_NAME,
      )
      service.displayName = args.display_name

    if args.description:
      update_mask = api_lib_utils.AddToUpdateMask(
          update_mask,
          api_lib_consts.UpdateApplicationService.UPDATE_MASK_DESCRIPTION_FIELD_NAME,
      )
      service.description = args.description

    if attributes.criticality:
      update_mask = api_lib_utils.AddToUpdateMask(
          update_mask,
          api_lib_consts.UpdateApplicationService.UPDATE_MASK_ATTR_CRITICALITY_FIELD_NAME,
      )
    if attributes.environment:
      update_mask = api_lib_utils.AddToUpdateMask(
          update_mask,
          api_lib_consts.UpdateApplicationService.UPDATE_MASK_ATTR_ENVIRONMENT_FIELD_NAME,
      )
    if attributes.businessOwners:
      update_mask = api_lib_utils.AddToUpdateMask(
          update_mask,
          api_lib_consts.UpdateApplicationService.UPDATE_MASK_ATTR_BUSINESS_OWNERS_FIELD_NAME,
      )
    if attributes.developerOwners:
      update_mask = api_lib_utils.AddToUpdateMask(
          update_mask,
          api_lib_consts.UpdateApplicationService.UPDATE_MASK_ATTR_DEVELOPER_OWNERS_FIELD_NAME,
      )
    if attributes.operatorOwners:
      update_mask = api_lib_utils.AddToUpdateMask(
          update_mask,
          api_lib_consts.UpdateApplicationService.UPDATE_MASK_ATTR_OPERATOR_OWNERS_FIELD_NAME,
      )

    service.attributes = attributes

    return service, update_mask
