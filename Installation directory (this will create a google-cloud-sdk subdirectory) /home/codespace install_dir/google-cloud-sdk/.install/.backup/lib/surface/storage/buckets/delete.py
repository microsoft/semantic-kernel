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
"""Implementation of rb command for deleting buckets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import name_expansion
from googlecloudsdk.command_lib.storage import plurality_checkable_iterator
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_graph_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.rm import delete_task_iterator_factory


class Delete(base.Command):
  """Deletes Cloud Storage buckets."""

  detailed_help = {
      'DESCRIPTION':
          """
      Deletes one or more Cloud Storage buckets.
      """,
      'EXAMPLES':
          """

      Delete a Google Cloud Storage bucket named "my-bucket":

        $ {command} gs://my-bucket

      Delete two buckets:

        $ {command} gs://my-bucket gs://my-other-bucket
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'urls', nargs='+', help='Specifies the URLs of the buckets to delete.')
    flags.add_additional_headers_flag(parser)
    flags.add_continue_on_error_flag(parser)

  def Run(self, args):
    for url_string in args.urls:
      url = storage_url.storage_url_from_string(url_string)
      errors_util.raise_error_if_not_bucket(args.command_path, url)

    task_status_queue = task_graph_executor.multiprocessing_context.Queue()

    bucket_iterator = delete_task_iterator_factory.DeleteTaskIteratorFactory(
        name_expansion.NameExpansionIterator(
            args.urls, include_buckets=name_expansion.BucketSetting.YES
        ),
        task_status_queue=task_status_queue,
    ).bucket_iterator()
    plurality_checkable_bucket_iterator = (
        plurality_checkable_iterator.PluralityCheckableIterator(
            bucket_iterator))

    self.exit_code = task_executor.execute_tasks(
        plurality_checkable_bucket_iterator,
        parallelizable=True,
        task_status_queue=task_status_queue,
        progress_manager_args=task_status.ProgressManagerArgs(
            increment_type=task_status.IncrementType.INTEGER,
            manifest_path=None),
        continue_on_error=args.continue_on_error)
