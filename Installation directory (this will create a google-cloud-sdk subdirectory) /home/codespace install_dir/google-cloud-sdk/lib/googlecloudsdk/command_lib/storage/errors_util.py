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
"""Utils for common error logic."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import storage_url


def _raise_error_for_wrong_resource_type(
    command_list, expected_resource_type, example, url
):
  """Raises error for user input mismatched with command resource type.

  Example message:

  "gcloud storage buckets" create only accepts bucket URLs.
  Example: "gs://bucket"
  Received: "gs://user-bucket/user-object.txt"

  Args:
    command_list (list[str]): The command being run. Can be gotten from an
      argparse object with `args.command_path`.
    expected_resource_type (str): Raise an error because we did not get this.
    example: (str): An example of a URL to a resource with the correct type.
    url (StorageUrl): The erroneous URL received.

  Raises:
    InvalidUrlError: Explains that the user entered a URL for the wrong type
      of resource.
  """

  raise errors.InvalidUrlError(
      '"{}" only accepts {} URLs.\nExample: "{}"\nReceived: "{}"'.format(
          ' '.join(command_list), expected_resource_type, example, url
      )
  )


def raise_error_if_not_bucket(command_list, url):
  if not (isinstance(url, storage_url.CloudUrl) and url.is_bucket()):
    _raise_error_for_wrong_resource_type(
        command_list, 'bucket', 'gs://bucket', url
    )


def raise_error_if_not_cloud_object(command_list, url):
  if not (isinstance(url, storage_url.CloudUrl) and url.is_object()):
    _raise_error_for_wrong_resource_type(
        command_list, 'object', 'gs://bucket/object.txt', url
    )


def raise_error_if_not_gcs(command_list, url, example='gs://bucket'):
  if not (
      isinstance(url, storage_url.CloudUrl)
      and url.scheme is storage_url.ProviderPrefix.GCS
  ):
    _raise_error_for_wrong_resource_type(
        command_list, 'Google Cloud Storage', example, url
    )


def raise_error_if_not_gcs_bucket(command_list, url):
  raise_error_if_not_gcs(command_list, url)
  raise_error_if_not_bucket(command_list, url)


def raise_error_if_not_gcs_managed_folder(command_list, url):
  raise_error_if_not_gcs(command_list, url, example='gs://bucket/folder/')
  if not (isinstance(url, storage_url.CloudUrl) and url.is_object()):
    _raise_error_for_wrong_resource_type(
        command_list,
        'Google Cloud Storage managed folder',
        'gs://bucket/folder/',
        url,
    )
