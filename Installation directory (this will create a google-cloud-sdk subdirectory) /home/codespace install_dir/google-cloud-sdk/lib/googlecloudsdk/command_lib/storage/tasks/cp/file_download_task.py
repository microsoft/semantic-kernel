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

"""Task for file downloads.

Typically executed in a task iterator:
googlecloudsdk.command_lib.storage.tasks.task_executor.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import os

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.command_lib.storage import fast_crc32c_util
from googlecloudsdk.command_lib.storage import manifest_util
from googlecloudsdk.command_lib.storage import posix_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import symlink_util
from googlecloudsdk.command_lib.storage import tracker_file_util
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.command_lib.storage.tasks import task_util
from googlecloudsdk.command_lib.storage.tasks.cp import copy_component_util
from googlecloudsdk.command_lib.storage.tasks.cp import copy_util
from googlecloudsdk.command_lib.storage.tasks.cp import download_util
from googlecloudsdk.command_lib.storage.tasks.cp import file_part_download_task
from googlecloudsdk.command_lib.storage.tasks.cp import finalize_sliced_download_task
from googlecloudsdk.command_lib.storage.tasks.rm import delete_task
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import scaled_integer


def _should_perform_sliced_download(source_resource, destination_resource):
  """Returns True if conditions are right for a sliced download."""
  if destination_resource.storage_url.is_stream:
    # Can't write to different indices of streams.
    return False
  if (not source_resource.crc32c_hash and
      properties.VALUES.storage.check_hashes.Get() !=
      properties.CheckHashes.NEVER.value):
    # Do not perform sliced download if hash validation is not possible.
    return False

  threshold = scaled_integer.ParseInteger(
      properties.VALUES.storage.sliced_object_download_threshold.Get())
  component_size = scaled_integer.ParseInteger(
      properties.VALUES.storage.sliced_object_download_component_size.Get())
  # TODO(b/183017513): Only perform sliced downloads with parallelism.
  api_capabilities = api_factory.get_capabilities(
      source_resource.storage_url.scheme)
  return (source_resource.size and threshold != 0 and
          source_resource.size > threshold and component_size and
          cloud_api.Capability.SLICED_DOWNLOAD in api_capabilities and
          task_util.should_use_parallelism())


class FileDownloadTask(copy_util.ObjectCopyTaskWithExitHandler):
  """Represents a command operation triggering a file download."""

  def __init__(
      self,
      source_resource,
      destination_resource,
      delete_source=False,
      do_not_decompress=False,
      posix_to_set=None,
      print_created_message=False,
      print_source_version=False,
      system_posix_data=None,
      user_request_args=None,
      verbose=False,
  ):
    """Initializes task.

    Args:
      source_resource (ObjectResource): Must contain the full path of object to
        download, including bucket. Directories will not be accepted. Does not
        need to contain metadata.
      destination_resource (FileObjectResource|UnknownResource): Must contain
        local filesystem path to destination object. Does not need to contain
        metadata.
      delete_source (bool): If copy completes successfully, delete the source
        object afterwards.
      do_not_decompress (bool): Prevents automatically decompressing downloaded
        gzips.
      posix_to_set (PosixAttributes|None): See parent class.
      print_created_message (bool): See parent class.
      print_source_version (bool): See parent class.
      system_posix_data (SystemPosixData): System-wide POSIX info.
      user_request_args (UserRequestArgs|None): See parent class..
      verbose (bool): See parent class.
    """
    super(FileDownloadTask, self).__init__(
        source_resource,
        destination_resource,
        posix_to_set=posix_to_set,
        print_created_message=print_created_message,
        print_source_version=print_source_version,
        user_request_args=user_request_args,
        verbose=verbose,
    )
    self._delete_source = delete_source
    self._do_not_decompress = do_not_decompress
    self._system_posix_data = system_posix_data

    self._temporary_destination_resource = (
        self._get_temporary_destination_resource())

    if (self._source_resource.size and
        self._source_resource.size >= scaled_integer.ParseInteger(
            properties.VALUES.storage.resumable_threshold.Get())):
      self._strategy = cloud_api.DownloadStrategy.RESUMABLE
    else:
      self._strategy = cloud_api.DownloadStrategy.RETRIABLE_IN_FLIGHT

    self.parallel_processing_key = (
        self._destination_resource.storage_url.url_string)

  def _get_temporary_destination_resource(self):
    temporary_resource = copy.deepcopy(self._destination_resource)
    temporary_resource.storage_url.object_name += (
        storage_url.TEMPORARY_FILE_SUFFIX)
    return temporary_resource

  def _get_sliced_download_tasks(self):
    """Creates all tasks necessary for a sliced download."""
    component_offsets_and_lengths = (
        copy_component_util.get_component_offsets_and_lengths(
            self._source_resource.size,
            copy_component_util.get_component_count(
                self._source_resource.size,
                properties.VALUES.storage.sliced_object_download_component_size
                .Get(),
                properties.VALUES.storage.sliced_object_download_max_components
                .GetInt())))

    download_component_task_list = []
    for i, (offset, length) in enumerate(component_offsets_and_lengths):
      download_component_task_list.append(
          file_part_download_task.FilePartDownloadTask(
              self._source_resource,
              self._temporary_destination_resource,
              offset=offset,
              length=length,
              component_number=i,
              total_components=len(component_offsets_and_lengths),
              strategy=self._strategy,
              user_request_args=self._user_request_args))

    finalize_sliced_download_task_list = [
        finalize_sliced_download_task.FinalizeSlicedDownloadTask(
            self._source_resource,
            self._temporary_destination_resource,
            self._destination_resource,
            delete_source=self._delete_source,
            do_not_decompress=self._do_not_decompress,
            posix_to_set=self._posix_to_set,
            system_posix_data=self._system_posix_data,
            user_request_args=self._user_request_args,
        )
    ]

    return (download_component_task_list, finalize_sliced_download_task_list)

  def _restart_download(self):
    log.status.Print('Temporary download file corrupt.'
                     ' Restarting download {}'.format(self._source_resource))
    temporary_download_url = self._temporary_destination_resource.storage_url
    os.remove(temporary_download_url.object_name)
    tracker_file_util.delete_download_tracker_files(temporary_download_url)

  def execute(self, task_status_queue=None):
    """Creates appropriate download tasks."""
    posix_util.run_if_setting_posix(
        self._posix_to_set,
        self._user_request_args,
        posix_util.raise_if_invalid_file_permissions,
        self._system_posix_data,
        self._source_resource,
        known_posix=self._posix_to_set,
    )

    destination_url = self._destination_resource.storage_url
    # We need to call os.remove here for two reasons:
    # 1. It saves on disk space during a transfer.
    # 2. Os.rename fails if a file exists at the destination. Avoiding this by
    # removing files after a download makes us susceptible to a race condition
    # between two running instances of gcloud storage. See the following PR for
    # more information: https://github.com/GoogleCloudPlatform/gsutil/pull/1202.
    # Note that it's not enough to check the results of `exists()`, since that
    # method returns False if the path points to a broken symlink.
    is_destination_symlink = os.path.islink(destination_url.object_name)
    if is_destination_symlink or destination_url.exists():
      if self._user_request_args and self._user_request_args.no_clobber:
        log.status.Print(copy_util.get_no_clobber_message(destination_url))
        if self._send_manifest_messages:
          manifest_util.send_skip_message(
              task_status_queue, self._source_resource,
              self._destination_resource,
              copy_util.get_no_clobber_message(destination_url))
        return
      os.remove(destination_url.object_name)

    temporary_download_file_exists = (
        self._temporary_destination_resource.storage_url.exists())
    if temporary_download_file_exists and os.path.getsize(
        self._temporary_destination_resource.storage_url.object_name
    ) > self._source_resource.size:
      self._restart_download()

    if _should_perform_sliced_download(self._source_resource,
                                       self._destination_resource):
      fast_crc32c_util.log_or_raise_crc32c_issues()
      download_component_task_list, finalize_sliced_download_task_list = (
          self._get_sliced_download_tasks())

      _, found_tracker_file = (
          tracker_file_util.read_or_create_download_tracker_file(
              self._source_resource,
              self._temporary_destination_resource.storage_url,
              total_components=len(download_component_task_list),
          ))
      if found_tracker_file:
        log.debug('Resuming sliced download with {} components.'.format(
            len(download_component_task_list)))
      else:
        if temporary_download_file_exists:
          # Component count may have changed, invalidating earlier download.
          self._restart_download()
        log.debug('Launching sliced download with {} components.'.format(
            len(download_component_task_list)))

      copy_component_util.create_file_if_needed(
          self._source_resource, self._temporary_destination_resource)

      return task.Output(
          additional_task_iterators=[
              download_component_task_list,
              finalize_sliced_download_task_list,
          ],
          messages=None)

    part_download_task_output = file_part_download_task.FilePartDownloadTask(
        self._source_resource,
        self._temporary_destination_resource,
        offset=0,
        length=self._source_resource.size,
        do_not_decompress=self._do_not_decompress,
        strategy=self._strategy,
        user_request_args=self._user_request_args,
    ).execute(task_status_queue=task_status_queue)

    temporary_file_url = self._temporary_destination_resource.storage_url
    server_encoding = task_util.get_first_matching_message_payload(
        part_download_task_output.messages, task.Topic.API_DOWNLOAD_RESULT
    )

    preserve_symlinks = symlink_util.get_preserve_symlink_from_user_request(
        self._user_request_args
    )
    download_util.finalize_download(
        self._source_resource,
        temporary_file_url.object_name,
        destination_url.object_name,
        convert_symlinks=preserve_symlinks,
        do_not_decompress_flag=self._do_not_decompress,
        server_encoding=server_encoding,
    )
    # For sliced download, cleanup is done in the finalized sliced download task
    # We perform cleanup here for all other types in case some corrupt files
    # were left behind.
    tracker_file_util.delete_download_tracker_files(temporary_file_url)

    posix_util.run_if_setting_posix(
        self._posix_to_set,
        self._user_request_args,
        posix_util.set_posix_attributes_on_file_if_valid,
        self._system_posix_data,
        self._source_resource,
        self._destination_resource,
        known_source_posix=self._posix_to_set,
        preserve_symlinks=preserve_symlinks,
    )

    self._print_created_message_if_requested(self._destination_resource)
    if self._send_manifest_messages:
      manifest_util.send_success_message(
          task_status_queue,
          self._source_resource,
          self._destination_resource,
          md5_hash=task_util.get_first_matching_message_payload(
              part_download_task_output.messages, task.Topic.MD5))

    if self._delete_source:
      return task.Output(
          additional_task_iterators=[[
              delete_task.DeleteObjectTask(self._source_resource.storage_url),
          ]],
          messages=None,
      )
