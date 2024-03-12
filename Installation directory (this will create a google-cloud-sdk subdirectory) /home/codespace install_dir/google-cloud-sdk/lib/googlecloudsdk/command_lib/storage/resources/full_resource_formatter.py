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
"""Base class for handling ls -L formatting of CloudResource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import collections
import datetime

from googlecloudsdk.api_lib.storage import errors
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.resources import resource_util
import six

ACL_KEY = 'acl'
DEFAULT_ACL_KEY = 'default_acl'


class FieldDisplayTitleAndDefault(object):
  """Holds the title and default value to be displayed for a resource field."""

  def __init__(self, title, default, field_name=None):
    """Initializes FieldDisplayTitleAndDefault.

    Args:
      title (str): The title for the field.
      default (str): The default value to be used if value is missing.
      field_name (str|None): The field name to be used to extract
        the data from Resource object.
        If None, the field name from BucketDisplayTitlesAndDefaults or
        ObjectDisplayTitlesAndDefaults is used.
    """
    self.title = title
    self.default = default
    self.field_name = field_name


# Determines the order in which the fields should be displayed for
# a BucketResource.
BucketDisplayTitlesAndDefaults = collections.namedtuple(
    'BucketDisplayTitlesAndDefaults',
    (
        'name',
        'default_storage_class',
        'location_type',
        'location',
        'data_locations',
        'versioning_enabled',
        'logging_config',
        'website_config',
        'cors_config',
        'lifecycle_config',
        'requester_pays',
        'per_object_retention',
        'retention_policy',
        'default_event_based_hold',
        'labels',
        'default_kms_key',
        'creation_time',
        'update_time',
        'metageneration',
        'uniform_bucket_level_access',
        'public_access_prevention',
        'rpo',
        'autoclass',
        'autoclass_enabled_time',
        'satisfies_pzs',
        'soft_delete_policy',
        ACL_KEY,
        DEFAULT_ACL_KEY,
    ),
)


# Determines the order in which the fields should be displayed for
# a ManagedFolderResource.
ManagedFolderDisplayTitlesAndDefaults = collections.namedtuple(
    'ManagedFolderDisplayTitlesAndDefaults',
    (
        'name',
        'bucket',
        'create_time',
        'metageneration',
        'update_time',
    ),
)


# Determines the order in which the fields should be displayed for
# an ObjectResource.
ObjectDisplayTitlesAndDefaults = collections.namedtuple(
    'ObjectDisplayTitlesAndDefaults',
    (
        'name',
        'bucket',
        'creation_time',
        'update_time',
        'soft_delete_time',
        'hard_delete_time',
        'storage_class_update_time',
        'storage_class',
        'temporary_hold',
        'event_based_hold',
        'retention_expiration',
        'retention_settings',
        'kms_key',
        'cache_control',
        'content_disposition',
        'content_encoding',
        'content_language',
        'size',
        'content_type',
        'component_count',
        'custom_time',
        'noncurrent_time',
        'custom_fields',
        'crc32c_hash',
        'md5_hash',
        'encryption_algorithm',
        'decryption_key_hash_sha256',
        'etag',
        'generation',
        'metageneration',
        ACL_KEY,
    ),
)


def _get_formatted_line(display_name, value, default_value=None):
  """Returns a formatted line for ls -L output."""
  if value is not None:
    if value and (isinstance(value, dict) or isinstance(value, list)):
      return resource_util.get_metadata_json_section_string(display_name, value)
    elif isinstance(value, datetime.datetime):
      return resource_util.get_padded_metadata_time_line(display_name, value)
    elif isinstance(value, errors.CloudApiError):
      return resource_util.get_padded_metadata_key_value_line(
          display_name, str(value))
    return resource_util.get_padded_metadata_key_value_line(display_name, value)
  elif default_value is not None:
    return resource_util.get_padded_metadata_key_value_line(
        display_name, default_value)
  return None


def get_formatted_string(
    resource,
    display_titles_and_defaults,
    show_acl=True,
    show_version_in_url=False,
):
  """Returns the formatted string representing the resource.

  Args:
    resource (resource_reference.Resource): Object holding resource metadata
      that needs to be displayed.
    display_titles_and_defaults ([Bucket|Object]DisplayTitlesAndDefaults): Holds
      the display titles and default values for each field present in the
      Resource.
    show_acl (bool): Include ACLs list in resource display.
    show_version_in_url (bool): Display extended URL with versioning info.

  Returns:
    A string representing the Resource for ls -L command.
  """
  lines = []

  if show_acl:
    formatted_acl_dict = resource.get_formatted_acl()
  else:
    formatted_acl_dict = {}

  # In namedtuple, to prevent conflicts with field names,
  # the method and attribute names start with an underscore.
  for key in display_titles_and_defaults._fields:
    if not show_acl and key == ACL_KEY:
      continue
    field_display_title_and_default = getattr(display_titles_and_defaults, key)
    if field_display_title_and_default is None:
      # Field not supported for this output style.
      continue
    # The field_name present in field_display_title_and_default takes
    # precedence over the key in display_titles_and_defaults.
    if field_display_title_and_default.field_name is not None:
      field_name = field_display_title_and_default.field_name
    else:
      field_name = key

    if field_name in formatted_acl_dict:
      value = formatted_acl_dict.get(field_name)
    else:
      value = getattr(resource, field_name, None)

    if value == resource_reference.NOT_SUPPORTED_DO_NOT_DISPLAY:
      continue

    line = _get_formatted_line(
        field_display_title_and_default.title,
        value,
        field_display_title_and_default.default,
    )
    if line:
      lines.append(line)

  if show_version_in_url:
    url_string = resource.storage_url.url_string
  else:
    url_string = resource.storage_url.versionless_url_string
  return ('{url_string}:\n'
          '{fields}').format(
              url_string=url_string,
              fields='\n'.join(lines))


class FullResourceFormatter(six.with_metaclass(abc.ABCMeta, object)):
  """Base class for a formatter to format the Resource object.

  This FullResourceFormatter is specifically used for ls -L output formatting.
  """

  def format_bucket(self, bucket_resource):
    """Returns a formatted string representing the BucketResource.

    Args:
      bucket_resource (resource_reference.BucketResource): A BucketResource
        instance.

    Returns:
      Formatted multi-line string representing the BucketResource.
    """
    raise NotImplementedError('format_bucket must be overridden.')

  def format_object(
      self, object_resource, show_acl=True, show_version_in_url=False, **kwargs
  ):
    """Returns a formatted string representing the ObjectResource.

    Args:
      object_resource (resource_reference.Resource): A Resource instance.
      show_acl (bool): Include ACLs list in resource display.
      show_version_in_url (bool): Display extended URL with versioning info.
      **kwargs (dict): Unused. May apply to other resource format functions.

    Returns:
      Formatted multi-line string represnting the ObjectResource.
    """
    raise NotImplementedError('format_object must be overridden.')

  def format(self, resource, **kwargs):
    """Type-checks resource and returns a formatted metadata string."""
    if isinstance(resource, resource_reference.BucketResource):
      return self.format_bucket(resource)
    if isinstance(resource, resource_reference.ObjectResource):
      return self.format_object(resource, **kwargs)
    raise NotImplementedError(
        '{} does not support {}'.format(self.__class__, type(resource))
    )
