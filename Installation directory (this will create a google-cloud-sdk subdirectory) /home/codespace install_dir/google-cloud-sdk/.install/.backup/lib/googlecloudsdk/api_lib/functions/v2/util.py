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
"""Functionality related to Cloud Functions v2 API clients."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import enum

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
import frozendict
from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.cloudresourcemanager import projects_util as projects_api_util
from googlecloudsdk.api_lib.functions.v2 import exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import encoding as encoder
from googlecloudsdk.core.util import retry
import six

_API_NAME = 'cloudfunctions'

_V2_ALPHA = 'v2alpha'
_V2_BETA = 'v2beta'
_V2_GA = 'v2'

_DEFAULT_ABORTED_MESSAGE = (
    'Aborted by user (background API operations may still be in progress).'
)

RELEASE_TRACK_TO_API_VERSION = {
    calliope_base.ReleaseTrack.ALPHA: 'v2alpha',
    calliope_base.ReleaseTrack.BETA: 'v2beta',
    calliope_base.ReleaseTrack.GA: 'v2',
}

MAX_WAIT_MS = 1820000
SLEEP_MS = 1000

# EventArc types
EA_PUBSUB_MESSAGE_PUBLISHED = 'google.cloud.pubsub.topic.v1.messagePublished'
EA_STORAGE_ARCHIVE = 'google.cloud.storage.object.v1.archived'
EA_STORAGE_DELETE = 'google.cloud.storage.object.v1.deleted'
EA_STORAGE_FINALIZE = 'google.cloud.storage.object.v1.finalized'
EA_STORAGE_UPDATE = 'google.cloud.storage.object.v1.metadataUpdated'

EVENTARC_STORAGE_TYPES = (
    EA_STORAGE_ARCHIVE,
    EA_STORAGE_DELETE,
    EA_STORAGE_FINALIZE,
    EA_STORAGE_UPDATE,
)

# EventFlow types
EF_PUBSUB_MESSAGE_PUBLISH = 'google.pubsub.topic.publish'
EF_STORAGE_ARCHIVE = 'google.storage.object.archive'
EF_STORAGE_DELETE = 'google.storage.object.delete'
EF_STORAGE_FINALIZE = 'google.storage.object.finalize'
EF_STORAGE_METADATA_UPDATE = 'google.storage.object.metadataUpdate'

EVENTFLOW_TO_EVENTARC_STORAGE_MAP = frozendict.frozendict({
    EF_STORAGE_ARCHIVE: EA_STORAGE_ARCHIVE,
    EF_STORAGE_DELETE: EA_STORAGE_DELETE,
    EF_STORAGE_FINALIZE: EA_STORAGE_FINALIZE,
    EF_STORAGE_METADATA_UPDATE: EA_STORAGE_UPDATE,
})

# Legacy types
LEGACY_PUBSUB_MESSAGE_PUBLISH = (
    'providers/cloud.pubsub/eventTypes/topic.publish'
)

PUBSUB_MESSAGE_PUBLISH_TYPES = (
    EA_PUBSUB_MESSAGE_PUBLISHED,
    EF_PUBSUB_MESSAGE_PUBLISH,
    LEGACY_PUBSUB_MESSAGE_PUBLISH,
)


class ApiEnv(enum.Enum):
  TEST = 1
  AUTOPUSH = 2
  STAGING = 3
  PROD = 4


def GetProject():
  # type: () -> str
  """Returns the value of the core/project config prooerty.

  Config properties can be overridden with command line flags. If the --project
  flag was provided, this will return the value provided with the flag.
  """
  return properties.VALUES.core.project.Get(required=True)


def GetMessagesModule(release_track):
  """Returns the API messages module for GCFv2."""
  api_version = RELEASE_TRACK_TO_API_VERSION.get(release_track)
  return apis.GetMessagesModule(_API_NAME, api_version)


def GetStage(messages):
  """Returns corresponding GoogleCloudFunctionsV2(alpha|beta|ga)Stage."""
  if messages is apis.GetMessagesModule(_API_NAME, _V2_ALPHA):
    return messages.GoogleCloudFunctionsV2alphaStage
  elif messages is apis.GetMessagesModule(_API_NAME, _V2_BETA):
    return messages.GoogleCloudFunctionsV2betaStage
  else:
    return messages.GoogleCloudFunctionsV2Stage


def GetStateMessage(messages):
  """Returns corresponding GoogleCloudFunctionsV2(alpha|beta|ga)stateMessage."""
  if messages is apis.GetMessagesModule(_API_NAME, _V2_ALPHA):
    return messages.GoogleCloudFunctionsV2alphaStateMessage
  elif messages is apis.GetMessagesModule(_API_NAME, _V2_BETA):
    return messages.GoogleCloudFunctionsV2betaStateMessage
  else:
    return messages.GoogleCloudFunctionsV2StateMessage


def GetApiEndpointOverride():
  # type: () -> str | None
  """Returns the API endpoint override property value for GCF."""
  try:
    return properties.VALUES.api_endpoint_overrides.Property(
        'cloudfunctions'
    ).Get()
  except properties.NoSuchPropertyError:
    return None


def GetClientInstance(release_track):
  """Returns an API client for GCFv2."""
  api_version = RELEASE_TRACK_TO_API_VERSION.get(release_track)
  return apis.GetClientInstance(_API_NAME, api_version)


def GetStateMessagesStrings(state_messages):
  """Returns the list of string representations of the state messages."""
  return map(
      lambda st: '[{}] {}'.format(str(st.severity), st.message), state_messages
  )


def GetOperationMetadata(messages):
  """Returns corresponding GoogleCloudFunctionsV2(alpha|beta|ga)OperationMetadata."""
  if messages is apis.GetMessagesModule(_API_NAME, _V2_ALPHA):
    return messages.GoogleCloudFunctionsV2alphaOperationMetadata
  elif messages is apis.GetMessagesModule(_API_NAME, _V2_BETA):
    return messages.GoogleCloudFunctionsV2betaOperationMetadata
  elif messages is apis.GetMessagesModule(_API_NAME, _V2_GA):
    return messages.GoogleCloudFunctionsV2OperationMetadata
  else:
    raise NotImplementedError('Invalid messages module.')


def _GetOperationMetadata(messages, operation):
  return encoding.PyValueToMessage(
      GetOperationMetadata(messages),
      encoding.MessageToPyValue(operation.metadata),
  )


def _GetStageHeader(name_enum):
  """Converts NameValueValuesEnum into the header to use in progress stages."""
  return '[{}]'.format(six.text_type(name_enum).replace('_', ' ').title())


def _GetOperation(client, request):
  """Get operation and return None if doesn't exist."""
  try:
    # We got response for a GET request, so an operation exists.
    return client.projects_locations_operations.Get(request)
  except apitools_exceptions.HttpError as error:
    if error.status_code == six.moves.http_client.NOT_FOUND:
      return None
    raise


