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
"""Utils for managng the many transfer job flags.

Tested through surface/transfer/jobs/create_test.py.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.transfer import creds_util
from googlecloudsdk.command_lib.transfer import jobs_flag_util
from googlecloudsdk.command_lib.transfer import name_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import times


UPDATE_FIELD_MASK = ('description,logging_config,notification_config,schedule,'
                     'status,transfer_spec')
VALID_TRANSFER_SCHEMES = [
    storage_url.ProviderPrefix.POSIX,
    storage_url.ProviderPrefix.GCS,
    storage_url.ProviderPrefix.S3,
    storage_url.ProviderPrefix.HTTP,
    storage_url.ProviderPrefix.HTTPS,
]


def _prompt_and_add_valid_scheme(url):
  """Has user select a valid scheme from a list and returns new URL."""
  if not console_io.CanPrompt():
    raise errors.InvalidUrlError('Did you mean "posix://{}"'.format(
        url.object_name))
  scheme_index = console_io.PromptChoice(
      [scheme.value + '://' for scheme in VALID_TRANSFER_SCHEMES],
      cancel_option=True,
      message=('Storage Transfer does not support direct file URLs: {}\n'
               'Did you mean to use "posix://"?\n'
               'Run this command with "--help" for more info,\n'
               'or select a valid scheme below.').format(url))

  new_scheme = VALID_TRANSFER_SCHEMES[scheme_index]
  return storage_url.switch_scheme(url, new_scheme)


def _create_or_modify_transfer_options(transfer_spec, args, messages):
  """Creates or modifies TransferOptions object based on args."""
  if not (getattr(args, 'overwrite_when', None) or getattr(
      args, 'delete_from', None) or getattr(args, 'preserve_metadata', None) or
          getattr(args, 'custom_storage_class', None)):
    return
  if not transfer_spec.transferOptions:
    transfer_spec.transferOptions = messages.TransferOptions()

  overwrite_when_argument = getattr(args, 'overwrite_when', None)
  if overwrite_when_argument:
    transfer_spec.transferOptions.overwriteWhen = getattr(
        messages.TransferOptions.OverwriteWhenValueValuesEnum,
        overwrite_when_argument.upper())

  if getattr(args, 'delete_from', None):
    delete_option = jobs_flag_util.DeleteOption(args.delete_from)
    if delete_option is jobs_flag_util.DeleteOption.SOURCE_AFTER_TRANSFER:
      transfer_spec.transferOptions.deleteObjectsFromSourceAfterTransfer = True
    elif delete_option is jobs_flag_util.DeleteOption.DESTINATION_IF_UNIQUE:
      transfer_spec.transferOptions.deleteObjectsUniqueInSink = True

  metadata_options = messages.MetadataOptions()
  if getattr(args, 'preserve_metadata', None):
    for field_value in args.preserve_metadata:
      field_key = jobs_flag_util.PreserveMetadataField(field_value)
      if field_key == jobs_flag_util.PreserveMetadataField.ACL:
        metadata_options.acl = (
            messages.MetadataOptions.AclValueValuesEnum.ACL_PRESERVE)
      elif field_key == jobs_flag_util.PreserveMetadataField.GID:
        metadata_options.gid = (
            messages.MetadataOptions.GidValueValuesEnum.GID_NUMBER)
      elif field_key == jobs_flag_util.PreserveMetadataField.UID:
        metadata_options.uid = (
            messages.MetadataOptions.UidValueValuesEnum.UID_NUMBER)
      elif field_key == jobs_flag_util.PreserveMetadataField.KMS_KEY:
        metadata_options.kmsKey = (
            messages.MetadataOptions.KmsKeyValueValuesEnum.KMS_KEY_PRESERVE)
      elif field_key == jobs_flag_util.PreserveMetadataField.MODE:
        metadata_options.mode = (
            messages.MetadataOptions.ModeValueValuesEnum.MODE_PRESERVE)
      elif field_key == jobs_flag_util.PreserveMetadataField.STORAGE_CLASS:
        metadata_options.storageClass = (
            messages.MetadataOptions.StorageClassValueValuesEnum
            .STORAGE_CLASS_PRESERVE)
      elif field_key == jobs_flag_util.PreserveMetadataField.SYMLINK:
        metadata_options.symlink = (
            messages.MetadataOptions.SymlinkValueValuesEnum.SYMLINK_PRESERVE)
      elif field_key == jobs_flag_util.PreserveMetadataField.TEMPORARY_HOLD:
        metadata_options.temporaryHold = (
            messages.MetadataOptions.TemporaryHoldValueValuesEnum
            .TEMPORARY_HOLD_PRESERVE)
      elif field_key == jobs_flag_util.PreserveMetadataField.TIME_CREATED:
        metadata_options.timeCreated = (
            messages.MetadataOptions.TimeCreatedValueValuesEnum.TIME_CREATED_PRESERVE_AS_CUSTOM_TIME
        )
  if getattr(args, 'custom_storage_class', None):
    metadata_options.storageClass = getattr(
        messages.MetadataOptions.StorageClassValueValuesEnum,
        'STORAGE_CLASS_' + args.custom_storage_class.upper())

  if metadata_options != messages.MetadataOptions():
    transfer_spec.transferOptions.metadataOptions = metadata_options


def _create_or_modify_object_conditions(transfer_spec, args, messages):
  """Creates or modifies ObjectConditions based on args."""
  if not (getattr(args, 'include_prefixes', None) or
          getattr(args, 'exclude_prefixes', None) or
          getattr(args, 'include_modified_before_absolute', None) or
          getattr(args, 'include_modified_after_absolute', None) or
          getattr(args, 'include_modified_before_relative', None) or
          getattr(args, 'include_modified_after_relative', None)):
    return
  if not transfer_spec.objectConditions:
    transfer_spec.objectConditions = messages.ObjectConditions()

  if getattr(args, 'include_prefixes', None):
    transfer_spec.objectConditions.includePrefixes = args.include_prefixes
  if getattr(args, 'exclude_prefixes', None):
    transfer_spec.objectConditions.excludePrefixes = args.exclude_prefixes
  if getattr(args, 'include_modified_before_absolute', None):
    modified_before_datetime_string = (
        args.include_modified_before_absolute.astimezone(times.UTC).isoformat())
    transfer_spec.objectConditions.lastModifiedBefore = modified_before_datetime_string
  if getattr(args, 'include_modified_after_absolute', None):
    modified_after_datetime_string = (
        args.include_modified_after_absolute.astimezone(times.UTC).isoformat())
    transfer_spec.objectConditions.lastModifiedSince = modified_after_datetime_string
  if getattr(args, 'include_modified_before_relative', None):
    transfer_spec.objectConditions.minTimeElapsedSinceLastModification = '{}s'.format(
        args.include_modified_before_relative)
  if getattr(args, 'include_modified_after_relative', None):
    transfer_spec.objectConditions.maxTimeElapsedSinceLastModification = '{}s'.format(
        args.include_modified_after_relative)


def _create_or_modify_creds(transfer_spec, args, messages):
  """Creates or modifies TransferSpec source creds based on args."""
  if transfer_spec.awsS3DataSource:
    if getattr(args, 'source_creds_file', None):
      access_key_id, secret_access_key, role_arn = (
          creds_util.get_aws_creds_from_file(args.source_creds_file))
    else:
      log.warning('No --source-creds-file flag. Checking system config files'
                  ' for AWS credentials.')
      access_key_id, secret_access_key = creds_util.get_default_aws_creds()
      role_arn = None

    if not ((access_key_id and secret_access_key) or role_arn):
      log.warning('Missing AWS source creds.')

    transfer_spec.awsS3DataSource.awsAccessKey = messages.AwsAccessKey(
        accessKeyId=access_key_id, secretAccessKey=secret_access_key)
    transfer_spec.awsS3DataSource.roleArn = role_arn

  elif transfer_spec.azureBlobStorageDataSource:
    if getattr(args, 'source_creds_file', None):
      sas_token = creds_util.get_values_for_keys_from_file(
          args.source_creds_file, ['sasToken'])['sasToken']
    else:
      log.warning('No Azure source creds set. Consider adding'
                  ' --source-creds-file flag.')
      sas_token = None
    transfer_spec.azureBlobStorageDataSource.azureCredentials = (
        messages.AzureCredentials(sasToken=sas_token))


def _get_s3_compatible_metadata(args, messages):
  """Generates advanced settings for S3-compatible providers."""
  if not (args.source_auth_method or args.source_list_api or
          args.source_network_protocol or args.source_request_model):
    return None
  s3_compatible_metadata = messages.S3CompatibleMetadata()
  if args.source_auth_method:
    s3_compatible_metadata.authMethod = getattr(
        messages.S3CompatibleMetadata.AuthMethodValueValuesEnum,
        'AUTH_METHOD_' + args.source_auth_method)
  if args.source_list_api:
    s3_compatible_metadata.listApi = getattr(
        messages.S3CompatibleMetadata.ListApiValueValuesEnum,
        args.source_list_api)
  if args.source_network_protocol:
    s3_compatible_metadata.protocol = getattr(
        messages.S3CompatibleMetadata.ProtocolValueValuesEnum,
        'NETWORK_PROTOCOL_' + args.source_network_protocol)
  if args.source_request_model:
    s3_compatible_metadata.requestModel = getattr(
        messages.S3CompatibleMetadata.RequestModelValueValuesEnum,
        'REQUEST_MODEL_' + args.source_request_model)

  return s3_compatible_metadata


def _create_or_modify_transfer_spec(job, args, messages):
  """Creates or modifies TransferSpec based on args."""
  if not job.transferSpec:
    job.transferSpec = messages.TransferSpec()

  if getattr(args, 'source', None):
    # Clear any existing source to make space for new one.
    job.transferSpec.httpDataSource = None
    job.transferSpec.posixDataSource = None
    job.transferSpec.gcsDataSource = None
    job.transferSpec.awsS3CompatibleDataSource = None
    job.transferSpec.awsS3DataSource = None
    job.transferSpec.azureBlobStorageDataSource = None
    job.transferSpec.hdfsDataSource = None

    try:
      source_url = storage_url.storage_url_from_string(args.source)
    except errors.InvalidUrlError:
      if args.source.startswith(storage_url.ProviderPrefix.HTTP.value):
        job.transferSpec.httpDataSource = messages.HttpData(listUrl=args.source)
        source_url = None
      else:
        raise
    else:
      if source_url.scheme is storage_url.ProviderPrefix.FILE:
        source_url = _prompt_and_add_valid_scheme(source_url)
      if source_url.scheme is storage_url.ProviderPrefix.HDFS:
        job.transferSpec.hdfsDataSource = messages.HdfsData(
            path=source_url.object_name)
      if source_url.scheme is storage_url.ProviderPrefix.POSIX:
        job.transferSpec.posixDataSource = messages.PosixFilesystem(
            rootDirectory=source_url.object_name)
      elif source_url.scheme is storage_url.ProviderPrefix.GCS:
        job.transferSpec.gcsDataSource = messages.GcsData(
            bucketName=source_url.bucket_name,
            path=source_url.object_name,
        )
      elif source_url.scheme is storage_url.ProviderPrefix.S3:
        if args.source_endpoint:
          job.transferSpec.awsS3CompatibleDataSource = (
              messages.AwsS3CompatibleData(
                  bucketName=source_url.bucket_name,
                  endpoint=args.source_endpoint,
                  path=source_url.object_name,
                  region=args.source_signing_region,
                  s3Metadata=_get_s3_compatible_metadata(args, messages)))
        else:
          job.transferSpec.awsS3DataSource = messages.AwsS3Data(
              bucketName=source_url.bucket_name,
              path=source_url.object_name,
          )
      elif isinstance(source_url, storage_url.AzureUrl):
        job.transferSpec.azureBlobStorageDataSource = (
            messages.AzureBlobStorageData(
                container=source_url.bucket_name,
                path=source_url.object_name,
                storageAccount=source_url.account,
            ))

  if getattr(args, 'destination', None):
    # Clear any existing destination to make space for new one.
    job.transferSpec.posixDataSink = None
    job.transferSpec.gcsDataSink = None

    destination_url = storage_url.storage_url_from_string(args.destination)
    if destination_url.scheme is storage_url.ProviderPrefix.FILE:
      destination_url = _prompt_and_add_valid_scheme(destination_url)

    if destination_url.scheme is storage_url.ProviderPrefix.GCS:
      job.transferSpec.gcsDataSink = messages.GcsData(
          bucketName=destination_url.bucket_name,
          path=destination_url.object_name,
      )
    elif destination_url.scheme is storage_url.ProviderPrefix.POSIX:
      job.transferSpec.posixDataSink = messages.PosixFilesystem(
          rootDirectory=destination_url.object_name)

  if getattr(args, 'destination_agent_pool', None):
    job.transferSpec.sinkAgentPoolName = name_util.add_agent_pool_prefix(
        args.destination_agent_pool)
  if getattr(args, 'source_agent_pool', None):
    job.transferSpec.sourceAgentPoolName = name_util.add_agent_pool_prefix(
        args.source_agent_pool)
  if getattr(args, 'intermediate_storage_path', None):
    intermediate_storage_url = storage_url.storage_url_from_string(
        args.intermediate_storage_path)
    job.transferSpec.gcsIntermediateDataLocation = messages.GcsData(
        bucketName=intermediate_storage_url.bucket_name,
        path=intermediate_storage_url.object_name)
  if getattr(args, 'manifest_file', None):
    job.transferSpec.transferManifest = messages.TransferManifest(
        location=args.manifest_file)

  _create_or_modify_creds(job.transferSpec, args, messages)
  _create_or_modify_object_conditions(job.transferSpec, args, messages)
  _create_or_modify_transfer_options(job.transferSpec, args, messages)


def _create_or_modify_event_stream_configuration(job, args, messages):
  """Creates or modifies event stream config. Returns if flag present."""
  event_stream_name = getattr(args, 'event_stream_name', None)
  event_stream_start = getattr(args, 'event_stream_starts', None)
  event_stream_expire = getattr(args, 'event_stream_expires', None)
  if not (event_stream_name or event_stream_start or event_stream_expire):
    # Nothing needs modification.
    return False

  if not job.eventStream:
    job.eventStream = messages.EventStream()
  job.eventStream.name = event_stream_name
  job.eventStream.eventStreamStartTime = event_stream_start
  job.eventStream.eventStreamExpirationTime = event_stream_expire
  return True


def _create_or_modify_schedule(job, args, messages, is_update,
                               has_event_stream_flag):
  """Creates or modifies transfer Schedule object based on args."""
  schedule_starts = getattr(args, 'schedule_starts', None)
  schedule_repeats_every = getattr(args, 'schedule_repeats_every', None)
  schedule_repeats_until = getattr(args, 'schedule_repeats_until', None)
  has_schedule_flag = (
      schedule_starts or schedule_repeats_every or schedule_repeats_until)

  if has_schedule_flag:
    if not is_update and args.do_not_run:
      raise ValueError('Cannot set schedule and do-not-run flag.')
    if has_event_stream_flag:
      raise ValueError('Cannot set schedule and event stream.')

  if (not is_update and
      args.do_not_run) or has_event_stream_flag or (is_update and
                                                    not has_schedule_flag):
    # (1) Cannot have schedule for non-running job.
    # (2) Cannot have schedule and event stream.
    # (3) Nothing needs updating.
    return
  if not job.schedule:
    job.schedule = messages.Schedule()

  if schedule_starts:
    start = schedule_starts.astimezone(times.UTC)

    job.schedule.scheduleStartDate = messages.Date(
        day=start.day,
        month=start.month,
        year=start.year,
    )
    job.schedule.startTimeOfDay = messages.TimeOfDay(
        hours=start.hour,
        minutes=start.minute,
        seconds=start.second,
    )
  elif not is_update:
    # By default, run job immediately on create.
    today_date = datetime.date.today()
    job.schedule.scheduleStartDate = messages.Date(
        day=today_date.day, month=today_date.month, year=today_date.year)

  if schedule_repeats_every:
    job.schedule.repeatInterval = '{}s'.format(schedule_repeats_every)
    # Default behavior of running job every 24 hours if field not set will be
    # blocked by schedule_repeats_until handling.

  if schedule_repeats_until:
    if not job.schedule.repeatInterval:
      raise ValueError(
          'Scheduling a job end time requires setting a frequency with'
          ' --schedule-repeats-every. If no job end time is set, the job will'
          ' run one time.')
    end = schedule_repeats_until.astimezone(times.UTC)
    job.schedule.scheduleEndDate = messages.Date(
        day=end.day,
        month=end.month,
        year=end.year,
    )
    job.schedule.endTimeOfDay = messages.TimeOfDay(
        hours=end.hour,
        minutes=end.minute,
        seconds=end.second,
    )
  elif not is_update and not job.schedule.repeatInterval:
    # By default, run operation once on create.
    # If job frequency set, allow operation to repeat endlessly.
    job.schedule.scheduleEndDate = job.schedule.scheduleStartDate


def _create_or_modify_notification_config(job, args, messages, is_update=False):
  """Creates or modifies transfer NotificationConfig object based on args."""
  notification_pubsub_topic = getattr(args, 'notification_pubsub_topic', None)
  notification_event_types = getattr(args, 'notification_event_types', None)
  notification_payload_format = getattr(args, 'notification_payload_format',
                                        None)
  if not (notification_pubsub_topic or notification_event_types or
          notification_payload_format):
    # Nothing to modify with.
    return

  if notification_pubsub_topic:
    if not job.notificationConfig:
      # Create config with required PubSub topic.
      job.notificationConfig = messages.NotificationConfig(
          pubsubTopic=notification_pubsub_topic)
    else:
      job.notificationConfig.pubsubTopic = notification_pubsub_topic

  if (notification_event_types or
      notification_payload_format) and not job.notificationConfig:
    raise ValueError('Cannot set notification config without'
                     ' --notification-pubsub-topic.')

  if notification_payload_format:
    payload_format_key = notification_payload_format.upper()
    job.notificationConfig.payloadFormat = getattr(
        messages.NotificationConfig.PayloadFormatValueValuesEnum,
        payload_format_key)
  elif not is_update:
    # New job default.
    job.notificationConfig.payloadFormat = (
        messages.NotificationConfig.PayloadFormatValueValuesEnum.JSON)

  if notification_event_types:
    event_types = []
    for event_type_arg in notification_event_types:
      event_type_key = 'TRANSFER_OPERATION_' + event_type_arg.upper()
      event_type = getattr(
          messages.NotificationConfig.EventTypesValueListEntryValuesEnum,
          event_type_key)
      event_types.append(event_type)
    job.notificationConfig.eventTypes = event_types
  elif not is_update:
    # New job default.
    job.notificationConfig.eventTypes = [
        (messages.NotificationConfig.EventTypesValueListEntryValuesEnum
         .TRANSFER_OPERATION_SUCCESS),
        (messages.NotificationConfig.EventTypesValueListEntryValuesEnum
         .TRANSFER_OPERATION_FAILED),
        (messages.NotificationConfig.EventTypesValueListEntryValuesEnum
         .TRANSFER_OPERATION_ABORTED)
    ]


def _create_or_modify_logging_config(job, args, messages):
  """Creates or modifies transfer LoggingConfig object based on args."""
  # TODO(b/322289474): enable-posix-transfer-logs logic can be cleaned up once
  #                    POSIX logs are deprecated.
  enable_posix_transfer_logs = getattr(args, 'enable_posix_transfer_logs', None)
  if not job.loggingConfig:
    if enable_posix_transfer_logs is None:
      # Default to creating new jobs with logging enabled.
      job.loggingConfig = messages.LoggingConfig(
          enableOnpremGcsTransferLogs=True)
    else:
      job.loggingConfig = messages.LoggingConfig()

  if enable_posix_transfer_logs is not None:
    # Update new and existing jobs with user setting.
    job.loggingConfig.enableOnpremGcsTransferLogs = enable_posix_transfer_logs

  if job.transferSpec.hdfsDataSource is not None:
    # HDFS supports only the newer logging.
    job.loggingConfig.enableOnpremGcsTransferLogs = False

  log_actions = getattr(args, 'log_actions', None)
  log_action_states = getattr(args, 'log_action_states', None)
  if not (log_actions or log_action_states):
    # Nothing remaining to modify with.
    return

  existing_log_actions = job.loggingConfig and job.loggingConfig.logActions
  existing_log_action_states = (
      job.loggingConfig and job.loggingConfig.logActionStates)

  if (not (log_actions and log_action_states) and
      ((log_actions and not existing_log_action_states) or
       (log_action_states and not existing_log_actions))):
    raise ValueError('Both --log-actions and --log-action-states are required'
                     ' for a complete log config.')

  if log_actions:
    actions = []
    for action in log_actions:
      actions.append(
          getattr(job.loggingConfig.LogActionsValueListEntryValuesEnum,
                  action.upper()))
    job.loggingConfig.logActions = actions

  if log_action_states:
    action_states = []
    for action_state in log_action_states:
      action_states.append(
          getattr(job.loggingConfig.LogActionStatesValueListEntryValuesEnum,
                  action_state.upper()))
    job.loggingConfig.logActionStates = action_states


def generate_patch_transfer_job_message(messages, job, field_mask):
  """Generates Apitools patch message for transfer jobs."""
  project_id = job.projectId
  job.projectId = None

  if job.schedule == messages.Schedule():
    # Jobs returned by API are populated with their user-set schedule or an
    # empty schedule. Empty schedules cannot be re-submitted to the API.
    job.schedule = None

  return messages.StoragetransferTransferJobsPatchRequest(
      jobName=job.name,
      updateTransferJobRequest=messages.UpdateTransferJobRequest(
          projectId=project_id,
          transferJob=job,
          updateTransferJobFieldMask=field_mask,
      ))


def generate_transfer_job_message(args, messages, existing_job=None):
  """Generates Apitools transfer message based on command arguments."""
  if existing_job:
    job = existing_job
  else:
    job = messages.TransferJob()

  if not job.projectId:
    job.projectId = properties.VALUES.core.project.Get()

  if getattr(args, 'name', None):
    job.name = name_util.add_job_prefix(args.name)

  if getattr(args, 'description', None):
    job.description = args.description

  if existing_job:
    # Is job update instead of create.
    if getattr(args, 'status', None):
      status_key = args.status.upper()
      job.status = getattr(messages.TransferJob.StatusValueValuesEnum,
                           status_key)
  else:
    job.status = messages.TransferJob.StatusValueValuesEnum.ENABLED

  _create_or_modify_transfer_spec(job, args, messages)
  has_event_stream_flag = _create_or_modify_event_stream_configuration(
      job, args, messages)
  _create_or_modify_schedule(
      job,
      args,
      messages,
      is_update=bool(existing_job),
      has_event_stream_flag=has_event_stream_flag)
  _create_or_modify_notification_config(
      job, args, messages, is_update=bool(existing_job))
  _create_or_modify_logging_config(job, args, messages)

  if existing_job:
    return generate_patch_transfer_job_message(messages, job, UPDATE_FIELD_MASK)
  return job
