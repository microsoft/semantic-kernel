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
"""Task for rewriting an object's underlying data to update the metadata."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import request_config_factory
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import progress_callbacks
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.command_lib.storage.tasks.objects import patch_object_task
from googlecloudsdk.core import log


class RewriteObjectTask(task.Task):
  """Rewrites a cloud storage object's underlying data, changing metadata."""

  def __init__(self, object_resource, user_request_args=None):
    """Initializes task.

    Args:
      object_resource (resource_reference.ObjectResource): The object to update.
      user_request_args (UserRequestArgs|None): Describes metadata updates to
        perform.
    """
    super(RewriteObjectTask, self).__init__()
    self._object_resource = object_resource
    self._user_request_args = user_request_args

  def execute(self, task_status_queue=None):
    log.status.Print('Rewriting {}...'.format(self._object_resource))
    provider = self._object_resource.storage_url.scheme
    request_config = request_config_factory.get_request_config(
        self._object_resource.storage_url,
        user_request_args=self._user_request_args)

    api_client = api_factory.get_api(provider)
    existing_object_resource = api_client.get_object_metadata(
        self._object_resource.storage_url.bucket_name,
        self._object_resource.storage_url.object_name,
        generation=self._object_resource.storage_url.generation,
        request_config=request_config)

    if existing_object_resource.kms_key:  # Existing CMEK.
      encryption_changing = existing_object_resource.kms_key != getattr(
          encryption_util.get_encryption_key(), 'key', None)
    elif existing_object_resource.decryption_key_hash_sha256:  # Existing CSEK.
      encryption_changing = (
          existing_object_resource.decryption_key_hash_sha256 != getattr(
              encryption_util.get_encryption_key(), 'sha256', None))
    else:  # No existing encryption.
      # Clear flag can still reset an object to bucket's default encryption.
      encryption_changing = encryption_util.get_encryption_key() is not None

    new_storage_class = getattr(request_config.resource_args, 'storage_class',
                                None)
    storage_class_changing = (
        new_storage_class and
        new_storage_class != existing_object_resource.storage_class)

    if not (encryption_changing or storage_class_changing):
      log.warning('Proposed encryption key and storage class for' +
                  ' {} match the existing data.'.format(self._object_resource) +
                  ' Performing patch instead of rewrite.')
      return task.Output(
          additional_task_iterators=[
              [
                  patch_object_task.PatchObjectTask(
                      self._object_resource,
                      user_request_args=self._user_request_args,
                  )
              ]
          ],
          messages=None,
      )

    if storage_class_changing and not encryption_changing:
      # Preserve current encryption.
      new_encryption_key = encryption_util.get_encryption_key(
          existing_object_resource.decryption_key_hash_sha256,
          self._object_resource.storage_url)
    else:
      new_encryption_key = encryption_util.get_encryption_key()

    request_config_with_encryption = request_config_factory.get_request_config(
        self._object_resource.storage_url,
        user_request_args=self._user_request_args,
        decryption_key_hash_sha256=existing_object_resource
        .decryption_key_hash_sha256,
        encryption_key=new_encryption_key)

    api_client.copy_object(
        existing_object_resource,
        self._object_resource,
        request_config_with_encryption,
        should_deep_copy_metadata=True)

    if task_status_queue:
      progress_callbacks.increment_count_callback(task_status_queue)

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return NotImplemented
    return (self._object_resource == other._object_resource and
            self._user_request_args == other._user_request_args)
