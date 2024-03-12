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
"""Implementation of update command for updating Anywhere Cache instances."""

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_graph_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.buckets.anywhere_caches import patch_anywhere_cache_task


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update Anywhere Cache instances."""

  detailed_help = {
      'DESCRIPTION': """

      Update one or more Anywhere Cache instances. A cache instance can be
      updated if its state is created or pending creation.
      """,
      'EXAMPLES': """

      The following command updates cache entry's ttl, and admisson policy of
      anywhere cache instance in bucket ``my-bucket'' having anywhere_cache_id
      ``my-cache-id'':

        $ {command} my-bucket/my-cache-id --ttl=6h --admission-policy='ADMIT_ON_SECOND_MISS'

      The following command updates cache entry's ttl of anywhere cache
      instances in bucket ``bucket-1'' and ``bucket-2'' having anywhere_cache_id
      ``my-cache-id-1'', and ``my-cache-id-2'' respectively:

        $ {command} bucket-1/my-cache-id-1 bucket-2/my-cache-id-2 --ttl=6h
      """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'id',
        type=str,
        nargs='+',
        help=(
            'Identifiers for a Anywhere Cache Instance.They are combination of'
            ' bucket_name/anywhere_cache_id. For example :'
            ' test-bucket/my-cache-id.'
        ),
    )

    parser.add_argument(
        '--ttl',
        type=arg_parsers.Duration(),
        help='Cache entry time-to-live. Default to 24h if not provided.',
    )

    flags.add_admission_policy_flag(parser)

  def get_task_iterator(self, args, task_status_queue):
    progress_callbacks.workload_estimator_callback(
        task_status_queue, len(args.id)
    )

    ttl = str(args.ttl) + 's' if args.ttl else None

    for id_str in args.id:
      bucket_name, _, anywhere_cache_id = id_str.rpartition('/')
      yield patch_anywhere_cache_task.PatchAnywhereCacheTask(
          bucket_name,
          anywhere_cache_id,
          admission_policy=args.admission_policy,
          ttl=ttl,
      )

  def Run(self, args):
    task_status_queue = task_graph_executor.multiprocessing_context.Queue()
    task_iterator = self.get_task_iterator(args, task_status_queue)

    self.exit_code = task_executor.execute_tasks(
        task_iterator,
        parallelizable=True,
        task_status_queue=task_status_queue,
        progress_manager_args=task_status.ProgressManagerArgs(
            increment_type=task_status.IncrementType.INTEGER, manifest_path=None
        ),
    )
