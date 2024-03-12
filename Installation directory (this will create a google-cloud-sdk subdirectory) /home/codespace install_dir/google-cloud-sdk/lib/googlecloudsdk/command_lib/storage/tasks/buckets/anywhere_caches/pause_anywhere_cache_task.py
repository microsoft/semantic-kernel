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
"""Task for pausing an Anywhere Cache instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.core import log


class PauseAnywhereCacheTask(task.Task):
  """Task for pausing an Anywhere Cache instance."""

  def __init__(self, bucket_name, zone):
    """Initializes task."""
    super(PauseAnywhereCacheTask, self).__init__()
    self._bucket_name = bucket_name
    self._anywhere_cache_id = zone
    self.parallel_processing_key = '{}/{}'.format(bucket_name, zone)

  def execute(self, task_status_queue=None):
    log.status.Print(
        'Requesting to pause a cache instance of bucket gs://{} having'
        ' anywhere_cache_id {}'.format(
            self._bucket_name, self._anywhere_cache_id
        )
    )
    provider = storage_url.ProviderPrefix.GCS
    api_factory.get_api(provider).pause_anywhere_cache(
        self._bucket_name,
        self._anywhere_cache_id,
    )

    if task_status_queue:
      progress_callbacks.increment_count_callback(task_status_queue)

  def __eq__(self, other):
    if not isinstance(other, PauseAnywhereCacheTask):
      return NotImplemented
    return (
        self._bucket_name == other._bucket_name
        and self._anywhere_cache_id == other._anywhere_cache_id
    )
