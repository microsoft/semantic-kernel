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
"""Utils for resource classes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import calendar
import datetime
import enum
import json
import textwrap

from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.core.resource import resource_projector


LONGEST_METADATA_KEY_LENGTH = 26
METADATA_LINE_INDENT_LENGTH = 2
METADATA_LINE_INDENT_STRING = ' ' * METADATA_LINE_INDENT_LENGTH

# For transporting symlink info through an object's custom metadata.
SYMLINK_METADATA_KEY = 'goog-reserved-file-is-symlink'

UNSUPPORTED_OBJECT_WARNING_FORMAT = (
    'Skipping item {} with unsupported object type: {}'
)


class UnsupportedObjectType(enum.Enum):
  GLACIER = 'GLACIER'


def get_unsupported_object_type(resource):
  """Returns unsupported type or None if object is supported for copies.

  Currently, S3 Glacier objects are the only unsupported object type.

  Args:
    resource (ObjectResource|FileObjectResource): Check if this resource is
      supported for copies.

  Returns:
    (UnsupportedObjectType|None) If resource is unsupported, the unsupported
      type, else None.
  """
  if (
      isinstance(resource, resource_reference.ObjectResource)
      and resource.storage_url.scheme == storage_url.ProviderPrefix.S3
      and resource.storage_class == 'GLACIER'
  ):
    return UnsupportedObjectType.GLACIER
  return None


def configured_json_dumps(item):
  """Return json.dumps with formatting options set."""
  return json.dumps(item, indent=METADATA_LINE_INDENT_LENGTH)


def convert_to_json_parsable_type(value):
  """Converts values encountered in metadata to be JSON-parsable."""
  if isinstance(value, Exception):
    return str(value)
  if isinstance(value, datetime.datetime):
    return value.strftime('%Y-%m-%dT%H:%M:%S%z')
  # datetime.datetime is an instance of datetime.date, but not the opposite.
  if isinstance(value, datetime.date):
    return value.strftime('%Y-%m-%d')
  return value


def get_display_dict_for_resource(
    resource, display_titles_and_defaults, display_raw_keys
):
  """Makes a resource better for returning from describe and list commands.

  Display = Removes complex nested objects and makes other string tweaks.

  Args:
    resource (resource_reference.Resource): Resource to format.
    display_titles_and_defaults (namedtuple): Contains names of fields for
      display.
    display_raw_keys (bool): Displays raw API responses if True, otherwise
      standardizes metadata keys. If True, `resource` must have a metadata
      attribute.

  Returns:
    Dictionary representing input resource with optimizations described above.
  """
  if display_raw_keys:
    display_data = resource.metadata

  else:
    # Avoid printing all the attributes of StorageUrl.
    display_data = {'storage_url': resource.storage_url.url_string}

    formatted_acl_dict = resource.get_formatted_acl()
    for field in display_titles_and_defaults._fields:
      if field in formatted_acl_dict:
        value = formatted_acl_dict.get(field)
      else:
        value = getattr(resource, field, None)
      display_data[field] = convert_to_json_parsable_type(value)

  # MakeSerializable will omit all the None values.
  return resource_projector.MakeSerializable(display_data)


def convert_datetime_object_to_utc(datetime_object):
  """Converts datetime object to UTC and returns it."""
  # Can't use CloudSDK core.util.times.FormatDateTime because of:
  # https://bugs.python.org/issue29097.
  # Also cannot use datetime.astimezone because the function doesn't alter
  # datetimes that have different offsets if they have the same timezone.
  offset = datetime_object.utcoffset()
  if offset:
    return (datetime_object - offset).replace(tzinfo=datetime.timezone.utc)
  return datetime_object


def get_formatted_timestamp_in_utc(datetime_object):
  """Converts datetime to UTC and returns formatted string representation."""
  if not datetime_object:
    return 'None'
  return convert_datetime_object_to_utc(datetime_object).strftime(
      '%Y-%m-%dT%H:%M:%SZ')


def get_unix_timestamp_in_utc(datetime_object):
  """Converts datetime to UTC and returns Unix seconds-since-epoch int."""
  return int(
      calendar.timegm(
          convert_datetime_object_to_utc(datetime_object).timetuple()
      )
  )


def get_metadata_json_section_string(key_string, value_to_convert_to_json,):
  """Returns metadata section with potentially multiple lines of JSON.

  Args:
    key_string (str): Key to give section.
    value_to_convert_to_json (list|object): json_dump_method run on this.

  Returns:
    String with key followed by JSON version of value.
  """
  json_string = textwrap.indent(
      configured_json_dumps(value_to_convert_to_json),
      prefix=METADATA_LINE_INDENT_STRING)
  return '{indent}{key}:\n{json}'.format(
      indent=METADATA_LINE_INDENT_STRING, key=key_string, json=json_string)


def get_padded_metadata_key_value_line(key_string,
                                       value_string,
                                       extra_indent=0):
  """Returns metadata line with correct padding."""
  # Align all values to the right.
  spaces_left_of_value = max(1, (LONGEST_METADATA_KEY_LENGTH - len(key_string) +
                                 METADATA_LINE_INDENT_LENGTH - extra_indent))
  return '{indent}{key}:{_:>{left_spacing}}{value}'.format(
      _='',
      indent=' ' * (METADATA_LINE_INDENT_LENGTH + extra_indent),
      key=key_string,
      left_spacing=spaces_left_of_value,
      value=value_string)


def get_padded_metadata_time_line(key_string, value_time):
  """Returns _get_padded_metadata_value_line with formatted time value."""
  formatted_time = get_formatted_timestamp_in_utc(value_time)
  return get_padded_metadata_key_value_line(key_string, formatted_time)


def should_preserve_falsy_metadata_value(value):
  """There are falsy values we want to keep as metadata."""
  # pylint:disable=g-explicit-bool-comparison, singleton-comparison
  return value in (0, 0.0, False)
  # pylint:enable=g-explicit-bool-comparison, singleton-comparison


def get_exists_string(item):
  """Returns string showing if item exists. May return 'None', '[]', etc."""
  if item or should_preserve_falsy_metadata_value(item):
    return 'Present'
  else:
    return str(item)
