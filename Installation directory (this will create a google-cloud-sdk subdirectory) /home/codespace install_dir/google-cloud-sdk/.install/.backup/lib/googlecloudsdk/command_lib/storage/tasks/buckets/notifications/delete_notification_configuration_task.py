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
"""Task for deleting a notification configuration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage.tasks import task


class DeleteNotificationConfigurationTask(task.Task):
  """Deletes a notification configuration."""

  def __init__(self, bucket_url, notification_id):
    """Initializes task.

    Args:
      bucket_url (storage_url.CloudUrl): URL of bucket that notification
        configuration exists on.
      notification_id (str): Name of the notification configuration (integer as
        string).
    """
    super(__class__, self).__init__()
    self._bucket_url = bucket_url
    self._notification_id = notification_id

    self.parallel_processing_key = bucket_url.url_string + '|' + notification_id

  def execute(self, task_status_queue=None):
    provider = self._bucket_url.scheme
    api_factory.get_api(provider).delete_notification_configuration(
        self._bucket_url, self._notification_id)
    if task_status_queue:
      progress_callbacks.increment_count_callback(task_status_queue)

  def __eq__(self, other):
    if not isinstance(other, DeleteNotificationConfigurationTask):
      return NotImplemented
    return self.parallel_processing_key == other.parallel_processing_key
