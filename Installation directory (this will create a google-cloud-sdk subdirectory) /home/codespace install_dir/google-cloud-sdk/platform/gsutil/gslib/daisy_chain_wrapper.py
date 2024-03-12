# -*- coding: utf-8 -*-
# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Wrapper for use in daisy-chained copies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections
import contextlib
import os
import threading
import time

from gslib.cloud_api import BadRequestException
from gslib.cloud_api import CloudApi
from gslib.utils import constants
from gslib.utils import parallelism_framework_util
from gslib.utils.encryption_helper import CryptoKeyWrapperFromKey

# This controls the amount of bytes downloaded per download request.
# We do not buffer this many bytes in memory at a time - that is controlled by
# DaisyChainWrapper.max_buffer_size. This is the upper bound of bytes that may
# be unnecessarily downloaded if there is a break in the resumable upload.
_DEFAULT_DOWNLOAD_CHUNK_SIZE = 1024 * 1024 * 100


class BufferWrapper(object):
  """Wraps the download file pointer to use our in-memory buffer."""

  def __init__(self, daisy_chain_wrapper, mode='b'):
    """Provides a buffered write interface for a file download.

    Args:
      daisy_chain_wrapper: DaisyChainWrapper instance to use for buffer and
                           locking.
    """
    self.daisy_chain_wrapper = daisy_chain_wrapper
    if hasattr(daisy_chain_wrapper, 'mode'):
      self.mode = daisy_chain_wrapper.mode
    else:
      self.mode = mode

  def write(self, data):  # pylint: disable=invalid-name
    """Waits for space in the buffer, then writes data to the buffer."""
    while True:
      with self.daisy_chain_wrapper.lock:
        if (self.daisy_chain_wrapper.bytes_buffered
            < self.daisy_chain_wrapper.max_buffer_size):
          break
      # Buffer was full, yield thread priority so the upload can pull from it.
      time.sleep(0)
    data_len = len(data)
    if data_len:
      with self.daisy_chain_wrapper.lock:
        self.daisy_chain_wrapper.buffer.append(data)
        self.daisy_chain_wrapper.bytes_buffered += data_len


@contextlib.contextmanager
def AcquireLockWithTimeout(lock, timeout):  # pylint: disable=invalid-name
  result = lock.acquire(timeout=timeout)
  yield result
  if result:
    lock.release()


