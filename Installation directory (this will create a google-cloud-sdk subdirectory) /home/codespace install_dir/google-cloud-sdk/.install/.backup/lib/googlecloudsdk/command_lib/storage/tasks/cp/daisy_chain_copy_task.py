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

"""Task for daisy-chain copies.

Typically executed in a task iterator:
googlecloudsdk.command_lib.storage.tasks.task_executor.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import io
import os
import threading

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import request_config_factory
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import manifest_util
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.cp import copy_util
from googlecloudsdk.command_lib.storage.tasks.cp import upload_util
from googlecloudsdk.command_lib.storage.tasks.rm import delete_task
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


_MAX_ALLOWED_READ_SIZE = 100 * 1024 * 1024  # 100 MiB
_MAX_BUFFER_QUEUE_SIZE = 100
# TODO(b/174075495) Determine the max size based on the destination scheme.
_QUEUE_ITEM_MAX_SIZE = 8 * 1024  # 8 KiB
_PROGRESS_CALLBACK_THRESHOLD = 16 * 1024 * 1024  # 16 MiB.


class _AbruptShutdownError(errors.Error):
  """Raised if a thread is terminated because of an error in another thread."""


class _WritableStream:
  """A write-only stream class that writes to the buffer queue."""

  def __init__(self, buffer_queue, buffer_condition, shutdown_event):
    """Initializes WritableStream.

    Args:
      buffer_queue (collections.deque): A queue where the data gets written.
      buffer_condition (threading.Condition): The condition object to wait on if
        the buffer is full.
      shutdown_event (threading.Event): Used for signaling the thread to
        terminate.
    """
    self._buffer_queue = buffer_queue
    self._buffer_condition = buffer_condition
    self._shutdown_event = shutdown_event

  def write(self, data):
    """Writes data to the buffer queue.

    This method writes the data in chunks of QUEUE_ITEM_MAX_SIZE. In most cases,
    the read operation is performed with size=QUEUE_ITEM_MAX_SIZE.
    Splitting the data in QUEUE_ITEM_MAX_SIZE chunks improves the performance.

    This method will be blocked if MAX_BUFFER_QUEUE_SIZE is reached to avoid
    writing all the data in-memory.

    Args:
      data (bytes): The bytes that should be added to the queue.

    Raises:
      _AbruptShutdownError: If self._shudown_event was set.
    """
    start = 0
    end = min(start + _QUEUE_ITEM_MAX_SIZE, len(data))
    while start < len(data):
      with self._buffer_condition:
        while (len(self._buffer_queue) >= _MAX_BUFFER_QUEUE_SIZE and
               not self._shutdown_event.is_set()):
          self._buffer_condition.wait()

        if self._shutdown_event.is_set():
          raise _AbruptShutdownError()

        self._buffer_queue.append(data[start:end])
        start = end
        end = min(start + _QUEUE_ITEM_MAX_SIZE, len(data))
        self._buffer_condition.notify_all()


class _ReadableStream:
  """A read-only stream that reads from the buffer queue."""

  def __init__(self, buffer_queue, buffer_condition, shutdown_event,
               end_position, restart_download_callback,
               progress_callback=None,
               seekable=True):
    """Initializes ReadableStream.

    Args:
      buffer_queue (collections.deque): The underlying queue from which the data
        gets read.
      buffer_condition (threading.Condition): The condition object to wait on if
        the buffer is empty.
      shutdown_event (threading.Event): Used for signaling the thread to
        terminate.
      end_position (int): Position at which the stream reading stops. This is
        usually the total size of the data that gets read.
      restart_download_callback (func): This must be the
        BufferController.restart_download function.
      progress_callback (progress_callbacks.FilesAndBytesProgressCallback):
        Accepts processed bytes and submits progress info for aggregation.
      seekable (bool): Value for the "seekable" method call.
    """
    self._buffer_queue = buffer_queue
    self._buffer_condition = buffer_condition
    self._end_position = end_position
    self._shutdown_event = shutdown_event
    self._position = 0
    self._unused_data_from_previous_read = b''
    self._progress_callback = progress_callback
    self._restart_download_callback = restart_download_callback
    self._bytes_read_since_last_progress_callback = 0
    self._seekable = seekable
    self._is_closed = False

  def _restart_download(self, offset):
    self._restart_download_callback(offset)
    self._unused_data_from_previous_read = b''
    self._bytes_read_since_last_progress_callback = 0
    self._position = offset

  def read(self, size=-1):
    """Reads size bytes from the buffer queue and returns it.

    This method will be blocked if the buffer_queue is empty.
    If size > length of data available, the entire data is sent over.

    Args:
      size (int): The number of bytes to be read.

    Returns:
      Bytes of length 'size'. May return bytes of length less than the size
        if there are no more bytes left to be read.

    Raises:
      _AbruptShutdownError: If self._shudown_event was set.
      storage.errors.Error: If size is not within the allowed range of
        [-1, MAX_ALLOWED_READ_SIZE] OR
        If size is -1 but the object size is greater than MAX_ALLOWED_READ_SIZE.
    """
    if size == 0:
      return b''

    if size > _MAX_ALLOWED_READ_SIZE:
      raise errors.Error(
          'Invalid HTTP read size {} during daisy chain operation, expected'
          ' -1 <= size <= {} bytes.'.format(size, _MAX_ALLOWED_READ_SIZE))

    if size == -1:
      # This indicates that we have to read the entire object at once.
      if self._end_position <= _MAX_ALLOWED_READ_SIZE:
        chunk_size = self._end_position
      else:
        raise errors.Error('Read with size=-1 is not allowed for object'
                           ' size > {} bytes to prevent reading large objects'
                           ' in-memory.'.format(_MAX_ALLOWED_READ_SIZE))
    else:
      chunk_size = size

    result = io.BytesIO()
    bytes_read = 0

    while bytes_read < chunk_size and self._position < self._end_position:
      if not self._unused_data_from_previous_read:
        with self._buffer_condition:
          while not self._buffer_queue and not self._shutdown_event.is_set():
            self._buffer_condition.wait()

          # The shutdown_event needs to be checked before the data is fetched
          # from the buffer.
          if self._shutdown_event.is_set():
            raise _AbruptShutdownError()

          data = self._buffer_queue.popleft()
          self._buffer_condition.notify_all()
      else:
        # Data is already present from previous read.
        if self._shutdown_event.is_set():
          raise _AbruptShutdownError()
        data = self._unused_data_from_previous_read

      if bytes_read + len(data) > chunk_size:
        self._unused_data_from_previous_read = data[chunk_size - bytes_read:]
        data_to_return = data[:chunk_size - bytes_read]
      else:
        self._unused_data_from_previous_read = b''
        data_to_return = data
      result.write(data_to_return)
      bytes_read += len(data_to_return)
      self._position += len(data_to_return)

    result_data = result.getvalue()
    if result_data and self._progress_callback:
      self._bytes_read_since_last_progress_callback += len(result_data)
      if (self._bytes_read_since_last_progress_callback >=
          _PROGRESS_CALLBACK_THRESHOLD):
        self._bytes_read_since_last_progress_callback = 0
        self._progress_callback(self._position)

    return result_data

  def seek(self, offset, whence=os.SEEK_SET):
    """Seek to the given offset position.

    Ideally, seek changes the stream position to the given byte offset.
    But we only handle resumable retry for S3 to GCS transfers at this time,
    which means, seek will be called only by the Apitools library.
    Since Apitools calls seek only for limited cases, we avoid implementing
    seek for all possible cases here in order to avoid unnecessary complexity
    in the code.

    Following are the cases where Apitools calls seek:
    1) At the end of the transfer
    https://github.com/google/apitools/blob/ca2094556531d61e741dc2954fdfccbc650cdc32/apitools/base/py/transfer.py#L986
    to determine if it has read everything from the stream.
    2) For any transient errors during uploads to seek back to a particular
    position. This call is always made with whence == os.SEEK_SET.

    Args:
      offset (int): Defines the position realative to the `whence` where the
        current position of the stream should be moved.
      whence (int): The reference relative to which offset is interpreted.
        Values for whence are: os.SEEK_SET or 0 - start of the stream
        (thedefault). os.SEEK_END or 2 - end of the stream. We do not support
        other os.SEEK_* constants.

    Returns:
      (int) The current position.

    Raises:
      Error:
        If seek is called with whence == os.SEEK_END for offset not
        equal to the last position.
        If seek is called with whence == os.SEEK_CUR.
    """
    if whence == os.SEEK_END:
      if offset:
        raise errors.Error(
            'Non-zero offset from os.SEEK_END is not allowed.'
            'Offset: {}.'.format(offset)
        )
    elif whence == os.SEEK_SET:
      # Relative to the start of the stream, the offset should be the size
      # of the stream
      if offset != self._position:
        self._restart_download(offset)
    else:
      raise errors.Error(
          'Seek is only supported for os.SEEK_END and os.SEEK_SET.'
      )
    return self._position

  def seekable(self):
    """Returns True if the stream should be treated as a seekable stream."""
    return self._seekable

  def tell(self):
    """Returns the current position."""
    return self._position

  def close(self):
    """Updates progress callback if needed."""
    if self._is_closed:
      # Ensures that close called multiple times does not have any side-effect.
      return

    if (self._progress_callback and
        (self._bytes_read_since_last_progress_callback or
         # Update progress for zero-sized object.
         self._end_position == 0)):
      self._bytes_read_since_last_progress_callback = 0
      self._progress_callback(self._position)
    self._is_closed = True


class BufferController:
  """Manages a  bidirectional buffer to read and write simultaneously.

  Attributes:
    buffer_queue (collections.deque): The underlying queue that acts like a
      buffer for the streams
    buffer_condition (threading.Condition): The condition object used for
      waiting based on the underlying buffer_queue state.
      All threads waiting on this condition are notified when data is added or
      removed from buffer_queue. Streams that write to the buffer wait on this
      condition until the buffer has space, and streams that read from the
      buffer wait on this condition until the buffer has data.
    shutdown_event (threading.Event): Used for signaling the operations to
      terminate.
    writable_stream (_WritableStream): Stream that writes to the buffer.
    readable_stream (_ReadableStream): Stream that reads from the buffer.
    exception_raised (Exception): Stores the Exception instance responsible for
      termination of the operation.
  """

  def __init__(self, source_resource, destination_scheme,
               user_request_args=None,
               progress_callback=None):
    """Initializes BufferController.

    Args:
      source_resource (resource_reference.ObjectResource): Must
        contain the full object path of existing object.
      destination_scheme (storage_url.ProviderPrefix): The destination provider.
      user_request_args (UserRequestArgs|None): Values for RequestConfig.
      progress_callback (progress_callbacks.FilesAndBytesProgressCallback):
        Accepts processed bytes and submits progress info for aggregation.
    """
    self._source_resource = source_resource
    self._user_request_args = user_request_args
    self.buffer_queue = collections.deque()
    self.buffer_condition = threading.Condition()
    self.shutdown_event = threading.Event()
    self.writable_stream = _WritableStream(self.buffer_queue,
                                           self.buffer_condition,
                                           self.shutdown_event)

    destination_capabilities = api_factory.get_capabilities(destination_scheme)
    self.readable_stream = _ReadableStream(
        self.buffer_queue,
        self.buffer_condition,
        self.shutdown_event,
        self._source_resource.size,
        restart_download_callback=self.restart_download,
        progress_callback=progress_callback,
        seekable=(cloud_api.Capability.DAISY_CHAIN_SEEKABLE_UPLOAD_STREAM
                  in destination_capabilities))
    self._download_thread = None
    self.exception_raised = None

  def _run_download(self, start_byte):
    """Performs the download operation."""
    request_config = request_config_factory.get_request_config(
        self._source_resource.storage_url,
        user_request_args=self._user_request_args)

    client = api_factory.get_api(self._source_resource.storage_url.scheme)
    try:
      if self._source_resource.size != 0:
        client.download_object(
            self._source_resource,
            self.writable_stream,
            request_config,
            start_byte=start_byte,
            download_strategy=cloud_api.DownloadStrategy.ONE_SHOT)
    except _AbruptShutdownError:
      # Shutdown caused by interruption from another thread.
      pass
    except Exception as e:  # pylint: disable=broad-except
      # The stack trace of the exception raised in the thread is not visible
      # in the caller thread. Hence we catch any exception so that we can
      # re-raise them from the parent thread.
      self.shutdown(e)

  def start_download_thread(self, start_byte=0):
    self._download_thread = threading.Thread(target=self._run_download,
                                             args=(start_byte,))
    self._download_thread.start()

  def wait_for_download_thread_to_terminate(self):
    if self._download_thread is not None:
      self._download_thread.join()

  def restart_download(self, start_byte):
    """Restarts the download_thread.

    Args:
      start_byte (int): The start byte for the new download call.
    """
    # Signal the download to end.
    self.shutdown_event.set()
    with self.buffer_condition:
      self.buffer_condition.notify_all()

    self.wait_for_download_thread_to_terminate()

    # Clear all the data in the underlying buffer.
    self.buffer_queue.clear()

    # Reset the shutdown signal.
    self.shutdown_event.clear()
    self.start_download_thread(start_byte)

  def shutdown(self, error):
    """Sets the shutdown event and stores the error to re-raise later.

    Args:
      error (Exception): The error responsible for triggering shutdown.
    """
    self.shutdown_event.set()
    with self.buffer_condition:
      self.buffer_condition.notify_all()
      self.exception_raised = error


class DaisyChainCopyTask(copy_util.ObjectCopyTaskWithExitHandler):
  """Represents an operation to copy by downloading and uploading.

  This task downloads from one cloud location and uplaods to another cloud
  location by keeping an in-memory buffer.
  """

  def __init__(
      self,
      source_resource,
      destination_resource,
      delete_source=False,
      posix_to_set=None,
      print_created_message=False,
      print_source_version=False,
      user_request_args=None,
      verbose=False,
  ):
    """Initializes task.

    Args:
      source_resource (resource_reference.ObjectResource): Must contain the full
        object path of existing object. Directories will not be accepted.
      destination_resource (resource_reference.UnknownResource): Must contain
        the full object path. Object may not exist yet. Existing objects at the
        this location will be overwritten. Directories will not be accepted.
      delete_source (bool): If copy completes successfully, delete the source
        object afterwards.
      posix_to_set (PosixAttributes|None): See parent class.
      print_created_message (bool): See parent class.
      print_source_version (bool): See parent class.
      user_request_args (UserRequestArgs|None): See parent class.
      verbose (bool): See parent class.
    """
    super(DaisyChainCopyTask, self).__init__(
        source_resource,
        destination_resource,
        posix_to_set=posix_to_set,
        print_created_message=print_created_message,
        print_source_version=print_source_version,
        user_request_args=user_request_args,
        verbose=verbose,
    )
    if (not isinstance(source_resource.storage_url, storage_url.CloudUrl)
        or not isinstance(destination_resource.storage_url,
                          storage_url.CloudUrl)):
      raise errors.Error(
          'DaisyChainCopyTask is for copies between cloud providers.'
      )

    self._delete_source = delete_source

    self.parallel_processing_key = (
        self._destination_resource.storage_url.url_string)

  def _get_md5_hash(self):
    """Returns the MD5 Hash if present and hash validation is requested."""
    if (properties.VALUES.storage.check_hashes.Get() ==
        properties.CheckHashes.NEVER.value):
      return None

    if self._source_resource.md5_hash is None:
      # For composite uploads, MD5 hash might be missing.
      # TODO(b/191975989) Add support for crc32c once -D option is implemented.
      # Composite uploads will have crc32c information, which we should
      # pass to the request.
      log.warning(
          'Found no hashes to validate object downloaded from %s and'
          ' uploaded to %s. Integrity cannot be assured without hashes.',
          self._source_resource, self._destination_resource)
    return self._source_resource.md5_hash

  def _gapfill_request_config_field(self, resource_args,
                                    request_config_field_name,
                                    source_resource_field_name):
    request_config_value = getattr(resource_args, request_config_field_name,
                                   None)
    if request_config_value is None:
      setattr(resource_args, request_config_field_name,
              getattr(self._source_resource, source_resource_field_name))

  def _populate_request_config_with_resource_values(self, request_config):
    resource_args = request_config.resource_args
    # Does not cover all fields. Just the ones gsutil does.
    self._gapfill_request_config_field(resource_args, 'cache_control',
                                       'cache_control')
    self._gapfill_request_config_field(resource_args, 'content_disposition',
                                       'content_disposition')
    self._gapfill_request_config_field(resource_args, 'content_encoding',
                                       'content_encoding')
    self._gapfill_request_config_field(resource_args, 'content_language',
                                       'content_language')
    self._gapfill_request_config_field(resource_args, 'content_type',
                                       'content_type')
    self._gapfill_request_config_field(resource_args, 'custom_time',
                                       'custom_time')
    self._gapfill_request_config_field(resource_args, 'md5_hash',
                                       'md5_hash')
    # Storage class is intentionally excluded here, since gsutil uses the
    # bucket's default for daisy chain destinations:
    # https://github.com/GoogleCloudPlatform/gsutil/blob/db22c6cf44e4f58a56864f0a6f9bcdf868a3c156/gslib/utils/copy_helper.py#L3860

  def execute(self, task_status_queue=None):
    """Copies file by downloading and uploading in parallel."""
    # TODO (b/168712813): Add option to use the Data Transfer component.
    destination_client = api_factory.get_api(
        self._destination_resource.storage_url.scheme)
    if copy_util.check_for_cloud_clobber(self._user_request_args,
                                         destination_client,
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
        operation_name=task_status.OperationName.DAISY_CHAIN_COPYING,
        process_id=os.getpid(),
        thread_id=threading.get_ident(),
    )

    buffer_controller = BufferController(
        self._source_resource,
        self._destination_resource.storage_url.scheme,
        self._user_request_args,
        progress_callback)

    # Perform download in a separate thread so that upload can be performed
    # simultaneously.
    buffer_controller.start_download_thread()

    content_type = (
        self._source_resource.content_type or
        request_config_factory.DEFAULT_CONTENT_TYPE)

    request_config = request_config_factory.get_request_config(
        self._destination_resource.storage_url,
        content_type=content_type,
        md5_hash=self._get_md5_hash(),
        size=self._source_resource.size,
        user_request_args=self._user_request_args)
    # Request configs are designed to translate between providers.
    self._populate_request_config_with_resource_values(request_config)

    result_resource = None
    try:
      upload_strategy = upload_util.get_upload_strategy(
          api=destination_client,
          object_length=self._source_resource.size)
      result_resource = destination_client.upload_object(
          buffer_controller.readable_stream,
          self._destination_resource,
          request_config,
          posix_to_set=self._posix_to_set,
          source_resource=self._source_resource,
          upload_strategy=upload_strategy,
      )
    except _AbruptShutdownError:
      # Not raising daisy_chain_stream.exception_raised here because we want
      # to wait for the download thread to finish.
      pass
    except Exception as e:  # pylint: disable=broad-except
      # For all the other errors raised during upload, we want to to make
      # sure that the download thread is terminated before we re-reaise.
      # Hence we catch any exception and store it to be re-raised later.
      buffer_controller.shutdown(e)

    buffer_controller.wait_for_download_thread_to_terminate()
    buffer_controller.readable_stream.close()
    if buffer_controller.exception_raised:
      raise buffer_controller.exception_raised

    if result_resource:
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
