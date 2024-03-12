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
"""Implementation of CatTaskIterator for calling the StreamingDownloadTask."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.tasks.cp import streaming_download_task


def _get_start_byte(start_byte, source_resource_size):
  """Returns the byte index to start streaming from.

  Gets an absolute start byte for object download API calls.

  Args:
    start_byte (int): The start index entered by the user. Negative values are
      interpreted as offsets from the end of the object.
    source_resource_size (int|None): The size of the source resource.

  Returns:
    int: The byte index to start the object download from.
  """
  if start_byte < 0:
    if abs(start_byte) >= source_resource_size:
      return 0
    return source_resource_size - abs(start_byte)
  return start_byte


def get_cat_task_iterator(source_iterator, show_url, start_byte, end_byte):
  """An iterator that yields StreamingDownloadTasks for cat sources.

  Given a list of strings that are object URLs ("gs://foo/object1"), yield a
  StreamingDownloadTask.

  Args:
    source_iterator (NameExpansionIterator): Yields sources resources that
      should be packaged in StreamingDownloadTasks.
    show_url (bool): Says whether or not to print the header before each
      object's content.
    start_byte (int): The byte index to start streaming from.
    end_byte (int|None): The byte index to stop streaming from.

  Yields:
    StreamingDownloadTask

  """

  stdout = os.fdopen(1, 'wb')
  dummy_destination_resource = resource_reference.FileObjectResource(
      storage_url.FileUrl('-')
  )
  for item in source_iterator:
    yield streaming_download_task.StreamingDownloadTask(
        item.resource,
        dummy_destination_resource,
        download_stream=stdout,
        show_url=show_url,
        start_byte=_get_start_byte(start_byte, item.resource.size),
        end_byte=end_byte,
    )
