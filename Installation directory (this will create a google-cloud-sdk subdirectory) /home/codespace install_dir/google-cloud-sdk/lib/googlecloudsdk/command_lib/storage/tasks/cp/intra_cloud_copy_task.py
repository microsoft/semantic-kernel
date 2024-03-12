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

"""Task for copying an object around the cloud.

Typically executed in a task iterator:
googlecloudsdk.command_lib.storage.tasks.task_executor.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import threading

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import request_config_factory
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import manifest_util
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.cp import copy_util
from googlecloudsdk.command_lib.storage.tasks.rm import delete_task
from googlecloudsdk.core import log


class IntraCloudCopyTask(copy_util.ObjectCopyTaskWithExitHandler):
  """Represents a command operation copying an object around the cloud."""

  def __init__(
      self,
      source_resource,
      destination_resource,
      delete_source=False,
      fetch_source_fields_scope=None,
      posix_to_set=None,
      print_created_message=False,
      print_source_version=False,
      user_request_args=None,
      verbose=False,
  ):
    """Initializes task.

    Args:
      source_resource (resource_reference.Resource): Must contain the full
        object path. Directories will not be accepted.
      destination_resource (resource_reference.Resource): Must contain the full
        object path. Directories will not be accepted. Existing objects at the
        this location will be overwritten.
      delete_source (bool): If copy completes successfully, delete the source
        object afterwards.
      fetch_source_fields_scope (FieldsScope|None): If present, refetch
        source_resource, populated with metadata determined by this FieldsScope.
        Useful for lazy or parallelized GET calls.
      posix_to_set (PosixAttributes|None): See parent class.
      print_created_message (bool): See parent class.
      print_source_version (bool): See parent class.
      user_request_args (UserRequestArgs|None): See parent class
      verbose (bool): See parent class.
    """
    super(IntraCloudCopyTask, self).__init__(
        source_resource,
        destination_resource,
        posix_to_set=posix_to_set,
        print_created_message=print_created_message,
        print_source_version=print_source_version,
        user_request_args=user_request_args,
        verbose=verbose,
    )

    if ((source_resource.storage_url.scheme
         != destination_resource.storage_url.scheme)
        or not isinstance(source_resource.storage_url,
                          storage_url.CloudUrl)):
      raise errors.InvalidUrlError(
          'IntraCloudCopyTask takes two URLs from the same cloud provider.'
      )

    self._delete_source = delete_source
    self._fetch_source_fields_scope = fetch_source_fields_scope

    self.parallel_processing_key = (
        self._destination_resource.storage_url.url_string)

  def execute(self, task_status_queue=None):
    api_client = api_factory.get_api(self._source_resource.storage_url.scheme)
    if copy_util.check_for_cloud_clobber(self._user_request_args, api_client,
                                         self._destination_resource):
      log.status.Print(
          copy_util.get_no_clobber_message(
              self._destination_resource.storage_url))
      if self._send_manifest_messages:
        manifest_util.send_skip_message(
            task_status_queue, self._source_resource,
            self._destination_resource,
            copy_util.get_no_clobber_message(
                self._destination_resource.storage_url))
      return

    progress_callback = progress_callbacks.FilesAndBytesProgressCallback(
        status_queue=task_status_queue,
        offset=0,
        length=self._source_resource.size,
        source_url=self._source_resource.storage_url,
        destination_url=self._destination_resource.storage_url,
        operation_name=task_status.OperationName.INTRA_CLOUD_COPYING,
        process_id=os.getpid(),
        thread_id=threading.get_ident(),
    )

    if self._fetch_source_fields_scope:
      copy_source = api_client.get_object_metadata(
          self._source_resource.bucket,
          self._source_resource.name,
          generation=self._source_resource.generation,
          fields_scope=self._fetch_source_fields_scope,
      )
    else:
      copy_source = self._source_resource

    request_config = request_config_factory.get_request_config(
        self._destination_resource.storage_url,
        decryption_key_hash_sha256=(
            self._source_resource.decryption_key_hash_sha256),
        user_request_args=self._user_request_args)
    result_resource = api_client.copy_object(
        copy_source,
        self._destination_resource,
        request_config,
        posix_to_set=self._posix_to_set,
        progress_callback=progress_callback,
    )

    self._print_created_message_if_requested(result_resource)
    if self._send_manifest_messages:
      manifest_util.send_success_message(
          task_status_queue,
          self._source_resource,
          self._destination_resource,
          md5_hash=result_resource.md5_hash)
    if self._delete_source:
      return task.Output(
          additional_task_iterators=[
              [delete_task.DeleteObjectTask(self._source_resource.storage_url)]
          ],
          messages=None,
      )

  def __eq__(self, other):
    if not isinstance(other, IntraCloudCopyTask):
      return NotImplemented
    return (
        self._source_resource == other._source_resource
        and self._destination_resource == other._destination_resource
        and self._delete_source == other._delete_source
        and self._fetch_source_fields_scope == other._fetch_source_fields_scope
        and self._posix_to_set == other._posix_to_set
        and self._print_created_message == other._print_created_message
        and self._print_source_version == other._print_source_version
        and self._user_request_args == other._user_request_args
        and self._verbose == other._verbose
    )
