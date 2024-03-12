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

"""Task for copying a managed folder."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import threading

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import errors
from googlecloudsdk.api_lib.storage import gcs_iam_util
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.cp import copy_util


class CopyManagedFolderTask(copy_util.CopyTaskWithExitHandler):
  """Represents a command operation copying an object around the cloud."""

  def __init__(
      self,
      source_resource,
      destination_resource,
      print_created_message=False,
      user_request_args=None,
      verbose=False,
  ):
    """Initializes CopyManagedFolderTask. Parent class documents arguments."""
    super(CopyManagedFolderTask, self).__init__(
        source_resource=source_resource,
        destination_resource=destination_resource,
        print_created_message=print_created_message,
        user_request_args=user_request_args,
        verbose=verbose,
    )
    self.parallel_processing_key = (
        self._destination_resource.storage_url.url_string
    )

  def execute(self, task_status_queue=None):
    source_url = self._source_resource.storage_url
    destination_url = self._destination_resource.storage_url
    api_client = api_factory.get_api(source_url.scheme)

    if task_status_queue is not None:
      progress_callback = progress_callbacks.FilesAndBytesProgressCallback(
          status_queue=task_status_queue,
          offset=0,
          length=0,
          source_url=self._source_resource.storage_url,
          destination_url=self._destination_resource.storage_url,
          operation_name=task_status.OperationName.INTRA_CLOUD_COPYING,
          process_id=os.getpid(),
          thread_id=threading.get_ident(),
      )
    else:
      progress_callback = None

    source_policy = api_client.get_managed_folder_iam_policy(
        source_url.bucket_name, source_url.object_name
    )

    try:
      api_client.create_managed_folder(
          destination_url.bucket_name,
          destination_url.object_name,
      )
    except errors.ConflictError:
      pass

    self._print_created_message_if_requested(self._destination_resource)

    # Source etag will not match the destination causing precondition failures.
    source_policy.etag = None
    # Version must be specified.
    source_policy.version = gcs_iam_util.IAM_POLICY_VERSION

    api_client.set_managed_folder_iam_policy(
        destination_url.bucket_name,
        destination_url.object_name,
        source_policy,
    )

    if progress_callback:
      progress_callback(0)

  def __eq__(self, other):
    if not isinstance(other, CopyManagedFolderTask):
      return NotImplemented
    return (
        self._source_resource == other._source_resource
        and self._destination_resource == other._destination_resource
        and self._print_created_message == other._print_created_message
        and self._user_request_args == other._user_request_args
        and self._verbose == other._verbose
    )
