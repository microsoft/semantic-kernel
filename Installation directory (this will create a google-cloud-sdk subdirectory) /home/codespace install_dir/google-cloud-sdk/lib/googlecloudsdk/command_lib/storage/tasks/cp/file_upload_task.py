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

"""Task for file uploads.

Typically executed in a task iterator:
googlecloudsdk.command_lib.storage.tasks.task_executor.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import random

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.command_lib.storage import gzip_util
from googlecloudsdk.command_lib.storage import manifest_util
from googlecloudsdk.command_lib.storage import symlink_util
from googlecloudsdk.command_lib.storage import tracker_file_util
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.command_lib.storage.tasks import task_util
from googlecloudsdk.command_lib.storage.tasks.cp import copy_component_util
from googlecloudsdk.command_lib.storage.tasks.cp import copy_util
from googlecloudsdk.command_lib.storage.tasks.cp import file_part_upload_task
from googlecloudsdk.command_lib.storage.tasks.cp import finalize_composite_upload_task
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


def _get_random_prefix():
  """Returns an ID distinguishing upload components from different machines."""
  return str(random.randint(1, 10**10))


class FileUploadTask(copy_util.ObjectCopyTaskWithExitHandler):
  """Represents a command operation triggering a file upload."""

  def __init__(
      self,
      source_resource,
      destination_resource,
      delete_source=False,
      is_composite_upload_eligible=False,
      posix_to_set=None,
      print_created_message=False,
      print_source_version=False,
      user_request_args=None,
      verbose=False,
  ):
    """Initializes task.

    Args:
      source_resource (resource_reference.FileObjectResource): Must contain
        local filesystem path to upload object. Does not need to contain
        metadata.
      destination_resource (resource_reference.ObjectResource|UnknownResource):
        Must contain the full object path. Directories will not be accepted.
        Existing objects at the this location will be overwritten.
      delete_source (bool): If copy completes successfully, delete the source
        object afterwards.
      is_composite_upload_eligible (bool): If True, parallel composite upload
        may be performed.
      posix_to_set (PosixAttributes|None): See parent class.
      print_created_message (bool): See parent class.
      print_source_version (bool): See parent class.
      user_request_args (UserRequestArgs|None): See parent class.
      verbose (bool): See parent class.
    """
    super(FileUploadTask, self).__init__(
        source_resource,
        destination_resource,
        posix_to_set=posix_to_set,
        print_created_message=print_created_message,
        print_source_version=print_source_version,
        user_request_args=user_request_args,
        verbose=verbose,
    )
    self._delete_source = delete_source
    self._is_composite_upload_eligible = is_composite_upload_eligible

    self.parallel_processing_key = (
        self._destination_resource.storage_url.url_string
    )

  def _perform_single_transfer(
      self,
      size,
      source_path,
      task_status_queue,
      temporary_paths_to_clean_up,
  ):
    task_output = file_part_upload_task.FilePartUploadTask(
        self._source_resource,
        self._destination_resource,
        source_path,
        offset=0,
        length=size,
        posix_to_set=self._posix_to_set,
        user_request_args=self._user_request_args,
    ).execute(task_status_queue)
    result_resource = task_util.get_first_matching_message_payload(
        task_output.messages, task.Topic.CREATED_RESOURCE
    )
    if result_resource:
      self._print_created_message_if_requested(result_resource)
      if self._send_manifest_messages:
        manifest_util.send_success_message(
            task_status_queue,
            self._source_resource,
            self._destination_resource,
            md5_hash=result_resource.md5_hash,
        )

    for path in temporary_paths_to_clean_up:
      os.remove(path)

    if self._delete_source:
      # Delete original source file.
      os.remove(self._source_resource.storage_url.object_name)

  def _perform_composite_upload(
      self,
      api_client,
      component_count,
      size,
      source_path,
      task_status_queue,
      temporary_paths_to_clean_up,
  ):
    tracker_file_path = tracker_file_util.get_tracker_file_path(
        self._destination_resource.storage_url,
        tracker_file_util.TrackerFileType.PARALLEL_UPLOAD,
        source_url=self._source_resource.storage_url,
    )
    tracker_data = tracker_file_util.read_composite_upload_tracker_file(
        tracker_file_path
    )

    if tracker_data:
      random_prefix = tracker_data.random_prefix
    else:
      random_prefix = _get_random_prefix()

    component_offsets_and_lengths = (
        copy_component_util.get_component_offsets_and_lengths(
            size, component_count
        )
    )
    temporary_component_resources = []
    for i in range(len(component_offsets_and_lengths)):
      temporary_component_resource = (
          copy_component_util.get_temporary_component_resource(
              self._source_resource,
              self._destination_resource,
              random_prefix,
              i,
          )
      )
      temporary_component_resources.append(temporary_component_resource)

      component_name_length = len(
          temporary_component_resource.storage_url.object_name.encode()
      )

      if component_name_length > api_client.MAX_OBJECT_NAME_LENGTH:
        log.warning(
            'Performing a non-composite upload for {}, as a temporary'
            ' component resource would have a name of length {}. This is'
            ' longer than the maximum object name length supported by this'
            ' API: {} UTF-8 encoded bytes. You may be able to change the'
            ' storage/parallel_composite_upload_prefix config option to perform'
            ' a composite upload with this object.'.format(
                self._source_resource.storage_url,
                component_name_length,
                api_client.MAX_OBJECT_NAME_LENGTH,
            )
        )
        return self._perform_single_transfer(
            size,
            source_path,
            task_status_queue,
            temporary_paths_to_clean_up,
        )

    file_part_upload_tasks = []
    for i, (offset, length) in enumerate(component_offsets_and_lengths):
      upload_task = file_part_upload_task.FilePartUploadTask(
          self._source_resource,
          temporary_component_resources[i],
          source_path,
          offset,
          length,
          component_number=i,
          total_components=len(component_offsets_and_lengths),
          user_request_args=self._user_request_args,
      )

      file_part_upload_tasks.append(upload_task)

    finalize_upload_task = (
        finalize_composite_upload_task.FinalizeCompositeUploadTask(
            expected_component_count=len(file_part_upload_tasks),
            source_resource=self._source_resource,
            destination_resource=self._destination_resource,
            delete_source=self._delete_source,
            posix_to_set=self._posix_to_set,
            print_created_message=self._print_created_message,
            random_prefix=random_prefix,
            temporary_paths_to_clean_up=temporary_paths_to_clean_up,
            user_request_args=self._user_request_args,
        )
    )

    tracker_file_util.write_composite_upload_tracker_file(
        tracker_file_path, random_prefix
    )

    return task.Output(
        additional_task_iterators=[
            file_part_upload_tasks,
            [finalize_upload_task],
        ],
        messages=None,
    )

  def _handle_symlink_placeholder_transform(
      self, source_path, temporary_paths_to_clean_up
  ):
    """Create a symlink placeholder if necessary.

    Args:
      source_path (str): The source of the upload.
      temporary_paths_to_clean_up (list[str]): Adds the paths of any temporary
        files created to this list.

    Returns:
      The path to the symlink placeholder if one was created. Otherwise, returns
        source_path.
    """
    should_create_symlink_placeholder = (
        symlink_util.get_preserve_symlink_from_user_request(
            self._user_request_args
        )
        and self._source_resource.is_symlink
    )
    if should_create_symlink_placeholder:
      symlink_path = symlink_util.get_symlink_placeholder_file(
          self._source_resource.storage_url.object_name
      )
      temporary_paths_to_clean_up.append(symlink_path)
      return symlink_path
    else:
      return source_path

  def _handle_gzip_transform(self, source_path, temporary_paths_to_clean_up):
    """Gzip the file at source_path necessary.

    Args:
      source_path (str): The source of the upload.
      temporary_paths_to_clean_up (list[str]): Adds the paths of any temporary
        files created to this list.

    Returns:
      The path to the gzipped temporary file if one was created. Otherwise,
        returns source_path.
    """
    should_gzip_locally = gzip_util.should_gzip_locally(
        getattr(self._user_request_args, 'gzip_settings', None), source_path
    )
    if should_gzip_locally:
      gzip_path = gzip_util.get_temporary_gzipped_file(source_path)
      temporary_paths_to_clean_up.append(gzip_path)
      return gzip_path
    else:
      return source_path

  def execute(self, task_status_queue=None):
    destination_provider = self._destination_resource.storage_url.scheme
    api_client = api_factory.get_api(destination_provider)

    if copy_util.check_for_cloud_clobber(
        self._user_request_args, api_client, self._destination_resource
    ):
      log.status.Print(
          copy_util.get_no_clobber_message(
              self._destination_resource.storage_url
          )
      )
      if self._send_manifest_messages:
        manifest_util.send_skip_message(
            task_status_queue,
            self._source_resource,
            self._destination_resource,
            copy_util.get_no_clobber_message(
                self._destination_resource.storage_url
            ),
        )
      return

    source_url = self._source_resource.storage_url
    temporary_paths_to_clean_up = []
    if source_url.is_stream:
      source_path = source_url.object_name
      size = None
    else:
      symlink_transformed_path = self._handle_symlink_placeholder_transform(
          source_url.object_name,
          temporary_paths_to_clean_up
      )
      source_path = self._handle_gzip_transform(
          symlink_transformed_path,
          temporary_paths_to_clean_up
      )
      size = os.path.getsize(source_path)

    component_count = copy_component_util.get_component_count(
        size,
        properties.VALUES.storage.parallel_composite_upload_component_size.Get(),
        api_client.MAX_OBJECTS_PER_COMPOSE_CALL,
    )
    should_perform_single_transfer = (
        not self._is_composite_upload_eligible
        or not task_util.should_use_parallelism()
        or component_count <= 1
    )

    if should_perform_single_transfer:
      self._perform_single_transfer(
          size, source_path, task_status_queue, temporary_paths_to_clean_up
      )
    else:
      return self._perform_composite_upload(
          api_client,
          component_count,
          size,
          source_path,
          task_status_queue,
          temporary_paths_to_clean_up,
      )
