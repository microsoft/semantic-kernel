# -*- coding: utf-8 -*-
# Copyright 2010 Google Inc. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
"""Package marker file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import pkgutil
import sys
import tempfile

import gslib.exception  # pylint: disable=g-import-not-at-top
from gslib.utils.version_check import check_python_version_support

supported, err = check_python_version_support()
if not supported:
  raise gslib.exception.CommandException(err)

coverage_outfile = os.getenv('GSUTIL_COVERAGE_OUTPUT_FILE', None)
if coverage_outfile:
  try:
    import coverage  # pylint: disable=g-import-not-at-top
    coverage_controller = coverage.coverage(data_file=coverage_outfile,
                                            data_suffix=True,
                                            auto_data=True,
                                            source=['gslib'],
                                            omit=[
                                                'gslib/third_party/*',
                                                'gslib/tests/*',
                                                tempfile.gettempdir() + '*',
                                            ])
    coverage_controller.start()
  except ImportError:
    pass

# Directory containing the gslib module.
GSLIB_DIR = os.path.dirname(os.path.realpath(__file__))
# Path to gsutil executable. This assumes gsutil is the running script.
GSUTIL_PATH = os.path.realpath(sys.argv[0])
# The directory that contains the gsutil executable.
GSUTIL_DIR = os.path.dirname(GSUTIL_PATH)

# Whether or not this was installed via a package manager like pip, deb, rpm,
# etc. If installed by just extracting a tarball or zip file, this will be
# False.
IS_PACKAGE_INSTALL = True

# Whether or not this was installed via setup.py develop mode. This creates a
# symlink directly to the source directory.
IS_EDITABLE_INSTALL = False

# Directory where program files like VERSION and CHECKSUM will be. When
# installed via tarball, this is the gsutil directory, but the files are moved
# to the gslib directory when installed via setup.py.
PROGRAM_FILES_DIR = GSLIB_DIR

# The gslib directory will be underneath the gsutil directory when installed
# from a tarball, but somewhere else on the machine if installed via setup.py.
if (not os.path.isfile(os.path.join(PROGRAM_FILES_DIR, 'VERSION')) and
    os.path.commonprefix((GSUTIL_DIR, GSLIB_DIR)) == GSUTIL_DIR):
  IS_PACKAGE_INSTALL = False
  PROGRAM_FILES_DIR = GSUTIL_DIR

# If the module was installed from source using editable mode
# (i.e. pip install -e) then the files might be one directory up.
if not os.path.isfile(os.path.join(PROGRAM_FILES_DIR, 'VERSION')):
  PROGRAM_FILES_DIR = os.path.normpath(os.path.join(GSLIB_DIR, '..'))
  IS_EDITABLE_INSTALL = True

# Give USER_AGENT a default value for web doc generation.
USER_AGENT = ''


def _AddVendoredDepsToPythonPath():
  """Fix our Python path so that it correctly finds our vendored libraries."""
  vendored_path = os.path.join(GSLIB_DIR, 'vendored')
  # Similar structure to the THIRD_PARTY_LIBS list in gsutil.py:
  vendored_lib_dirs = [
      ('boto', ''),
      ('oauth2client', ''),
  ]

  # Prepend our vendored libraries to be in the front of the Python path so that
  # they're found before any system installations that might be present.
  for libdir, subdir in vendored_lib_dirs:
    sys.path.insert(0, os.path.join(vendored_path, libdir, subdir))

  # This is the location of mock_storage_location module. Not every directory
  # in this path has an __init__.py file, so we couldn't just run
  # `from boto.tests.integration.s3 import mock_storage_service`.
  #
  # We add this to the end, rather than prepending it, so that if other
  # modules in this directory have the same name as something in our library,
  # we find our version first.
  sys.path.append(
      os.path.join(vendored_path, 'boto', 'tests', 'integration', 's3'))


_AddVendoredDepsToPythonPath()


def _GetFileContents(filename):
  """Tries to find the given filename on disk or via pkgutil.get_data.

  Args:
    filename: String name of the file.

  Returns:
    A tuple containing the absolute path to the requested file and the file's
    contents as a string (or None if the file doesn't exist).
  """
  fpath = os.path.join(PROGRAM_FILES_DIR, filename)
  if os.path.isfile(fpath):
    with open(fpath, 'r') as f:
      content = f.read()
  else:
    content = pkgutil.get_data('gslib', filename)
    fpath = None
  if content is not None:
    if sys.version_info.major > 2 and isinstance(content, bytes):
      content = content.decode('utf-8')
    content = content.strip()
  return (fpath, content)


# Get the version file and store it.
VERSION_FILE, VERSION = _GetFileContents('VERSION')
if not VERSION:
  raise gslib.exception.CommandException(
      'VERSION file not found. Please reinstall gsutil from scratch')
__version__ = VERSION

# Get the checksum file and store it.
CHECKSUM_FILE, CHECKSUM = _GetFileContents('CHECKSUM')
if not CHECKSUM:
  raise gslib.exception.CommandException(
      'CHECKSUM file not found. Please reinstall gsutil from scratch')


def GetGsutilVersionModifiedTime():
  """Returns unix timestamp of when the VERSION file was last modified."""
  if not VERSION_FILE:
    return 0
  return int(os.path.getmtime(VERSION_FILE))
