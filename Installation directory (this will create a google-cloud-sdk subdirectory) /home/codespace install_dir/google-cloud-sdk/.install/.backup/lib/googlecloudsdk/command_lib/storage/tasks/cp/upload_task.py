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
"""Base class for tasks that upload files."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.storage.tasks import task


class UploadTask(task.Task):
  """Base class for tasks that upload files."""

  def __init__(self, source_resource, destination_resource, length):
    """Initializes a task instance.

    Args:
      source_resource (resource_reference.FileObjectResource): The file to
        upload.
      destination_resource (resource_reference.ObjectResource|UnknownResource):
        Destination metadata for the upload.
      length (int): The size of source_resource.
    """
    super(UploadTask, self).__init__()
    self._source_resource = source_resource
    self._destination_resource = destination_resource
    self._length = length

  def __eq__(self, other):
    if not isinstance(other, self.__class__):
      return NotImplemented
    return (
        self._source_resource == other._source_resource and
        self._destination_resource == other._destination_resource and
        self._length == other._length
    )
