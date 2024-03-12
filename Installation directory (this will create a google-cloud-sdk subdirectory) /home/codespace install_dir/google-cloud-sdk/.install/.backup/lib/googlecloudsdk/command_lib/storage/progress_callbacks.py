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
"""Messages parallel workers might send to the main thread."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import time

from googlecloudsdk.command_lib.storage import thread_messages


class FilesAndBytesProgressCallback:
  """Tracks file count and bytes progress info for large file operations.

  Information is sent to the status_queue, which will print aggregate it
  for printing to the user. Useful for heavy operations like copy or hash.
  Arguments similar to thread_messages.ProgressMessage.
  """

  def __init__(self,
               status_queue,
               offset,
               length,
               source_url,
               destination_url=None,
               component_number=None,
               total_components=None,
               operation_name=None,
               process_id=None,
               thread_id=None):
    """Initializes callback, saving non-changing variables.

    Args:
      status_queue (multiprocessing.Queue): Where to submit progress messages.
        If we spawn new worker processes, they will lose their reference to the
        correct version of this queue if we don't package it here.
      offset (int): Start of byte range to start operation at.
      length (int): Total size of file or component in bytes.
      source_url (StorageUrl): Represents source of data used by operation.
      destination_url (StorageUrl|None): Represents destination of data used by
        operation. None for unary operations like hashing.
      component_number (int|None): If a multipart operation, indicates the
        component number.
      total_components (int|None): If a multipart operation, indicates the total
        number of components.
      operation_name (task_status.OperationName|None): Name of the operation
        running on target data.
      process_id (int|None): Identifies process that produced the instance of
        this message (overridable for testing).
      thread_id (int|None): Identifies thread that produced the instance of this
        message (overridable for testing).
    """
    self._status_queue = status_queue
    self._offset = offset
    self._length = length
    self._source_url = source_url
    self._destination_url = destination_url
    self._component_number = component_number
    self._total_components = total_components
    self._operation_name = operation_name
    self._process_id = process_id
    self._thread_id = thread_id

  def __call__(self, current_byte, *args):
    """Sends operation progress information to global status queue.

    Args:
      current_byte (int): Index of byte being operated on.
      *args (list[any]): Unused.
    """
    del args  # Unused.

    # Time progress callback is triggered in seconds since epoch (float).
    current_time = time.time()
    self._status_queue.put(
        thread_messages.DetailedProgressMessage(
            offset=self._offset,
            length=self._length,
            current_byte=current_byte,
            time=current_time,
            source_url=self._source_url,
            destination_url=self._destination_url,
            component_number=self._component_number,
            total_components=self._total_components,
            operation_name=self._operation_name,
            process_id=self._process_id,
            thread_id=self._thread_id))


def increment_count_callback(status_queue):
  status_queue.put(thread_messages.IncrementProgressMessage())


def workload_estimator_callback(status_queue, item_count, size=None):
  """Tracks expected item count and bytes for large operations.

  Information is sent to the status_queue, which will aggregate it
  for printing to the user. Useful for heavy operations like copy. For example,
  this sets the "100" in "copied 5/100 files."
  Arguments similar to thread_messages.WorkloadEstimatorMessage.

  Args:
    status_queue (multiprocessing.Queue): Reference to global queue.
    item_count (int): Number of items to add to workload estimation.
    size (int|None): Number of bytes to add to workload estimation.
  """
  status_queue.put(
      thread_messages.WorkloadEstimatorMessage(
          item_count=item_count, size=size))
