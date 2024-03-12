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
"""Utility functions for performing download operation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import gzip_util
from googlecloudsdk.command_lib.storage import hash_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import symlink_util
from googlecloudsdk.command_lib.storage import tracker_file_util

SYMLINK_TEMPORARY_PLACEHOLDER_SUFFIX = '_sym'


def _decompress_or_rename_file(
    source_resource,
    temporary_file_path,
    final_file_path,
    do_not_decompress_flag=False,
    server_encoding=None,
):
  """Converts temporary file to final form by decompressing or renaming.

  Args:
    source_resource (ObjectResource): May contain encoding metadata.
    temporary_file_path (str): File path to unzip or rename.
    final_file_path (str): File path to write final file to.
    do_not_decompress_flag (bool): User flag that blocks decompression.
    server_encoding (str|None): Server-reported `content-encoding` of file.

  Returns:
    (bool) True if file was decompressed or renamed, and
      False if file did not exist.
  """
  if not os.path.exists(temporary_file_path):
    return False

  if gzip_util.decompress_gzip_if_necessary(source_resource,
                                            temporary_file_path,
                                            final_file_path,
                                            do_not_decompress_flag,
                                            server_encoding):
    os.remove(temporary_file_path)
  else:
    os.rename(temporary_file_path, final_file_path)
  return True


def finalize_download(
    source_resource,
    temporary_file_path,
    final_file_path,
    do_not_decompress_flag=False,
    server_encoding=None,
    convert_symlinks=False,
):
  """Converts temporary file to final form.

  This may involve decompressing, renaming, and/or converting symlink
  placeholders to actual symlinks.

  Args:
    source_resource (ObjectResource): May contain encoding metadata.
    temporary_file_path (str): File path to unzip or rename.
    final_file_path (str): File path to write final file to.
    do_not_decompress_flag (bool): User flag that blocks decompression.
    server_encoding (str|None): Server-reported `content-encoding` of file.
    convert_symlinks (bool): Whether symlink placeholders should be converted to
      actual symlinks.

  Returns:
    (bool) True if file was decompressed, renamed, and/or converted to a
      symlink; False if file did not exist.
  """
  make_symlink = convert_symlinks and source_resource.is_symlink
  if make_symlink:
    # The decompressed/renamed content is a symlink placeholder, so store it as
    # as a temporary placeholder alongside the original temporary_file_path.
    decompress_or_rename_path = (temporary_file_path +
                                 SYMLINK_TEMPORARY_PLACEHOLDER_SUFFIX)
  else:
    decompress_or_rename_path = final_file_path

  decompress_or_rename_result = _decompress_or_rename_file(
      source_resource=source_resource,
      temporary_file_path=temporary_file_path,
      final_file_path=decompress_or_rename_path,
      do_not_decompress_flag=do_not_decompress_flag,
      server_encoding=server_encoding,
  )
  if not decompress_or_rename_result:
    return False
  if make_symlink:
    symlink_util.create_symlink_from_temporary_placeholder(
        placeholder_path=decompress_or_rename_path, symlink_path=final_file_path
    )
    os.remove(decompress_or_rename_path)
  return decompress_or_rename_result


def validate_download_hash_and_delete_corrupt_files(download_path, source_hash,
                                                    destination_hash):
  """Confirms hashes match for copied objects.

  Args:
    download_path (str): URL of object being validated.
    source_hash (str): Hash of source object.
    destination_hash (str): Hash of downloaded object.

  Raises:
    HashMismatchError: Hashes are not equal.
  """
  try:
    hash_util.validate_object_hashes_match(download_path, source_hash,
                                           destination_hash)
  except errors.HashMismatchError:
    os.remove(download_path)
    tracker_file_util.delete_download_tracker_files(
        storage_url.storage_url_from_string(download_path))
    raise


def return_and_report_if_nothing_to_download(cloud_resource, progress_callback):
  """Returns valid download range bool and reports progress if not."""
  if cloud_resource.size == 0:
    if progress_callback:
      progress_callback(0)
    return True
  return False