def _GetOperationAndStages(client, request, messages):
  """Returns the stages in the operation."""
  operation = _GetOperation(client, request)
  if operation.error:
    raise exceptions.StatusToFunctionsError(operation.error)

  stages = []
  if operation.metadata:
    operation_metadata = _GetOperationMetadata(messages, operation)

    for stage in operation_metadata.stages:
      stages.append(
          progress_tracker.Stage(
              _GetStageHeader(stage.name), key=six.text_type(stage.name)
          )
      )

  return operation, stages


def _GetOperationAndLogProgress(client, request, tracker, messages):
  """Returns a Boolean indicating whether the request has completed."""
  operation = client.projects_locations_operations.Get(request)
  if operation.error:
    raise exceptions.StatusToFunctionsError(
        operation.error, error_message=OperationErrorToString(operation.error)
    )

  operation_metadata = _GetOperationMetadata(messages, operation)
  # cs/symbol:google.cloud.functions.v2main.OperationMetadata.Stage
  for stage in operation_metadata.stages:
    stage_in_progress = (
        stage.state is GetStage(messages).StateValueValuesEnum.IN_PROGRESS
    )
    stage_complete = (
        stage.state is GetStage(messages).StateValueValuesEnum.COMPLETE
    )

    if not stage_in_progress and not stage_complete:
      continue

    stage_key = str(stage.name)
    if tracker.IsComplete(stage_key):
      # Cannot update a completed stage in the tracker
      continue

    # Start running a stage
    if tracker.IsWaiting(stage_key):
      tracker.StartStage(stage_key)

    # Update stage message, including Build logs URL if applicable
    stage_message = stage.message or ''
    if stage_in_progress:
      stage_message = (stage_message or 'In progress') + '... '
    else:
      stage_message = ''

    if stage.resourceUri and stage_key == 'BUILD':
      stage_message += 'Logs are available at [{}]'.format(stage.resourceUri)

    tracker.UpdateStage(stage_key, stage_message)

    # Complete a finished stage
    if stage_complete:
      if stage.stateMessages:
        tracker.CompleteStageWithWarnings(
            stage_key, GetStateMessagesStrings(stage.stateMessages)
        )
      else:
        tracker.CompleteStage(stage_key)

  return operation


