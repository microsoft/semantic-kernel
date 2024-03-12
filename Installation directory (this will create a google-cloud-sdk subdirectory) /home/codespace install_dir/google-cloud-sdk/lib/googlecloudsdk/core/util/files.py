# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""Some general file utilities used that can be used by the Cloud SDK."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import enum
import errno
import hashlib
import io
import logging
import os
import shutil
import stat
import sys
import tempfile
import time

from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import encoding as encoding_util
from googlecloudsdk.core.util import platforms
from googlecloudsdk.core.util import retry

import six
from six.moves import range  # pylint: disable=redefined-builtin

NUM_RETRIES = 10

# WindowsError only exists when running on Windows
try:
  # pylint: disable=invalid-name, We are not defining this name.
  WindowsError
except NameError:
  # pylint: disable=invalid-name, We are not defining this name.
  WindowsError = None


class Error(Exception):
  """Base exception for the file_utils module."""
  pass


class MissingFileError(Error):
  """Error for when a file does not exist."""
  pass


def CopyTree(src, dst):
  """Copies a directory recursively, without copying file stat info.

  More specifically, behaves like `cp -R` rather than `cp -Rp`, which means that
  the destination directory and its contents will be *writable* and *deletable*.

  (Yes, an omnipotent being can shutil.copytree a directory so read-only that
  they cannot delete it. But they cannot do that with this function.)

  Adapted from shutil.copytree.

  Args:
    src: str, the path to the source directory
    dst: str, the path to the destination directory. Must not already exist and
      be writable.

  Raises:
    shutil.Error: if copying failed for any reason.
  """
  os.makedirs(dst)
  errors = []
  for name in os.listdir(src):
    name = encoding_util.Decode(name)
    srcname = os.path.join(src, name)
    dstname = os.path.join(dst, name)
    try:
      if os.path.isdir(srcname):
        CopyTree(srcname, dstname)
      else:
        # Will raise a SpecialFileError for unsupported file types
        shutil.copy2(srcname, dstname)
    # catch the Error from the recursive copytree so that we can
    # continue with other files
    except shutil.Error as err:
      errors.extend(err.args[0])
    except EnvironmentError as why:
      errors.append((srcname, dstname, six.text_type(why)))
  if errors:
    raise shutil.Error(errors)


def MakeDir(path, mode=0o777, convert_invalid_windows_characters=False):
  """Creates the given directory and its parents and does not fail if it exists.

  Args:
    path: str, The path of the directory to create.
    mode: int, The permissions to give the created directories. 0777 is the
      default mode for os.makedirs(), allowing reading, writing, and listing by
      all users on the machine.
    convert_invalid_windows_characters: bool, Convert invalid Windows path
      characters with an 'unsupported' symbol rather than trigger an OSError on
      Windows (e.g. "file|.txt" -> "file$.txt").

  Raises:
    Error: if the operation fails and we can provide extra information.
    OSError: if the operation fails.
  """
  if (convert_invalid_windows_characters and
      platforms.OperatingSystem.Current() == platforms.OperatingSystem.WINDOWS):
    path = platforms.MakePathWindowsCompatible(path)
  try:
    os.makedirs(path, mode=mode)
  except OSError as ex:
    base_msg = 'Could not create directory [{0}]: '.format(path)
    if ex.errno == errno.EEXIST and os.path.isdir(path):
      pass
    elif ex.errno == errno.EEXIST and os.path.isfile(path):
      raise Error(base_msg + 'A file exists at that location.\n\n')
    elif ex.errno == errno.EACCES:
      raise Error(
          base_msg + 'Permission denied.\n\n' +
          ('Please verify that you have permissions to write to the parent '
           'directory.'))
    else:
      raise


def _WaitForRetry(retries_left):
  """Sleeps for a period of time based on the retry count.

  Args:
    retries_left: int, The number of retries remaining.  Should be in the range
      of NUM_RETRIES - 1 to 0.
  """
  time_to_wait = .1 * (2 * (NUM_RETRIES - retries_left))
  logging.debug('Waiting for retry: [%s]', time_to_wait)
  time.sleep(time_to_wait)


RETRY_ERROR_CODES = [5, 32, 145]


def _ShouldRetryOperation(func, exc_info):
  """Matches specific error types that should be retried.

  This will retry the following errors:
    WindowsError(5, 'Access is denied'), When trying to delete a readonly file
    WindowsError(32, 'The process cannot access the file because it is being '
      'used by another process'), When a file is in use.
    WindowsError(145, 'The directory is not empty'), When a directory cannot be
      deleted.

  Args:
    func: function, The function that failed.
    exc_info: sys.exc_info(), The current exception state.

  Returns:
    True if the error can be retried or false if we should just fail.
  """
  # os.unlink is the same as os.remove
  if not (func == os.remove or func == os.rmdir or func == os.unlink):
    return False
  if not WindowsError:
    return False
  e = exc_info[1]
  return getattr(e, 'winerror', None) in RETRY_ERROR_CODES


