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
"""General utilities for copies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import errors as api_errors
from googlecloudsdk.command_lib.storage import errors as command_errors
from googlecloudsdk.command_lib.storage import manifest_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import resource_util
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

_EARLY_DELETION_MINIMUM_DAYS = {
    'nearline': 30,
    'coldline': 90,
    'archive': 365,
}


class CopyTask(task.Task):
  """Parent task that handles common attributes and an __init__ status print."""

  def __init__(
      self,
      source_resource,
      destination_resource,
      print_created_message=False,
      print_source_version=False,
      user_request_args=None,
      verbose=False,
  ):
    """Initializes task.

    Args:
      source_resource (resource_reference.Resource): Source resource to copy.
      destination_resource (resource_reference.Resource): Target resource to
        copy to.
      print_created_message (bool): Print a message containing the URL of the
        copy result.
      print_source_version (bool): Print source object version in status message
        enabled by the `verbose` kwarg.
      user_request_args (UserRequestArgs|None): Various user-set values
        typically converted to an API-specific RequestConfig.
      verbose (bool): Print a "copying" status message on initialization.
    """
    super(CopyTask, self).__init__()
    self._source_resource = source_resource
    self._destination_resource = destination_resource
    self._print_created_message = print_created_message
    self._print_source_version = print_source_version
    self._user_request_args = user_request_args
    self._verbose = verbose

    self._send_manifest_messages = bool(
        self._user_request_args and self._user_request_args.manifest_path
    )

    if verbose:
      if self._print_source_version:
        source_string = source_resource.storage_url.url_string
      else:
        source_string = source_resource.storage_url.versionless_url_string
      log.status.Print(
          'Copying {} to {}'.format(
              source_string,
              destination_resource.storage_url.versionless_url_string,
          )
      )

  def _print_created_message_if_requested(self, resource):
    if self._print_created_message:
      log.status.Print('Created: {}'.format(resource))


class ObjectCopyTask(CopyTask):
  """Parent task that handles common attributes for object copy tasks."""

  def __init__(
      self,
      source_resource,
      destination_resource,
      posix_to_set=None,
      print_created_message=False,
      print_source_version=False,
      user_request_args=None,
      verbose=False,
  ):
    """Initializes task.

    Args:
      source_resource (resource_reference.Resource): See parent class.
      destination_resource (resource_reference.Resource): See parent class.
      posix_to_set (PosixAttributes|None): POSIX info set as custom cloud
        metadata on target.
      print_created_message (bool): See parent class.
      print_source_version (bool): See parent class.
      user_request_args (UserRequestArgs|None): See parent class.
      verbose (bool): Print a "copying" status message on initialization.
    """
    self._posix_to_set = posix_to_set
    # Set before super().__init__ call because otherwise the attribute won't be
    # available for the _get_source_string_for_status_message call.
    self._print_source_version = print_source_version

    super(ObjectCopyTask, self).__init__(
        source_resource,
        destination_resource,
        print_created_message,
        print_source_version,
        user_request_args,
        verbose,
    )


class _ExitHandlerMixin:
  """Provides an exit handler for copy tasks."""

  def exit_handler(self, error=None, task_status_queue=None):
    """Send copy result info to manifest if requested."""
    if error and self._send_manifest_messages:
      if not task_status_queue:
        raise command_errors.Error(
            'Unable to send message to manifest for source: {}'.format(
                self._source_resource
            )
        )
      manifest_util.send_error_message(task_status_queue, self._source_resource,
                                       self._destination_resource, error)


class CopyTaskWithExitHandler(
    # _ExitHandlerMixin must precede CopyTask, otherwise task.Task.exit_hander
    # overrides the intended implementation.
    _ExitHandlerMixin,
    CopyTask,
):
  """Parent task with an exit handler for non-object copy tasks."""


class ObjectCopyTaskWithExitHandler(_ExitHandlerMixin, ObjectCopyTask):
  """Parent task with an exit handler for object copy tasks."""


def get_no_clobber_message(destination_url):
  """Returns standardized no clobber warning."""
  return 'Skipping existing destination item (no-clobber): {}'.format(
      destination_url)


def check_for_cloud_clobber(user_request_args, api_client,
                            destination_resource):
  """Returns if cloud destination object exists if no-clobber enabled."""
  if not (user_request_args and user_request_args.no_clobber):
    return False
  try:
    api_client.get_object_metadata(
        destination_resource.storage_url.bucket_name,
        destination_resource.storage_url.object_name,
        fields_scope=cloud_api.FieldsScope.SHORT)
  except api_errors.NotFoundError:
    return False
  return True


def get_generation_match_value(request_config):
  """Prioritizes user-input generation over no-clobber zero value."""
  if request_config.precondition_generation_match is not None:
    return request_config.precondition_generation_match
  if request_config.no_clobber:
    return 0
  return None


def raise_if_mv_early_deletion_fee_applies(object_resource):
  """Raises error if Google Cloud Storage object will incur an extra charge."""
  if not (properties.VALUES.storage.check_mv_early_deletion_fee.GetBool() and
          object_resource.storage_url.scheme is storage_url.ProviderPrefix.GCS
          and object_resource.creation_time and
          object_resource.storage_class in _EARLY_DELETION_MINIMUM_DAYS):
    return

  minimum_lifetime = _EARLY_DELETION_MINIMUM_DAYS[
      object_resource.storage_class.lower()]
  creation_datetime_utc = resource_util.convert_datetime_object_to_utc(
      object_resource.creation_time)
  current_datetime_utc = resource_util.convert_datetime_object_to_utc(
      datetime.datetime.now())

  if current_datetime_utc < creation_datetime_utc + datetime.timedelta(
      days=minimum_lifetime):
    raise exceptions.Error(
        ('Deleting {} may incur an early deletion charge. Note: the source'
         ' object of a mv operation is deleted.\nThe object appears to have'
         ' been created on {}, and the minimum time before deletion for the {}'
         ' storage class is {} days.\nTo allow deleting the object anyways, run'
         ' "gcloud config set storage/check_mv_early_deletion_fee False"'
        ).format(object_resource, object_resource.creation_time,
                 object_resource.storage_class, minimum_lifetime))