def WaitForOperation(
    client, messages, operation, description, extra_stages=None
):
  """Wait for a long-running operation (LRO) to complete.

  Args:
    client: The GCFv2 API client.
    messages: The GCFv2 message stubs.
    operation: The operation message response.
    description: str, the description of the waited operation.
    extra_stages: List[progress_tracker.Stage]|None, list of optional stages for
      the progress tracker to watch. The GCF 2nd api returns unexpected stages
      in the case of rollbacks.

  Returns:
    cloudfunctions_v2_messages.Operation, the finished operation.
  """

  def IsNotDoneAndIsMissingStages(res, _):
    op, stages = res
    return not stages and not op.done

  request = messages.CloudfunctionsProjectsLocationsOperationsGetRequest(
      name=operation.name
  )
  # Wait for stages to be loaded.
  with progress_tracker.ProgressTracker(
      'Preparing function', aborted_message=_DEFAULT_ABORTED_MESSAGE
  ) as tracker:
    retryer = retry.Retryer(max_wait_ms=MAX_WAIT_MS)
    try:
      # List[progress_tracker.Stage]
      operation, stages = retryer.RetryOnResult(
          _GetOperationAndStages,
          args=[client, request, messages],
          should_retry_if=IsNotDoneAndIsMissingStages,
          sleep_ms=SLEEP_MS,
      )
    except retry.WaitException:
      raise exceptions.FunctionsError(
          'Operation {0} is taking too long'.format(operation.name)
      )

  if extra_stages is not None:
    stages += extra_stages

  # Wait for LRO to complete.
  description += '...'

  with progress_tracker.StagedProgressTracker(
      description, stages, aborted_message=_DEFAULT_ABORTED_MESSAGE
  ) as tracker:
    if operation.done and not stages:
      # No stages to show in the progress tracker so just return the operation.
      return operation

    retryer = retry.Retryer(max_wait_ms=MAX_WAIT_MS)
    try:
      operation = retryer.RetryOnResult(
          _GetOperationAndLogProgress,
          args=[client, request, tracker, messages],
          should_retry_if=lambda op, _: not op.done,
          sleep_ms=SLEEP_MS,
      )
    except retry.WaitException:
      raise exceptions.FunctionsError(
          'Operation {0} is taking too long'.format(request.name)
      )

  return operation


def OperationErrorToString(error):
  """Returns a human readable string representation from the operation.

  Args:
    error: A string representing the raw json of the operation error.

  Returns:
    A human readable string representation of the error.
  """
  error_message = 'OperationError: code={0}, message={1}'.format(
      error.code, encoder.Decode(error.message)
  )
  messages = apis.GetMessagesModule('cloudfunctions', _V2_ALPHA)
  if error.details:
    for detail in error.details:
      sub_error = encoding.PyValueToMessage(
          messages.Status, encoding.MessageToPyValue(detail)
      )
      if sub_error.code is not None or sub_error.message is not None:
        error_message += '\n' + OperationErrorToString(sub_error)
  return error_message


def HasRoleBinding(iam_policy, sa_email, role):
  # type(Policy, str, str) -> bool
  """Returns whether the given SA has the given role bound in given policy.

  Args:
    iam_policy: The IAM policy to check.
    sa_email: The service account to check.
    role: The role to check for.
  """
  # iam_policy.bindings structure:
  # list[<Binding
  #       members=['serviceAccount:member@thing.iam.gserviceaccount.com', ...],
  #       role='roles/somerole'>...]
  return any(
      'serviceAccount:{}'.format(sa_email) in b.members and b.role == role
      for b in iam_policy.bindings
  )


def PromptToBindRoleIfMissing(sa_email, role, alt_roles=None, reason=''):
  # type: (str, str, tuple[str] | None, str) -> None
  """Prompts to bind the role to the service account if missing.

  If the console cannot prompt, a warning is logged instead.

  Args:
    sa_email: The service account email to bind the role to.
    role: The role to bind if missing.
    alt_roles: Alternative roles to check that dismiss the need to bind the
      specified role.
    reason: Extra information to print explaining why the binding is necessary.
  """
  alt_roles = alt_roles or []
  project_ref = projects_util.ParseProject(GetProject())
  member = 'serviceAccount:{}'.format(sa_email)
  try:
    iam_policy = projects_api.GetIamPolicy(project_ref)
    if any(HasRoleBinding(iam_policy, sa_email, r) for r in [role, *alt_roles]):
      return

    log.status.Print(
        'Service account [{}] is missing the role [{}].\n{}'.format(
            sa_email, role, reason
        )
    )

    bind = console_io.CanPrompt() and console_io.PromptContinue(
        prompt_string='\nBind the role [{}] to service account [{}]?'.format(
            role, sa_email
        )
    )
    if not bind:
      log.warning('Manual binding of above role may be necessary.\n')
      return

    projects_api.AddIamPolicyBinding(project_ref, member, role)
    log.status.Print('Role successfully bound.\n')
  except apitools_exceptions.HttpForbiddenError:
    log.warning(
        (
            'Your account does not have permission to check or bind IAM'
            ' policies to project [%s]. If the deployment fails, ensure [%s]'
            ' has the role [%s] before retrying.'
        ),
        project_ref,
        sa_email,
        role,
    )


