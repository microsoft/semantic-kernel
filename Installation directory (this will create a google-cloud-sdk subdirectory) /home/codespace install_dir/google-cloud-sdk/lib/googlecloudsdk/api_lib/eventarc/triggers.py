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
"""Utilities for Eventarc Triggers API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.eventarc import common
from googlecloudsdk.api_lib.eventarc.base import EventarcClientBase
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.eventarc import types
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import iso_duration
from googlecloudsdk.core.util import times

MAX_ACTIVE_DELAY_MINUTES = 2


class NoFieldsSpecifiedError(exceptions.Error):
  """Error when no fields were specified for a Patch operation."""


def CreateTriggersClient(release_track):
  api_version = common.GetApiVersion(release_track)
  if release_track == base.ReleaseTrack.GA:
    return _TriggersClient(api_version)
  else:
    return _TriggersClientBeta(api_version)


def GetTriggerURI(resource):
  trigger = resources.REGISTRY.ParseRelativeName(
      resource.name, collection='eventarc.projects.locations.triggers')
  return trigger.SelfLink()


def TriggerActiveTime(event_type, update_time):
  """Computes the time by which the trigger will become active.

  Args:
    event_type: str, the trigger's event type.
    update_time: str, the time when the trigger was last modified.

  Returns:
    The active time as a string, or None if the trigger is already active.
  """
  if not types.IsAuditLogType(event_type):
    # The delay only applies to Audit Log triggers.
    return None
  update_dt = times.ParseDateTime(update_time)
  delay = iso_duration.Duration(minutes=MAX_ACTIVE_DELAY_MINUTES)
  active_dt = times.GetDateTimePlusDuration(update_dt, delay)
  if times.Now() >= active_dt:
    return None
  return times.FormatDateTime(active_dt, fmt='%H:%M:%S', tzinfo=times.LOCAL)


class _BaseTriggersClient(EventarcClientBase):
  """Base Triggers Client with common methods for v1 and v1beta1 clients."""

  def __init__(self, api_version):
    super(_BaseTriggersClient, self).__init__(common.API_NAME, api_version,
                                              'trigger')
    client = apis.GetClientInstance(common.API_NAME, api_version)
    self._messages = client.MESSAGES_MODULE
    self._service = client.projects_locations_triggers
    self._operation_service = client.projects_locations_operations

  def Create(self, trigger_ref, trigger_message):
    """Creates a new Trigger.

    Args:
      trigger_ref: Resource, the Trigger to create.
      trigger_message: Trigger, the trigger message that holds trigger's
        event_filters, service account, destination, transport, etc.

    Returns:
      A long-running operation for create.
    """
    create_req = self._messages.EventarcProjectsLocationsTriggersCreateRequest(
        parent=trigger_ref.Parent().RelativeName(),
        trigger=trigger_message,
        triggerId=trigger_ref.Name())
    return self._service.Create(create_req)

  def Delete(self, trigger_ref):
    """Deletes a Trigger.

    Args:
      trigger_ref: Resource, the Trigger to delete.

    Returns:
      A long-running operation for delete.
    """
    delete_req = self._messages.EventarcProjectsLocationsTriggersDeleteRequest(
        name=trigger_ref.RelativeName())
    return self._service.Delete(delete_req)

  def Get(self, trigger_ref):
    """Gets a Trigger.

    Args:
      trigger_ref: Resource, the Trigger to get.

    Returns:
      The Trigger message.
    """
    get_req = self._messages.EventarcProjectsLocationsTriggersGetRequest(
        name=trigger_ref.RelativeName())
    return self._service.Get(get_req)

  def List(self, location_ref, limit, page_size):
    """Lists Triggers in a given location.

    Args:
      location_ref: Resource, the location to list Triggers in.
      limit: int or None, the total number of results to return.
      page_size: int, the number of entries in each batch (affects requests
        made, but not the yielded results).

    Returns:
      A generator of Triggers in the location.
    """
    list_req = self._messages.EventarcProjectsLocationsTriggersListRequest(
        parent=location_ref.RelativeName(), pageSize=page_size)
    return list_pager.YieldFromList(
        self._service,
        list_req,
        field='triggers',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize')

  def Patch(self, trigger_ref, trigger_message, update_mask):
    """Updates a Trigger.

    Args:
      trigger_ref: Resource, the Trigger to update.
      trigger_message: Trigger, the trigger message that holds trigger's
        event_filters, service account, destination, transport, etc.
      update_mask: str, a comma-separated list of Trigger fields to update.

    Returns:
      A long-running operation for update.
    """
    patch_req = self._messages.EventarcProjectsLocationsTriggersPatchRequest(
        name=trigger_ref.RelativeName(),
        trigger=trigger_message,
        updateMask=update_mask)
    return self._service.Patch(patch_req)


class _TriggersClient(_BaseTriggersClient):
  """Client for Triggers service in the Eventarc GA API."""

  def BuildTriggerMessage(
      self,
      trigger_ref,
      event_filters,
      event_filters_path_pattern,
      event_data_content_type,
      service_account,
      destination_message,
      transport_topic_ref,
      channel_ref,
  ):
    """Builds a Trigger message with the given data.

    Args:
      trigger_ref: Resource, the Trigger to create.
      event_filters: dict or None, the Trigger's event filters.
      event_filters_path_pattern: dict or None, the Trigger's event filters in
        path pattern format.
      event_data_content_type: str or None, the data content type of the
        Trigger's event.
      service_account: str or None, the Trigger's service account.
      destination_message: Destination message or None, the Trigger's
        destination.
      transport_topic_ref: Resource or None, the user-provided transport topic.
      channel_ref: Resource or None, the channel for 3p events

    Returns:
      A Trigger message with a destination service.
    """
    filter_messages = [] if event_filters is None else [
        self._messages.EventFilter(attribute=key, value=value)
        for key, value in event_filters.items()
    ]
    if event_filters_path_pattern is not None:
      for key, value in event_filters_path_pattern.items():
        filter_messages.append(
            self._messages.EventFilter(
                attribute=key, value=value, operator='match-path-pattern'))

    transport_topic_name = transport_topic_ref.RelativeName(
    ) if transport_topic_ref else None

    pubsub = self._messages.Pubsub(topic=transport_topic_name)
    transport = self._messages.Transport(pubsub=pubsub)
    channel = channel_ref.RelativeName() if channel_ref else None
    return self._messages.Trigger(
        name=trigger_ref.RelativeName(),
        eventFilters=filter_messages,
        eventDataContentType=event_data_content_type,
        serviceAccount=service_account,
        destination=destination_message,
        transport=transport,
        channel=channel,
    )

  def BuildCloudRunDestinationMessage(self, destination_run_service,
                                      destination_run_job, destination_run_path,
                                      destination_run_region):
    """Builds a Destination message for a destination Cloud Run service.

    Args:
      destination_run_service: str or None, the destination Cloud Run service.
      destination_run_job: str or None, the destination Cloud Run job.
      destination_run_path: str or None, the path on the destination Cloud Run
        service.
      destination_run_region: str or None, the destination Cloud Run service's
        region.

    Returns:
      A Destination message for a destination Cloud Run service.
    """
    # Because the flags for service and job are in a mutually exclusive group,
    # we can set both here under the assumption one of them will be None.
    run_message = self._messages.CloudRun(
        service=destination_run_service,
        job=destination_run_job,
        path=destination_run_path,
        region=destination_run_region)
    return self._messages.Destination(cloudRun=run_message)

  def BuildGKEDestinationMessage(self, destination_gke_cluster,
                                 destination_gke_location,
                                 destination_gke_namespace,
                                 destination_gke_service, destination_gke_path):
    """Builds a Destination message for a destination GKE service.

    Args:
      destination_gke_cluster: str or None, the destination GKE service's
        cluster.
      destination_gke_location: str or None, the location of the destination GKE
        service's cluster.
      destination_gke_namespace: str or None, the destination GKE service's
        namespace.
      destination_gke_service: str or None, the destination GKE service.
      destination_gke_path: str or None, the path on the destination GKE
        service.

    Returns:
      A Destination message for a destination GKE service.
    """
    gke_message = self._messages.GKE(
        cluster=destination_gke_cluster,
        location=destination_gke_location,
        namespace=destination_gke_namespace,
        service=destination_gke_service,
        path=destination_gke_path)
    return self._messages.Destination(gke=gke_message)

  def BuildWorkflowDestinationMessage(self, project_id, destination_workflow,
                                      destination_workflow_location):
    """Builds a Workflow Destination message with the given data.

    Args:
      project_id: the ID of the project.
      destination_workflow: str or None, the Trigger's destination Workflow ID.
      destination_workflow_location: str or None, the location of the Trigger's
        destination Workflow. It defaults to the Trigger's location.

    Returns:
      A Destination message with a Workflow destination.
    """

    workflow_message = 'projects/{}/locations/{}/workflows/{}'.format(
        project_id, destination_workflow_location, destination_workflow)
    return self._messages.Destination(workflow=workflow_message)

  def BuildFunctionDestinationMessage(self, project_id, destination_function,
                                      destination_function_location):
    """Builds a Function Destination message with the given data.

    Args:
      project_id: the ID of the project.
      destination_function: str or None, the Trigger's destination Function ID.
      destination_function_location: str or None, the location of the Trigger's
        destination Function. It defaults to the Trigger's location.

    Returns:
      A Destination message with a Function destination.
    """

    function_message = 'projects/{}/locations/{}/functions/{}'.format(
        project_id, destination_function_location, destination_function)
    return self._messages.Destination(cloudFunction=function_message)

  def BuildHTTPEndpointDestinationMessage(
      self,
      destination_http_endpoint_uri,
      network_attachment
  ):
    """Builds a HTTP Endpoint Destination message with the given data.

    Args:
      destination_http_endpoint_uri: str or None, the Trigger's destination uri.
      network_attachment: str or None, the Trigger's destination
        network attachment.

    Returns:
      A Destination message with a HTTP Endpoint destination.
    """
    http_endpoint_message = self._messages.HttpEndpoint(
        uri=destination_http_endpoint_uri,
    )
    network_config_message = self._messages.NetworkConfig(
        networkAttachment=network_attachment
    )
    return self._messages.Destination(
        httpEndpoint=http_endpoint_message,
        networkConfig=network_config_message
    )

  def BuildUpdateMask(
      self,
      event_filters,
      event_filters_path_pattern,
      event_data_content_type,
      service_account,
      destination_run_service,
      destination_run_job,
      destination_run_path,
      destination_run_region,
      destination_gke_namespace,
      destination_gke_service,
      destination_gke_path,
      destination_workflow,
      destination_workflow_location,
      destination_function,
      destination_function_location,
  ):
    """Builds an update mask for updating a Cloud Run trigger.

    Args:
      event_filters: bool, whether to update the event filters.
      event_filters_path_pattern: bool, whether to update the event filters with
        path pattern syntax.
      event_data_content_type: bool, whether to update the event data content
        type.
      service_account: bool, whether to update the service account.
      destination_run_service: bool, whether to update the destination Cloud Run
        service.
      destination_run_job: bool, whether to update the desintation Cloud Run
        job.
      destination_run_path: bool, whether to update the destination Cloud Run
        path.
      destination_run_region: bool, whether to update the destination Cloud Run
        region.
      destination_gke_namespace: bool, whether to update the destination GKE
        service namespace.
      destination_gke_service: bool, whether to update the destination GKE
        service name.
      destination_gke_path: bool, whether to update the destination GKE path.
      destination_workflow: bool, whether to update the destination workflow.
      destination_workflow_location: bool, whether to update the destination
        workflow location.
      destination_function: bool, whether to update the destination function.
      destination_function_location: bool, whether to update the destination
        function location.

    Returns:
      The update mask as a string.

    Raises:
      NoFieldsSpecifiedError: No fields are being updated.
    """
    update_mask = []
    if destination_run_path:
      update_mask.append('destination.cloudRun.path')
    if destination_run_region:
      update_mask.append('destination.cloudRun.region')
    if destination_run_service:
      update_mask.append('destination.cloudRun.service')
    if destination_run_job:
      update_mask.append('destination.cloudRun.job')
    if destination_gke_namespace:
      update_mask.append('destination.gke.namespace')
    if destination_gke_service:
      update_mask.append('destination.gke.service')
    if destination_gke_path:
      update_mask.append('destination.gke.path')
    if destination_workflow or destination_workflow_location:
      update_mask.append('destination.workflow')
    if destination_function or destination_function_location:
      update_mask.append('destination.cloudFunction')
    if event_filters or event_filters_path_pattern:
      update_mask.append('eventFilters')
    if service_account:
      update_mask.append('serviceAccount')
    if event_data_content_type:
      update_mask.append('eventDataContentType')
    if not update_mask:
      raise NoFieldsSpecifiedError('Must specify at least one field to update.')
    return ','.join(update_mask)

  def GetEventType(self, trigger_message):
    """Gets the Trigger's event type."""
    return types.EventFiltersMessageToType(trigger_message.eventFilters)


