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
"""Task for IAM policies on storage resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage.tasks import task


class _SetIamPolicyTask(task.Task):
  """Base class for tasks that set IAM policies."""

  def __init__(self, url, policy):
    """Initializes task.

    Args:
      url (StorageUrl): Used to identify cloud resource to set policy on.
      policy (object): Provider-specific data type. Currently, only available
        for GCS so Apitools messages.Policy object. If supported for more
        providers in the future, use a generic container.
    """
    super(_SetIamPolicyTask, self).__init__()
    self._url = url
    self._policy = policy

  @abc.abstractmethod
  def _make_set_api_call(self, client):
    """Makes an API call to set the IAM policy. Overridden by children."""
    pass

  def execute(self, task_status_queue=None):
    """Executes task."""
    client = api_factory.get_api(self._url.scheme)
    new_policy = self._make_set_api_call(client)

    if task_status_queue:
      progress_callbacks.increment_count_callback(task_status_queue)

    return task.Output(
        additional_task_iterators=None,
        messages=[task.Message(task.Topic.SET_IAM_POLICY, payload=new_policy)])

  def __eq__(self, other):
    if not isinstance(other, _SetIamPolicyTask):
      return NotImplemented
    return self._url == other._url and self._policy == other._policy


class SetBucketIamPolicyTask(_SetIamPolicyTask):

  def _make_set_api_call(self, client):
    return client.set_bucket_iam_policy(self._url.bucket_name, self._policy)


class SetManagedFolderIamPolicyTask(_SetIamPolicyTask):

  def _make_set_api_call(self, client):
    return client.set_managed_folder_iam_policy(
        self._url.bucket_name, self._url.object_name, self._policy
    )


class SetObjectIamPolicyTask(_SetIamPolicyTask):

  def _make_set_api_call(self, client):
    return client.set_object_iam_policy(
        self._url.bucket_name,
        self._url.object_name,
        self._policy,
        generation=self._url.generation,
    )
