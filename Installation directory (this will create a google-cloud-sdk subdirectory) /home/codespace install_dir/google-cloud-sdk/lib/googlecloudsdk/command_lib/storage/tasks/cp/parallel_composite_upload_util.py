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
"""Utilities for parallel composite upload operation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import errors
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import scaled_integer


_STANDARD_STORAGE_CLASS = 'STANDARD'


def is_destination_composite_upload_compatible(destination_resource,
                                               user_request_args):
  """Checks if destination bucket is compatible for parallel composite upload.

  This function performs a GET bucket call to determine if the bucket's default
  storage class and retention period meet the criteria.

  Args:
    destination_resource(CloudResource|UnknownResource):
      Destination resource to which the files should be uploaded.
    user_request_args (UserRequestArgs|None): Values from user flags.

  Returns:
    True if the bucket satisfies the storage class and retention policy
    criteria.

  """
  api_client = api_factory.get_api(destination_resource.storage_url.scheme)
  try:
    bucket_resource = api_client.get_bucket(
        destination_resource.storage_url.bucket_name)
  except errors.CloudApiError as e:
    status = getattr(e, 'status_code', None)
    if status in (401, 403):
      log.error(
          'Cannot check if the destination bucket is compatible for running'
          ' parallel composite uploads as the user does not permission to'
          ' perform GET operation on the bucket. The operation will be'
          ' performed without parallel composite upload feature and hence'
          ' might perform relatively slower.')
      return False
    else:
      raise

  resource_args = getattr(user_request_args, 'resource_args', None)
  object_storage_class = getattr(resource_args, 'storage_class', None)
  if bucket_resource.retention_period is not None:
    reason = 'Destination bucket has retention period set'
  elif bucket_resource.default_event_based_hold:
    reason = 'Destination bucket has event-based hold set'
  elif getattr(resource_args, 'event_based_hold', None):
    reason = 'Object will be created with event-based hold'
  elif getattr(resource_args, 'temporary_hold', None):
    reason = 'Object will be created with temporary hold'
  elif (bucket_resource.default_storage_class != _STANDARD_STORAGE_CLASS and
        object_storage_class != _STANDARD_STORAGE_CLASS):
    reason = 'Destination has a default storage class other than "STANDARD"'
  elif object_storage_class not in (None, _STANDARD_STORAGE_CLASS):
    reason = 'Object will be created with a storage class other than "STANDARD"'
  else:
    return True

  log.warning(
      '{}, hence parallel'
      ' composite upload will not be performed. If you would like to disable'
      ' this check, run: gcloud config set '
      'storage/parallel_composite_upload_compatibility_check=False'.format(
          reason))
  return False


def is_composite_upload_eligible(source_resource,
                                 destination_resource,
                                 user_request_args=None):
  """Checks if parallel composite upload should be performed.

  Logs tailored warning based on user configuration and the context
  of the operation.
  Informs user about configuration options they may want to set.
  In order to avoid repeated warning raised for each task,
  this function updates the storage/parallel_composite_upload_enabled
  so that the warnings are logged only once.

  Args:
    source_resource (FileObjectResource): The source file
      resource to be uploaded.
    destination_resource(CloudResource|UnknownResource):
      Destination resource to which the files should be uploaded.
    user_request_args (UserRequestArgs|None): Values for RequestConfig.

  Returns:
    True if the parallel composite upload can be performed. However, this does
    not guarantee that parallel composite upload will be performed as the
    parallelism check can happen only after the task executor starts running
    because it sets the process_count and thread_count. We also let the task
    determine the component count.
  """
  composite_upload_enabled = (
      properties.VALUES.storage.parallel_composite_upload_enabled.GetBool())
  if composite_upload_enabled is False:  # pylint: disable=g-bool-id-comparison
    # Can't do "if not composite_upload_enabled" here because
    # None has a different behavior.
    return False

  if not isinstance(source_resource, resource_reference.FileObjectResource):
    # Source resource can be of type UnknownResource, hence check the type.
    return False

  try:
    if (source_resource.size is None or
        source_resource.size < scaled_integer.ParseInteger(
            properties.VALUES.storage.parallel_composite_upload_threshold.Get()
        )):
      return False
  except OSError as e:
    log.warning('Size cannot be determined for resource: %s. Error: %s',
                source_resource, e)
    return False

  compatibility_check_required = (
      properties.VALUES.storage.parallel_composite_upload_compatibility_check
      .GetBool())
  if composite_upload_enabled and not compatibility_check_required:
    return True

  api_capabilities = api_factory.get_capabilities(
      destination_resource.storage_url.scheme)
  if cloud_api.Capability.COMPOSE_OBJECTS not in api_capabilities:
    # We can silently disable parallel composite upload because the destination
    # capability will not change during the execution.
    # TODO(b/245738490) Explore if setting this property can be avoided.
    properties.VALUES.storage.parallel_composite_upload_enabled.Set(False)
    return False

  if compatibility_check_required:
    can_perform_composite_upload = (
        is_destination_composite_upload_compatible(destination_resource,
                                                   user_request_args))
    # Indicates that we don't have to repeat compatibility check.
    properties.VALUES.storage.parallel_composite_upload_compatibility_check.Set(
        False)
  else:
    can_perform_composite_upload = True

  if can_perform_composite_upload and composite_upload_enabled is None:
    log.warning(
        textwrap.fill(
            'Parallel composite upload was turned ON to get the best'
            ' performance on uploading large objects.'
            ' If you would like to opt-out and instead perform a normal upload,'
            ' run:'
            '\n`gcloud config set storage/parallel_composite_upload_enabled'
            ' False`'
            '\nIf you would like to disable this warning, run:'
            '\n`gcloud config set storage/parallel_composite_upload_enabled'
            ' True`'
            # We say "might" here because whether parallel composite upload is
            # used or not also depends on whether parallelism is True.
            '\nNote that with parallel composite uploads, your object might be'
            ' uploaded as a composite object'
            ' (https://cloud.google.com/storage/docs/composite-objects),'
            ' which means that any user who downloads your object will need to'
            ' use crc32c checksums to verify data integrity.'
            ' gcloud storage is capable of computing crc32c checksums, but'
            ' this might pose a problem for other clients.') + '\n')
  # TODO(b/245738490) Explore if setting this property can be avoided.
  properties.VALUES.storage.parallel_composite_upload_enabled.Set(
      can_perform_composite_upload)

  return can_perform_composite_upload
