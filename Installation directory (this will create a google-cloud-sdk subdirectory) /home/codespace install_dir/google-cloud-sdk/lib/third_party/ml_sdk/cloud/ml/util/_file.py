# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Some file reading utilities.
"""

import glob
import logging
import os
import shutil
import subprocess
import time

from apache_beam.io import gcsio


# TODO(user): Remove use of gsutil


def create_directory(path):
  """Creates a local directory.

  Does nothing if a Google Cloud Storage path is passed.

  Args:
    path: the path to create.

  Raises:
    ValueError: if path is a file or os.makedir fails.
  """
  if path.startswith('gs://'):
    return
  if os.path.isdir(path):
    return
  if os.path.isfile(path):
    raise ValueError('Unable to create location. "%s" exists and is a file.' %
                     path)

  try:
    os.makedirs(path)
  except:  # pylint: disable=broad-except
    raise ValueError('Unable to create location. "%s"' % path)


def open_local_or_gcs(path, mode):
  """Opens the given path."""
  if path.startswith('gs://'):
    try:
      return gcsio.GcsIO().open(path, mode)
    except Exception as e:  # pylint: disable=broad-except
      # Currently we retry exactly once, to work around flaky gcs calls.
      logging.error('Retrying after exception reading gcs file: %s', e)
      time.sleep(10)
      return gcsio.GcsIO().open(path, mode)
  else:
    return open(path, mode)


def file_exists(path):
  """Returns whether the file exists."""
  if path.startswith('gs://'):
    return gcsio.GcsIO().exists(path)
  else:
    return os.path.exists(path)


def copy_file(src, dest):
  """Copy a file from src to dest.

  Supports local and Google Cloud Storage.

  Args:
    src: source path.
    dest: destination path.
  """
  with open_local_or_gcs(src, 'r') as h_src:
    with open_local_or_gcs(dest, 'w') as h_dest:
      shutil.copyfileobj(h_src, h_dest)


def write_file(path, data):
  """Writes data to a file.

  Supports local and Google Cloud Storage.

  Args:
    path: output file path.
    data: data to write to file.
  """
  with open_local_or_gcs(path, 'w') as h_dest:
    h_dest.write(data)  # pylint: disable=no-member


def load_file(path):
  if path.startswith('gs://'):
    content = _read_cloud_file(path)
  else:
    content = _read_local_file(path)

  if content is None:
    raise ValueError('File cannot be loaded from %s' % path)

  return content


def glob_files(path):
  if path.startswith('gs://'):
    return gcsio.GcsIO().glob(path)
  else:
    return glob.glob(path)


def _read_local_file(local_path):
  with open(local_path, 'r') as f:
    return f.read()


def _read_cloud_file(storage_path):
  with open_local_or_gcs(storage_path, 'r') as src:
    return src.read()


def read_file_stream(file_list):
  for path in file_list if not isinstance(file_list, basestring) else [
      file_list
  ]:
    if path.startswith('gs://'):
      for line in _read_cloud_file_stream(path):
        yield line
    else:
      for line in _read_local_file_stream(path):
        yield line


def _read_local_file_stream(path):
  with open(path) as file_in:
    for line in file_in:
      yield line


def _read_cloud_file_stream(path):
  read_file = subprocess.Popen(
      ['gsutil', 'cp', path, '-'],
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE)
  with read_file.stdout as file_in:
    for line in file_in:
      yield line
  if read_file.wait() != 0:
    raise IOError('Unable to read data from Google Cloud Storage: "%s"' % path)
