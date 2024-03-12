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

import os
import threading


class ThreadMessage(object):
  """Message that can be sent from multithreading workers to global status."""


class IncrementProgressMessage(ThreadMessage):
  """Simple message indicating one of something has completed."""


class DetailedProgressMessage(ThreadMessage):
  """Message class for sending information about operation progress.

  This class contains specific information on the progress of operating on a
  file, cloud object, or single component.

  Attributes:
    offset (int): Start of byte range to start operation at.
    length (int): Total size of file or component in bytes.
    current_byte (int): Index of byte being operated on.
    finished (bool): Indicates if the operation is complete.
    time (float): When message was created (seconds since epoch).
    source_url (StorageUrl): Represents source of data used by operation.
    destination_url (StorageUrl|None): Represents destination of data used by
      operation. None for unary operations like hashing.
    component_number (int|None): If a multipart operation, indicates the
      component number.
    total_components (int|None): If a multipart operation, indicates the
      total number of components.
    operation_name (task_status.OperationName|None): Name of the operation
      running on target data.
    process_id (int|None): Identifies process that produced the instance of this
      message (overridable for testing).
    thread_id (int|None): Identifies thread that produced the instance of this
      message (overridable for testing).
  """

  def __init__(self,
               offset,
               length,
               current_byte,
               time,
               source_url,
               destination_url=None,
               component_number=None,
               total_components=None,
               operation_name=None,
               process_id=None,
               thread_id=None):
    # pylint:disable=g-doc-args
    """Initializes a ProgressMessage. See attributes docstring for arguments."""
    # pylint:enable=g-doc-args
    self.offset = offset
    self.length = length
    self.current_byte = current_byte
    self.time = time

    self.source_url = source_url
    self.destination_url = destination_url
    self.component_number = component_number
    self.total_components = total_components

    self.operation_name = operation_name
    self.process_id = process_id or os.getpid()
    self.thread_id = thread_id or threading.current_thread().ident

  def __eq__(self, other):
    if not isinstance(other, self.__class__):
      return NotImplemented
    return self.__dict__ == other.__dict__

  def __repr__(self):
    """Returns a string with a valid constructor for this message."""
    source_url_string = "'{}'".format(self.source_url)
    destination_url_string = ("'{}'".format(
        self.destination_url)) if self.destination_url else None
    operation_name_string = ("'{}'".format(
        self.operation_name.value)) if self.operation_name else None
    return ('{class_name}(time={time}, offset={offset},'
            ' length={length}, current_byte={current_byte},'
            ' source_url={source_url}, destination_url={destination_url},'
            ' component_number={component_number},'
            ' total_components={total_components},'
            ' operation_name={operation_name}, process_id={process_id},'
            ' thread_id={thread_id})').format(
                class_name=self.__class__.__name__,
                time=self.time,
                offset=self.offset,
                length=self.length,
                current_byte=self.current_byte,
                source_url=source_url_string,
                destination_url=destination_url_string,
                component_number=self.component_number,
                total_components=self.total_components,
                operation_name=operation_name_string,
                process_id=self.process_id,
                thread_id=self.thread_id)


class ManifestMessage(ThreadMessage):
  """Message class for updating manifest file with result of copy.

  Attributes:
    source_url (StorageUrl): Source URL. Used to match information recorded by
      copy progress infra (FilesAndBytesStatusTracker).
    destination_url (StorageUrl): Destination URL.
    end_time (datetime): Date and time copy completed.
    size (int): Size of file or object.
    result_status (manifest_utils.ResultStatus): End status of copy. Either
      "OK", "skip", or "error".
    md5_hash (str|None): Hash of copied file or object.
    description (str|None): Message about something that happened during a copy.
  """

  def __init__(self,
               source_url,
               destination_url,
               end_time,
               size,
               result_status,
               md5_hash=None,
               description=None):
    """Initializes ManifestMessage. Args in attributes docstring."""
    self.source_url = source_url
    self.destination_url = destination_url
    self.end_time = end_time
    self.size = size
    self.result_status = result_status
    self.md5_hash = md5_hash
    self.description = description

  def __repr__(self):
    """Returns a string with a valid constructor for this message."""
    source_url_string = "'{}'".format(self.source_url)
    destination_url_string = "'{}'".format(self.destination_url)
    end_time_string = "'{}'".format(self.end_time)
    md5_hash_string = "'{}'".format(self.md5_hash) if self.md5_hash else 'None'
    description_string = "'{}'".format(
        self.description) if self.description else 'None'
    return ('{class_name}(source_url={source_url},'
            ' destination_url={destination_url}, end_time={end_time},'
            ' size={size}, result_status={result_status},'
            ' md5_hash={md5_hash}, description={description})').format(
                class_name=self.__class__.__name__,
                source_url=source_url_string,
                destination_url=destination_url_string,
                end_time=end_time_string,
                size=self.size,
                result_status=self.result_status,
                md5_hash=md5_hash_string,
                description=description_string)

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return NotImplemented
    return (self.source_url == other.source_url and
            self.destination_url == other.destination_url and
            self.end_time == other.end_time and self.size == other.size and
            self.result_status == other.result_status and
            self.md5_hash == other.md5_hash and
            self.description == other.description)


class WorkloadEstimatorMessage(ThreadMessage):
  """Message class for estimating total workload of operation.

  Attributes:
    item_count (int): Number of items to add to workload estimation.
    size (int|None): Number of bytes to add to workload estimation.
  """

  def __init__(self, item_count, size=None):
    # pylint:disable=g-doc-args
    """Initializes WorkloadEstimatorMessage. Args in attributes docstring."""
    # pylint:enable=g-doc-args
    self.item_count = item_count
    self.size = size

  def __eq__(self, other):
    if not isinstance(other, self.__class__):
      return NotImplemented
    return self.__dict__ == other.__dict__

  def __repr__(self):
    """Returns a string with a valid constructor for this message."""
    return '{class_name}(item_count={item_count}, size={size})'.format(
        class_name=self.__class__.__name__,
        item_count=self.item_count,
        size=self.size)
