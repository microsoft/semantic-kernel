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
"""Command to delete notification configurations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import notification_configuration_iterator
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_graph_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.buckets.notifications import delete_notification_configuration_task


def _delete_notification_configuration_task_iterator(urls):
  """Creates delete tasks from notification_configuration_iterator."""
  for notification_configuration_iterator_result in (
      notification_configuration_iterator
      .get_notification_configuration_iterator(urls)):
    yield (delete_notification_configuration_task
           .DeleteNotificationConfigurationTask(
               notification_configuration_iterator_result.bucket_url,
               notification_configuration_iterator_result
               .notification_configuration.id))


class Delete(base.DeleteCommand):
  """Delete notification configurations from a bucket."""

  detailed_help = {
      'DESCRIPTION':
          """
      *{command}* deletes notification configurations from a bucket. If a
      notification configuration name is passed as a parameter, that
      configuration alone is deleted. If a bucket name is passed, all
      notification configurations associated with the bucket are deleted.

      Cloud Pub/Sub topics associated with this notification configuration
      are not deleted by this command. Those must be deleted separately,
      for example with the command "gcloud pubsub topics delete".
      """,
      'EXAMPLES':
          """
      Delete a single notification configuration (with ID 3) in the
      bucket `example-bucket`:

        $ {command} projects/_/buckets/example-bucket/notificationConfigs/3

      Delete all notification configurations in the bucket `example-bucket`:

        $ {command} gs://example-bucket
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'urls',
        nargs='+',
        help='Specifies notification configuration names or buckets.')

  def Run(self, args):
    task_status_queue = task_graph_executor.multiprocessing_context.Queue()
    task_executor.execute_tasks(
        _delete_notification_configuration_task_iterator(args.urls),
        parallelizable=True,
        task_status_queue=task_status_queue,
        progress_manager_args=task_status.ProgressManagerArgs(
            increment_type=task_status.IncrementType.INTEGER,
            manifest_path=None),
    )