def _RetryOperation(exc_info, func, args,
                    retry_test_function=lambda func, exc_info: True):
  """Attempts to retry the failed file operation.

  Args:
    exc_info: sys.exc_info(), The current exception state.
    func: function, The function that failed.
    args: (str, ...), The tuple of args that should be passed to func when
      retrying.
    retry_test_function: The function to call to determine if a retry should be
      attempted.  Takes the function that is being retried as well as the
      current exc_info.

  Returns:
    True if the operation eventually succeeded or False if it continued to fail
    for all retries.
  """
  retries_left = NUM_RETRIES
  while retries_left > 0 and retry_test_function(func, exc_info):
    logging.debug(
        'Retrying file system operation: %s, %s, %s, retries_left=%s',
        func, args, exc_info, retries_left)
    retries_left -= 1
    try:
      _WaitForRetry(retries_left)
      func(*args)
      return True
    # pylint: disable=bare-except, We look at the exception later.
    except:
      exc_info = sys.exc_info()
  return False


def _HandleRemoveError(func, failed_path, exc_info):
  """A function to pass as the onerror arg to rmdir for handling errors.

  Args:
    func: function, The function that failed.
    failed_path: str, The path of the file the error occurred on.
    exc_info: sys.exc_info(), The current exception state.
  """
  logging.debug('Handling file system error: %s, %s, %s',
                func, failed_path, exc_info)

  # Access denied on Windows. This happens when trying to delete a readonly
  # file. Change the permissions and retry the delete.
  #
  # In python 3.3+, WindowsError is an alias of OSError and exc_info[0] can be
  # a subclass of OSError.
  # In Python 3.12+ exc_info is an exception instance instead of a
  # (typ, val, tb) triplet.
  if not isinstance(exc_info, tuple):
    exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
  if (WindowsError and issubclass(exc_info[0], WindowsError) and
      getattr(exc_info[1], 'winerror', None) == 5):
    os.chmod(failed_path, stat.S_IWUSR)

  # Don't remove the trailing comma in the passed arg tuple.  It indicates that
  # it is a tuple of 1, rather than a tuple of characters that will get expanded
  # by *args.
  if not _RetryOperation(exc_info, func, (failed_path,), _ShouldRetryOperation):
    # Always raise the original error.
    exceptions.reraise(exc_info[1], tb=exc_info[2])


def RmTree(path):
  """Calls shutil.rmtree() with error handling to fix Windows problems.

  It also ensures that the top level directory deletion is actually reflected
  in the file system before this returns.

  Args:
    path: str, The path to remove.
  """
  # The subdirectories and/or files under dir_path may have file names
  # containing unicode characters. If the arg to shutil.rmtree() is not unicode
  # then any child unicode files will raise an exception. Coercing dir_path to
  # unicode makes shutil.rmtree() play nice with unicode.
  path = six.text_type(path)
  if sys.version_info[:2] < (3, 12):
    shutil.rmtree(path, onerror=_HandleRemoveError)
  else:
    shutil.rmtree(path, onexc=_HandleRemoveError)  # pylint: disable=unexpected-keyword-arg
  retries_left = NUM_RETRIES
  while os.path.isdir(path) and retries_left > 0:
    logging.debug('Waiting for directory to disappear: %s', path)
    retries_left -= 1
    _WaitForRetry(retries_left)


def _DestInSrc(src, dst):
  # Copied directly from shutil
  src = os.path.abspath(src)
  dst = os.path.abspath(dst)
  if not src.endswith(os.path.sep):
    src += os.path.sep
  if not dst.endswith(os.path.sep):
    dst += os.path.sep
  return dst.startswith(src)


def MoveDir(src, dst):
  """Recursively moves a directory to another location.

  This code is mostly copied from shutil.move(), but has been scoped down to
  specifically handle only directories.  The src must be a directory, and
  the dst must not exist.  It uses functions from this module to be resilient
  against spurious file system errors in Windows.  It will try to do an
  os.rename() of the directory.  If that fails, the tree will be copied to the
  new location and then deleted from the old location.

  Args:
    src: str, The directory path to move.
    dst: str, The path to move the directory to.

  Raises:
    Error: If the src or dst directories are not valid.
  """
  if not os.path.isdir(src):
    raise Error("Source path '{0}' must be a directory".format(src))
  if os.path.exists(dst):
    raise Error("Destination path '{0}' already exists".format(dst))
  if _DestInSrc(src, dst):
    raise Error("Cannot move a directory '{0}' into itself '{1}'."
                .format(src, dst))
  try:
    logging.debug('Attempting to move directory [%s] to [%s]', src, dst)
    try:
      os.rename(src, dst)
    except OSError:
      if not _RetryOperation(sys.exc_info(), os.rename, (src, dst)):
        raise
  except OSError as e:
    logging.debug('Directory rename failed.  Falling back to copy. [%s]', e)
    shutil.copytree(src, dst, symlinks=True)
    RmTree(src)


def FindDirectoryContaining(starting_dir_path, directory_entry_name):
  """Searches directories upwards until it finds one with the given contents.

  This can be used to find the directory above you that contains the given
  entry.  It is useful for things like finding the workspace root you are under
  that contains a configuration directory.

  Args:
    starting_dir_path: str, The path of the directory to start searching
      upwards from.
    directory_entry_name: str, The name of the directory that must be present
      in order to return the current directory.

  Returns:
    str, The full path to the directory above the starting dir that contains the
    given entry, or None if the root of the file system was hit without finding
    it.
  """
  prev_path = None
  path = encoding_util.Decode(os.path.realpath(starting_dir_path))
  while path != prev_path:
    search_dir = os.path.join(path, directory_entry_name)
    if os.path.isdir(search_dir):
      return path
    prev_path = path
    path, _ = os.path.split(path)
  return None


