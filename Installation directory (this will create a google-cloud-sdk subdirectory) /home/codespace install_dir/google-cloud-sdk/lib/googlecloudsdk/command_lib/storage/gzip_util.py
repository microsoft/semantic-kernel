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
"""Gzip utils for gcloud storage."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import gzip
import os
import shutil

from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import user_request_args_factory
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files


def decompress_gzip_if_necessary(source_resource,
                                 gzipped_path,
                                 destination_path,
                                 do_not_decompress_flag=False,
                                 server_encoding=None):
  """Checks if file is elligible for decompression and decompresses if true.

  Args:
    source_resource (ObjectResource): May contain encoding metadata.
    gzipped_path (str): File path to unzip.
    destination_path (str): File path to write unzipped file to.
    do_not_decompress_flag (bool): User flag that blocks decompression.
    server_encoding (str|None): Server-reported `content-encoding` of file.

  Returns:
    (bool) True if file was successfully decompressed, else False.
  """
  content_encoding = getattr(source_resource.metadata, 'contentEncoding', '')
  if do_not_decompress_flag or not (
      content_encoding and 'gzip' in content_encoding.split(',') or
      server_encoding and 'gzip' in server_encoding.split(',')):
    return False

  try:
    with gzip.open(gzipped_path, 'rb') as gzipped_file:
      with files.BinaryFileWriter(
          destination_path,
          create_path=True,
          convert_invalid_windows_characters=(
              properties.VALUES.storage
              .convert_incompatible_windows_path_characters.GetBool()
          )) as ungzipped_file:
        shutil.copyfileobj(gzipped_file, ungzipped_file)
    return True
  except OSError:
    # May indicate trying to decompress non-gzipped file. Clean up.
    os.remove(destination_path)

  return False


def _should_gzip_file_type(gzip_settings, file_path):
  """Determines what, if any, type of file should be gzipped."""
  if not (gzip_settings and file_path):
    return None
  gzip_extensions = gzip_settings.extensions
  if gzip_settings.extensions == user_request_args_factory.GZIP_ALL:
    return gzip_settings.type
  elif isinstance(gzip_extensions, list):
    for extension in gzip_extensions:
      dot_separated_extension = '.' + extension.lstrip(' .')
      if file_path.endswith(dot_separated_extension):
        return gzip_settings.type
  return None


def should_gzip_in_flight(gzip_settings, file_path):
  """Determines if file qualifies for in-flight gzip encoding."""
  return _should_gzip_file_type(
      gzip_settings, file_path) == user_request_args_factory.GzipType.IN_FLIGHT


def should_gzip_locally(gzip_settings, file_path):
  return _should_gzip_file_type(
      gzip_settings, file_path) == user_request_args_factory.GzipType.LOCAL


def get_temporary_gzipped_file(file_path):
  zipped_file_path = file_path + storage_url.TEMPORARY_FILE_SUFFIX
  with files.BinaryFileReader(file_path) as file_reader:
    with gzip.open(zipped_file_path, 'wb') as gzip_file_writer:
      shutil.copyfileobj(file_reader, gzip_file_writer)
  return zipped_file_path
