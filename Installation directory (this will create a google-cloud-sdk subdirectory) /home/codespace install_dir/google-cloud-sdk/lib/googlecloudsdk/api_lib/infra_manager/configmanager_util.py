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
"""Utilities for the Config API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import progress_tracker

_API_NAME = 'config'

# The maximum amount of time to wait in between polling long-running operations.
_WAIT_CEILING_MS = 10 * 1000

# The maximum amount of time to wait for the long-running operation.
_MAX_WAIT_TIME_MS = 3 * 60 * 60 * 1000

RELEASE_TRACK_TO_API_VERSION = {
    base.ReleaseTrack.ALPHA: 'v1alpha2',
    base.ReleaseTrack.GA: 'v1',
}


def GetMessagesModule(release_track=base.ReleaseTrack.GA):
  """Returns the messages module for Config API.

  Args:
    release_track: The desired value of the enum
      googlecloudsdk.calliope.base.ReleaseTrack.

  Returns:
    Module containing the definitions of messages for Config API.
  """
  return apis.GetMessagesModule(
      _API_NAME, RELEASE_TRACK_TO_API_VERSION[release_track]
  )


def GetClientInstance(release_track=base.ReleaseTrack.GA, use_http=True):
  """Returns an instance of the Config client.

  Args:
    release_track: The desired value of the enum
      googlecloudsdk.calliope.base.ReleaseTrack.
    use_http: bool, True to create an http object for this client.

  Returns:
    base_api.BaseApiClient, An instance of the Config client.
  """
  return apis.GetClientInstance(
      _API_NAME,
      RELEASE_TRACK_TO_API_VERSION[release_track],
      no_http=(not use_http),
  )


def GetDeployment(name):
  """Calls into the GetDeployment API.

  Args:
    name: the fully qualified name of the deployment, e.g.
      "projects/p/locations/l/deployments/d".

  Returns:
    A messages.Deployment.

  Raises:
    HttpNotFoundError: if the deployment doesn't exist.
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE
  return client.projects_locations_deployments.Get(
      messages.ConfigProjectsLocationsDeploymentsGetRequest(name=name)
  )


def CreateDeployment(deployment, deployment_id, location):
  """Calls into the CreateDeployment API.

  Args:
    deployment: a messages.Deployment resource (containing properties like the
      blueprint).
    deployment_id: the ID of the deployment, e.g. "my-deployment" in
      "projects/p/locations/l/deployments/my-deployment".
    location: the location in which to create the deployment.

  Returns:
    A messages.OperationMetadata representing a long-running operation.
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE
  return client.projects_locations_deployments.Create(
      messages.ConfigProjectsLocationsDeploymentsCreateRequest(
          parent=location, deployment=deployment, deploymentId=deployment_id
      )
  )


def UpdateDeployment(deployment, deployment_full_name):
  """Calls into the UpdateDeployment API.

  Args:
    deployment: a messages.Deployment resource (containing properties like the
      blueprint).
    deployment_full_name: the fully qualified name of the deployment.

  Returns:
    A messages.OperationMetadata representing a long-running operation.
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE
  return client.projects_locations_deployments.Patch(
      messages.ConfigProjectsLocationsDeploymentsPatchRequest(
          deployment=deployment, name=deployment_full_name, updateMask=None
      )
  )


def WaitForApplyDeploymentOperation(
    operation, progress_message='Applying the deployment'
):
  """Waits for the given "apply deployment" LRO to complete.

  Args:
    operation: the operation to poll.
    progress_message: string to display for default progress_tracker.

  Raises:
    apitools.base.py.HttpError: if the request returns an HTTP error.

  Returns:
    A messages.Deployment resource.
  """
  client = GetClientInstance()
  operation_ref = resources.REGISTRY.ParseRelativeName(
      operation.name, collection='config.projects.locations.operations'
  )
  poller = waiter.CloudOperationPoller(
      client.projects_locations_deployments,
      client.projects_locations_operations,
  )

  poller.detailed_message = ''

  def TrackerUpdateFunc(tracker, result, unused_status):
    """Updates the progress tracker with the result of the operation.

    Args:
      tracker: The ProgressTracker for the operation.
      result: the operation poll result.
      unused_status: map of stages with key as stage key (string) and value is
        the progress_tracker.Stage.
    """
    messages = GetMessagesModule()

    # Need to encode to JSON and then decode to Message to be able to reasonably
    # access attributes.
    json_val = encoding.MessageToJson(result.metadata)
    deployment_metadata = encoding.JsonToMessage(
        messages.OperationMetadata, json_val
    ).deploymentMetadata

    logs = ''
    step = ''
    if deployment_metadata is not None:
      logs = deployment_metadata.logs
      step = deployment_metadata.step

    if logs is not None and step is None:
      poller.detailed_message = 'logs={0} '.format(logs)
    elif logs is not None and step is not None:
      poller.detailed_message = 'logs={0}, step={1} '.format(logs, step)

    tracker.Tick()

  def DetailMessageCallback():
    """Returns the detailed progress message to be updated on the progress tracker."""

    return poller.detailed_message

  aborted_message = 'Aborting wait for operation {0}.\n'.format(operation_ref)
  custom_tracker = progress_tracker.ProgressTracker(
      message=progress_message,
      detail_message_callback=DetailMessageCallback,
      aborted_message=aborted_message,
  )

  result = waiter.WaitFor(
      poller,
      operation_ref,
      progress_message,
      custom_tracker=custom_tracker,
      tracker_update_func=TrackerUpdateFunc,
      max_wait_ms=_MAX_WAIT_TIME_MS,
      wait_ceiling_ms=_WAIT_CEILING_MS,
  )
  return result