def IsDirAncestorOf(ancestor_directory, path):
  """Returns whether ancestor_directory is an ancestor of path.

  Args:
    ancestor_directory: str, path to the directory that is the potential
      ancestor of path
    path: str, path to the file/directory that is a potential descendant of
      ancestor_directory

  Returns:
    bool, whether path has ancestor_directory as an ancestor.

  Raises:
    ValueError: if the given ancestor_directory is not, in fact, a directory.
  """
  if not os.path.isdir(ancestor_directory):
    raise ValueError('[{0}] is not a directory.'.format(ancestor_directory))

  path = encoding_util.Decode(os.path.realpath(path))
  ancestor_directory = encoding_util.Decode(
      os.path.realpath(ancestor_directory))

  try:
    rel = os.path.relpath(path, ancestor_directory)
  except ValueError:  # On Windows, relpath raises for paths on different drives
    return False

  # rel can be just '..' if path is a child of ancestor_directory
  return not rel.startswith('..' + os.path.sep) and rel != '..'


def _GetSystemPath():
  """Returns properly encoded system PATH variable string."""
  return encoding_util.GetEncodedValue(os.environ, 'PATH')


def SearchForExecutableOnPath(executable, path=None):
  """Tries to find all 'executable' in the directories listed in the PATH.

  This is mostly copied from distutils.spawn.find_executable() but with a
  few differences.  It does not check the current directory for the
  executable.  We only want to find things that are actually on the path, not
  based on what the CWD is.  It also returns a list of all matching
  executables.  If there are multiple versions of an executable on the path
  it will return all of them at once.

  Args:
    executable: The name of the executable to find
    path: A path to search.  If none, the system PATH will be used.

  Returns:
    A list of full paths to matching executables or an empty list if none
    are found.
  """
  if not path:
    path = _GetSystemPath()
    if not path:
      return []
  paths = path.split(os.pathsep)

  matching = []
  for p in paths:
    f = os.path.join(p, executable)
    if os.path.isfile(f):
      matching.append(f)

  return matching


def _FindExecutableOnPath(executable, path, pathext):
  """Internal function to a find an executable.

  Args:
    executable: The name of the executable to find.
    path: A list of directories to search separated by 'os.pathsep'.
    pathext: An iterable of file name extensions to use.

  Returns:
    str, the path to a file on `path` with name `executable` + `p` for
      `p` in `pathext`.

  Raises:
    ValueError: invalid input.
  """

  if isinstance(pathext, six.string_types):
    raise ValueError('_FindExecutableOnPath(..., pathext=\'{0}\') failed '
                     'because pathext must be an iterable of strings, but got '
                     'a string.'.format(pathext))

  # Prioritize preferred extension over earlier in path.
  for ext in pathext:
    for directory in path.split(os.pathsep):
      # Windows can have paths quoted.
      directory = directory.strip('"')
      full = os.path.normpath(os.path.join(directory, executable) + ext)
      # On Windows os.access(full, os.X_OK) is always True.
      if os.path.isfile(full) and os.access(full, os.X_OK):
        return full
  return None


def _PlatformExecutableExtensions(platform):
  if platform == platforms.OperatingSystem.WINDOWS:
    return ('.exe', '.cmd', '.bat', '.com', '.ps1')
  else:
    return ('', '.sh')


def FindExecutableOnPath(executable, path=None, pathext=None,
                         allow_extensions=False):
  """Searches for `executable` in the directories listed in `path` or $PATH.

  Executable must not contain a directory or an extension.

  Args:
    executable: The name of the executable to find.
    path: A list of directories to search separated by 'os.pathsep'.  If None
      then the system PATH is used.
    pathext: An iterable of file name extensions to use.  If None then
      platform specific extensions are used.
    allow_extensions: A boolean flag indicating whether extensions in the
      executable are allowed.

  Returns:
    The path of 'executable' (possibly with a platform-specific extension) if
    found and executable, None if not found.

  Raises:
    ValueError: if executable has a path or an extension, and extensions are
      not allowed, or if there's an internal error.
  """

  if not allow_extensions and os.path.splitext(executable)[1]:
    raise ValueError('FindExecutableOnPath({0},...) failed because first '
                     'argument must not have an extension.'.format(executable))

  if os.path.dirname(executable):
    raise ValueError('FindExecutableOnPath({0},...) failed because first '
                     'argument must not have a path.'.format(executable))

  if path is None:
    effective_path = _GetSystemPath()
    if effective_path is None:
      return None
  else:
    effective_path = path
  effective_pathext = (pathext if pathext is not None
                       else _PlatformExecutableExtensions(
                           platforms.OperatingSystem.Current()))

  return _FindExecutableOnPath(executable, effective_path,
                               effective_pathext)


