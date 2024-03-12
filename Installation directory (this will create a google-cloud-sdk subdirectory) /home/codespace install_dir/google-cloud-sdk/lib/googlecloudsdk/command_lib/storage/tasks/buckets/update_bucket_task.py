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
"""Task for updating a bucket."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import errors
from googlecloudsdk.api_lib.storage import request_config_factory
from googlecloudsdk.command_lib.artifacts import requests
from googlecloudsdk.command_lib.storage import errors as command_errors
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class UpdateBucketTask(task.Task):
  """Updates a cloud storage bucket's metadata."""

  def __init__(self, bucket_resource, user_request_args=None):
    """Initializes task.

    Args:
      bucket_resource (BucketResource|UnknownResource): The bucket to update.
      user_request_args (UserRequestArgs|None): Describes metadata updates to
          perform.
    """
    super(UpdateBucketTask, self).__init__()
    self._bucket_resource = bucket_resource
    self._user_request_args = user_request_args

  def __eq__(self, other):
    if not isinstance(other, UpdateBucketTask):
      return NotImplemented
    return (self._bucket_resource == other._bucket_resource and
            self._user_request_args == other._user_request_args)

  def _confirm_and_lock_retention_policy(self, api_client, bucket_resource,
                                         request_config):
    """Locks a buckets retention policy if possible and the user confirms.

    Args:
      api_client (cloud_api.CloudApi): API client that should issue the lock
        request.
      bucket_resource (BucketResource): Metadata of the bucket containing the
        retention policy to lock.
      request_config (request_config_factory._RequestConfig): Contains
        additional request parameters.
    """
    lock_prompt = (
        'This will permanently set the retention policy on "{}" to the'
        ' following:\n\n{}\n\nThis setting cannot be reverted. Continue? '
    ).format(self._bucket_resource, bucket_resource.retention_policy)

    if not bucket_resource.retention_policy:
      raise command_errors.Error(
          'Bucket "{}" does not have a retention policy.'.format(
              self._bucket_resource))
    elif bucket_resource.retention_policy_is_locked:
      log.error('Retention policy on "{}" is already locked.'.format(
          self._bucket_resource))
    elif console_io.PromptContinue(message=lock_prompt, default=False):
      log.status.Print('Locking retention policy on {}...'.format(
          self._bucket_resource))
      api_client.lock_bucket_retention_policy(bucket_resource, request_config)
    else:
      # Gsutil does not update the exit code here, so we cannot use
      # cancel_or_no with PromptContinue.
      log.error('Abort locking retention policy on "{}".'.format(
          self._bucket_resource))

  def execute(self, task_status_queue=None):
    log.status.Print('Updating {}...'.format(self._bucket_resource))
    request_config = request_config_factory.get_request_config(
        self._bucket_resource.storage_url,
        user_request_args=self._user_request_args)

    provider = self._bucket_resource.storage_url.scheme
    api_client = api_factory.get_api(provider)

    try:
      bucket_metadata = api_client.patch_bucket(
          self._bucket_resource, request_config=request_config)
    except errors.GcsApiError as e:
      # Service agent does not have the encrypter/decrypter role.
      if (e.payload.status_code == 403 and
          request_config.resource_args.default_encryption_key):

        service_agent = api_client.get_service_agent()
        requests.AddCryptoKeyPermission(
            request_config.resource_args.default_encryption_key,
            'serviceAccount:' + service_agent)

        bucket_metadata = api_client.patch_bucket(
            self._bucket_resource, request_config=request_config)
      else:
        raise

    if getattr(
        request_config.resource_args, 'retention_period_to_be_locked', None):
      self._confirm_and_lock_retention_policy(
          api_client, bucket_metadata, request_config)

    if task_status_queue:
      progress_callbacks.increment_count_callback(task_status_queue)