class DaisyChainWrapper(object):
  """Wrapper class for daisy-chaining a cloud download to an upload.

  This class instantiates a BufferWrapper object to buffer the download into
  memory, consuming a maximum of max_buffer_size. It implements intelligent
  behavior around read and seek that allow for all of the operations necessary
  to copy a file.

  This class is coupled with the XML and JSON implementations in that it
  expects that small buffers (maximum of constants.TRANSFER_BUFFER_SIZE) in
  size will be used.
  """

  def __init__(self,
               src_url,
               src_obj_size,
               gsutil_api,
               compressed_encoding=False,
               progress_callback=None,
               download_chunk_size=_DEFAULT_DOWNLOAD_CHUNK_SIZE,
               decryption_key=None):
    """Initializes the daisy chain wrapper.

    Args:
      src_url: Source CloudUrl to copy from.
      src_obj_size: Size of source object.
      gsutil_api: gsutil Cloud API to use for the copy.
      compressed_encoding: If true, source object has content-encoding: gzip.
      progress_callback: Optional callback function for progress notifications
          for the download thread. Receives calls with arguments
          (bytes_transferred, total_size).
      download_chunk_size: Integer number of bytes to download per
          GetObjectMedia request. This is the upper bound of bytes that may be
          unnecessarily downloaded if there is a break in the resumable upload.
      decryption_key: Base64-encoded decryption key for the source object,
          if any.
    Raises:
      Exception: if the download thread doesn't start within 60 seconds
    """
    # Current read position for the upload file pointer.
    self.position = 0
    self.buffer = collections.deque()

    self.bytes_buffered = 0
    # Maximum amount of bytes in memory at a time.
    self.max_buffer_size = 1024 * 1024  # 1 MiB

    self._download_chunk_size = download_chunk_size

    # We save one buffer's worth of data as a special case for boto,
    # which seeks back one buffer and rereads to compute hashes. This is
    # unnecessary because we can just compare cloud hash digests at the end,
    # but it allows this to work without modfiying boto.
    self.last_position = 0
    self.last_data = None

    # Protects buffer, position, bytes_buffered, last_position, and last_data.
    self.lock = parallelism_framework_util.CreateLock()

    # Protects download_exception.
    self.download_exception_lock = parallelism_framework_util.CreateLock()

    self.src_obj_size = src_obj_size
    self.src_url = src_url
    self.compressed_encoding = compressed_encoding
    self.decryption_tuple = CryptoKeyWrapperFromKey(decryption_key)

    # This is safe to use the upload and download thread because the download
    # thread calls only GetObjectMedia, which creates a new HTTP connection
    # independent of gsutil_api. Thus, it will not share an HTTP connection
    # with the upload.
    self.gsutil_api = gsutil_api

    # If self.download_thread dies due to an exception, it is saved here so
    # that it can also be raised in the upload thread.
    self.download_exception = None
    self.download_thread = None
    self.progress_callback = progress_callback
    self.download_started = threading.Event()
    self.stop_download = threading.Event()
    self.StartDownloadThread(progress_callback=self.progress_callback)
    if not self.download_started.wait(60):
      raise Exception('Could not start download thread after 60 seconds.')
    self._unused_data_from_previous_read = b''

  def StartDownloadThread(self, start_byte=0, progress_callback=None):  # pylint: disable=invalid-name
    """Starts the download thread for the source object (from start_byte)."""

    def PerformDownload(start_byte, progress_callback):  # pylint: disable=invalid-name
      """Downloads the source object in chunks.

      This function checks the stop_download event and exits early if it is set.
      It should be set when there is an error during the daisy-chain upload,
      then this function can be called again with the upload's current position
      as start_byte.

      Args:
        start_byte: Byte from which to begin the download.
        progress_callback: Optional callback function for progress
            notifications. Receives calls with arguments
            (bytes_transferred, total_size).
      """
      # TODO: Support resumable downloads. This would require the BufferWrapper
      # object to support seek() and tell() which requires coordination with
      # the upload.
      self.download_started.set()
      try:
        while start_byte + self._download_chunk_size < self.src_obj_size:
          self.gsutil_api.GetObjectMedia(
              self.src_url.bucket_name,
              self.src_url.object_name,
              BufferWrapper(self),
              compressed_encoding=self.compressed_encoding,
              start_byte=start_byte,
              end_byte=start_byte + self._download_chunk_size - 1,
              generation=self.src_url.generation,
              object_size=self.src_obj_size,
              download_strategy=CloudApi.DownloadStrategy.ONE_SHOT,
              provider=self.src_url.scheme,
              progress_callback=progress_callback,
              decryption_tuple=self.decryption_tuple)
          if self.stop_download.is_set():
            # Download thread needs to be restarted, so exit.
            self.stop_download.clear()
            return
          start_byte += self._download_chunk_size
        self.gsutil_api.GetObjectMedia(
            self.src_url.bucket_name,
            self.src_url.object_name,
            BufferWrapper(self),
            compressed_encoding=self.compressed_encoding,
            start_byte=start_byte,
            generation=self.src_url.generation,
            object_size=self.src_obj_size,
            download_strategy=CloudApi.DownloadStrategy.ONE_SHOT,
            provider=self.src_url.scheme,
            progress_callback=progress_callback,
            decryption_tuple=self.decryption_tuple)
      # We catch all exceptions here because we want to store them.
      except Exception as e:  # pylint: disable=broad-except
        # Save the exception so that it can be seen in the upload thread.
        with self.download_exception_lock:
          self.download_exception = e
          raise

    # TODO: If we do gzip encoding transforms mid-transfer, this will fail.
    self.download_thread = threading.Thread(target=PerformDownload,
                                            args=(start_byte,
                                                  progress_callback))
    self.download_thread.start()

  def read(self, amt=None):  # pylint: disable=invalid-name
    """Exposes a stream from the in-memory buffer to the upload."""
    if self.position == self.src_obj_size or amt == 0:
      # If there is no data left or 0 bytes were requested, return an empty
      # string so callers can call still call len() and read(0).
      return ''
    if amt is None or amt > constants.TRANSFER_BUFFER_SIZE:
      raise BadRequestException(
          'Invalid HTTP read size %s during daisy chain operation, '
          'expected <= %s.' % (amt, constants.TRANSFER_BUFFER_SIZE))

    if self._unused_data_from_previous_read:
      valid_data = self._unused_data_from_previous_read[:amt]
      self._unused_data_from_previous_read = (
          self._unused_data_from_previous_read[amt:])
    else:
      valid_data = b''

      while True:
        with self.lock:
          if self.buffer:
            break
          if AcquireLockWithTimeout(self.download_exception_lock, 30):
            if self.download_exception:
              # Download thread died, so we will never recover. Raise the
              # exception that killed it.
              raise self.download_exception  # pylint: disable=raising-bad-type
          else:
            if not self.download_thread.is_alive():
              raise Exception('Download thread died suddenly.')
        # Buffer was empty, yield thread priority so the download thread can fill.
        time.sleep(0)
    with self.lock:
      # In a rare case where len(valid_data) < amt, and there are
      # elements in the buffer, e.g let's say valid_data = 'foo' and amt = 5,
      # and we have 'barbaz' in self.buffer, instead of returning 'fooba'
      # in the current call, we return 'foo', and in the subsequent calls
      # we will return 'barba' and 'z'. Given that we set
      # TRANSFER_BUFFER_SIZE as a multiple of the amt (8KiB),
      # we can safely assume that this will never happen practically.
      # This assumption helps us keep the logic simple and avoid
      # string concatenations and splits ('foo' + 'ba' in the above case).
      if not valid_data:
        data = self.buffer.popleft()
        valid_data = data[:amt]
        self._unused_data_from_previous_read = data[amt:]

      self.last_position = self.position
      self.last_data = valid_data
      data_len = len(valid_data)
      self.position += data_len
      self.bytes_buffered -= data_len
    if data_len > amt:
      raise BadRequestException(
          'Invalid read during daisy chain operation, got data of size '
          '%s, expected size %s.' % (data_len, amt))
    return valid_data

  def tell(self):  # pylint: disable=invalid-name
    with self.lock:
      return self.position

  def seek(self, offset, whence=os.SEEK_SET):  # pylint: disable=invalid-name
    """Sets current read position of the stream."""
    restart_download = False
    if whence == os.SEEK_END:
      if offset:
        raise IOError(
            'Invalid seek during daisy chain operation. Non-zero offset %s '
            'from os.SEEK_END is not supported' % offset)
      with self.lock:
        self.last_position = self.position
        self.last_data = None
        # Safe because we check position against src_obj_size in read.
        self.position = self.src_obj_size
    elif whence == os.SEEK_SET:
      with self.lock:
        if offset == self.position:
          pass
        elif offset == self.last_position:
          self.position = self.last_position
          if self.last_data:
            # If we seek to end and then back, we won't have last_data; we'll
            # get it on the next call to read.
            self.buffer.appendleft(self.last_data)
            self.bytes_buffered += len(self.last_data)
        else:
          # Once a download is complete, boto seeks to 0 and re-reads to
          # compute the hash if an md5 isn't already present (for example a GCS
          # composite object), so we have to re-download the whole object.
          # Also, when daisy-chaining to a resumable upload, on error the
          # service may have received any number of the bytes; the download
          # needs to be restarted from that point.
          restart_download = True

      if restart_download:
        self.stop_download.set()

        # Consume any remaining bytes in the download thread so that
        # the thread can exit, then restart the thread at the desired position.
        while self.download_thread.is_alive():
          with self.lock:
            while self.bytes_buffered:
              self.bytes_buffered -= len(self.buffer.popleft())
          time.sleep(0)

        with self.lock:
          self.position = offset
          self.buffer = collections.deque()
          self.bytes_buffered = 0
          self.last_position = 0
          self.last_data = None
          self.stop_download.clear()
        self.StartDownloadThread(start_byte=offset,
                                 progress_callback=self.progress_callback)
    else:
      raise IOError('Daisy-chain download wrapper does not support '
                    'seek mode %s' % whence)

  def seekable(self):  # pylint: disable=invalid-name
    return True
