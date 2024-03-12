# -*- coding: utf-8 -*-
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Helper functions for Split Trust Encryption Tool integration."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import shutil

from gslib import storage_url
from gslib.utils import execution_util
from gslib.utils import temporary_file_util

from boto import config


class StetSubcommandName(object):
  """Enum class for available STET subcommands."""
  ENCRYPT = 'encrypt'
  DECRYPT = 'decrypt'


def _get_stet_binary_from_path():
  """Retrieves STET binary from path if available. Python 2 compatible."""
  for path_directory in os.getenv('PATH').split(os.path.pathsep):
    binary_path = os.path.join(path_directory, 'stet')
    if os.path.exists(binary_path):
      return binary_path


def _stet_transform(subcommand, blob_id, in_file_path, out_file_path, logger):
  """Runs a STET transform on a file.

  Encrypts for uploads. Decrypts for downloads. Automatically populates
  flags for the STET binary.

  Args:
    subcommand (StetSubcommandName): Subcommand to call on STET binary.
    blob_id (str): Cloud URL that binary uses for validation.
    in_file_path (str): File to be transformed source.
    out_file_path (str): Where to write result of transform.
    logger (logging.Logger): For logging STET binary output.

  Raises:
    KeyError: STET binary or config could not be found.
  """
  binary_path = config.get('GSUtil', 'stet_binary_path',
                           _get_stet_binary_from_path())
  if not binary_path:
    raise KeyError('Could not find STET binary in boto config or PATH.')

  command_args = [os.path.expanduser(binary_path), subcommand]
  config_path = config.get('GSUtil', 'stet_config_path', None)
  if config_path:
    command_args.append('--config-file=' + os.path.expanduser(config_path))
  command_args.extend(['--blob-id=' + blob_id, in_file_path, out_file_path])

  _, stderr = execution_util.ExecuteExternalCommand(command_args)
  logger.debug(stderr)


def encrypt_upload(source_url, destination_url, logger):
  """Encrypts a file with STET binary before upload.

  Args:
    source_url (StorageUrl): Copy source.
    destination_url (StorageUrl): Copy destination.
    logger (logging.Logger): For logging STET binary output.

  Returns:
    stet_temporary_file_url (StorageUrl): Path to STET-encrypted file.
  """
  in_file = source_url.object_name
  out_file = temporary_file_util.GetStetTempFileName(source_url)
  blob_id = destination_url.url_string

  _stet_transform(StetSubcommandName.ENCRYPT, blob_id, in_file, out_file,
                  logger)
  return storage_url.StorageUrlFromString(out_file)


def decrypt_download(source_url, destination_url, temporary_file_name, logger):
  """STET-decrypts downloaded file.

  Args:
    source_url (StorageUrl): Copy source.
    destination_url (StorageUrl): Copy destination.
    temporary_file_name (str): Path to temporary file used for download.
    logger (logging.Logger): For logging STET binary output.
  """
  in_file = temporary_file_name
  out_file = temporary_file_util.GetStetTempFileName(destination_url)
  blob_id = source_url.url_string

  _stet_transform(StetSubcommandName.DECRYPT, blob_id, in_file, out_file,
                  logger)
  shutil.move(out_file, in_file)