class _TriggersClientBeta(_BaseTriggersClient):
  """Client for Triggers service in the Eventarc beta API."""

  def BuildTriggerMessage(
      self,
      trigger_ref,
      event_filters,
      event_filters_path_pattern,
      event_data_content_type,
      service_account,
      destination_message,
      transport_topic_ref,
      channel_ref,
  ):
    """Builds a Trigger message with the given data.

    Args:
      trigger_ref: Resource, the Trigger to create.
      event_filters: dict or None, the Trigger's event filters.
      event_filters_path_pattern: dict or None, the Trigger's event filters in
        path pattern format. Ignored in Beta.
      event_data_content_type: str or None, the data content type of the
        Trigger's event. Ignored in Beta.
      service_account: str or None, the Trigger's service account.
      destination_message: Destination message or None, the Trigger's
        destination.
      transport_topic_ref: Resource or None, the user-provided transport topic.
      channel_ref: Resource or None, the channel for 3p events. Ignored in Beta.

    Returns:
      A Trigger message with a destination service.
    """
    criteria_messages = [] if event_filters is None else [
        self._messages.MatchingCriteria(attribute=key, value=value)
        for key, value in event_filters.items()
    ]
    transport = None
    if transport_topic_ref:
      transport_topic_name = transport_topic_ref.RelativeName()
      pubsub = self._messages.Pubsub(topic=transport_topic_name)
      transport = self._messages.Transport(pubsub=pubsub)
    return self._messages.Trigger(
        name=trigger_ref.RelativeName(),
        matchingCriteria=criteria_messages,
        serviceAccount=service_account,
        destination=destination_message,
        transport=transport)

  def BuildCloudRunDestinationMessage(self, destination_run_service,
                                      destination_run_job, destination_run_path,
                                      destination_run_region):
    """Builds a Destination message for a destination Cloud Run service.

    Args:
      destination_run_service: str or None, the destination Cloud Run service.
      destination_run_job: this destination is not supported in the beta API,
        but is included as an argument here for method consistency with v1.
      destination_run_path: str or None, the path on the destination Cloud Run
        service.
      destination_run_region: str or None, the destination Cloud Run service's
        region.

    Returns:
      A Destination message for a destination Cloud Run service.
    """
    del destination_run_job  # Not supported in beta API

    run_message = self._messages.CloudRunService(
        service=destination_run_service,
        path=destination_run_path,
        region=destination_run_region)
    return self._messages.Destination(cloudRunService=run_message)

  def BuildUpdateMask(
      self,
      event_filters,
      event_data_content_type,
      service_account,
      destination_run_service,
      destination_run_job,
      destination_run_path,
      destination_run_region,
  ):
    """Builds an update mask for updating a trigger.

    Args:
      event_filters: bool, whether to update the event filters.
      event_data_content_type: bool, whether to update the event data content
        type.
      service_account: bool, whether to update the service account.
      destination_run_service: bool, whether to update the destination service.
      destination_run_job: this destination is not supported in the beta API,
        but is included as an argument here for method consistency with v1.
      destination_run_path: bool, whether to update the destination path.
      destination_run_region: bool, whether to update the destination region.

    Returns:
      The update mask as a string.

    Raises:
      NoFieldsSpecifiedError: No fields are being updated.
    """
    del destination_run_job  # Not supported in beta API

    update_mask = []
    if destination_run_path:
      update_mask.append('destination.cloudRunService.path')
    if destination_run_region:
      update_mask.append('destination.cloudRunService.region')
    if destination_run_service:
      update_mask.append('destination.cloudRunService.service')
    if event_filters:
      update_mask.append('matchingCriteria')
    if service_account:
      update_mask.append('serviceAccount')
    if event_data_content_type:
      update_mask.append('eventDataContentType')
    if not update_mask:
      raise NoFieldsSpecifiedError('Must specify at least one field to update.')
    return ','.join(update_mask)

  def GetEventType(self, trigger_message):
    """Gets the Trigger's event type."""
    return types.EventFiltersMessageToType(trigger_message.matchingCriteria)