def HasWriteAccessInDir(directory):
  """Determines if the current user is able to modify the contents of the dir.

  Args:
    directory: str, The full path of the directory to check.

  Raises:
    ValueError: If the given directory path is not a valid directory.

  Returns:
    True if the current user has missing write and execute permissions.
  """
  if not os.path.isdir(directory):
    raise ValueError(
        'The given path [{path}] is not a directory.'.format(path=directory))
  # Appending . tests search permissions, especially on windows, by forcing
  # 'directory' to be treated as a directory
  path = os.path.join(directory, '.')
  if not os.access(path, os.X_OK) or not os.access(path, os.W_OK):
    # We can believe os.access() indicating no access.
    return False

  # At this point the only platform and filesystem independent method is to
  # attempt to create or delete a file in the directory.
  #
  # Why? os.accesss() and os.stat() use the underlying C library on Windows,
  # which doesn't check the correct user and group permissions and almost always
  # results in false positive writability tests.

  path = os.path.join(directory,
                      '.HasWriteAccessInDir{pid}'.format(pid=os.getpid()))
  # while True: should work here, but we limit the retries just in case.
  for _ in range(10):

    try:
      fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o666)
      os.close(fd)
    except OSError as e:
      if e.errno == errno.EACCES:
        # No write access.
        return False
      if e.errno in [errno.ENOTDIR, errno.ENOENT]:
        # The directory has been removed or replaced by a file.
        raise ValueError('The given path [{path}] is not a directory.'.format(
            path=directory))
      raise

    try:
      os.remove(path)
      # Write access.
      return True
    except OSError as e:
      if e.errno == errno.EACCES:
        # No write access.
        return False
      # os.remove() could fail with ENOENT if we're in a race with another
      # process/thread (which just succeeded) or if the directory has been
      # removed.
      if e.errno != errno.ENOENT:
        raise

  return False


def GetCWD():
  """Returns os.getcwd() properly decoded."""
  return encoding_util.Decode(os.getcwd())


class TemporaryDirectory(object):
  """A class to easily create and dispose of temporary directories.

  Securely creates a directory for temporary use.  This class can be used with
  a context manager (the with statement) to ensure cleanup in exceptional
  situations.
  """

  def __init__(self, change_to=False):
    self.__temp_dir = tempfile.mkdtemp()
    self._curdir = None
    if change_to:
      self._curdir = GetCWD()
      os.chdir(self.__temp_dir)

  @property
  def path(self):
    return self.__temp_dir

  def __enter__(self):
    return self.path

  def __exit__(self, prev_exc_type, prev_exc_val, prev_exc_trace):
    try:
      self.Close()
    except:  # pylint: disable=bare-except
      exceptions.RaiseWithContext(
          prev_exc_type, prev_exc_val, prev_exc_trace, *sys.exc_info())
    # Always return False so any previous exception will be re-raised.
    return False

  def Close(self):
    if self._curdir is not None:
      os.chdir(self._curdir)
    if self.path:
      RmTree(self.path)
      self.__temp_dir = None
      return True
    return False


class Checksum(object):
  """Consistently handles calculating checksums across the Cloud SDK."""

  def __init__(self, algorithm=hashlib.sha256):
    """Creates a new Checksum."""
    self.__hash = algorithm()
    self.__files = set()

  def AddContents(self, contents):
    """Adds the given contents to the checksum.

    Args:
      contents: str or bytes, The contents to add.

    Returns:
      self, For method chaining.
    """
    self.__hash.update(six.ensure_binary(contents))
    return self

  def AddFileContents(self, file_path):
    """Adds the contents of the given file to the checksum.

    Args:
      file_path: str, The file path of the contents to add.

    Returns:
      self, For method chaining.
    """
    with BinaryFileReader(file_path) as fp:
      while True:
        chunk = fp.read(4096)
        if not chunk:
          break
        self.__hash.update(chunk)
    return self

  def AddDirectory(self, dir_path):
    """Adds all files under the given directory to the checksum.

    This adds both the contents of the files as well as their names and
    locations to the checksum.  If the checksums of two directories are equal
    this means they have exactly the same files, and contents.

    Args:
      dir_path: str, The directory path to add all files from.

    Returns:
      self, For method chaining.
    """
    # The subdirectories and/or files under dir_path may have file names
    # containing unicode characters. If the arg to os.walk() is not unicode then
    # any child unicode files will raise an exception. Coercing dir_path to
    # unicode makes os.walk() play nice with unicode.
    dir_path = six.text_type(dir_path)
    for root, dirs, files in os.walk(dir_path):
      dirs.sort(key=os.path.normcase)
      files.sort(key=os.path.normcase)
      for d in dirs:
        path = os.path.join(root, d)
        # We don't traverse directory links, but add the fact that it was found
        # in the tree.
        if os.path.islink(path):
          relpath = os.path.relpath(path, dir_path)
          self.__files.add(relpath)
          self.AddContents(relpath)
          self.AddContents(os.readlink(path))
      for f in files:
        path = os.path.join(root, f)
        relpath = os.path.relpath(path, dir_path)
        self.__files.add(relpath)
        self.AddContents(relpath)
        if os.path.islink(path):
          self.AddContents(os.readlink(path))
        else:
          self.AddFileContents(path)
    return self

  def HexDigest(self):
    """Gets the hex digest for all content added to this checksum.

    Returns:
      str, The checksum digest as a hex string.
    """
    return self.__hash.hexdigest()

  def Files(self):
    """Gets the list of all files that were discovered when adding a directory.

    Returns:
      {str}, The relative paths of all files that were found when traversing the
      directory tree.
    """
    return self.__files

  @staticmethod
  def FromSingleFile(input_path, algorithm=hashlib.sha256):
    """Creates a Checksum containing one file.

    Args:
      input_path: str, The file path of the contents to add.
      algorithm: a hashing algorithm method, a la hashlib.algorithms

    Returns:
      Checksum, The checksum containing the file.
    """
    return Checksum(algorithm=algorithm).AddFileContents(input_path)

  @staticmethod
  def HashSingleFile(input_path, algorithm=hashlib.sha256):
    """Gets the hex digest of a single file.

    Args:
      input_path: str, The file path of the contents to add.
      algorithm: a hashing algorithm method, ala hashlib.algorithms

    Returns:
      str, The checksum digest of the file as a hex string.
    """
    return Checksum.FromSingleFile(input_path, algorithm=algorithm).HexDigest()


