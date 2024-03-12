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

"""Task for file uploads.

Typically executed in a task iterator:
googlecloudsdk.command_lib.storage.tasks.task_executor.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import functools
import os

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import errors as api_errors
from googlecloudsdk.api_lib.storage import request_config_factory
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import errors as command_errors
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import tracker_file_util
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.command_lib.storage.tasks.cp import file_part_task
from googlecloudsdk.command_lib.storage.tasks.cp import upload_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import retry


UploadedComponent = collections.namedtuple(
    'UploadedComponent',
    ['component_number', 'object_resource']
)


class FilePartUploadTask(file_part_task.FilePartTask):
  """Uploads a range of bytes from a file."""

  def __init__(
      self,
      source_resource,
      destination_resource,
      source_path,
      offset,
      length,
      component_number=None,
      posix_to_set=None,
      total_components=None,
      user_request_args=None,
  ):
    """Initializes task.

    Args:
      source_resource (resource_reference.FileObjectResource): Must contain
        local filesystem path to upload object. Does not need to contain
        metadata.
      destination_resource (resource_reference.ObjectResource|UnknownResource):
        Must contain the full object path. Directories will not be accepted.
        Existing objects at the this location will be overwritten.
      source_path (str): Path to file to upload. May be the original or a
        transformed temporary file.
      offset (int): The index of the first byte in the upload range.
      length (int): The number of bytes in the upload range.
      component_number (int|None): If a multipart operation, indicates the
        component number.
      posix_to_set (PosixAttributes|None): POSIX info set as custom cloud
        metadata on target. If provided and preserving POSIX, skip re-parsing
        from file system.
      total_components (int|None): If a multipart operation, indicates the total
        number of components.
      user_request_args (UserRequestArgs|None): Values for RequestConfig.
    """
    super(FilePartUploadTask,
          self).__init__(source_resource, destination_resource, offset, length,
                         component_number, total_components)
    self._source_path = source_path

    self._posix_to_set = posix_to_set
    self._user_request_args = user_request_args

    self._transformed_source_resource = resource_reference.FileObjectResource(
        storage_url.storage_url_from_string(self._source_path))

  def _get_output(self, destination_resource):
    messages = []
    if self._component_number is not None:
      messages.append(
          task.Message(
              topic=task.Topic.UPLOADED_COMPONENT,
              payload=UploadedComponent(
                  component_number=self._component_number,
                  object_resource=destination_resource)))
    else:
      messages.append(
          task.Message(
              topic=task.Topic.CREATED_RESOURCE, payload=destination_resource))
    return task.Output(additional_task_iterators=None, messages=messages)

  def _existing_destination_is_valid(self, destination_resource):
    """Returns True if a completed temporary component can be reused."""
    digesters = upload_util.get_digesters(
        self._source_resource, destination_resource)
    with upload_util.get_stream(
        self._transformed_source_resource,
        length=self._length,
        offset=self._offset,
        digesters=digesters) as stream:
      stream.seek(0, whence=os.SEEK_END)  # Populates digesters.

    try:
      upload_util.validate_uploaded_object(
          digesters, destination_resource, task_status_queue=None)
      return True
    except command_errors.HashMismatchError:
      return False

  def execute(self, task_status_queue=None):
    """Performs upload."""
    digesters = upload_util.get_digesters(
        self._source_resource, self._destination_resource)
    destination_url = self._destination_resource.storage_url
    provider = destination_url.scheme
    api = api_factory.get_api(provider)
    request_config = request_config_factory.get_request_config(
        destination_url,
        content_type=upload_util.get_content_type(
            self._source_resource.storage_url.object_name,
            self._source_resource.storage_url.is_stream),
        md5_hash=self._source_resource.md5_hash,
        size=self._length,
        user_request_args=self._user_request_args)

    if self._component_number is None:
      source_resource_for_metadata = self._source_resource
    else:
      source_resource_for_metadata = None
      # This disables the Content-MD5 header for multi-part uploads.
      request_config.resource_args.md5_hash = None

    with upload_util.get_stream(
        self._transformed_source_resource,
        length=self._length,
        offset=self._offset,
        digesters=digesters,
        task_status_queue=task_status_queue,
        destination_resource=self._destination_resource,
        component_number=self._component_number,
        total_components=self._total_components) as source_stream:
      upload_strategy = upload_util.get_upload_strategy(api, self._length)
      if upload_strategy == cloud_api.UploadStrategy.RESUMABLE:
        tracker_file_path = tracker_file_util.get_tracker_file_path(
            self._destination_resource.storage_url,
            tracker_file_util.TrackerFileType.UPLOAD,
            component_number=self._component_number)

        complete = False
        encryption_key_hash_sha256 = getattr(
            encryption_util.get_encryption_key(), 'sha256', None)
        tracker_callback = functools.partial(
            tracker_file_util.write_resumable_upload_tracker_file,
            tracker_file_path, complete, encryption_key_hash_sha256)

        tracker_data = tracker_file_util.read_resumable_upload_tracker_file(
            tracker_file_path)

        if (tracker_data is None or
            tracker_data.encryption_key_sha256 != encryption_key_hash_sha256):
          serialization_data = None
        else:
          # TODO(b/190093425): Print a better message for component uploads once
          # the final destination resource is available in ComponentUploadTask.
          log.status.Print('Resuming upload for ' + destination_url.object_name)

          serialization_data = tracker_data.serialization_data

          if tracker_data.complete:
            try:
              metadata_request_config = (
                  request_config_factory.get_request_config(
                      destination_url,
                      decryption_key_hash_sha256=encryption_key_hash_sha256))
              # Providing a decryption key means the response will include the
              # object's hash if the keys match, and raise an error if they do
              # not. This is desirable since we want to re-upload objects with
              # the wrong key, and need the object's hash for validation.
              destination_resource = api.get_object_metadata(
                  destination_url.bucket_name, destination_url.object_name,
                  metadata_request_config)
            except api_errors.CloudApiError:
              # Any problem fetching existing object metadata can be ignored,
              # since we'll just re-upload the object.
              pass
            else:
              # The API call will not error if we provide an encryption key but
              # the destination is unencrypted, hence the additional (defensive)
              # check below.
              destination_key_hash = (
                  destination_resource.decryption_key_hash_sha256)
              if (destination_key_hash == encryption_key_hash_sha256 and
                  self._existing_destination_is_valid(destination_resource)):
                return self._get_output(destination_resource)

        attempt_upload = functools.partial(
            api.upload_object,
            source_stream,
            self._destination_resource,
            request_config,
            posix_to_set=self._posix_to_set,
            serialization_data=serialization_data,
            source_resource=source_resource_for_metadata,
            tracker_callback=tracker_callback,
            upload_strategy=upload_strategy,
        )

        def _handle_resumable_upload_error(exc_type, exc_value, exc_traceback,
                                           state):
          """Returns true if resumable upload should retry on error argument."""
          del exc_traceback  # Unused.
          if not (exc_type is api_errors.NotFoundError or
                  getattr(exc_value, 'status_code', None) == 410):

            if exc_type is api_errors.ResumableUploadAbortError:
              tracker_file_util.delete_tracker_file(tracker_file_path)

            # Otherwise the error is probably a persistent network issue
            # that is already retried by API clients, so we'll keep the tracker
            # file to allow the user to retry the upload in a separate run.

            return False

          tracker_file_util.delete_tracker_file(tracker_file_path)

          if state.retrial == 0:
            # Ping bucket to see if it exists.
            try:
              api.get_bucket(self._destination_resource.storage_url.bucket_name)
            except api_errors.CloudApiError as e:
              # The user may not have permission to view the bucket metadata,
              # so the ping may still be valid for access denied errors.
              status = getattr(e, 'status_code', None)
              if status not in (401, 403):
                raise

          return True

        # Convert seconds to miliseconds by multiplying by 1000.
        destination_resource = retry.Retryer(
            max_retrials=properties.VALUES.storage.max_retries.GetInt(),
            wait_ceiling_ms=properties.VALUES.storage.max_retry_delay.GetInt() *
            1000,
            exponential_sleep_multiplier=(
                properties.VALUES.storage.exponential_sleep_multiplier.GetInt()
            )).RetryOnException(
                attempt_upload,
                sleep_ms=properties.VALUES.storage.base_retry_delay.GetInt() *
                1000,
                should_retry_if=_handle_resumable_upload_error)

        tracker_data = tracker_file_util.read_resumable_upload_tracker_file(
            tracker_file_path)
        if tracker_data is not None:
          if self._component_number is not None:
            tracker_file_util.write_resumable_upload_tracker_file(
                tracker_file_path,
                complete=True,
                encryption_key_sha256=tracker_data.encryption_key_sha256,
                serialization_data=tracker_data.serialization_data)
          else:
            tracker_file_util.delete_tracker_file(tracker_file_path)
      else:
        destination_resource = api.upload_object(
            source_stream,
            self._destination_resource,
            request_config,
            posix_to_set=self._posix_to_set,
            source_resource=source_resource_for_metadata,
            upload_strategy=upload_strategy,
        )

      upload_util.validate_uploaded_object(digesters, destination_resource,
                                           task_status_queue)

    return self._get_output(destination_resource)