def ImportStateFile(import_state_file_request, deployment_id):
  """Calls ImportStateFile API.

  Args:
    import_state_file_request: a messages.ImportStateFileRequest.
    deployment_id: the ID of the deployment, e.g. "my-deployment" in
      "projects/p/locations/l/deployments/my-deployment".

  Returns:
    (Statefile) The response message.
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE

  return client.projects_locations_deployments.ImportState(
      messages.ConfigProjectsLocationsDeploymentsImportStateRequest(
          importStatefileRequest=import_state_file_request, parent=deployment_id
      )
  )


def ExportDeploymentStateFile(
    export_deployment_state_file_request,
    deployment_id,
):
  """Calls ExportDeploymentStateFile API.

  Args:
    export_deployment_state_file_request: A ExportDeploymentStatefileRequest
      resource to be passed as the request body.
    deployment_id: the ID of the deployment, e.g. "my-deployment" in
      "projects/p/locations/l/deployments/my-deployment".

  Returns:
    (Statefile) The response message.
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE

  return client.projects_locations_deployments.ExportState(
      messages.ConfigProjectsLocationsDeploymentsExportStateRequest(
          exportDeploymentStatefileRequest=export_deployment_state_file_request,
          parent=deployment_id,
      )
  )


def ExportRevisionStateFile(
    export_revision_state_file_request,
    deployment_id,
):
  """Calls ExportDeploymentRevisionsStateFile API.

  Args:
    export_revision_state_file_request: A ExportRevisionStatefileRequest
      resource to be passed as the request body.
    deployment_id: the ID of the deployment, e.g. "my-deployment" in
      "projects/p/locations/l/deployments/my-deployment".

  Returns:
    (Statefile) The response message.
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE

  return client.projects_locations_deployments_revisions.ExportState(
      messages.ConfigProjectsLocationsDeploymentsRevisionsExportStateRequest(
          exportRevisionStatefileRequest=export_revision_state_file_request,
          parent=deployment_id,
      )
  )


def ExportLock(deployment_full_name):
  """Calls ExportLock API.

  Args:
    deployment_full_name: string, the fully qualified name of the deployment,
      e.g. "projects/p/locations/l/deployments/d".

  Returns:
    A lock info response.
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE

  return client.projects_locations_deployments.ExportLock(
      messages.ConfigProjectsLocationsDeploymentsExportLockRequest(
          name=deployment_full_name,
      )
  )


def LockDeployment(
    lock_deployment_request,
    deployment_full_name,
):
  """Calls deployment Lock API.

  Args:
    lock_deployment_request: A LockDeploymentRequest resource to be passed as
      the request body
    deployment_full_name: the ID of the deployment, e.g. "my-deployment" in
      "projects/p/locations/l/deployments/my-deployment".

  Returns:
    A long running operation.
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE

  return client.projects_locations_deployments.Lock(
      messages.ConfigProjectsLocationsDeploymentsLockRequest(
          lockDeploymentRequest=lock_deployment_request,
          name=deployment_full_name,
      )
  )


def UnlockDeployment(
    unlock_deployment_request,
    deployment_full_name,
):
  """Calls deployment Unlock API.

  Args:
    unlock_deployment_request: A UnlockDeploymentRequest resource to be passed
      as the request body
    deployment_full_name: the ID of the deployment, e.g. "my-deployment" in
      format "projects/p/locations/l/deployments/my-deployment".

  Returns:
    A long running operation.
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE

  return client.projects_locations_deployments.Unlock(
      messages.ConfigProjectsLocationsDeploymentsUnlockRequest(
          unlockDeploymentRequest=unlock_deployment_request,
          name=deployment_full_name,
      )
  )


