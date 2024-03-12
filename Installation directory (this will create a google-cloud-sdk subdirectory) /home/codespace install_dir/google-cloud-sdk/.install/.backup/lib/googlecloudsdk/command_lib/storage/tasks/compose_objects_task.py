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
"""Task for composing storage objects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import request_config_factory
from googlecloudsdk.command_lib.storage import errors as command_errors
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.core import log


class ComposeObjectsTask(task.Task):
  """Composes storage objects."""

  def __init__(
      self,
      source_resources,
      destination_resource,
      original_source_resource=None,
      posix_to_set=None,
      print_status_message=False,
      user_request_args=None,
  ):
    """Initializes task.

    Args:
      source_resources (list[ObjectResource|UnknownResource]): The objects to
        compose. This field accepts UnknownResources since it should allow
        ComposeObjectsTasks to be initialized before the target objects have
        been created.
      destination_resource (resource_reference.UnknownResource): Metadata for
        the resulting composite object.
      original_source_resource (Resource|None): Useful for finding metadata to
        apply to final object. For instance, if doing a composite upload, this
        would represent the pre-split local file.
      posix_to_set (PosixAttributes|None): POSIX info set as custom cloud
        metadata on target. If preserving POSIX, avoids re-parsing metadata from
        file system.
      print_status_message (bool): If True, the task prints the status message.
      user_request_args (UserRequestArgs|None): Values for RequestConfig.
    """
    super(ComposeObjectsTask, self).__init__()
    self._source_resources = source_resources
    self._destination_resource = destination_resource
    self._original_source_resource = original_source_resource
    self._posix_to_set = posix_to_set
    self._print_status_message = print_status_message
    self._user_request_args = user_request_args

  def execute(self, task_status_queue=None):
    del task_status_queue  # Unused.
    provider = self._destination_resource.storage_url.scheme
    api = api_factory.get_api(provider)
    if cloud_api.Capability.COMPOSE_OBJECTS not in api.capabilities:
      raise command_errors.Error(
          'Compose is not available with requested provider: {}'.format(
              provider))
    for source_resource in self._source_resources:
      if source_resource.storage_url.bucket_name != self._destination_resource.storage_url.bucket_name:
        raise command_errors.Error(
            'Inter-bucket composing not supported')
    request_config = request_config_factory.get_request_config(
        self._destination_resource.storage_url,
        user_request_args=self._user_request_args)

    if self._print_status_message:
      log.status.write('Composing {} from {} component object(s).\n'.format(
          self._destination_resource, len(self._source_resources)))

    created_resource = api.compose_objects(
        self._source_resources,
        self._destination_resource,
        request_config,
        original_source_resource=self._original_source_resource,
        posix_to_set=self._posix_to_set,
    )

    return task.Output(
        messages=[
            task.Message(
                topic=task.Topic.CREATED_RESOURCE, payload=created_resource),
        ],
        additional_task_iterators=[])

  def __eq__(self, other):
    if not isinstance(other, ComposeObjectsTask):
      return NotImplemented
    return (self._source_resources == other._source_resources and
            self._destination_resource == other._destination_resource and
            self._user_request_args == other._user_request_args)
