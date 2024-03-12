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
"""Task for file downloads.

Typically executed in a task iterator:
googlecloudsdk.command_lib.storage.tasks.task_executor.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import threading

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import request_config_factory
from googlecloudsdk.command_lib.storage import fast_crc32c_util
from googlecloudsdk.command_lib.storage import hash_util
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage import tracker_file_util
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.cp import copy_component_util
from googlecloudsdk.command_lib.storage.tasks.cp import download_util
from googlecloudsdk.command_lib.storage.tasks.cp import file_part_task
from googlecloudsdk.command_lib.util import crc32c
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import hashing


_READ_SIZE = 8192  # 8 KiB.
NULL_BYTE = b'\x00'


def _get_first_null_byte_index(destination_url, offset, length):
  """Checks to see how many bytes in range have already been downloaded.

  Args:
    destination_url (storage_url.FileUrl): Has path of file being downloaded.
    offset (int): For components, index to start reading bytes at.
    length (int): For components, where to stop reading bytes.

  Returns:
    Int byte count of size of partially-downloaded file. Returns 0 if file is
    an invalid size, empty, or non-existent.
  """
  if not destination_url.exists():
    return 0

  # Component is slice of larger file. Find how much of slice is downloaded.
  first_null_byte = offset
  end_of_range = offset + length
  with files.BinaryFileReader(destination_url.object_name) as file_reader:
    file_reader.seek(offset)
    while first_null_byte < end_of_range:
      data = file_reader.read(_READ_SIZE)
      if not data:
        break
      null_byte_index = data.find(NULL_BYTE)
      if null_byte_index != -1:
        first_null_byte += null_byte_index
        break
      first_null_byte += len(data)
  return first_null_byte


def _get_digesters(component_number, resource):
  """Returns digesters dictionary for download hash validation.

  Note: The digester object is not picklable. It cannot be passed between
  tasks through the task graph.

  Args:
    component_number (int|None): Used to determine if downloading a slice in a
      sliced download, which uses CRC32C for hashing.
    resource (resource_reference.ObjectResource): For checking if object has
      known hash to validate against.

  Returns:
    Digesters dict.

  Raises:
    errors.Error: gcloud storage set to fail if performance-optimized digesters
      could not be created.
  """
  digesters = {}
  check_hashes = properties.VALUES.storage.check_hashes.Get()
  if check_hashes != properties.CheckHashes.NEVER.value:
    if component_number is None and resource.md5_hash:
      digesters[hash_util.HashAlgorithm.MD5] = hashing.get_md5()
    elif resource.crc32c_hash and (
        check_hashes == properties.CheckHashes.ALWAYS.value
        or fast_crc32c_util.check_if_will_use_fast_crc32c(
            install_if_missing=True
        )
    ):
      digesters[hash_util.HashAlgorithm.CRC32C] = fast_crc32c_util.get_crc32c()

  if not digesters:
    log.warning(
        'Found no hashes to validate download of object: %s.'
        ' Integrity cannot be assured without hashes.', resource)

  return digesters


class FilePartDownloadTask(file_part_task.FilePartTask):
  """Downloads a byte range."""

  def __init__(self,
               source_resource,
               destination_resource,
               offset,
               length,
               component_number=None,
               total_components=None,
               do_not_decompress=False,
               strategy=cloud_api.DownloadStrategy.RETRIABLE_IN_FLIGHT,
               user_request_args=None):
    """Initializes task.

    Args:
      source_resource (resource_reference.ObjectResource): Must contain the full
        path of object to download, including bucket. Directories will not be
        accepted. Does not need to contain metadata.
      destination_resource (resource_reference.FileObjectResource): Must contain
        local filesystem path to upload object. Does not need to contain
        metadata.
      offset (int): The index of the first byte in the upload range.
      length (int): The number of bytes in the upload range.
      component_number (int|None): If a multipart operation, indicates the
        component number.
      total_components (int|None): If a multipart operation, indicates the total
        number of components.
      do_not_decompress (bool): Prevents automatically decompressing
        downloaded gzips.
      strategy (cloud_api.DownloadStrategy): Determines what download
        implementation to use.
      user_request_args (UserRequestArgs|None): Values for RequestConfig.
    """
    super(FilePartDownloadTask,
          self).__init__(source_resource, destination_resource, offset, length,
                         component_number, total_components)
    self._do_not_decompress_flag = do_not_decompress
    self._strategy = strategy
    self._user_request_args = user_request_args

  def _calculate_deferred_hashes(self, digesters):
    """DeferredCrc32c does not hash on-the-fly and needs a summation call."""
    if isinstance(
        digesters.get(hash_util.HashAlgorithm.CRC32C),
        fast_crc32c_util.DeferredCrc32c,
    ):
      digesters[hash_util.HashAlgorithm.CRC32C].sum_file(
          self._destination_resource.storage_url.object_name,
          self._offset,
          self._length,
      )

  def _disable_in_flight_decompression(self, is_resumable_or_sliced_download):
    """Whether or not to disable on-the-fly decompression."""
    if self._do_not_decompress_flag:
      # Respect user preference.
      return True
    if not is_resumable_or_sliced_download:
      # If we don't decompress in-flight, we'll do it later on the disk, which
      # is probably slower. However, the requests library might add the
      # "accept-encoding: gzip" header anyways.
      return False
    # Decompressing in flight changes file size, making resumable and sliced
    # downloads impossible.
    return bool(self._source_resource.content_encoding and
                'gzip' in self._source_resource.content_encoding)

  def _perform_download(self, request_config, progress_callback,
                        do_not_decompress, download_strategy, start_byte,
                        end_byte, write_mode, digesters):
    """Prepares file stream, calls API, and validates hash."""
    with files.BinaryFileWriter(
        self._destination_resource.storage_url.object_name,
        create_path=True,
        mode=write_mode,
        convert_invalid_windows_characters=(
            properties.VALUES.storage
            .convert_incompatible_windows_path_characters.GetBool()
        )) as download_stream:
      download_stream.seek(start_byte)
      provider = self._source_resource.storage_url.scheme
      # TODO(b/162264437): Support all of download_object's parameters.
      api_download_result = api_factory.get_api(provider).download_object(
          self._source_resource,
          download_stream,
          request_config,
          digesters=digesters,
          do_not_decompress=do_not_decompress,
          download_strategy=download_strategy,
          progress_callback=progress_callback,
          start_byte=start_byte,
          end_byte=end_byte)

    self._calculate_deferred_hashes(digesters)
    if hash_util.HashAlgorithm.MD5 in digesters:
      calculated_digest = hash_util.get_base64_hash_digest_string(
          digesters[hash_util.HashAlgorithm.MD5])
      download_util.validate_download_hash_and_delete_corrupt_files(
          self._destination_resource.storage_url.object_name,
          self._source_resource.md5_hash, calculated_digest)
    elif hash_util.HashAlgorithm.CRC32C in digesters:
      # Only for one-shot composite object downloads as final CRC32C validated
      # in FinalizeSlicedDownloadTask.
      if self._component_number is None:
        calculated_digest = crc32c.get_hash(
            digesters[hash_util.HashAlgorithm.CRC32C])
        download_util.validate_download_hash_and_delete_corrupt_files(
            self._destination_resource.storage_url.object_name,
            self._source_resource.crc32c_hash, calculated_digest)

    return api_download_result

  def _perform_retriable_download(self, request_config, progress_callback,
                                  digesters):
    """Sets up a basic download based on task attributes."""
    start_byte = self._offset
    end_byte = self._offset + self._length - 1

    return self._perform_download(
        request_config, progress_callback,
        self._disable_in_flight_decompression(False),
        cloud_api.DownloadStrategy.RETRIABLE_IN_FLIGHT, start_byte, end_byte,
        files.BinaryFileWriterMode.TRUNCATE, digesters)

  def _catch_up_digesters(self, digesters, start_byte, end_byte):
    """Gets hash of partially-downloaded file as start for validation."""
    for hash_algorithm in digesters:
      if isinstance(digesters[hash_algorithm], fast_crc32c_util.DeferredCrc32c):
        # Deferred calculation runs at end, no on-the-fly.
        continue
      digesters[hash_algorithm] = hash_util.get_hash_from_file(
          self._destination_resource.storage_url.object_name,
          hash_algorithm,
          start=start_byte,
          stop=end_byte,
      )

  def _perform_resumable_download(self, request_config, progress_callback,
                                  digesters):
    """Resume or start download that can be resumabled."""
    copy_component_util.create_file_if_needed(self._source_resource,
                                              self._destination_resource)

    destination_url = self._destination_resource.storage_url
    first_null_byte = _get_first_null_byte_index(destination_url,
                                                 self._offset, self._length)
    _, found_tracker_file = (
        tracker_file_util.read_or_create_download_tracker_file(
            self._source_resource, destination_url))
    start_byte = first_null_byte if found_tracker_file else 0
    end_byte = self._source_resource.size - 1

    if start_byte:
      write_mode = files.BinaryFileWriterMode.MODIFY
      self._catch_up_digesters(digesters, start_byte=0, end_byte=start_byte)
      log.status.Print('Resuming download for {}'.format(self._source_resource))
    else:
      # TRUNCATE can create new file unlike MODIFY.
      write_mode = files.BinaryFileWriterMode.TRUNCATE

    return self._perform_download(request_config, progress_callback,
                                  self._disable_in_flight_decompression(True),
                                  cloud_api.DownloadStrategy.RESUMABLE,
                                  start_byte, end_byte, write_mode, digesters)

  def _get_output(self, digesters, server_encoding):
    """Generates task.Output from download execution results.

    Args:
      digesters (dict): Contains hash objects for download checksums.
      server_encoding (str|None): Generic information from API client about the
        download results.

    Returns:
      task.Output: Data the parent download or finalize download class would
        like to have.
    """
    messages = []
    if hash_util.HashAlgorithm.MD5 in digesters:
      md5_digest = hash_util.get_base64_hash_digest_string(
          digesters[hash_util.HashAlgorithm.MD5])
      messages.append(task.Message(topic=task.Topic.MD5, payload=md5_digest))

    if hash_util.HashAlgorithm.CRC32C in digesters:
      crc32c_checksum = crc32c.get_checksum(
          digesters[hash_util.HashAlgorithm.CRC32C])
      messages.append(
          task.Message(
              topic=task.Topic.CRC32C,
              payload={
                  'component_number': self._component_number,
                  'crc32c_checksum': crc32c_checksum,
                  'length': self._length,
              }))

    if server_encoding:
      messages.append(
          task.Message(
              topic=task.Topic.API_DOWNLOAD_RESULT, payload=server_encoding
          )
      )

    return task.Output(additional_task_iterators=None, messages=messages)

  def _perform_component_download(self, request_config, progress_callback,
                                  digesters):
    """Component download does not validate hash or delete tracker."""
    destination_url = self._destination_resource.storage_url
    end_byte = self._offset + self._length - 1

    if self._strategy == cloud_api.DownloadStrategy.RESUMABLE:
      _, found_tracker_file = (
          tracker_file_util.read_or_create_download_tracker_file(
              self._source_resource,
              destination_url,
              slice_start_byte=self._offset,
              component_number=self._component_number))
      first_null_byte = _get_first_null_byte_index(
          destination_url, offset=self._offset, length=self._length)
      start_byte = first_null_byte if found_tracker_file else self._offset

      if start_byte > end_byte:
        log.status.Print('{} component {} already downloaded.'.format(
            self._source_resource, self._component_number))
        self._calculate_deferred_hashes(digesters)
        self._catch_up_digesters(
            digesters,
            start_byte=self._offset,
            end_byte=self._source_resource.size)
        return
      if found_tracker_file and start_byte != self._offset:
        self._catch_up_digesters(
            digesters, start_byte=self._offset, end_byte=start_byte)
        log.status.Print('Resuming download for {} component {}'.format(
            self._source_resource, self._component_number))
    else:
      # For non-resumable sliced downloads.
      start_byte = self._offset

    return self._perform_download(request_config, progress_callback,
                                  self._disable_in_flight_decompression(True),
                                  self._strategy, start_byte, end_byte,
                                  files.BinaryFileWriterMode.MODIFY, digesters)

  def execute(self, task_status_queue=None):
    """Performs download."""
    digesters = _get_digesters(self._component_number, self._source_resource)

    progress_callback = progress_callbacks.FilesAndBytesProgressCallback(
        status_queue=task_status_queue,
        offset=self._offset,
        length=self._length,
        source_url=self._source_resource.storage_url,
        destination_url=self._destination_resource.storage_url,
        component_number=self._component_number,
        total_components=self._total_components,
        operation_name=task_status.OperationName.DOWNLOADING,
        process_id=os.getpid(),
        thread_id=threading.get_ident(),
    )

    request_config = request_config_factory.get_request_config(
        self._source_resource.storage_url,
        decryption_key_hash_sha256=(
            self._source_resource.decryption_key_hash_sha256),
        user_request_args=self._user_request_args,
    )

    if self._source_resource.size and self._component_number is not None:
      try:
        server_encoding = self._perform_component_download(
            request_config, progress_callback, digesters
        )
      # pylint:disable=broad-except
      except Exception as e:
        # pylint:enable=broad-except
        return task.Output(
            additional_task_iterators=None,
            messages=[task.Message(topic=task.Topic.ERROR, payload=e)])

    elif self._strategy is cloud_api.DownloadStrategy.RESUMABLE:
      server_encoding = self._perform_resumable_download(
          request_config, progress_callback, digesters
      )
    else:
      server_encoding = self._perform_retriable_download(
          request_config, progress_callback, digesters
      )
    return self._get_output(digesters, server_encoding)
