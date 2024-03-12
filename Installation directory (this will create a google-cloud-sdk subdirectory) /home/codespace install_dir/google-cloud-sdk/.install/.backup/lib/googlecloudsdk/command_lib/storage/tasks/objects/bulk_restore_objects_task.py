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
"""Task for bulk restoring soft-deleted objects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import request_config_factory
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.core import log


class BulkRestoreObjectsTask(task.Task):
  """Restores soft-deleted cloud storage objects."""

  def __init__(
      self,
      bucket_url,
      object_globs,
      allow_overwrite=False,
      deleted_after_time=None,
      deleted_before_time=None,
      user_request_args=None,
  ):
    """Initializes task.

    Args:
      bucket_url (StorageUrl): Launch a bulk restore operation for this bucket.
      object_globs (list[str]): Objects in the target bucket matching these glob
        patterns will be restored.
      allow_overwrite (bool): Overwrite existing live objects.
      deleted_after_time (datetime): Filter results to objects soft-deleted
        after this time. Backend will reject if used with `live_at_time`.
      deleted_before_time (datetime): Filter results to objects soft-deleted
        before this time. Backend will reject if used with `live_at_time`.
      user_request_args (UserRequestArgs|None): Contains restore settings.
    """
    super(BulkRestoreObjectsTask, self).__init__()
    self._bucket_url = bucket_url
    self._object_globs = object_globs
    self._allow_overwrite = allow_overwrite
    self._deleted_after_time = deleted_after_time
    self._deleted_before_time = deleted_before_time
    self._user_request_args = user_request_args

  def execute(self, task_status_queue=None):
    log.status.Print(
        'Creating bulk restore operation for bucket {} with globs: {}'.format(
            self._bucket_url, self._object_globs
        )
    )
    request_config = request_config_factory.get_request_config(
        # Arbitrarily use first glob to get CloudUrl for object.
        self._bucket_url.join(self._object_globs[0]),
        user_request_args=self._user_request_args,
    )

    created_operation = api_factory.get_api(
        self._bucket_url.scheme
    ).bulk_restore_objects(
        self._bucket_url,
        self._object_globs,
        request_config=request_config,
        allow_overwrite=self._allow_overwrite,
        deleted_after_time=self._deleted_after_time,
        deleted_before_time=self._deleted_before_time,
    )

    log.status.Print('Created: ' + created_operation.name)
    if task_status_queue:
      progress_callbacks.increment_count_callback(task_status_queue)

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return NotImplemented
    return (
        self._bucket_url == other._bucket_url
        and self._object_globs == other._object_globs
        and self._allow_overwrite == other._allow_overwrite
        and self._deleted_after_time == other._deleted_after_time
        and self._deleted_before_time == other._deleted_before_time
        and self._user_request_args == other._user_request_args
    )