_rm_messages = projects_api_util.GetMessages()

_LOG_TYPES = frozenset([
    _rm_messages.AuditLogConfig.LogTypeValueValuesEnum.ADMIN_READ,
    _rm_messages.AuditLogConfig.LogTypeValueValuesEnum.DATA_READ,
    _rm_messages.AuditLogConfig.LogTypeValueValuesEnum.DATA_WRITE,
])


def _LookupAuditConfig(iam_policy, service):
  # type: (Policy, str) -> AuditConfig
  """Looks up the audit config for the given service.

  If no audit config is found, a new one is created and attached to the given
  policy.

  Args:
    iam_policy: The IAM policy to look through.
    service: The service to find the audit config for.

  Returns:
    The audit config for the given service or a blank new one if not found.
  """
  # iam_policy.auditConfigs structure:
  # list[<AuditConfig
  #       auditLogConfigs=[<AuditLogConfig<logType=...>, ...],
  #       service='foo.googleapis.com'>...]
  for ac in iam_policy.auditConfigs:
    if ac.service == service:
      return ac

  audit_config = _rm_messages.AuditConfig(service=service, auditLogConfigs=[])
  iam_policy.auditConfigs.append(audit_config)
  return audit_config


def PromptToEnableDataAccessAuditLogs(service):
  # type: (str) -> None
  """Prompts to enable Data Access audit logs for the given service.

  If the console cannot prompt, a warning is logged instead.

  Args:
    service: The service to enable Data Access audit logs for.
  """
  project = GetProject()
  project_ref = projects_util.ParseProject(project)
  warning_msg = (
      'If audit logs are not fully enabled for [{}], your function may'
      ' fail to receive some events.'.format(service)
  )

  try:
    policy = projects_api.GetIamPolicy(project_ref)
  except apitools_exceptions.HttpForbiddenError:
    log.warning(
        'You do not have permission to retrieve the IAM policy and check'
        ' whether Data Access audit logs are enabled for [{}]. {}'.format(
            service, warning_msg
        )
    )
    return

  audit_config = _LookupAuditConfig(policy, service)

  enabled_log_types = set(lc.logType for lc in audit_config.auditLogConfigs)
  if enabled_log_types == _LOG_TYPES:
    return

  log.status.Print(
      'Some Data Access audit logs are disabled for [{}]: '
      'https://console.cloud.google.com/iam-admin/audit?project={}'.format(
          service, project
      )
  )

  if not console_io.CanPrompt():
    log.warning(warning_msg)
    return

  log.status.Print(warning_msg)
  if not console_io.PromptContinue(
      prompt_string='\nEnable all Data Access audit logs for [{}]?'.format(
          service
      )
  ):
    return

  # Create log configs for any missing log types.
  log_types_to_enable = [lt for lt in _LOG_TYPES if lt not in enabled_log_types]
  audit_config.auditLogConfigs.extend(
      [_rm_messages.AuditLogConfig(logType=lt) for lt in log_types_to_enable]
  )

  try:
    projects_api.SetIamPolicy(project_ref, policy, update_mask='auditConfigs')
    log.status.Print('Data Access audit logs successfully enabled.')
  except apitools_exceptions.HttpForbiddenError:
    log.warning(
        'You do not have permission to update the IAM policy and ensure Data'
        ' Access audit logs are enabled for [{}].'.format(service)
    )


def GetCloudFunctionsApiEnv():
  """Determine the cloudfunctions API env the gcloud cmd is using."""
  api_string = GetApiEndpointOverride()
  if api_string is None:
    return ApiEnv.PROD
  if 'test-cloudfunctions' in api_string:
    return ApiEnv.TEST
  if 'autopush-cloudfunctions' in api_string:
    return ApiEnv.AUTOPUSH
  if 'staging-cloudfunctions' in api_string:
    return ApiEnv.STAGING

  return ApiEnv.PROD
