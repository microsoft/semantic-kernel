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
"""Shim-related utils for storage resource formatters."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import errors
from googlecloudsdk.command_lib.storage.resources import resource_util
from googlecloudsdk.core.util import scaled_integer

_BUCKET_FIELDS_WITH_PRESENT_VALUE = ('cors_config', 'lifecycle_config',
                                     'logging_config', 'retention_policy',
                                     'website_config')
_BYTE_EXPONENTS_AND_UNIT_STRINGS = [
    (0, 'B'),
    (10, 'KiB'),
    (20, 'MiB'),
    (30, 'GiB'),
    (40, 'TiB'),
    (50, 'PiB'),
    (60, 'EiB'),
]
# Using literal strings as default so that they get displayed
# if the value is missing.
NONE_STRING = 'None'
EMPTY_LIST_STRING = '[]'
PRESENT_STRING = 'Present'


def _gsutil_format_byte_values(byte_count):
  """Generates a gsutil-style human-readable string for a number of bytes."""
  final_exponent, final_unit_string = _BYTE_EXPONENTS_AND_UNIT_STRINGS[0]
  for exponent, unit_string in _BYTE_EXPONENTS_AND_UNIT_STRINGS:
    if byte_count < 2**exponent:
      break
    final_exponent = exponent
    final_unit_string = unit_string

  rounded_number = round(byte_count / 2**final_exponent, 2)
  return '{:g} {}'.format(rounded_number, final_unit_string)


def _gsutil_format_datetime_string(datetime_object):
  """Returns datetime in gsutil format, e.g. 'Tue, 08 Jun 2021 21:15:33 GMT'."""
  return datetime_object.strftime('%a, %d %b %Y %H:%M:%S GMT')


def get_human_readable_byte_value(byte_count, use_gsutil_style=False):
  """Generates a string for bytes with human-readable units.

  Args:
    byte_count (int): A number of bytes to format.
    use_gsutil_style (bool): Outputs units in the style of the gsutil CLI (e.g.
      gcloud -> "1.00kiB", gsutil -> "1 KiB").

  Returns:
    A string form of the number using size abbreviations (KiB, MiB, etc).
  """
  if use_gsutil_style:
    return _gsutil_format_byte_values(byte_count)
  return scaled_integer.FormatBinaryNumber(byte_count, decimal_places=2)


def replace_autoclass_value_with_prefixed_time(bucket_resource,
                                               use_gsutil_time_style=False):
  """Converts raw datetime to 'Enabled on [formatted string]'."""
  datetime_object = getattr(bucket_resource, 'autoclass_enabled_time', None)
  if not datetime_object:
    return
  if use_gsutil_time_style:
    datetime_string = _gsutil_format_datetime_string(datetime_object)
  else:
    datetime_string = resource_util.get_formatted_timestamp_in_utc(
        datetime_object)
  bucket_resource.autoclass_enabled_time = 'Enabled on ' + datetime_string


def replace_bucket_values_with_present_string(bucket_resource):
  """Updates fields with complex data to a simple 'Present' string."""
  for field in _BUCKET_FIELDS_WITH_PRESENT_VALUE:
    value = getattr(bucket_resource, field)
    if value and not isinstance(value, errors.CloudApiError):
      setattr(bucket_resource, field, PRESENT_STRING)


def replace_object_values_with_encryption_string(object_resource,
                                                 encrypted_marker_string):
  """Updates fields to reflect that they are encrypted."""
  if object_resource.encryption_algorithm is None:
    return
  # crc32c_hash may be set to NOT_SUPPORTED_DO_NOT_DISPLAY.
  for key in ('md5_hash', 'crc32c_hash'):
    if getattr(object_resource, key) is None:
      setattr(object_resource, key, encrypted_marker_string)


def replace_time_values_with_gsutil_style_strings(resource):
  """Updates fields in gcloud time format to gsutil time format."""
  # Convert "2022-06-30T16:02:49Z" to "Thu, 30 Jun 2022 16:02:49 GMT".
  for key in (
      'creation_time',
      'custom_time',
      'noncurrent_time',
      'retention_expiration',
      'storage_class_update_time',
      'update_time',
  ):
    gcloud_datetime = getattr(resource, key, None)
    if gcloud_datetime is not None:
      setattr(resource, key, _gsutil_format_datetime_string(gcloud_datetime))


def reformat_custom_fields_for_gsutil(object_resource):
  """Reformats custom metadata full format string in gsutil style."""
  metadata = object_resource.custom_fields
  if not metadata:
    return

  if isinstance(metadata, dict):
    iterable_metadata = metadata.items()
  else:
    # Assuming GCS format: [{"key": "_", "value": "_"}, ...]
    iterable_metadata = [(d['key'], d['value']) for d in metadata]

  metadata_lines = []
  for k, v in iterable_metadata:
    metadata_lines.append(
        resource_util.get_padded_metadata_key_value_line(k, v, extra_indent=2))
  object_resource.custom_fields = '\n' + '\n'.join(metadata_lines)
