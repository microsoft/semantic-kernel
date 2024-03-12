# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

"""Function for executing the tasks contained in a Task Iterator.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.storage import optimize_parameters_util
from googlecloudsdk.command_lib.storage import plurality_checkable_iterator
from googlecloudsdk.command_lib.storage.tasks import task_graph_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks import task_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


def _execute_tasks_sequential(task_iterator,
                              received_messages=None,
                              task_status_queue=None,
                              continue_on_error=False):
  """Executes task objects sequentially.

  Args:
    task_iterator (Iterable[task.Task]): An iterator for task objects.
    received_messages (Iterable[task.Message]): Messages sent to each
      task in task_iterator.
    task_status_queue (multiprocessing.Queue|None): Used by task to report it
      progress to a central location.
    continue_on_error (bool): If True, execution will continue even if
      errors occur.

  Returns:
    Tuple[int, Iterable[task.Message]]: The first element in the tuple
      is the exit code and the second element is an iterable of messages
      emitted by the tasks in task_iterator.
  """
  exit_code = 0
  messages_from_current_task_iterator = []
  for task in task_iterator:
    if received_messages is not None:
      task.received_messages = received_messages

    task_execution_error = None
    try:
      task_output = task.execute(task_status_queue=task_status_queue)
    except core_exceptions.Error as e:
      task_execution_error = e
      if continue_on_error:
        log.warning(str(e))
        exit_code = 1
        continue
      else:
        raise
    finally:
      task.exit_handler(task_execution_error, task_status_queue)

    if task_output is None:
      continue

    if task_output.messages is not None:
      messages_from_current_task_iterator.extend(task_output.messages)

    if task_output.additional_task_iterators is not None:
      messages_for_dependent_tasks = []
      for additional_task_iterator in task_output.additional_task_iterators:
        exit_code_from_dependent_tasks, messages_for_dependent_tasks = (
            _execute_tasks_sequential(
                additional_task_iterator,
                messages_for_dependent_tasks,
                task_status_queue=task_status_queue,
                continue_on_error=continue_on_error))
        exit_code = max(exit_code_from_dependent_tasks, exit_code)

  return exit_code, messages_from_current_task_iterator


def execute_tasks(task_iterator,
                  parallelizable=False,
                  task_status_queue=None,
                  progress_manager_args=None,
                  continue_on_error=False):
  """Call appropriate executor.

  Args:
    task_iterator: An iterator for task objects.
    parallelizable (boolean): Should tasks be executed in parallel.
    task_status_queue (multiprocessing.Queue|None): Used by task to report its
      progress to a central location.
    progress_manager_args (task_status.ProgressManagerArgs|None):
      Determines what type of progress indicator to display.
    continue_on_error (bool): Only applicable for sequential mode. If True,
      execution will continue even if errors occur.

  Returns:
    An integer indicating the exit_code. Zero indicates no fatal errors were
      raised.
  """
  task_util.require_python_3_5()
  plurality_checkable_task_iterator = (
      plurality_checkable_iterator.PluralityCheckableIterator(task_iterator))
  optimize_parameters_util.detect_and_set_best_config(
      is_estimated_multi_file_workload=(
          plurality_checkable_task_iterator.is_plural()))

  # Some tasks operate under the assumption that they will only be executed when
  # parallelizable is True, and use should_use_parallelism to determine how they
  # are executed.
  if parallelizable and task_util.should_use_parallelism():
    exit_code = task_graph_executor.TaskGraphExecutor(
        plurality_checkable_task_iterator,
        max_process_count=properties.VALUES.storage.process_count.GetInt(),
        thread_count=properties.VALUES.storage.thread_count.GetInt(),
        task_status_queue=task_status_queue,
        progress_manager_args=progress_manager_args).run()
  else:
    with task_status.progress_manager(task_status_queue, progress_manager_args):
      exit_code, _ = _execute_tasks_sequential(
          plurality_checkable_task_iterator,
          task_status_queue=task_status_queue,
          continue_on_error=continue_on_error)
  return exit_code
