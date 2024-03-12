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
"""Tasks for deleting resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import os

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import request_config_factory
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.core import log


class DeleteTask(task.Task):
  """Base class for tasks that delete a resource."""

  def __init__(self, url, user_request_args=None, verbose=True):
    """Initializes task.

    Args:
      url (storage_url.StorageUrl): URL of the resource to delete.
      user_request_args (UserRequestArgs|None): Values for RequestConfig.
      verbose (bool): If true, prints status messages. Otherwise, does not print
        anything.
    """
    super().__init__()
    self._url = url
    self._user_request_args = user_request_args
    self._verbose = verbose

    self.parallel_processing_key = url.url_string

  @abc.abstractmethod
  def _perform_deletion(self):
    """Deletes a resource. Overridden by children."""
    raise NotImplementedError

  def execute(self, task_status_queue=None):
    if self._verbose:
      log.status.Print('Removing {}...'.format(self._url))

    self._perform_deletion()

    if task_status_queue:
      progress_callbacks.increment_count_callback(task_status_queue)

  def __eq__(self, other):
    if not isinstance(other, self.__class__):
      return NotImplemented
    return (
        self._url == other._url
        and self._user_request_args == other._user_request_args
        and self._verbose == other._verbose
    )


class DeleteFileTask(DeleteTask):
  """Task to delete a file."""

  def _perform_deletion(self):
    os.remove(self._url.object_name)


class CloudDeleteTask(DeleteTask):
  """Base class for tasks that delete a cloud resource."""

  @abc.abstractmethod
  def _make_delete_api_call(self, client, request_config):
    """Performs an API call to delete a resource. Overridden by children."""
    raise NotImplementedError

  def _perform_deletion(self):
    client = api_factory.get_api(self._url.scheme)
    request_config = request_config_factory.get_request_config(
        self._url, user_request_args=self._user_request_args
    )
    return self._make_delete_api_call(client, request_config)


class DeleteBucketTask(CloudDeleteTask):
  """Task to delete a bucket."""

  def _make_delete_api_call(self, client, request_config):
    try:
      client.delete_bucket(self._url.bucket_name, request_config)
    # pylint:disable=broad-except
    except Exception as error:
      # pylint:enable=broad-except
      if 'not empty' in str(error):
        raise type(error)(
            'Bucket is not empty. To delete all objects and then delete'
            ' bucket, use: gcloud storage rm -r'
        )
      else:
        raise


class DeleteManagedFolderTask(CloudDeleteTask):
  """Task to delete a managed folder."""

  @property
  def managed_folder_url(self):
    """The URL of the resource deleted by this task.

    Exposing this allows execution to respect containment order.
    """
    return self._url

  def _make_delete_api_call(self, client, request_config):
    del request_config  # Unused.
    client.delete_managed_folder(self._url.bucket_name, self._url.object_name)


class DeleteObjectTask(CloudDeleteTask):
  """Task to delete an object."""

  def _make_delete_api_call(self, client, request_config):
    client.delete_object(self._url, request_config)
