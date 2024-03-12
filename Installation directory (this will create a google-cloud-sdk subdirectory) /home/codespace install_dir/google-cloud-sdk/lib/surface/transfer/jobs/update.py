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
"""Command to update transfer jobs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.transfer import jobs_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.transfer import jobs_apitools_util
from googlecloudsdk.command_lib.transfer import jobs_flag_util


def _clear_fields(args, messages, job):
  """Removes fields from TransferJob based on clear flags."""
  if args.clear_description:
    job.description = None
  if args.clear_source_creds_file:
    if getattr(job.transferSpec, 'awsS3DataSource', None):
      job.transferSpec.awsS3DataSource.awsAccessKey = None
      job.transferSpec.awsS3DataSource.roleArn = None
    if getattr(job.transferSpec, 'azureBlobStorageDataSource', None):
      job.transferSpec.azureBlobStorageDataSource.azureCredentials = None
  if args.clear_event_stream:
    job.eventStream = None
  if args.clear_schedule:
    job.schedule = None
  if args.clear_source_agent_pool:
    job.transferSpec.sourceAgentPoolName = None
  if args.clear_destination_agent_pool:
    job.transferSpec.sinkAgentPoolName = None
  if args.clear_intermediate_storage_path:
    job.transferSpec.gcsIntermediateDataLocation = None
  if args.clear_manifest_file:
    job.transferSpec.transferManifest = None

  if getattr(job.transferSpec, 'objectConditions', None):
    object_conditions = job.transferSpec.objectConditions
    if args.clear_include_prefixes:
      object_conditions.includePrefixes = []
    if args.clear_exclude_prefixes:
      object_conditions.excludePrefixes = []
    if args.clear_include_modified_before_absolute:
      object_conditions.lastModifiedBefore = None
    if args.clear_include_modified_after_absolute:
      object_conditions.lastModifiedSince = None
    if args.clear_include_modified_before_relative:
      object_conditions.minTimeElapsedSinceLastModification = None
    if args.clear_include_modified_after_relative:
      object_conditions.maxTimeElapsedSinceLastModification = None

    if object_conditions == messages.ObjectConditions():
      job.transferSpec.objectConditions = None

  if getattr(job.transferSpec, 'transferOptions', None):
    transfer_options = job.transferSpec.transferOptions
    if args.clear_delete_from:
      transfer_options.deleteObjectsFromSourceAfterTransfer = None
      transfer_options.deleteObjectsUniqueInSink = None
    if args.clear_delete_from:
      transfer_options.deleteObjectsFromSourceAfterTransfer = None
      transfer_options.deleteObjectsUniqueInSink = None

    if transfer_options.metadataOptions:
      existing_metadata_options = transfer_options.metadataOptions
      new_metadata_options = existing_metadata_options

      if args.clear_preserve_metadata:
        new_metadata_options = messages.MetadataOptions()
        if (existing_metadata_options.storageClass != messages.MetadataOptions
            .StorageClassValueValuesEnum.STORAGE_CLASS_PRESERVE):
          # Maintain custom values that aren't the preserve flag.
          new_metadata_options.storageClass = (
              existing_metadata_options.storageClass)

      if args.clear_custom_storage_class:
        new_metadata_options.storageClass = None

      if new_metadata_options == messages.MetadataOptions():
        transfer_options.metadataOptions = None
      else:
        transfer_options.metadataOptions = new_metadata_options

    if transfer_options == messages.TransferOptions():
      job.transferSpec.transferOptions = None

  if args.clear_notification_config:
    job.notificationConfig = None
  if args.clear_notification_event_types:
    job.notificationConfig.eventTypes = []
  if args.clear_log_config:
    job.loggingConfig = None

  if getattr(job.transferSpec, 'awsS3CompatibleDataSource', None):
    if args.clear_source_endpoint:
      job.transferSpec.awsS3CompatibleDataSource.endpoint = None
    if args.clear_source_signing_region:
      job.transferSpec.awsS3CompatibleDataSource.region = None

    s3_compatible_metadata = getattr(job.transferSpec.awsS3CompatibleDataSource,
                                     's3Metadata', None)
    if s3_compatible_metadata:
      if args.clear_source_auth_method:
        s3_compatible_metadata.authMethod = None
      if args.clear_source_list_api:
        s3_compatible_metadata.listApi = None
      if args.clear_source_network_protocol:
        s3_compatible_metadata.protocol = None
      if args.clear_source_request_model:
        s3_compatible_metadata.requestModel = None

    if s3_compatible_metadata == messages.S3CompatibleMetadata():
      job.transferSpec.awsS3CompatibleDataSource.s3Metadata = None


class Update(base.Command):
  """Update a Transfer Service transfer job."""

  # pylint:disable=line-too-long
  detailed_help = {
      'DESCRIPTION':
          """\
      Update a Transfer Service transfer job.
      """,
      'EXAMPLES':
          """\
      To disable transfer job 'foo', run:

        $ {command} foo --status=disabled

      To remove the schedule for transfer job 'foo' so that it will only run
      when you manually start it, run:

        $ {command} foo --clear-schedule

      To clear the values from the `include=prefixes` object condition in
      transfer job 'foo', run:

        $ {command} foo --clear-include-prefixes
      """
  }

  @staticmethod
  def Args(parser):
    jobs_flag_util.setup_parser(parser, is_update=True)

  def Run(self, args):
    client = apis.GetClientInstance('transfer', 'v1')
    messages = apis.GetMessagesModule('transfer', 'v1')

    existing_job = jobs_util.api_get(args.name)
    _clear_fields(args, messages, existing_job)

    return client.transferJobs.Patch(
        jobs_apitools_util.generate_transfer_job_message(
            args, messages, existing_job=existing_job))
