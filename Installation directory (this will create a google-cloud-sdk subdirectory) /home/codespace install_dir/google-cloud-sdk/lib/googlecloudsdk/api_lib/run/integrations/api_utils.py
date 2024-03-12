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
"""Functionality related to Cloud Run Integration API clients."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
from typing import List, Optional

from apitools.base.py import encoding as apitools_encoding
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import exceptions as api_lib_exceptions
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.runapps import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import retry
from googlecloudsdk.generated_clients.apis.runapps.v1alpha1 import runapps_v1alpha1_client
from googlecloudsdk.generated_clients.apis.runapps.v1alpha1 import runapps_v1alpha1_messages


API_NAME = 'runapps'
API_VERSION = 'v1alpha1'

# Key for the config field of application dictionary.
APP_DICT_CONFIG_KEY = 'config'
# Key for the resource field within config field of application dictionary.
APP_CONFIG_DICT_RESOURCES_KEY = 'resources'

# Max wait time before timing out, match timeout of CP
_POLLING_TIMEOUT_MS = 30 * 60 * 1000
# Max wait time between poll retries before timing out
_RETRY_TIMEOUT_MS = 1000

_LOCATION_ERROR_REGEX = re.compile(r'Location [\w-]+ is not found')


def GetMessages():
  """Returns the messages module for the Runapps API.

  Returns:
    Module containing the definitions of messages for the Runapps API.
  """
  return apis.GetMessagesModule(API_NAME, API_VERSION)


def GetApplication(
    client: runapps_v1alpha1_client.RunappsV1alpha1,
    app_ref: resources) -> Optional[runapps_v1alpha1_messages.Application]:
  """Calls GetApplication API of Runapps for the specified reference.

  Args:
    client: The api client to use.
    app_ref: The resource reference of the application.

  Raises:
    exceptions.UnsupportedIntegrationsLocationError: if the region does not
      exist for the user.

  Returns:
    The application.  If the application does not exist, then
    None is returned.
  """
  request = (
      client.MESSAGES_MODULE.RunappsProjectsLocationsApplicationsGetRequest(
          name=app_ref.RelativeName())
  )
  try:
    return client.projects_locations_applications.Get(request)
  except apitools_exceptions.HttpNotFoundError:
    return None
  except apitools_exceptions.HttpForbiddenError as e:
    _HandleLocationError(app_ref.locationsId, e)


def ListApplications(
    client: runapps_v1alpha1_client.RunappsV1alpha1, app_ref: resources
) -> runapps_v1alpha1_messages.ListApplicationsResponse:
  """Calls ListApplications API of Runapps for the specified reference."""
  request = (
      client.MESSAGES_MODULE.RunappsProjectsLocationsApplicationsListRequest(
          parent=app_ref.RelativeName()
      )
  )

  response = client.projects_locations_applications.List(request)
  if response.unreachable:
    log.warning(
        'The following regions did not respond: {}. '
        'List results may be incomplete'.format(
            ', '.join(sorted(response.unreachable))
        )
    )

  return response


def GetApplicationStatus(
    client: runapps_v1alpha1_client.RunappsV1alpha1,
    app_ref: resources,
    resource_ids: Optional[List[runapps_v1alpha1_messages.ResourceID]] = None,
) -> Optional[runapps_v1alpha1_messages.ApplicationStatus]:
  """Calls GetApplicationStatus API of Runapps for the specified reference.

  Args:
    client: the api client to use.
    app_ref: the resource reference of the application.
    resource_ids: ResourceID of the resource to get status for. If not given,
      all resources in the application will be queried.

  Returns:
    The ApplicationStatus object. Or None if not found.
  """

  if resource_ids:
    res_filters = [
        res_id.type + '/' + res_id.name for res_id in resource_ids
    ]
  else:
    res_filters = []
  module = client.MESSAGES_MODULE
  request = module.RunappsProjectsLocationsApplicationsGetStatusRequest(
      name=app_ref.RelativeName(), resources=res_filters
  )
  try:
    return client.projects_locations_applications.GetStatus(request)
  except apitools_exceptions.HttpNotFoundError:
    return None


def CreateApplication(
    client: runapps_v1alpha1_client.RunappsV1alpha1,
    app_ref: resources,
    application: runapps_v1alpha1_messages.Application
    ) -> runapps_v1alpha1_messages.Operation:
  """Calls CreateApplicaton API of Runapps for the specified reference.

  Args:
    client: the api client to use.
    app_ref: the resource reference of
      the application.
    application: the application to create

  Returns:
    the LRO of this request.
  """
  return client.projects_locations_applications.Create(
      client.MESSAGES_MODULE.RunappsProjectsLocationsApplicationsCreateRequest(
          application=application,
          applicationId=application.name,
          parent=app_ref.Parent().RelativeName()))


def PatchApplication(
    client: runapps_v1alpha1_client.RunappsV1alpha1,
    app_ref: resources,
    application: runapps_v1alpha1_messages.Application,
    update_mask: Optional[str] = None) -> runapps_v1alpha1_messages.Operation:
  """Calls ApplicationPatch API of Runapps for the specified reference.

  Args:
    client: the api client to use.
    app_ref: the resource reference of
      the application.
    application: the application to patch
    update_mask: comma separated string listing the fields to be updated.

  Returns:
    the LRO of this request.
  """
  # API requires that only one of the resources or resourceList to be used
  # in order to determine which shape the client is using.
  # Thus unsetting the resources.
  application.config.resources = None
  return client.projects_locations_applications.Patch(
      client.MESSAGES_MODULE.RunappsProjectsLocationsApplicationsPatchRequest(
          application=application,
          updateMask=update_mask,
          name=app_ref.RelativeName()))


def CreateDeployment(
    client: runapps_v1alpha1_client.RunappsV1alpha1,
    app_ref: resources,
    deployment: runapps_v1alpha1_messages.Deployment,
    validate_only: Optional[bool] = False
    ) -> runapps_v1alpha1_messages.Operation:
  """Calls CreateDeployment API of Runapps.

  Args:
    client: the api client to use.
    app_ref: the resource reference of the application the deployment belongs to
    deployment: the deployment object
    validate_only: whether to only validate the deployment

  Returns:
    the LRO of this request.
  """
  return client.projects_locations_applications_deployments.Create(
      client.MESSAGES_MODULE
      .RunappsProjectsLocationsApplicationsDeploymentsCreateRequest(
          parent=app_ref.RelativeName(),
          deployment=deployment,
          deploymentId=deployment.name,
          validateOnly=validate_only)
      )


def GetDeployment(
    client: runapps_v1alpha1_client.RunappsV1alpha1,
    deployment_name: str) -> Optional[runapps_v1alpha1_messages.Deployment]:
  """Calls GetDeployment API of Runapps.

  Args:
    client: the api client to use.
    deployment_name: the canonical name of the deployment.  For example:
      projects/<project>/locations/<location>/applications/<app>/deployment/<id>

  Returns:
    the Deployment object.  None is returned if the deployment cannot be found.
  """
  try:
    return client.projects_locations_applications_deployments.Get(
        client.MESSAGES_MODULE
        .RunappsProjectsLocationsApplicationsDeploymentsGetRequest(
            name=deployment_name)
        )
  except apitools_exceptions.HttpNotFoundError:
    return None


def WaitForApplicationOperation(
    client: runapps_v1alpha1_client.RunappsV1alpha1,
    operation: runapps_v1alpha1_messages.Operation
    ) -> runapps_v1alpha1_messages.Application:
  """Waits for an operation to complete.

  Args:
    client:  client used to make requests.
    operation: object to wait for.

  Returns:
    the application from the operation.
  """

  return _WaitForOperation(client, operation,
                           client.projects_locations_applications)


def WaitForDeploymentOperation(
    client: runapps_v1alpha1_client.RunappsV1alpha1,
    operation: runapps_v1alpha1_messages.Operation,
    tracker, tracker_update_func) -> runapps_v1alpha1_messages.Deployment:
  """Waits for an operation to complete.

  Args:
    client: client used to make requests.
    operation: object to wait for.
    tracker: The ProgressTracker that tracks the operation progress.
    tracker_update_func: function to update the tracker on polling.

  Returns:
    the deployment from thex operation.
  """

  return _WaitForOperation(client, operation,
                           client.projects_locations_applications_deployments,
                           tracker, tracker_update_func)


def _WaitForOperation(client: runapps_v1alpha1_client.RunappsV1alpha1,
                      operation: runapps_v1alpha1_messages.Operation,
                      resource_type,
                      tracker=None,
                      tracker_update_func=None):
  """Waits for an operation to complete.

  Args:
    client:  client used to make requests.
    operation: object to wait for.
    resource_type: type, the expected type of resource response
    tracker: The ProgressTracker that tracks the operation progress.
    tracker_update_func: function to update the tracker on polling.

  Returns:
    The resulting resource of input paramater resource_type.
  """
  poller = waiter.CloudOperationPoller(resource_type,
                                       client.projects_locations_operations)
  operation_ref = resources.REGISTRY.ParseRelativeName(
      operation.name,
      collection='{}.projects.locations.operations'.format(API_NAME))

  def _StatusUpdate(result, status):
    if tracker is None:
      return
    if tracker_update_func:
      tracker_update_func(tracker, result, status)
    else:
      tracker.Tick()

  try:
    return poller.GetResult(
        waiter.PollUntilDone(
            poller,
            operation_ref,
            max_wait_ms=_POLLING_TIMEOUT_MS,
            wait_ceiling_ms=_RETRY_TIMEOUT_MS,
            status_update=_StatusUpdate))
  except waiter.OperationError:
    operation = poller.Poll(operation_ref)
    raise exceptions.IntegrationsOperationError(
        'OperationError: code={0}, message={1}'.format(
            operation.error.code, encoding.Decode(operation.error.message)))
  except retry.WaitException:
    # Operation timed out.
    raise waiter.TimeoutError(
        'Operation timed out after {0} seconds. The operations may still '
        'be underway remotely and may still succeed.'
        .format(_POLLING_TIMEOUT_MS / 1000))


def GetDeploymentOperationMetadata(
    messages,
    operation: runapps_v1alpha1_messages.Operation
    ) -> runapps_v1alpha1_messages.DeploymentOperationMetadata:
  """Get the metadata message for the deployment operation.

  Args:
    messages: Module containing the definitions of messages for the Runapps
      API.
    operation: The LRO

  Returns:
    The DeploymentOperationMetadata object.
  """

  return apitools_encoding.PyValueToMessage(
      messages.DeploymentOperationMetadata,
      apitools_encoding.MessageToPyValue(operation.metadata))


def ListLocations(
    client: runapps_v1alpha1_client.RunappsV1alpha1,
    proj_id: str) -> runapps_v1alpha1_messages.ListLocationsResponse:
  """Get the list of all available regions from control plane.

  Args:
    client: instance of a client to use for the list request.
    proj_id: project id of the project to query.

  Returns:
    A list of location resources.
  """
  request = client.MESSAGES_MODULE.RunappsProjectsLocationsListRequest(
      name='projects/{0}'.format(proj_id)
  )
  return client.projects_locations.List(request)


def _HandleLocationError(region: str, error: Exception) -> Exception:
  """Get the metadata message for the deployment operation.

  Args:
    region: target region of the request.
    error: original HttpError.

  Raises:
    UnsupportedIntegrationsLocationError if it's location error. Otherwise
    raise the original error.
  """
  parsed_err = api_lib_exceptions.HttpException(error)
  if _LOCATION_ERROR_REGEX.match(parsed_err.payload.status_message):
    raise exceptions.UnsupportedIntegrationsLocationError(
        'Location {} is not found or access is unauthorized.'.format(region)
    )
  raise error
