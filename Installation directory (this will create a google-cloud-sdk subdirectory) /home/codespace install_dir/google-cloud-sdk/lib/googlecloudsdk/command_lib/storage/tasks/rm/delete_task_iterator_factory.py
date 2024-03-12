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
"""Iterator for deleting buckets and objects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.tasks.rm import delete_task
from six.moves import queue


class DeleteTaskIteratorFactory:
  """Creates bucket and object delete task iterators."""

  def __init__(self,
               name_expansion_iterator,
               task_status_queue=None,
               user_request_args=None):
    """Initializes factory.

    Args:
      name_expansion_iterator (NameExpansionIterator): Iterable of wildcard
        iterators to flatten.
      task_status_queue (multiprocessing.Queue|None): Used for estimating total
        workload from this iterator.
      user_request_args (UserRequestArgs|None): Values for RequestConfig.
    """
    self._name_expansion_iterator = name_expansion_iterator
    self._task_status_queue = task_status_queue
    self._user_request_args = user_request_args

    self._bucket_delete_tasks = queue.Queue()
    self._managed_folder_delete_tasks = queue.Queue()
    self._object_delete_tasks = queue.Queue()
    self._flat_wildcard_results_iterator = (
        self._get_flat_wildcard_results_iterator())

  def _get_flat_wildcard_results_iterator(self):
    """Iterates through items matching delete query, dividing into two lists.

    Separates objects and buckets, so we can return two separate iterators.

    Yields:
      True if resource found.
    """
    for name_expansion_result in self._name_expansion_iterator:
      resource = name_expansion_result.resource
      resource_url = resource.storage_url
      # The wildcard iterator can return UnknownResources, so we use URLs to
      # check for buckets.
      if resource_url.is_bucket():
        self._bucket_delete_tasks.put(
            delete_task.DeleteBucketTask(resource_url)
        )
      elif isinstance(resource, resource_reference.ManagedFolderResource):
        self._managed_folder_delete_tasks.put(
            delete_task.DeleteManagedFolderTask(resource_url)
        )
      else:
        self._object_delete_tasks.put(
            delete_task.DeleteObjectTask(
                resource_url, user_request_args=self._user_request_args
            )
        )
      yield True

  def _resource_iterator(self, resource_queue):
    """Yields a resource from the queue."""
    resource_count = 0
    try:
      while not resource_queue.empty() or next(
          self._flat_wildcard_results_iterator
      ):
        if not resource_queue.empty():
          resource_count += 1
          yield resource_queue.get()
    except StopIteration:
      pass
    if resource_count:
      progress_callbacks.workload_estimator_callback(
          self._task_status_queue, resource_count
      )

  def bucket_iterator(self):
    return self._resource_iterator(self._bucket_delete_tasks)

  def managed_folder_iterator(self):
    return self._resource_iterator(self._managed_folder_delete_tasks)

  def object_iterator(self):
    return self._resource_iterator(self._object_delete_tasks)
