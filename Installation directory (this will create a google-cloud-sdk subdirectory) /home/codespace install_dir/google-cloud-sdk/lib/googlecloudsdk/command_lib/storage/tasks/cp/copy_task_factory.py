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
"""Preferred method of generating a copy task."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import posix_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.tasks.cp import copy_managed_folder_task
from googlecloudsdk.command_lib.storage.tasks.cp import daisy_chain_copy_task
from googlecloudsdk.command_lib.storage.tasks.cp import file_download_task
from googlecloudsdk.command_lib.storage.tasks.cp import file_upload_task
from googlecloudsdk.command_lib.storage.tasks.cp import intra_cloud_copy_task
from googlecloudsdk.command_lib.storage.tasks.cp import parallel_composite_upload_util
from googlecloudsdk.command_lib.storage.tasks.cp import streaming_download_task
from googlecloudsdk.command_lib.storage.tasks.cp import streaming_upload_task


def get_copy_task(
    source_resource,
    destination_resource,
    delete_source=False,
    do_not_decompress=False,
    fetch_source_fields_scope=None,
    force_daisy_chain=False,
    posix_to_set=None,
    print_created_message=False,
    print_source_version=False,
    shared_stream=None,
    user_request_args=None,
    verbose=False,
):
  """Factory method that returns the correct copy task for the arguments.

  Args:
    source_resource (resource_reference.Resource): Reference to file to copy.
    destination_resource (resource_reference.Resource): Reference to destination
      to copy file to.
    delete_source (bool): If copy completes successfully, delete the source
      object afterwards.
    do_not_decompress (bool): Prevents automatically decompressing downloaded
      gzips.
    fetch_source_fields_scope (FieldsScope|None): If present, refetch
      source_resource, populated with metadata determined by this FieldsScope.
      Useful for lazy or parallelized GET calls. Currently only implemented for
      intra-cloud copies.
    force_daisy_chain (bool): If True, yields daisy chain copy tasks in place of
      intra-cloud copy tasks.
    posix_to_set (PosixAttributes|None): Triggers setting POSIX on result of
      copy and avoids re-parsing POSIX info.
    print_created_message (bool): Print the versioned URL of each successfully
      copied object.
    print_source_version (bool): Print source object version in status message
      enabled by the `verbose` kwarg.
    shared_stream (stream): Multiple tasks may reuse this read or write stream.
    user_request_args (UserRequestArgs|None): Values for RequestConfig.
    verbose (bool): Print a "copying" status message on task initialization.

  Returns:
    Task object that can be executed to perform a copy.

  Raises:
    NotImplementedError: Cross-cloud copy.
    Error: Local filesystem copy.
  """
  source_url = source_resource.storage_url
  destination_url = destination_resource.storage_url

  if (isinstance(source_url, storage_url.FileUrl)
      and isinstance(destination_url, storage_url.FileUrl)):
    raise errors.Error(
        'Local copies not supported. Gcloud command-line tool is'
        ' meant for cloud operations. Received copy from {} to {}'.format(
            source_url, destination_url
        )
    )

  if (isinstance(source_url, storage_url.CloudUrl)
      and isinstance(destination_url, storage_url.FileUrl)):
    if destination_url.is_stream:
      return streaming_download_task.StreamingDownloadTask(
          source_resource,
          destination_resource,
          shared_stream,
          print_created_message=print_created_message,
          print_source_version=print_source_version,
          user_request_args=user_request_args,
          verbose=verbose,
      )

    return file_download_task.FileDownloadTask(
        source_resource,
        destination_resource,
        delete_source=delete_source,
        do_not_decompress=do_not_decompress,
        posix_to_set=posix_to_set,
        print_created_message=print_created_message,
        print_source_version=print_source_version,
        system_posix_data=posix_util.run_if_setting_posix(
            posix_to_set, user_request_args, posix_util.get_system_posix_data
        ),
        user_request_args=user_request_args,
        verbose=verbose,
    )

  if (isinstance(source_url, storage_url.FileUrl)
      and isinstance(destination_url, storage_url.CloudUrl)):
    if source_url.is_stream:
      return streaming_upload_task.StreamingUploadTask(
          source_resource,
          destination_resource,
          posix_to_set=posix_to_set,
          print_created_message=print_created_message,
          print_source_version=print_source_version,
          user_request_args=user_request_args,
          verbose=verbose,
      )
    else:
      is_composite_upload_eligible = (
          parallel_composite_upload_util.is_composite_upload_eligible(
              source_resource, destination_resource, user_request_args))
      return file_upload_task.FileUploadTask(
          source_resource,
          destination_resource,
          delete_source=delete_source,
          is_composite_upload_eligible=is_composite_upload_eligible,
          posix_to_set=posix_to_set,
          print_created_message=print_created_message,
          print_source_version=print_source_version,
          user_request_args=user_request_args,
          verbose=verbose,
      )

  if (isinstance(source_url, storage_url.CloudUrl)
      and isinstance(destination_url, storage_url.CloudUrl)):
    different_providers = source_url.scheme != destination_url.scheme
    if (different_providers and user_request_args and
        user_request_args.resource_args and
        user_request_args.resource_args.preserve_acl):
      raise errors.Error(
          'Cannot preserve ACLs while copying between cloud providers.'
      )

    if isinstance(source_resource, resource_reference.ManagedFolderResource):
      return copy_managed_folder_task.CopyManagedFolderTask(
          source_resource,
          destination_resource,
          print_created_message=print_created_message,
          user_request_args=user_request_args,
          verbose=verbose,
      )
    if different_providers or force_daisy_chain:
      return daisy_chain_copy_task.DaisyChainCopyTask(
          source_resource,
          destination_resource,
          delete_source=delete_source,
          posix_to_set=posix_to_set,
          print_created_message=print_created_message,
          print_source_version=print_source_version,
          user_request_args=user_request_args,
          verbose=verbose,
      )
    return intra_cloud_copy_task.IntraCloudCopyTask(
        source_resource,
        destination_resource,
        delete_source=delete_source,
        fetch_source_fields_scope=fetch_source_fields_scope,
        posix_to_set=posix_to_set,
        print_created_message=print_created_message,
        print_source_version=print_source_version,
        user_request_args=user_request_args,
        verbose=verbose,
    )
