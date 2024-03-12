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
"""Helper functions for progress callbacks."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import time

from gslib.thread_message import ProgressMessage
from gslib.utils import parallelism_framework_util

# Default upper and lower bounds for progress callback frequency.
_START_BYTES_PER_CALLBACK = 1024 * 256
_MAX_BYTES_PER_CALLBACK = 1024 * 1024 * 100
_TIMEOUT_SECONDS = 1

# Max width of URL to display in progress indicator. Wide enough to allow
# 15 chars for x/y display on an 80 char wide terminal.
MAX_PROGRESS_INDICATOR_COLUMNS = 65


class ProgressCallbackWithTimeout(object):
  """Makes progress callbacks at least once every _TIMEOUT_SECONDS.

  This prevents wrong throughput calculation while not being excessively
  overwhelming.
  """

  def __init__(self,
               total_size,
               callback_func,
               start_bytes_per_callback=_START_BYTES_PER_CALLBACK,
               timeout=_TIMEOUT_SECONDS):
    """Initializes the callback with timeout.

    Args:
      total_size: Total bytes to process. If this is None, size is not known
          at the outset.
      callback_func: Func of (int: processed_so_far, int: total_bytes)
          used to make callbacks.
      start_bytes_per_callback: Lower bound of bytes per callback.
      timeout: Number maximum of seconds without a callback.

    """
    self._bytes_per_callback = start_bytes_per_callback
    self._callback_func = callback_func
    self._total_size = total_size
    self._last_time = time.time()
    self._timeout = timeout
    self._bytes_processed_since_callback = 0
    self._callbacks_made = 0
    self._total_bytes_processed = 0

  def Progress(self, bytes_processed):
    """Tracks byte processing progress, making a callback if necessary."""
    self._bytes_processed_since_callback += bytes_processed
    cur_time = time.time()
    if (self._bytes_processed_since_callback > self._bytes_per_callback or
        (self._total_size is not None and self._total_bytes_processed +
         self._bytes_processed_since_callback >= self._total_size) or
        (self._last_time - cur_time) > self._timeout):
      self._total_bytes_processed += self._bytes_processed_since_callback
      # TODO: We check if >= total_size and truncate because JSON uploads count
      # multipart metadata during their send progress. If the size is unknown,
      # we can't do this and the progress message will make it appear that we
      # send more than the original stream.
      if self._total_size is not None:
        bytes_sent = min(self._total_bytes_processed, self._total_size)
      else:
        bytes_sent = self._total_bytes_processed
      self._callback_func(bytes_sent, self._total_size)
      self._bytes_processed_since_callback = 0
      self._callbacks_made += 1
      self._last_time = cur_time


class FileProgressCallbackHandler(object):
  """Tracks progress info for large operations like file copy or hash.

      Information is sent to the status_queue, which will print it in the
      UI Thread.
  """

  def __init__(self,
               status_queue,
               start_byte=0,
               override_total_size=None,
               src_url=None,
               component_num=None,
               dst_url=None,
               operation_name=None):
    """Initializes the callback handler.

    Args:
      status_queue: Queue for posting status messages for UI display.
      start_byte: The beginning of the file component, if one is being used.
      override_total_size: The size of the file component, if one is being used.
      src_url: FileUrl/CloudUrl representing the source file.
      component_num: Indicates the component number, if any.
      dst_url: FileUrl/CloudUrl representing the destination file, or None
        for unary operations like hashing.
      operation_name: String representing the operation name
    """
    self._status_queue = status_queue
    self._start_byte = start_byte
    self._override_total_size = override_total_size
    self._component_num = component_num
    self._src_url = src_url
    self._dst_url = dst_url
    self._operation_name = operation_name
    # Ensures final newline is written once even if we get multiple callbacks.
    self._last_byte_written = False

  # Function signature is in boto callback format, which cannot be changed.
  def call(
      self,  # pylint: disable=invalid-name
      last_byte_processed,
      total_size):
    """Gathers information describing the operation progress.

    Actual message is printed to stderr by UIThread.

    Args:
      last_byte_processed: The last byte processed in the file. For file
                           components, this number should be in the range
                           [start_byte:start_byte + override_total_size].
      total_size: Total size of the ongoing operation.
    """
    if self._last_byte_written:
      return

    if self._override_total_size:
      total_size = self._override_total_size

    parallelism_framework_util.PutToQueueWithTimeout(
        self._status_queue,
        ProgressMessage(total_size,
                        last_byte_processed - self._start_byte,
                        self._src_url,
                        time.time(),
                        component_num=self._component_num,
                        operation_name=self._operation_name,
                        dst_url=self._dst_url))
    if total_size and last_byte_processed - self._start_byte == total_size:
      self._last_byte_written = True
