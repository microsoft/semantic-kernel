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
"""Contains logic for finalizing composite uploads."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import manifest_util
from googlecloudsdk.command_lib.storage import tracker_file_util
from googlecloudsdk.command_lib.storage.tasks import compose_objects_task
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.command_lib.storage.tasks import task_util
from googlecloudsdk.command_lib.storage.tasks.cp import copy_util
from googlecloudsdk.command_lib.storage.tasks.cp import delete_temporary_components_task


class FinalizeCompositeUploadTask(copy_util.ObjectCopyTaskWithExitHandler):
  """Composes and deletes object resources received as messages."""

  def __init__(
      self,
      expected_component_count,
      source_resource,
      destination_resource,
      delete_source=False,
      posix_to_set=None,
      print_created_message=False,
      random_prefix='',
      temporary_paths_to_clean_up=None,
      user_request_args=None,
  ):
    """Initializes task.

    Args:
      expected_component_count (int): Number of temporary components expected.
      source_resource (resource_reference.FileObjectResource): The local
        uploaded file.
      destination_resource (resource_reference.UnknownResource): Metadata for
        the final composite object.
      delete_source (bool): If copy completes successfully, delete the source
        object afterwards.
      posix_to_set (PosixAttributes|None): See parent class.
      print_created_message (bool): See parent class.
      random_prefix (str): Random id added to component names.
      temporary_paths_to_clean_up (str): Paths to remove after the composite
        upload completes. This may include a temporary gzipped version of the
        source, or symlink placeholders.
      user_request_args (UserRequestArgs|None): See parent class.
    """
    super(FinalizeCompositeUploadTask, self).__init__(
        source_resource,
        destination_resource,
        posix_to_set=posix_to_set,
        print_created_message=print_created_message,
        user_request_args=user_request_args,
    )
    self._expected_component_count = expected_component_count
    self._delete_source = delete_source
    self._random_prefix = random_prefix
    self._temporary_paths_to_clean_up = temporary_paths_to_clean_up

  def execute(self, task_status_queue=None):
    uploaded_components = [
        message.payload
        for message in self.received_messages
        if message.topic == task.Topic.UPLOADED_COMPONENT
    ]

    if len(uploaded_components) != self._expected_component_count:
      raise errors.Error(
          'Temporary components were not uploaded correctly.'
          ' Please retry this upload.'
      )

    uploaded_objects = [
        component.object_resource
        for component in sorted(
            uploaded_components,
            key=lambda component: component.component_number)
    ]

    compose_task = compose_objects_task.ComposeObjectsTask(
        uploaded_objects,
        self._destination_resource,
        original_source_resource=self._source_resource,
        posix_to_set=self._posix_to_set,
        user_request_args=self._user_request_args,
    )
    compose_task_output = compose_task.execute(
        task_status_queue=task_status_queue
    )

    result_resource = task_util.get_first_matching_message_payload(
        compose_task_output.messages, task.Topic.CREATED_RESOURCE
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

    # After a successful compose call, we consider the upload complete and can
    # delete tracker files.
    tracker_file_path = tracker_file_util.get_tracker_file_path(
        self._destination_resource.storage_url,
        tracker_file_util.TrackerFileType.PARALLEL_UPLOAD,
        source_url=self._source_resource,
    )
    tracker_file_util.delete_tracker_file(tracker_file_path)

    for path in self._temporary_paths_to_clean_up or []:
      os.remove(path)
    if self._delete_source:
      # Delete original source file.
      os.remove(self._source_resource.storage_url.object_name)

    return task.Output(
        additional_task_iterators=[
            [
                delete_temporary_components_task.DeleteTemporaryComponentsTask(
                    self._source_resource,
                    self._destination_resource,
                    self._random_prefix,
                )
            ]
        ],
        messages=None,
    )

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return NotImplemented
    return (
        self._expected_component_count == other._expected_component_count
        and self._source_resource == other._source_resource
        and self._destination_resource == other._destination_resource
        and self._random_prefix == other._random_prefix
        and self._temporary_paths_to_clean_up
        == other._temporary_paths_to_clean_up
        and self._user_request_args == other._user_request_args
    )
