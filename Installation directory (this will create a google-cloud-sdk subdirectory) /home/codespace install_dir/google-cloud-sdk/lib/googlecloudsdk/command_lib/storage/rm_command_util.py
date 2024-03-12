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
"""Generic logic for rm and mv command surfaces.

Tested in mv_test.py, rm_test.py, and managed_folders/delete_test.py
"""

from googlecloudsdk.command_lib.storage import folder_util
from googlecloudsdk.command_lib.storage import plurality_checkable_iterator
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks import task_util
from googlecloudsdk.command_lib.storage.tasks.rm import delete_task_iterator_factory
from googlecloudsdk.core import log


def remove_managed_folders(
    args,
    source_expansion_iterator,
    task_status_queue,
    raise_error_for_unmatched_urls=False,
    verbose=False,
):
  """Creates and executes tasks for removing managed folders."""
  task_iterator_factory = (
      delete_task_iterator_factory.DeleteTaskIteratorFactory(
          source_expansion_iterator,
          task_status_queue=task_status_queue,
      )
  )
  delete_task_iterator = (
      plurality_checkable_iterator.PluralityCheckableIterator(
          folder_util.reverse_containment_order(
              task_iterator_factory.managed_folder_iterator(),
              get_url_function=(lambda task: task.managed_folder_url),
          )
      )
  )

  if delete_task_iterator.is_empty() and not raise_error_for_unmatched_urls:
    return 0

  if verbose:
    log.status.Print('Removing managed folders:')

  return task_executor.execute_tasks(
      delete_task_iterator,
      parallelizable=False,
      task_status_queue=task_status_queue,
      progress_manager_args=task_status.ProgressManagerArgs(
          task_status.IncrementType.INTEGER,
          manifest_path=None,
      ),
      # Exceptions halting execution at this stage would be unexpected when
      # using parallelization for other stages.
      continue_on_error=(
          args.continue_on_error or task_util.should_use_parallelism()
      ),
  )
