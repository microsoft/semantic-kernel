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
"""Task for performing final steps of sliced download.

Typically executed in a task iterator:
googlecloudsdk.command_lib.storage.tasks.task_executor.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import manifest_util
from googlecloudsdk.command_lib.storage import posix_util
from googlecloudsdk.command_lib.storage import symlink_util
from googlecloudsdk.command_lib.storage import tracker_file_util
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.command_lib.storage.tasks.cp import copy_util
from googlecloudsdk.command_lib.storage.tasks.cp import download_util
from googlecloudsdk.command_lib.storage.tasks.rm import delete_task
from googlecloudsdk.command_lib.util import crc32c
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class FinalizeSlicedDownloadTask(copy_util.ObjectCopyTaskWithExitHandler):
  """Performs final steps of sliced download."""

  def __init__(
      self,
      source_resource,
      temporary_destination_resource,
      final_destination_resource,
      delete_source=False,
      do_not_decompress=False,
      posix_to_set=None,
      print_created_message=False,
      system_posix_data=None,
      user_request_args=None,
  ):
    """Initializes task.

    Args:
      source_resource (resource_reference.ObjectResource): Should contain
        object's metadata for checking content encoding.
      temporary_destination_resource (resource_reference.FileObjectResource):
        Must contain a local path to the temporary file written to during
        transfers.
      final_destination_resource (resource_reference.FileObjectResource): Must
        contain local filesystem path to the final download destination.
      delete_source (bool): If copy completes successfully, delete the source
        object afterwards.
      do_not_decompress (bool): Prevents automatically decompressing downloaded
        gzips.
      posix_to_set (PosixAttributes|None): See parent class.
      print_created_message (bool): See parent class.
      system_posix_data (SystemPosixData): System-wide POSIX info.
      user_request_args (UserRequestArgs|None): See parent class.
    """
    super(FinalizeSlicedDownloadTask, self).__init__(
        source_resource,
        final_destination_resource,
        posix_to_set=posix_to_set,
        print_created_message=print_created_message,
        user_request_args=user_request_args,
    )
    self._temporary_destination_resource = temporary_destination_resource
    self._final_destination_resource = final_destination_resource
    self._delete_source = delete_source
    self._do_not_decompress = do_not_decompress
    self._system_posix_data = system_posix_data

  def execute(self, task_status_queue=None):
    """Validates and clean ups after sliced download."""
    component_error_occurred = False
    for message in self.received_messages:
      if message.topic is task.Topic.ERROR:
        log.error(message.payload)
        component_error_occurred = True
    if component_error_occurred:
      raise errors.Error(
          'Failed to download one or more component of sliced download.')

    temporary_object_path = (
        self._temporary_destination_resource.storage_url.object_name)
    final_destination_object_path = (
        self._final_destination_resource.storage_url.object_name)
    if (properties.VALUES.storage.check_hashes.Get() !=
        properties.CheckHashes.NEVER.value and
        self._source_resource.crc32c_hash):

      component_payloads = [
          message.payload
          for message in self.received_messages
          if message.topic == task.Topic.CRC32C
      ]
      if component_payloads:
        # Returns list of payload values sorted by component number.
        sorted_component_payloads = sorted(
            component_payloads, key=lambda d: d['component_number'])

        downloaded_file_checksum = sorted_component_payloads[0][
            'crc32c_checksum']
        for i in range(1, len(sorted_component_payloads)):
          payload = sorted_component_payloads[i]
          downloaded_file_checksum = crc32c.concat_checksums(
              downloaded_file_checksum,
              payload['crc32c_checksum'],
              b_byte_count=payload['length'])

        downloaded_file_hash_object = crc32c.get_crc32c_from_checksum(
            downloaded_file_checksum)
        downloaded_file_hash_digest = crc32c.get_hash(
            downloaded_file_hash_object)

        download_util.validate_download_hash_and_delete_corrupt_files(
            temporary_object_path, self._source_resource.crc32c_hash,
            downloaded_file_hash_digest)

    preserve_symlinks = symlink_util.get_preserve_symlink_from_user_request(
        self._user_request_args
    )
    download_util.finalize_download(
        self._source_resource,
        temporary_object_path,
        final_destination_object_path,
        convert_symlinks=preserve_symlinks,
        do_not_decompress_flag=self._do_not_decompress,
    )
    tracker_file_util.delete_download_tracker_files(
        self._temporary_destination_resource.storage_url)

    posix_util.run_if_setting_posix(
        self._posix_to_set,
        self._user_request_args,
        posix_util.set_posix_attributes_on_file_if_valid,
        self._system_posix_data,
        self._source_resource,
        self._final_destination_resource,
        known_source_posix=self._posix_to_set,
        preserve_symlinks=preserve_symlinks,
    )

    self._print_created_message_if_requested(self._final_destination_resource)
    if self._send_manifest_messages:
      # Does not send md5_hash because sliced download uses CRC32C.
      manifest_util.send_success_message(
          task_status_queue,
          self._source_resource,
          self._final_destination_resource,
      )

    if self._delete_source:
      return task.Output(
          additional_task_iterators=[[
              delete_task.DeleteObjectTask(self._source_resource.storage_url),
          ]],
          messages=None,
      )
