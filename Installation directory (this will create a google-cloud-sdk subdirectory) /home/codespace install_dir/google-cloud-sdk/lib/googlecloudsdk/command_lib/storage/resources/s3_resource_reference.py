# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""S3 API-specific resource subclasses."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.storage import errors
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.resources import resource_util


def _json_dump_recursion_helper(metadata):
  """See _get_json_dump docstring."""
  if isinstance(metadata, list):
    return [_json_dump_recursion_helper(item) for item in metadata]

  if not isinstance(metadata, dict):
    return resource_util.convert_to_json_parsable_type(metadata)

  # Sort by key to make sure dictionary always prints in correct order.
  formatted_dict = collections.OrderedDict(sorted(metadata.items()))
  for key, value in formatted_dict.items():
    if isinstance(value, dict):
      # Recursively handle dictionaries.
      formatted_dict[key] = _json_dump_recursion_helper(value)
    elif isinstance(value, list):
      # Recursively handled lists, which may contain more dicts, like ACLs.
      formatted_list = [_json_dump_recursion_helper(item) for item in value]
      if formatted_list:
        # Ignore empty lists.
        formatted_dict[key] = formatted_list
    elif value or resource_util.should_preserve_falsy_metadata_value(value):
      formatted_dict[key] = resource_util.convert_to_json_parsable_type(value)

  return formatted_dict


def _get_json_dump(resource):
  """Formats S3 resource metadata as JSON.

  Args:
    resource (S3BucketResource|S3ObjectResource): Resource object.

  Returns:
    Formatted JSON string.
  """
  return resource_util.configured_json_dumps(
      collections.OrderedDict([
          ('url', resource.storage_url.url_string),
          ('type', resource.TYPE_STRING),
          ('metadata', _json_dump_recursion_helper(resource.metadata)),
      ]))


def _get_error_or_exists_string(value):
  """Returns error if value is error or existence string."""
  if isinstance(value, errors.XmlApiError):
    return value
  else:
    return resource_util.get_exists_string(value)


class S3BucketResource(resource_reference.BucketResource):
  """API-specific subclass for handling metadata."""

  def get_json_dump(self):
    return _get_json_dump(self)


class S3ObjectResource(resource_reference.ObjectResource):
  """API-specific subclass for handling metadata."""

  # pylint:disable=useless-super-delegation
  def __init__(
      self,
      storage_url_object,
      acl=None,
      cache_control=None,
      component_count=None,
      content_disposition=None,
      content_encoding=None,
      content_language=None,
      content_type=None,
      # If this field is None, an encryption output formatter assumes
      # it is because it is encrpted. In this case, we want to
      # indicate we just don't support the field for S3.
      crc32c_hash=resource_reference.NOT_SUPPORTED_DO_NOT_DISPLAY,
      creation_time=None,
      custom_fields=None,
      custom_time=None,
      decryption_key_hash_sha256=None,
      encryption_algorithm=None,
      etag=None,
      event_based_hold=None,
      kms_key=None,
      md5_hash=None,
      metadata=None,
      metageneration=None,
      noncurrent_time=None,
      retention_expiration=None,
      size=None,
      storage_class=None,
      temporary_hold=None,
      update_time=None):
    """Initializes S3ObjectResource."""
    super(S3ObjectResource, self).__init__(
        storage_url_object,
        acl,
        cache_control,
        component_count,
        content_disposition,
        content_encoding,
        content_language,
        content_type,
        crc32c_hash,
        creation_time,
        custom_fields,
        custom_time,
        decryption_key_hash_sha256,
        encryption_algorithm,
        etag,
        event_based_hold,
        kms_key,
        md5_hash,
        metadata,
        metageneration,
        noncurrent_time,
        retention_expiration,
        size,
        storage_class,
        temporary_hold,
        update_time,
    )

  # pylint:enable=useless-super-delegation

  def get_json_dump(self):
    return _get_json_dump(self)