class ChDir(object):
  """Do some things from a certain directory, and reset the directory afterward.
  """

  def __init__(self, directory):
    self.__dir = directory

  def __enter__(self):
    self.__original_dir = GetCWD()
    os.chdir(self.__dir)
    return self.__dir

  def __exit__(self, typ, value, tb):
    os.chdir(self.__original_dir)


class FileLockLockingError(Error):
  pass


class FileLockTimeoutError(FileLockLockingError):
  """A case of FileLockLockingError."""
  pass


class FileLockUnlockingError(Error):
  pass


class FileLock(object):
  """A file lock for interprocess (not interthread) mutual exclusion.

  At most one FileLock instance may be locked at a time for a given local file
  path. FileLock instances may be used as context objects.
  """

  def __init__(self, path, timeout_secs=None):
    """Constructs the FileLock.

    Args:
      path: str, the path to the file to lock. The directory containing the
        file must already exist when Lock() is called.
      timeout_secs: int, seconds Lock() may wait for the lock to become
        available. If None, Lock() may block forever.
    """
    self._path = path
    self._timeout_secs = timeout_secs
    self._file = None
    self._locked = False
    if platforms.OperatingSystem.Current() == platforms.OperatingSystem.WINDOWS:
      self._impl = _WindowsLocking()
    else:
      self._impl = _PosixLocking()

  def Lock(self):
    """Opens and locks the file. A no-op if this FileLock is already locked.

    The lock file is created if it does not already exist.

    Raises:
      FileLockLockingError: if the file could not be opened (or created when
        necessary).
      FileLockTimeoutError: if the file could not be locked before the timeout
        elapsed.
    """
    if self._locked:
      return
    try:
      self._file = FileWriter(self._path)
    except Error as e:
      raise FileLockLockingError(e)

    max_wait_ms = None
    if self._timeout_secs is not None:
      max_wait_ms = 1000 * self._timeout_secs

    r = retry.Retryer(max_wait_ms=max_wait_ms)
    try:
      r.RetryOnException(self._impl.TryLock, args=[self._file.fileno()],
                         sleep_ms=100)
    except retry.RetryException as e:
      self._file.close()
      self._file = None
      raise FileLockTimeoutError(
          'Timed-out waiting to lock file: {0}'.format(self._path))
    else:
      self._locked = True

  def Unlock(self):
    """Unlocks and closes the file.

    A no-op if this object is not locked.

    Raises:
      FileLockUnlockingError: if a problem was encountered when unlocking the
        file. There is no need to retry.
    """
    if not self._locked:
      return
    try:
      self._impl.Unlock(self._file.fileno())
    except IOError as e:
      # We don't expect Unlock() to ever raise an error, but can't be sure.
      raise FileLockUnlockingError(e)
    finally:
      self._file.close()
      self._file = None
      self._locked = False

  def __enter__(self):
    """Locks and returns this FileLock object."""
    self.Lock()
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    """Unlocks, logging any errors encountered."""
    try:
      self.Unlock()
    except Error as e:
      logging.debug('Encountered error unlocking file %s: %s', self._path, e)
    # Have Python re-raise the exception which caused the context to exit, if
    # any.
    return False


# Imports fcntl, which is only available on POSIX.
class _PosixLocking(object):
  """Exclusive, non-blocking file locking on POSIX systems."""

  def TryLock(self, fd):
    """Raises IOError on failure."""
    # pylint: disable=g-import-not-at-top
    import fcntl
    # Exclusive lock, non-blocking
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

  def Unlock(self, fd):
    import fcntl  # pylint: disable=g-import-not-at-top
    fcntl.flock(fd, fcntl.LOCK_UN)


# Imports msvcrt, which is only available on Windows.
class _WindowsLocking(object):
  """Exclusive, non-blocking file locking on Windows."""

  def TryLock(self, fd):
    """Raises IOError on failure."""
    # pylint: disable=g-import-not-at-top
    import msvcrt
    # Exclusive lock, non-blocking
    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)

  def Unlock(self, fd):
    import msvcrt  # pylint: disable=g-import-not-at-top
    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)