def ListRevisions(deployment_full_name):
  """Lists all revisions for a deployment.

  Args:
    deployment_full_name: the fully qualified name of the deployment, e.g.
      "projects/p/locations/l/deployments/d".

  Returns:
    (ListRevisionsResponse) The response message.

  Raises:
    HttpNotFoundError: if the deployment doesn't exist.
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE
  return client.projects_locations_deployments_revisions.List(
      messages.ConfigProjectsLocationsDeploymentsRevisionsListRequest(
          parent=deployment_full_name
      )
  )


def ExportPreviewResult(
    export_preview_result_request,
    preview_id,
):
  """Calls ExportPreviewResult API.

  Args:
    export_preview_result_request: A ExportPreviewResultRequest
      resource to be passed as the request body.
    preview_id: the ID of the preview, e.g. "my-preview" in
      "projects/p/locations/l/previews/my-preview".

  Returns:
    (Statefile) The response message.
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE

  return client.projects_locations_previews.Export(
      messages.ConfigProjectsLocationsPreviewsExportRequest(
          exportPreviewResultRequest=export_preview_result_request,
          parent=preview_id,
      )
  )


def CreatePreview(preview, preview_id, location):
  """Calls into the CreatePreview API.

  Args:
    preview: a messages.Preview resource (containing properties like the
      blueprint).
    preview_id: the ID of the preview, e.g. "my-preview" in
      "projects/p/locations/l/previews/my-preview".
    location: the location in which to create the preview.

  Returns:
    A messages.OperationMetadata representing a long-running operation.
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE
  return client.projects_locations_previews.Create(
      messages.ConfigProjectsLocationsPreviewsCreateRequest(
          parent=location, preview=preview, previewId=preview_id
      )
  )


def WaitForCreatePreviewOperation(
    operation, progress_message='Creating the preview'
):
  """Waits for the given "create preview" LRO to complete.

  Args:
    operation: the operation to poll.
    progress_message: string to display for default progress_tracker.

  Raises:
    apitools.base.py.HttpError: if the request returns an HTTP error.

  Returns:
    A messages.Preview resource.
  """
  client = GetClientInstance()
  operation_ref = resources.REGISTRY.ParseRelativeName(
      operation.name, collection='config.projects.locations.operations'
  )
  poller = waiter.CloudOperationPoller(
      client.projects_locations_previews,
      client.projects_locations_operations,
  )

  poller.detailed_message = ''

  def TrackerUpdateFunc(tracker, result, unused_status):
    """Updates the progress tracker with the result of the operation.

    Args:
      tracker: The ProgressTracker for the operation.
      result: the operation poll result.
      unused_status: map of stages with key as stage key (string) and value is
        the progress_tracker.Stage.
    """
    messages = GetMessagesModule()

    # Need to encode to JSON and then decode to Message to be able to reasonably
    # access attributes.
    json_val = encoding.MessageToJson(result.metadata)
    preview_metadata = encoding.JsonToMessage(
        messages.OperationMetadata, json_val
    ).previewMetadata

    logs = ''
    step = ''
    if preview_metadata is not None:
      logs = preview_metadata.logs
      step = preview_metadata.step

    if logs is not None and step is None:
      poller.detailed_message = 'logs={0} '.format(logs)
    elif logs is not None and step is not None:
      poller.detailed_message = 'logs={0}, step={1} '.format(logs, step)

    tracker.Tick()

  def DetailMessageCallback():
    """Returns the detailed progress message to be updated on the progress tracker."""

    return poller.detailed_message

  aborted_message = 'Aborting wait for operation {0}.\n'.format(operation_ref)
  custom_tracker = progress_tracker.ProgressTracker(
      message=progress_message,
      detail_message_callback=DetailMessageCallback,
      aborted_message=aborted_message,
  )

  result = waiter.WaitFor(
      poller,
      operation_ref,
      progress_message,
      custom_tracker=custom_tracker,
      tracker_update_func=TrackerUpdateFunc,
      max_wait_ms=_MAX_WAIT_TIME_MS,
      wait_ceiling_ms=_WAIT_CEILING_MS,
  )
  return result
