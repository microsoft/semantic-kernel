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
"""Implementation of resume command for resuming Anywhere Cache instances."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_graph_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.buckets.anywhere_caches import resume_anywhere_cache_task


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Resume(base.Command):
  """Resume Anywhere Cache instances."""

  detailed_help = {
      'DESCRIPTION': """

      Resume operation could be used to revert the Paused and Disabled state.
      Once a paused/disabled cache is resumed, the cache will be set to
      RUNNING/CREATING state:
        1. RUNNING if the cache is active.
        2. CREATING if the cache is pending creation.
      """,
      'EXAMPLES': """

      The following command resume the anywhere cache instance of bucket
      ``my-bucket'' having anywhere_cache_id ``my-cache-id'':

        $ {command} my-bucket/my-cache-id
      """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'id',
        type=str,
        nargs='+',
        help=(
            'Identifiers for a Anywhere Cache instance. They are combination of'
            ' bucket_name/anywhere_cache_id. For example :'
            ' test-bucket/my-cache-id.'
        ),
    )

  def _get_task_iterator(self, args, task_status_queue):
    progress_callbacks.workload_estimator_callback(
        task_status_queue, len(args.id)
    )

    for id_str in args.id:
      bucket_name, _, anywhere_cache_id = id_str.rpartition(
          storage_url.CLOUD_URL_DELIMITER
      )
      yield resume_anywhere_cache_task.ResumeAnywhereCacheTask(
          bucket_name, anywhere_cache_id
      )

  def Run(self, args):
    task_status_queue = task_graph_executor.multiprocessing_context.Queue()
    task_iterator = self._get_task_iterator(args, task_status_queue)

    self.exit_code = task_executor.execute_tasks(
        task_iterator,
        parallelizable=True,
        task_status_queue=task_status_queue,
        progress_manager_args=task_status.ProgressManagerArgs(
            increment_type=task_status.IncrementType.INTEGER, manifest_path=None
        ),
    )