@contextlib.contextmanager
def _FileInBinaryMode(file_obj):
  """Context manager to temporarily swap a file to binary mode on Windows.

  On exit, the mode is swapped back to its original mode, whether that was text
  or binary.

  See the 'On Windows...' note in the Python docs for more info about text and
  binary mode:
  https://docs.python.org/2/tutorial/inputoutput.html#reading-and-writing-files

  Args:
    file_obj: File-like object to swap to binary mode.

  Yields:
    None.
  """
  # If file_obj does not define fileno, just pass it through. For example,
  # this happens for unit tests which replace sys.stdin with StringIO.
  try:
    fd = file_obj.fileno()
  except (AttributeError, io.UnsupportedOperation):
    yield
    return

  if platforms.OperatingSystem.IsWindows():
    # pylint: disable=g-import-not-at-top
    import msvcrt

    try:
      old_mode = msvcrt.setmode(fd, os.O_BINARY)
      yield
    finally:
      msvcrt.setmode(fd, old_mode)
  else:
    # On non-Windows platforms, text mode == binary mode, so just yield.
    yield


def WriteStreamBytes(stream, contents):
  """Write the given bytes to the stream.

  Args:
    stream: The raw stream to write to, usually sys.stdout or sys.stderr.
    contents: A byte string to write to the stream.
  """
  if six.PY2:
    with _FileInBinaryMode(stream):
      stream.write(contents)
      # Flush to force content to be written out with the correct mode.
      stream.flush()
  else:
    # This is raw byte stream, but it doesn't exist on PY2.
    stream.buffer.write(contents)


def ReadStdinBytes():
  """Reads raw bytes from sys.stdin without any encoding interpretation.

  Returns:
    bytes, The byte string that was read.
  """
  if six.PY2:
    with _FileInBinaryMode(sys.stdin):
      return sys.stdin.read()
  else:
    # This is raw byte stream, but it doesn't exist on PY2.
    return sys.stdin.buffer.read()


def WriteFileAtomically(file_name,
                        contents,
                        convert_invalid_windows_characters=False):
  """Writes a file to disk safely cross platform.

  Specified directories will be created if they don't exist.

  Writes a file to disk safely cross platform. Note that on Windows, there
  is no good way to atomically write a file to disk.

  Args:
    file_name: The actual file to write to.
    contents:  The file contents to write.
    convert_invalid_windows_characters: bool, Convert invalid Windows path
        characters with an 'unsupported' symbol rather than trigger an OSError
        on Windows (e.g. "file|.txt" -> "file$.txt").

  Raises:
    ValueError: file_name or contents is empty.
    TypeError: contents is not a valid string.
  """
  if not file_name or contents is None:
    raise ValueError('Empty file_name [{}] or contents [{}].'.format(
        file_name, contents))

  if not isinstance(contents, six.string_types):
    raise TypeError('Invalid contents [{}].'.format(contents))

  dirname = os.path.dirname(file_name)

  # Create the directories, if they dont exist.
  try:
    os.makedirs(dirname)
  except os.error:
    # Deliberately ignore errors here. This usually means that the directory
    # already exists. Other errors will surface from the write calls below.
    pass

  if platforms.OperatingSystem.IsWindows():
    # On Windows, there is no good way to atomically write this file.
    WriteFileContents(
        file_name,
        contents,
        private=True,
        convert_invalid_windows_characters=convert_invalid_windows_characters)
  else:
    # This opens files with 0600, which are the correct permissions.
    with tempfile.NamedTemporaryFile(
        mode='w', dir=dirname, delete=False) as temp_file:
      temp_file.write(contents)
      # This was a user-submitted patch to fix a race condition that we couldn't
      # reproduce. It may be due to the file being renamed before the OS's
      # buffer flushes to disk.
      temp_file.flush()
      # This pattern atomically writes the file on non-Windows systems.
      os.rename(temp_file.name, file_name)


def GetTreeSizeBytes(path, predicate=None):
  """Returns sum of sizes of not-ignored files under given path, in bytes."""
  result = 0
  if predicate is None:
    predicate = lambda x: True
  for directory in os.walk(six.text_type(path)):
    for file_name in directory[2]:
      file_path = os.path.join(directory[0], file_name)
      if predicate(file_path):
        result += os.path.getsize(file_path)
  return result


def GetDirectoryTreeListing(path,
                            include_dirs=False,
                            file_predicate=None,
                            dir_sort_func=None,
                            file_sort_func=None):
  """Yields a generator that list all the files in a directory tree.

  Walks directory tree from path and yeilds all files that it finds. Will expand
  paths relative to home dir e.g. those that start with '~'.

  Args:
    path: string, base of file tree to walk.
    include_dirs: bool, if true will yield directory names in addition to files.
    file_predicate: function, boolean function to determine which files should
      be included in the output. Default is all files.
    dir_sort_func: function, function that will determine order directories are
      processed. Default is lexical ordering.
    file_sort_func:  function, function that will determine order directories
      are processed. Default is lexical ordering.
  Yields:
    Generator: yields all files and directory paths matching supplied criteria.
  """
  if not file_sort_func:
    file_sort_func = sorted
  if file_predicate is None:
    file_predicate = lambda x: True
  if dir_sort_func is None:
    dir_sort_func = lambda x: x.sort()

  for root, dirs, files in os.walk(ExpandHomeDir(six.text_type(path))):
    dir_sort_func(dirs)
    if include_dirs:
      for dirname in dirs:
        yield dirname
    for file_name in file_sort_func(files):
      file_path = os.path.join(root, file_name)
      if file_predicate(file_path):
        yield file_path


