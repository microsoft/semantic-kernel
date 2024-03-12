# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Symlink utilities for storage commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.command_lib.storage import tracker_file_util
from googlecloudsdk.command_lib.storage.resources import resource_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files


def update_custom_metadata_dict_with_symlink_attributes(
    metadata_dict, is_symlink
):
  """Updates custom metadata_dict with symlink data."""
  if is_symlink:
    metadata_dict[resource_util.SYMLINK_METADATA_KEY] = 'true'
  elif resource_util.SYMLINK_METADATA_KEY in metadata_dict:
    del metadata_dict[resource_util.SYMLINK_METADATA_KEY]


def _create_symlink_directory_if_needed():
  """Looks up or creates the gcloud storage symlink file directory.

  Symlink placeholder files will be kept here.

  Returns:
    The path string to the symlink directory.
  """
  symlink_directory = (
      properties.VALUES.storage.symlink_placeholder_directory.Get()
  )
  # Thread-safe method to prevent parallel processing errors.
  files.MakeDir(symlink_directory)
  return symlink_directory


def get_symlink_placeholder_path(source_path):
  """Returns a path suitable for storing a placeholder file for a symlink."""
  symlink_directory = _create_symlink_directory_if_needed()
  symlink_filename = tracker_file_util.get_hashed_file_name(
      tracker_file_util.get_delimiterless_file_path(source_path)
  )
  tracker_file_util.raise_exceeds_max_length_error(symlink_filename)
  return os.path.join(symlink_directory, symlink_filename)


def get_symlink_placeholder_file(source_path):
  """Creates a placholder file for the given symlink.

  The placeholder will be created in the directory specified by the
  symlink_placeholder_directory property, and its content will be the path
  targeted by the given symlink.

  Args:
    source_path: The path to an existing symlink for which a placeholder should
      be created.

  Returns:
    The path to the placeholder file that was created to represent the given
    symlink.
  """
  placeholder_path = get_symlink_placeholder_path(source_path)
  with files.BinaryFileWriter(placeholder_path) as placeholder_writer:
    placeholder_writer.write(os.readlink(source_path).encode('utf-8'))
  return placeholder_path


def create_symlink_from_temporary_placeholder(placeholder_path, symlink_path):
  symlink_target = files.ReadFileContents(placeholder_path)
  os.symlink(symlink_target, symlink_path)


def get_preserve_symlink_from_user_request(user_request_args):
  return user_request_args.preserve_symlinks if user_request_args else None
