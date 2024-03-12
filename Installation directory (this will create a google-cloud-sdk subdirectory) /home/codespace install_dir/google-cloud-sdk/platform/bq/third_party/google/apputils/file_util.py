#!/usr/bin/env python
# Copyright 2007 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Simple file system utilities."""

__author__ = ('elaforge@google.com (Evan LaForge)',
              'matthewb@google.com (Matthew Blecker)')

import errno
import os
import pwd
import shutil
import stat
import tempfile


class PasswdError(Exception):
  """Exception class for errors loading a password from a file."""


def ListDirPath(dir_name):
  """Like os.listdir with prepended dir_name, which is often more convenient."""
  return [os.path.join(dir_name, fn) for fn in os.listdir(dir_name)]


def Read(filename):
  """Read entire contents of file with name 'filename'."""
  fp = open(filename)
  try:
    return fp.read()
  finally:
    fp.close()


def Write(filename, contents, overwrite_existing=True, mode=0o666):
  """Create a file 'filename' with 'contents', with the mode given in 'mode'.

  The 'mode' is modified by the umask, as in open(2).  If
  'overwrite_existing' is False, the file will be opened in O_EXCL mode.

  Args:
    filename: str; the name of the file
    contents: str; the data to write to the file
    overwrite_existing: bool; whether or not to allow the write if the file
                        already exists
    mode: int; permissions with which to create the file (default is 0666 octal)
  """
  flags = os.O_WRONLY | os.O_TRUNC | os.O_CREAT
  if not overwrite_existing:
    flags |= os.O_EXCL
  fd = os.open(filename, flags, mode)
  try:
    os.write(fd, contents)
  finally:
    os.close(fd)


def AtomicWrite(filename, contents, mode=0o666):
  """Create a file 'filename' with 'contents' atomically.

  As in Write, 'mode' is modified by the umask.  This creates and moves
  a temporary file, and errors doing the above will be propagated normally,
  though it will try to clean up the temporary file in that case.

  This is very similar to the prodlib function with the same name.

  Args:
    filename: str; the name of the file
    contents: str; the data to write to the file
    mode: int; permissions with which to create the file (default is 0666 octal)
  """
  (fd, tmp_filename) = tempfile.mkstemp(dir=os.path.dirname(filename))
  try:
    os.write(fd, contents)
  finally:
    os.close(fd)
  try:
    os.chmod(tmp_filename, mode)
    os.rename(tmp_filename, filename)
  except OSError as exc:
    try:
      os.remove(tmp_filename)
    except OSError as e:
      exc = OSError('%s. Additional errors cleaning up: %s' % (exc, e))
    raise exc


def MkDirs(directory, force_mode=None):
  """Makes a directory including its parent directories.

  This function is equivalent to os.makedirs() but it avoids a race
  condition that os.makedirs() has.  The race is between os.mkdir() and
  os.path.exists() which fail with errors when run in parallel.

  Args:
    directory: str; the directory to make
    force_mode: optional octal, chmod dir to get rid of umask interaction
  Raises:
    Whatever os.mkdir() raises when it fails for any reason EXCLUDING
    "dir already exists".  If a directory already exists, it does not
    raise anything.  This behaviour is different than os.makedirs()
  """
  name = os.path.normpath(directory)
  dirs = name.split(os.path.sep)
  for i in range(0, len(dirs)):
    path = os.path.sep.join(dirs[:i+1])
    try:
      if path:
        os.mkdir(path)
        # only chmod if we created
        if force_mode is not None:
          os.chmod(path, force_mode)
    except OSError as exc:
      if not (exc.errno == errno.EEXIST and os.path.isdir(path)):
        raise


def RmDirs(dir_name):
  """Removes dir_name and every non-empty directory in dir_name.

  Unlike os.removedirs and shutil.rmtree, this function doesn't raise an error
  if the directory does not exist.

  Args:
    dir_name: Directory to be removed.
  """
  try:
    shutil.rmtree(dir_name)
  except OSError as err:
    if err.errno != errno.ENOENT:
      raise

  try:
    parent_directory = os.path.dirname(dir_name)
    while parent_directory:
      try:
        os.rmdir(parent_directory)
      except OSError as err:
        if err.errno != errno.ENOENT:
          raise

      parent_directory = os.path.dirname(parent_directory)
  except OSError as err:
    if err.errno not in (errno.EACCES, errno.ENOTEMPTY):
      raise


def HomeDir(user=None):
  """Find the home directory of a user.

  Args:
    user: int, str, or None - the uid or login of the user to query for,
          or None (the default) to query for the current process' effective user

  Returns:
    str - the user's home directory

  Raises:
    TypeError: if user is not int, str, or None.
  """
  if user is None:
    pw_struct = pwd.getpwuid(os.geteuid())
  elif isinstance(user, int):
    pw_struct = pwd.getpwuid(user)
  elif isinstance(user, str):
    pw_struct = pwd.getpwnam(user)
  else:
    raise TypeError('user must be None or an instance of int or str')
  return pw_struct.pw_dir
