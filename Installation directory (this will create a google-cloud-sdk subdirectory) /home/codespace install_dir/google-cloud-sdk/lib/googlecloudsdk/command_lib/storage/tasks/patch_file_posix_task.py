# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Task for updating a local file's POSIX metadata."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.storage import posix_util
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.core import log


class PatchFilePosixTask(task.Task):
  """Updates a local file's POSIX metadata."""

  def __init__(
      self,
      system_posix_data,
      source_resource,
      destination_resource,
      known_source_posix=None,
      known_destination_posix=None,
  ):
    """Initializes task.

    Args:
      system_posix_data (SystemPosixData): Contains system-wide POSIX metadata.
      source_resource (resource_reference.ObjectResource): Contains custom POSIX
        metadata and URL for error logging.
      destination_resource (resource_reference.FileObjectResource): File to set
        POSIX metadata on.
      known_source_posix (PosixAttributes|None): Use pre-parsed POSIX data
        instead of extracting from source.
      known_destination_posix (PosixAttributes|None): Use pre-parsed POSIX data
        instead of extracting from destination.
    """
    super(PatchFilePosixTask, self).__init__()
    self._system_posix_data = system_posix_data
    self._source_resource = source_resource
    self._destination_resource = destination_resource
    self._known_source_posix = known_source_posix
    self._known_destination_posix = known_destination_posix

  def execute(self, task_status_queue=None):
    log.status.Print('Patching {}...'.format(self._destination_resource))
    posix_util.set_posix_attributes_on_file_if_valid(
        self._system_posix_data,
        self._source_resource,
        self._destination_resource,
        known_source_posix=self._known_source_posix,
        known_destination_posix=self._known_destination_posix,
    )

    if task_status_queue:
      progress_callbacks.increment_count_callback(task_status_queue)

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return NotImplemented
    return (
        self._system_posix_data == other._system_posix_data
        and self._source_resource == other._source_resource
        and self._destination_resource == other._destination_resource
        and self._known_source_posix == other._known_source_posix
        and self._known_destination_posix == other._known_destination_posix
    )
