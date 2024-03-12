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
"""Task for streaming downloads.

Typically executed in a task iterator:
googlecloudsdk.command_lib.storage.tasks.task_executor.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import sys
import threading

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import request_config_factory
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.cp import copy_util


class StreamingDownloadTask(copy_util.ObjectCopyTask):
  """Represents a command operation triggering a streaming download."""

  def __init__(
      self,
      source_resource,
      destination_resource,
      download_stream,
      print_created_message=False,
      print_source_version=False,
      show_url=False,
      start_byte=0,
      end_byte=None,
      user_request_args=None,
      verbose=False,
  ):
    """Initializes task.

    Args:
      source_resource (ObjectResource): Must contain the full path of object to
        download, including bucket. Directories will not be accepted. Does not
        need to contain metadata.
      destination_resource (resource_reference.Resource): Target resource to
        copy to. In this case, it contains the path of the destination stream or
        '-' for stdout.
      download_stream (stream): Reusable stream to write download to.
      print_created_message (bool): See parent class.
      print_source_version (bool): See parent class.
      show_url (bool): Says whether or not to print the header before each
        object's content
      start_byte (int): The byte index to start streaming from.
      end_byte (int|None): The byte index to stop streaming from.
      user_request_args (UserRequestArgs|None): See parent class.
      verbose (bool): See parent class.
    """
    super(StreamingDownloadTask, self).__init__(
        source_resource,
        destination_resource,
        print_created_message=print_created_message,
        print_source_version=print_source_version,
        user_request_args=user_request_args,
        verbose=verbose,
    )
    self._download_stream = download_stream
    self._show_url = show_url
    self._start_byte = start_byte
    self._end_byte = end_byte

  def execute(self, task_status_queue=None):
    if self._show_url:
      sys.stderr.write('==> {} <==\n'.format(self._source_resource))
    if task_status_queue:
      progress_callback = progress_callbacks.FilesAndBytesProgressCallback(
          status_queue=task_status_queue,
          offset=0,
          length=self._source_resource.size,
          source_url=self._source_resource.storage_url,
          destination_url=self._download_stream.name,
          operation_name=task_status.OperationName.DOWNLOADING,
          process_id=os.getpid(),
          thread_id=threading.get_ident(),
      )
    else:
      progress_callback = None

    if (self._source_resource.size and
        self._start_byte >= self._source_resource.size):
      if progress_callback:
        progress_callback(self._source_resource.size)
      return

    request_config = request_config_factory.get_request_config(
        self._source_resource.storage_url,
        decryption_key_hash_sha256=(
            self._source_resource.decryption_key_hash_sha256),
        user_request_args=self._user_request_args,
    )

    provider = self._source_resource.storage_url.scheme
    api_factory.get_api(provider).download_object(
        self._source_resource,
        self._download_stream,
        request_config,
        download_strategy=cloud_api.DownloadStrategy.ONE_SHOT,
        progress_callback=progress_callback,
        start_byte=self._start_byte,
        end_byte=self._end_byte)
    self._download_stream.flush()
    self._print_created_message_if_requested(self._destination_resource)

  def __eq__(self, other):
    if not isinstance(other, self.__class__):
      return NotImplemented
    return (
        self._source_resource == other._source_resource
        and self._destination_resource == other._destination_resource
        and self._download_stream == other._download_stream
        and self._print_created_message == other._print_created_message
        and self._user_request_args == other._user_request_args
        and self._show_url == other._show_url
        and self._start_byte == other._start_byte
        and self._end_byte == other._end_byte
    )