def ReadFileContents(path):
  """Reads the text contents from the given path.

  Args:
    path: str, The file path to read.

  Raises:
    Error: If the file cannot be read.

  Returns:
    str, The text string read from the file.
  """
  try:
    with FileReader(path) as f:
      return f.read()
  except EnvironmentError as e:
    # EnvironmentError is parent of IOError, OSError and WindowsError.
    # Raised when file does not exist or can't be opened/read.
    raise Error('Unable to read file [{0}]: {1}'.format(path, e))


def ReadBinaryFileContents(path):
  """Reads the binary contents from the given path.

  Args:
    path: str, The file path to read.

  Raises:
    Error: If the file cannot be read.

  Returns:
    bytes, The byte string read from the file.
  """
  try:
    with BinaryFileReader(path) as f:
      return f.read()
  except EnvironmentError as e:
    # EnvironmentError is parent of IOError, OSError and WindowsError.
    # Raised when file does not exist or can't be opened/read.
    raise Error('Unable to read file [{0}]: {1}'.format(path, e))


def WriteFileContents(path,
                      contents,
                      overwrite=True,
                      private=False,
                      create_path=True,
                      newline=None,
                      convert_invalid_windows_characters=False):
  """Writes the given text contents to a file at the given path.

  Args:
    path: str, The file path to write to.
    contents: str, The text string to write.
    overwrite: bool, False to error out if the file already exists.
    private: bool, True to make the file have 0o600 permissions.
    create_path: bool, True to create intermediate directories, if needed.
    newline: str, The line ending style to use, or None to use platform default.
    convert_invalid_windows_characters: bool, Convert invalid Windows path
        characters with an 'unsupported' symbol rather than trigger an OSError
        on Windows (e.g. "file|.txt" -> "file$.txt").

  Raises:
    Error: If the file cannot be written.
  """
  try:
    _CheckOverwrite(path, overwrite)
    with FileWriter(
        path,
        private=private,
        create_path=create_path,
        newline=newline,
        convert_invalid_windows_characters=convert_invalid_windows_characters
    ) as f:
      # This decode is here because a lot of libraries on Python 2 can return
      # both text or bytes depending on if unicode is present. If you truly
      # pass binary data to this, the decode will fail (as it should). If you
      # pass an ascii string (that you got from json.dumps() for example), this
      # will prevent it from crashing.
      f.write(encoding_util.Decode(contents))
  except EnvironmentError as e:
    # EnvironmentError is parent of IOError, OSError and WindowsError.
    # Raised when file does not exist or can't be opened/read.
    raise Error('Unable to write file [{0}]: {1}'.format(path, e))


def WriteBinaryFileContents(path,
                            contents,
                            overwrite=True,
                            private=False,
                            create_path=True,
                            convert_invalid_windows_characters=False):
  """Writes the given binary contents to a file at the given path.

  Args:
    path: str, The file path to write to.
    contents: str, The byte string to write.
    overwrite: bool, False to error out if the file already exists.
    private: bool, True to make the file have 0o600 permissions.
    create_path: bool, True to create intermediate directories, if needed.
    convert_invalid_windows_characters: bool, Convert invalid Windows path
        characters with an 'unsupported' symbol rather than trigger an OSError
        on Windows (e.g. "file|.txt" -> "file$7.txt").

  Raises:
    Error: If the file cannot be written.
  """
  try:
    _CheckOverwrite(path, overwrite)
    with BinaryFileWriter(
        path,
        private=private,
        create_path=create_path,
        convert_invalid_windows_characters=convert_invalid_windows_characters
    ) as f:
      f.write(contents)
  except EnvironmentError as e:
    # EnvironmentError is parent of IOError, OSError and WindowsError.
    # Raised when file does not exist or can't be opened/read.
    raise Error('Unable to write file [{0}]: {1}'.format(path, e))


def _CheckOverwrite(path, overwrite):
  if not overwrite and os.path.exists(path):
    raise Error(
        'File [{0}] already exists and cannot be overwritten'.format(path))


def FileReader(path):
  """Opens the given file for text read for use in a 'with' statement.

  Args:
    path: str, The file path to read from.

  Returns:
    A file-like object opened for read in text mode.
  """
  return _FileOpener(path, 'rt', 'read', encoding='utf-8')


def BinaryFileReader(path):
  """Opens the given file for binary read for use in a 'with' statement.

  Args:
    path: str, The file path to read from.

  Returns:
    A file-like object opened for read in binary mode.
  """
  return _FileOpener(encoding_util.Encode(path, encoding='utf-8'), 'rb', 'read')


