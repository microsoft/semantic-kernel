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
"""Task for creating an Anywhere Cache instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.core import log


class CreateAnywhereCacheTask(task.Task):
  """Creates an Anywhere Cache instance in particular zone of a bucket."""

  def __init__(self, bucket_url, zone, admission_policy=None, ttl=None):
    """Initializes task.

    Args:
      bucket_url (CloudUrl): The URL of the bucket where the Anywhere Cache
        should be created.
      zone (str): Name of the zonal locations where the Anywhere Cache should be
        created.
      admission_policy (str|None): The cache admission policy decides for each
        cache miss, that is whether to insert the missed block or not.
      ttl (str|None): Cache entry time-to-live in seconds
    """
    super(CreateAnywhereCacheTask, self).__init__()
    self._bucket_url = bucket_url
    self._zone = zone
    self._admission_policy = admission_policy
    self._ttl = ttl
    self.parallel_processing_key = '{}/{}'.format(bucket_url.bucket_name, zone)

  def execute(self, task_status_queue=None):
    log.status.Print(
        'Creating a cache instance for bucket {} in zone {}...'.format(
            self._bucket_url, self._zone
        )
    )

    provider = self._bucket_url.scheme
    api_client = api_factory.get_api(provider)
    response = api_client.create_anywhere_cache(
        self._bucket_url.bucket_name,
        self._zone,
        admission_policy=self._admission_policy,
        ttl=self._ttl,
    )

    log.status.Print(
        'Initiated the operation id: {} for creating a cache instance for'
        ' bucket {} in zone {}...'.format(
            response.name, self._bucket_url, self._zone
        )
    )

    if task_status_queue:
      progress_callbacks.increment_count_callback(task_status_queue)

  def __eq__(self, other):
    if not isinstance(other, CreateAnywhereCacheTask):
      return NotImplemented
    return (
        self._bucket_url == other._bucket_url
        and self._zone == other._zone
        and self._admission_policy == other._admission_policy
        and self._ttl == other._ttl
    )
