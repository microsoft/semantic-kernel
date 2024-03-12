# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Set of utilities for dealing with archives."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import shutil
import tempfile
import time
import zipfile
import googlecloudsdk.core.util.files as files
import six

try:
  # pylint: disable=unused-import
  # pylint: disable=g-import-not-at-top
  import zlib
  _ZIP_COMPRESSION = zipfile.ZIP_DEFLATED
except ImportError:
  _ZIP_COMPRESSION = zipfile.ZIP_STORED


def MakeZipFromDir(dest_zip_file, src_dir, predicate=None):
  """Create a ZIP archive from a directory.

  This is similar to shutil.make_archive. However, prior to Python 3.8,
  shutil.make_archive cannot create ZIP archives for files with mtimes older
  than 1980. So that's why this function exists.

  Examples:
    Filesystem:
    /tmp/a/
    /tmp/b/B

    >>> MakeZipFromDir('my.zip', '/tmp')
    Creates zip with content:
    a/
    b/B

  Note this is caller responsibility to use appropriate platform-dependent
  path separator.

  Note filenames containing path separator are supported.

  Args:
    dest_zip_file: str, filesystem path to the zip file to be created. Note that
      directory should already exist for destination zip file.
    src_dir: str, filesystem path to the directory to zip up
    predicate: callable, takes one argument (file path). File will be included
               in the zip if and only if the predicate(file_path). Defaults to
               always true.
  """

  if predicate is None:
    predicate = lambda x: True
  zip_file = zipfile.ZipFile(dest_zip_file, 'w', _ZIP_COMPRESSION)
  try:
    for root, _, filelist in os.walk(six.text_type(src_dir)):
      dir_path = os.path.normpath(os.path.relpath(root, src_dir))
      if not predicate(dir_path):
        continue
      if dir_path != os.curdir:
        AddToArchive(zip_file, src_dir, dir_path, False)
      for file_name in filelist:
        file_path = os.path.join(dir_path, file_name)
        if not predicate(file_path):
          continue
        AddToArchive(zip_file, src_dir, file_path, True)
  finally:
    zip_file.close()


def AddToArchive(zip_file, src_dir, rel_path, is_file):
  """Add a file or directory (without its contents) to a ZIP archive.

  Args:
    zip_file: the ZIP archive
    src_dir: the base directory for rel_path, will not be recorded in the
      archive
    rel_path: the relative path to the file or directory to add
    is_file: a Boolean indicating whether rel_path points to a file (rather than
      a directory)
  """
  full_path = os.path.join(src_dir, rel_path)
  mtime = os.path.getmtime(full_path)
  if time.gmtime(mtime)[0] < 1980:
    # ZIP files can't contain entries for which the mtime is older than 1980. So
    # we're going to create a temporary copy of the file or directory (which
    # will have a fresh mtime) and add it instead.
    if is_file:
      temp_file_handle, temp_file_path = tempfile.mkstemp()
      os.close(temp_file_handle)
      shutil.copyfile(full_path, temp_file_path)
      zip_file.write(temp_file_path, rel_path)
      os.remove(temp_file_path)
    else:
      with files.TemporaryDirectory() as temp_dir:
        zip_file.write(temp_dir, rel_path)
  else:
    zip_file.write(full_path, rel_path)