def FileWriter(path,
               private=False,
               append=False,
               create_path=False,
               newline=None,
               convert_invalid_windows_characters=False):
  """Opens the given file for text write for use in a 'with' statement.

  Args:
    path: str, The file path to write to.
    private: bool, True to create or update the file permission to be 0o600.
    append: bool, True to append to an existing file.
    create_path: bool, True to create intermediate directories, if needed.
    newline: str, The line ending style to use, or None to use plaform default.
    convert_invalid_windows_characters: bool, Convert invalid Windows path
        characters with an 'unsupported' symbol rather than trigger an OSError
        on Windows (e.g. "file|.txt" -> "file$7.txt").

  Returns:
    A file-like object opened for write in text mode.
  """
  mode = 'at' if append else 'wt'
  return _FileOpener(
      path,
      mode,
      'write',
      encoding='utf-8',
      private=private,
      create_path=create_path,
      newline=newline,
      convert_invalid_windows_characters=convert_invalid_windows_characters)


class BinaryFileWriterMode(enum.Enum):
  APPEND = 'ab'
  MODIFY = 'r+b'
  TRUNCATE = 'wb'


def BinaryFileWriter(path,
                     private=False,
                     mode=BinaryFileWriterMode.TRUNCATE,
                     create_path=False,
                     convert_invalid_windows_characters=False):
  """Opens the given file for binary write for use in a 'with' statement.

  Args:
    path: str, The file path to write to.
    private: bool, True to create or update the file permission to be 0o600.
    mode: BinaryFileWriterMode, Determines how to open file for writing.
    create_path: bool, True to create intermediate directories, if needed.
    convert_invalid_windows_characters: bool, Convert invalid Windows path
        characters with an 'unsupported' symbol rather than trigger an OSError
        on Windows (e.g. "file|.txt" -> "file$7.txt").

  Returns:
    A file-like object opened for write in binary mode.
  """
  return _FileOpener(
      path,
      mode.value,
      'write',
      private=private,
      create_path=create_path,
      convert_invalid_windows_characters=convert_invalid_windows_characters)


def _FileOpener(path,
                mode,
                verb,
                encoding=None,
                private=False,
                create_path=False,
                newline=None,
                convert_invalid_windows_characters=False):
  """Opens a file in various modes and does error handling."""
  if (convert_invalid_windows_characters and
      platforms.OperatingSystem.Current() == platforms.OperatingSystem.WINDOWS):
    path = platforms.MakePathWindowsCompatible(path)
  if private:
    PrivatizeFile(path)
  if create_path:
    _MakePathToFile(path)
  try:
    return io.open(path, mode, encoding=encoding, newline=newline)
  except EnvironmentError as e:
    # EnvironmentError is parent of IOError, OSError and WindowsError.
    # Raised when file does not exist or can't be opened/read.
    exc_type = Error
    if isinstance(e, IOError) and e.errno == errno.ENOENT:
      exc_type = MissingFileError
    raise exc_type('Unable to {0} file [{1}]: {2}'.format(verb, path, e))


def GetHomeDir():
  """Returns the current user HOME directory path."""
  return ExpandHomeDir('~')


def ExpandHomeDir(path):
  """Returns path with leading ~<SEP> or ~<USER><SEP> expanded."""
  return encoding_util.Decode(os.path.expanduser(path))


def ExpandHomeAndVars(path):
  """Expands ~ and ENV_VARS in path."""
  return encoding_util.Decode(os.path.expandvars(ExpandHomeDir(path)))


def NormalizePathFromURL(url):
  """Converts url to path string and normalizes path string."""
  url2pathname = six.moves.urllib.request.url2pathname
  return os.path.normcase(os.path.normpath(url2pathname(url)))


def _MakePathToFile(path, mode=0o777):
  parent_dir_path, _ = os.path.split(path)
  full_parent_dir_path = os.path.realpath(ExpandHomeDir(parent_dir_path))
  MakeDir(full_parent_dir_path, mode)


def PrivatizeFile(path):
  """Makes an existing file private or creates a new, empty private file.

  In theory it would be better to return the open file descriptor so that it
  could be used directly. The issue that we would need to pass an encoding to
  os.fdopen() and on Python 2. This is not supported. Instead we just create
  the empty file and then we will just open it normally later to do the write.

  Args:
    path: str, The path of the file to create or privatize.
  """
  try:
    if os.path.exists(path):
      os.chmod(path, 0o600)
    else:
      _MakePathToFile(path, mode=0o700)
      flags = os.O_RDWR | os.O_CREAT | os.O_TRUNC
      # Accommodate Windows; stolen from python2.6/tempfile.py.
      if hasattr(os, 'O_NOINHERIT'):
        flags |= os.O_NOINHERIT

      fd = os.open(path, flags, 0o600)
      os.close(fd)
  except EnvironmentError as e:
    # EnvironmentError is parent of IOError, OSError and WindowsError.
    # Raised when file does not exist or can't be opened/read.
    raise Error('Unable to create private file [{0}]: {1}'.format(path, e))


def FilteredFileReader(file_path, regex):
  """Read all lines from a text file matching regex."""
  with FileReader(file_path) as f:
    for line in f:
      if regex.match(line):
        yield line
