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
"""Task for updating an object's metadata."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import request_config_factory
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.core import log


class PatchObjectTask(task.Task):
  """Updates a cloud storage object's metadata."""

  def __init__(
      self, object_resource, posix_to_set=None, user_request_args=None
  ):
    """Initializes task.

    Args:
      object_resource (resource_reference.ObjectResource): The object to update.
      posix_to_set (PosixAttributes|None): POSIX info set as custom cloud
        metadata on target.
      user_request_args (UserRequestArgs|None): Describes metadata updates to
        perform.
    """
    super(PatchObjectTask, self).__init__()
    self._object_resource = object_resource
    self._posix_to_set = posix_to_set
    self._user_request_args = user_request_args

  def execute(self, task_status_queue=None):
    log.status.Print('Patching {}...'.format(self._object_resource))
    provider = self._object_resource.storage_url.scheme
    request_config = request_config_factory.get_request_config(
        self._object_resource.storage_url,
        user_request_args=self._user_request_args)

    api_factory.get_api(provider).patch_object_metadata(
        self._object_resource.storage_url.bucket_name,
        self._object_resource.storage_url.object_name,
        self._object_resource,
        request_config=request_config,
        posix_to_set=self._posix_to_set,
    )

    if task_status_queue:
      progress_callbacks.increment_count_callback(task_status_queue)

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return NotImplemented
    return (
        self._object_resource == other._object_resource
        and self._posix_to_set == other._posix_to_set
        and self._user_request_args == other._user_request_args
    )
