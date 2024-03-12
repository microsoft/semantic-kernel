# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Task for streaming uploads."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import request_config_factory
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import user_request_args_factory
from googlecloudsdk.command_lib.storage.tasks.cp import copy_util
from googlecloudsdk.command_lib.storage.tasks.cp import upload_util


class StreamingUploadTask(copy_util.ObjectCopyTask):
  """Represents a command operation triggering a streaming upload."""

  def __init__(
      self,
      source_resource,
      destination_resource,
      posix_to_set=None,
      print_created_message=False,
      print_source_version=False,
      user_request_args=None,
      verbose=False,
  ):
    """Initializes task.

    Args:
      source_resource (FileObjectResource): Points to the stream or named pipe
        to read from.
      destination_resource (UnknownResource|ObjectResource): The full path of
        object to upload to.
      posix_to_set (PosixAttributes|None): See parent class.
      print_created_message (bool): See parent class.
      print_source_version (bool): See parent class.
      user_request_args (UserRequestArgs|None): See parent class.
      verbose (bool): See parent class.
    """
    super(StreamingUploadTask, self).__init__(
        source_resource,
        destination_resource,
        posix_to_set=posix_to_set,
        print_created_message=print_created_message,
        print_source_version=print_source_version,
        user_request_args=user_request_args,
        verbose=verbose,
    )
    self._source_resource = source_resource
    self._destination_resource = destination_resource

  def execute(self, task_status_queue=None):
    """Runs upload from stream."""
    request_config = request_config_factory.get_request_config(
        self._destination_resource.storage_url,
        content_type=upload_util.get_content_type(
            self._source_resource.storage_url.object_name, is_stream=True),
        md5_hash=self._source_resource.md5_hash,
        user_request_args=self._user_request_args)

    if getattr(request_config, 'gzip_settings', None):
      gzip_type = getattr(request_config.gzip_settings, 'type', None)
      if gzip_type is user_request_args_factory.GzipType.LOCAL:
        # TODO(b/202729249): Can support this after dropping Python 2.
        raise errors.Error(
            'Gzip content encoding is not currently supported for streaming'
            ' uploads. Remove the compression flag or save the streamed output'
            ' to a file before uploading.')

    digesters = upload_util.get_digesters(
        self._source_resource,
        self._destination_resource)
    stream = upload_util.get_stream(
        self._source_resource,
        digesters=digesters,
        task_status_queue=task_status_queue,
        destination_resource=self._destination_resource)

    with stream:
      provider = self._destination_resource.storage_url.scheme
      uploaded_object_resource = api_factory.get_api(provider).upload_object(
          source_stream=stream,
          destination_resource=self._destination_resource,
          request_config=request_config,
          posix_to_set=self._posix_to_set,
          source_resource=self._source_resource,
          upload_strategy=cloud_api.UploadStrategy.STREAMING,
      )

    upload_util.validate_uploaded_object(
        digesters,
        uploaded_object_resource,
        task_status_queue)
    self._print_created_message_if_requested(uploaded_object_resource)
