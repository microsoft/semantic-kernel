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
"""Abstract task for handling components, slices, or parts of larger files.

Typically executed in a task iterator:
googlecloudsdk.command_lib.storage.tasks.task_executor.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc

from googlecloudsdk.command_lib.storage.tasks import task


class FilePartTask(task.Task):
  """Abstract class for handling a range of bytes in a file."""

  def __init__(self, source_resource, destination_resource, offset, length,
               component_number=None, total_components=None):
    """Initializes task.

    Args:
      source_resource (resource_reference.Resource): Source resource to copy.
      destination_resource (resource_reference.Resource): Target resource to
        copy to.
      offset (int): The index of the first byte in the range.
      length (int): The number of bytes in the range.
      component_number (int): If a multipart operation, indicates the
        component number.
      total_components (int): If a multipart operation, indicates the
        total number of components.
    """
    super(FilePartTask, self).__init__()
    self._source_resource = source_resource
    self._destination_resource = destination_resource
    self._offset = offset
    self._length = length
    self._component_number = component_number
    self._total_components = total_components

  @abc.abstractmethod
  def execute(self, task_status_queue=None):
    pass

  def __eq__(self, other):
    if not isinstance(other, FilePartTask):
      return NotImplemented
    return (self._destination_resource == other._destination_resource and
            self._source_resource == other._source_resource and
            self._offset == other._offset and self._length == other._length
            and self._component_number == other._component_number and
            self._total_components == other._total_components)
