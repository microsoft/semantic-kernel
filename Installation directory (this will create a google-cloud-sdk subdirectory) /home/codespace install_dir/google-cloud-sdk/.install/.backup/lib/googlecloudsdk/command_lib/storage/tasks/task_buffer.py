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
"""Implements a buffer for tasks used in task_graph_executor.

See go/parallel-processing-in-gcloud-storage for more information.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from six.moves import queue


class _PriorityWrapper:
  """Wraps a buffered task and tracks priority information.

  Attributes:
    task (Union[task.Task, str]): A buffered item. Expected to be a task or a
      string (to handle shutdowns) when used by task_graph_executor.
    priority (int): The priority of this task. A task with a lower value will be
      executed before a task with a higher value, since queue.PriorityQueue uses
      a min-heap.
  """

  def __init__(self, task, priority):
    self.task = task
    self.priority = priority

  def __lt__(self, other):
    return self.priority < other.priority


class TaskBuffer:
  """Stores and prioritizes tasks.

  The current implementation uses a queue.PriorityQueue under the hood, since
  in experiments we found that the heap it maintains did not add too much
  overhead. If it does end up being a bottleneck, the same API can be
  implemented with a collections.deque.
  """

  def __init__(self):
    self._queue = queue.PriorityQueue()

  def get(self):
    """Removes and returns an item from the buffer.

    Calls to `get` block if there are no elements in the queue, and return
    prioritized items before non-prioritized items.

    Returns:
      A buffered item. Expected to be a task or a string (to handle shutdowns)
      when used by task_graph_executor.
    """
    return self._queue.get().task

  def put(self, task, prioritize=False):
    """Adds an item to the buffer.

    Args:
      task (Union[task.Task, str]): A buffered item. Expected to be a task or a
        string (to handle shutdowns) when used by task_graph_executor.
      prioritize (bool): Tasks added with prioritize=True will be returned by
        `get` before tasks added with prioritize=False.
    """
    priority = 0 if prioritize else 1
    prioritized_item = _PriorityWrapper(task, priority)
    self._queue.put(prioritized_item)
