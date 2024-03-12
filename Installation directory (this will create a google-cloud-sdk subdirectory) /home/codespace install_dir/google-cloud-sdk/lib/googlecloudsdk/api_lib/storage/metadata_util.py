# -*- coding: utf-8 -*- #
# Copyright 2022 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Provider-neutral tools for manipulating metadata."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os

from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import posix_util
from googlecloudsdk.command_lib.storage import symlink_util
from googlecloudsdk.command_lib.storage import user_request_args_factory
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.core import yaml
from googlecloudsdk.core.cache import function_result_cache
from googlecloudsdk.core.util import files
import six


def read_yaml_json_from_string(string, source_path=None):
  """Converts JSON or YAML stream to an in-memory dict."""
  current_error_string = 'Found invalid JSON/YAML'
  if source_path:
    current_error_string += ' in {}'.format(source_path)

  try:
    parsed = yaml.load(string)
    if isinstance(parsed, dict) or isinstance(parsed, list):
      return parsed
  except yaml.YAMLParseError as e:
    current_error_string += '\n\nYAML Error: {}'.format(six.text_type(e))

  try:
    return json.loads(string)
  except json.JSONDecodeError as e:
    current_error_string += '\n\nJSON Error: {}'.format(six.text_type(e))

  raise errors.InvalidUrlError(current_error_string)


@function_result_cache.lru(maxsize=None)
def cached_read_yaml_json_file(file_path):
  """Converts JSON or YAML file to an in-memory dict.

  Args:
    file_path (str): Path for the file to parse passed in by the user.

  Returns:
    parsed (dict): Parsed value from the provided file_path.

  Raises:
    InvalidUrlError: The provided file_path either failed to load or be parsed
      as a dict.
  """
  expanded_file_path = os.path.realpath(os.path.expanduser(file_path))
  contents = files.ReadFileContents(expanded_file_path)
  return read_yaml_json_from_string(contents, source_path=file_path)


def has_updated_custom_fields(
    resource_args,
    preserve_posix,
    preserve_symlinks,
    attributes_resource=None,
    known_posix=None,
):
  """Checks for the storage provider's custom metadata field."""
  file_resource = isinstance(
      attributes_resource, resource_reference.FileObjectResource
  )

  should_parse_file_posix = preserve_posix and file_resource
  should_parse_symlinks = preserve_symlinks and file_resource

  return bool(
      should_parse_file_posix
      or known_posix
      or should_parse_symlinks
      or resource_args.custom_fields_to_set
      or resource_args.custom_fields_to_remove
      or resource_args.custom_fields_to_update
  )


def get_updated_custom_fields(
    existing_custom_fields,
    request_config,
    attributes_resource=None,
    known_posix=None,
):
  """Returns a dictionary containing new custom metadata for an object.

  Assumes that the custom metadata setter, clear flag, and a group containing
  the update and flags are in a mutually exclusive group, meaning values can be
  provided for one of these three flags/groups. The preserve POSIX flag is not a
  member of this group, meaning it can be set with any of these flags.

  Args:
    existing_custom_fields (dict): Existing custom metadata provided by an API.
    request_config (request_config): May contain custom metadata fields that
      should be modified.
    attributes_resource (Resource|None): If present, used for parsing POSIX and
      symlink data from a resource for the --preserve-posix and/or
      --preserve_symlink flags. This value is ignored unless it is an instance
      of FileObjectResource.
    known_posix (PosixAttributes|None): Set as custom metadata on target,
      skipping re-parsing from system.

  Returns:
    Optional[dict] that should be the value of the storage provider's custom
    metadata field. `None` means that existing metadata should remain unchanged.
    Empty dictionary means it should be cleared.

  Raises:
    errors.Error: If incompatible existing_custom_fields were encountered.
  """
  resource_args = request_config.resource_args
  if not resource_args:
    return

  file_resource = (
      attributes_resource
      if isinstance(attributes_resource, resource_reference.FileObjectResource)
      else None
  )
  if existing_custom_fields and file_resource:
    # existing_custom_fields is typically metadata from cloud objects, so it's
    # not expected to be present for a local file system object.
    raise errors.Error(
        'Existing custom fields should not exist when updating custom fields'
        ' using local source.'
    )

  if not has_updated_custom_fields(
      resource_args,
      request_config.preserve_posix,
      request_config.preserve_symlinks,
      attributes_resource=attributes_resource,
      known_posix=known_posix,
  ):
    return

  should_parse_file_posix = request_config.preserve_posix and file_resource
  should_parse_symlinks = request_config.preserve_symlinks and file_resource

  posix_metadata = {}
  if known_posix or should_parse_file_posix:
    if known_posix:
      posix_attributes = known_posix
    else:
      posix_attributes = posix_util.get_posix_attributes_from_resource(
          file_resource, preserve_symlinks=request_config.preserve_symlinks
      )
    posix_util.update_custom_metadata_dict_with_posix_attributes(
        posix_metadata, posix_attributes)

  if should_parse_symlinks:
    symlink_util.update_custom_metadata_dict_with_symlink_attributes(
        posix_metadata, file_resource.is_symlink
    )

  if resource_args.custom_fields_to_set == user_request_args_factory.CLEAR:
    # Providing preserve POSIX and clear flags means that an object's metadata
    # should only include POSIX information.
    return posix_metadata

  # POSIX metadata overrides existing values but is overridden by fields
  # provided in update, remove, and set flags.
  if resource_args.custom_fields_to_set:
    posix_metadata.update(resource_args.custom_fields_to_set)
    return posix_metadata

  custom_fields = dict(existing_custom_fields, **posix_metadata)

  # Removes fields before updating them to avoid metadata loss.
  if resource_args.custom_fields_to_remove:
    for key in resource_args.custom_fields_to_remove:
      if key in custom_fields:
        del custom_fields[key]

  if resource_args.custom_fields_to_update:
    custom_fields.update(resource_args.custom_fields_to_update)

  return custom_fields
