# -*- coding: utf-8 -*-
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Shared utility structures and methods for interacting with the host system.

The methods in this module should be limited to obtaining system information and
simple file operations (disk info, retrieving metadata about existing files,
creating directories, fetching environment variables, etc.).
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import errno
import locale
import os
import struct
import sys

import six

from gslib.utils.constants import WINDOWS_1252

_DEFAULT_NUM_TERM_LINES = 25
PLATFORM = str(sys.platform).lower()

# Detect platform types.
IS_WINDOWS = 'win32' in PLATFORM
IS_CYGWIN = 'cygwin' in PLATFORM
IS_LINUX = 'linux' in PLATFORM
IS_OSX = 'darwin' in PLATFORM
# pylint: disable=g-import-not-at-top
if IS_WINDOWS:
  from ctypes import c_int
  from ctypes import c_uint64
  from ctypes import c_char_p
  from ctypes import c_wchar_p
  from ctypes import windll
  from ctypes import POINTER
  from ctypes import WINFUNCTYPE
  from ctypes import WinError
  IS_CP1252 = locale.getdefaultlocale()[1] == WINDOWS_1252
else:
  IS_CP1252 = False


def CheckFreeSpace(path):
  """Return path/drive free space (in bytes)."""
  if IS_WINDOWS:
    try:
      # pylint: disable=invalid-name
      get_disk_free_space_ex = WINFUNCTYPE(c_int, c_wchar_p, POINTER(c_uint64),
                                           POINTER(c_uint64), POINTER(c_uint64))
      get_disk_free_space_ex = get_disk_free_space_ex(
          ('GetDiskFreeSpaceExW', windll.kernel32), (
              (1, 'lpszPathName'),
              (2, 'lpFreeUserSpace'),
              (2, 'lpTotalSpace'),
              (2, 'lpFreeSpace'),
          ))
    except AttributeError:
      get_disk_free_space_ex = WINFUNCTYPE(c_int, c_char_p, POINTER(c_uint64),
                                           POINTER(c_uint64), POINTER(c_uint64))
      get_disk_free_space_ex = get_disk_free_space_ex(
          ('GetDiskFreeSpaceExA', windll.kernel32), (
              (1, 'lpszPathName'),
              (2, 'lpFreeUserSpace'),
              (2, 'lpTotalSpace'),
              (2, 'lpFreeSpace'),
          ))

    def GetDiskFreeSpaceExErrCheck(result, unused_func, args):
      if not result:
        raise WinError()
      return args[1].value

    get_disk_free_space_ex.errcheck = GetDiskFreeSpaceExErrCheck

    return get_disk_free_space_ex(os.getenv('SystemDrive'))
  else:
    (_, f_frsize, _, _, f_bavail, _, _, _, _, _) = os.statvfs(path)
    return f_frsize * f_bavail


def CloudSdkCredPassingEnabled():
  return os.environ.get('CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL') == '1'


def CloudSdkVersion():
  return os.environ.get('CLOUDSDK_VERSION', '')


def CreateDirIfNeeded(dir_path, mode=0o777):
  """Creates a directory, suppressing already-exists errors."""
  if not os.path.exists(dir_path):
    try:
      # Unfortunately, even though we catch and ignore EEXIST, this call will
      # output a (needless) error message (no way to avoid that in Python).
      os.makedirs(dir_path, mode)
    # Ignore 'already exists' in case user tried to start up several
    # resumable uploads concurrently from a machine where no tracker dir had
    # yet been created.
    except OSError as e:
      if e.errno != errno.EEXIST and e.errno != errno.EISDIR:
        raise


def GetDiskCounters():
  """Retrieves disk I/O statistics for all disks.

  Adapted from the psutil module's psutil._pslinux.disk_io_counters:
    http://code.google.com/p/psutil/source/browse/trunk/psutil/_pslinux.py

  Originally distributed under under a BSD license.
  Original Copyright (c) 2009, Jay Loden, Dave Daeschler, Giampaolo Rodola.

  Returns:
    A dictionary containing disk names mapped to the disk counters from
    /disk/diskstats.
  """
  # iostat documentation states that sectors are equivalent with blocks and
  # have a size of 512 bytes since 2.4 kernels. This value is needed to
  # calculate the amount of disk I/O in bytes.
  sector_size = 512

  partitions = []
  with open('/proc/partitions', 'r') as f:
    lines = f.readlines()[2:]
    for line in lines:
      _, _, _, name = line.split()
      if name[-1].isdigit():
        partitions.append(name)

  retdict = {}
  with open('/proc/diskstats', 'r') as f:
    for line in f:
      values = line.split()[:11]
      _, _, name, reads, _, rbytes, rtime, writes, _, wbytes, wtime = values
      if name in partitions:
        rbytes = int(rbytes) * sector_size
        wbytes = int(wbytes) * sector_size
        reads = int(reads)
        writes = int(writes)
        rtime = int(rtime)
        wtime = int(wtime)
        retdict[name] = (reads, writes, rbytes, wbytes, rtime, wtime)
  return retdict


def GetFileSize(fp, position_to_eof=False):
  """Returns size of file, optionally leaving fp positioned at EOF."""
  if not position_to_eof:
    cur_pos = fp.tell()
  fp.seek(0, os.SEEK_END)
  cur_file_size = fp.tell()
  if not position_to_eof:
    fp.seek(cur_pos)
  return cur_file_size


def GetGsutilClientIdAndSecret():
  """Returns a tuple of the gsutil OAuth2 client ID and secret.

  Google OAuth2 clients always have a secret, even if the client is an installed
  application/utility such as gsutil.  Of course, in such cases the "secret" is
  actually publicly known; security depends entirely on the secrecy of refresh
  tokens, which effectively become bearer tokens.

  Returns:
    (str, str) A 2-tuple of (client ID, secret).
  """
  if InvokedViaCloudSdk() and CloudSdkCredPassingEnabled():
    # Cloud SDK installs have a separate client ID / secret.
    return (
        '32555940559.apps.googleusercontent.com',  # Cloud SDK client ID
        'ZmssLNjJy2998hD4CTg2ejr2')  # Cloud SDK secret

  return (
      '909320924072.apps.googleusercontent.com',  # gsutil client ID
      'p3RlpR10xMFh9ZXBS/ZNLYUu')  # gsutil secret


def GetStreamFromFileUrl(storage_url, mode='rb'):
  if storage_url.IsStream():
    return sys.stdin if six.PY2 else sys.stdin.buffer
  else:
    return open(storage_url.object_name, mode)


def GetTermLines():
  """Returns number of terminal lines."""
  # fcntl isn't supported in Windows.
  try:
    import fcntl  # pylint: disable=g-import-not-at-top
    import termios  # pylint: disable=g-import-not-at-top
  except ImportError:
    return _DEFAULT_NUM_TERM_LINES

  def ioctl_GWINSZ(fd):  # pylint: disable=invalid-name
    try:
      return struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))[0]
    except:  # pylint: disable=bare-except
      return 0  # Failure (so will retry on different file descriptor below).

  # Try to find a valid number of lines from termio for stdin, stdout,
  # or stderr, in that order.
  ioc = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
  if not ioc:
    try:
      fd = os.open(os.ctermid(), os.O_RDONLY)
      ioc = ioctl_GWINSZ(fd)
      os.close(fd)
    except:  # pylint: disable=bare-except
      pass
  if not ioc:
    ioc = os.environ.get('LINES', _DEFAULT_NUM_TERM_LINES)
  return int(ioc)


def InvokedViaCloudSdk():
  return os.environ.get('CLOUDSDK_WRAPPER') == '1'


def IsRunningInCiEnvironment():
  """Returns True if running in a CI environment, e.g. GitHub CI."""
  # https://docs.github.com/en/actions/reference/environment-variables
  on_github_ci = 'CI' in os.environ
  on_kokoro = 'KOKORO_ROOT' in os.environ
  return on_github_ci or on_kokoro


def IsRunningInteractively():
  """Returns True if currently running interactively on a TTY."""
  return sys.stdout.isatty() and sys.stderr.isatty() and sys.stdin.isatty()


def MonkeyPatchHttp():
  ver = sys.version_info
  # Checking for and applying monkeypatch for Python versions:
  # 3.0 - 3.6.6, 3.7.0
  if ver.major == 3:
    if (ver.minor < 6 or (ver.minor == 6 and ver.micro < 7) or
        (ver.minor == 7 and ver.micro == 0)):
      _MonkeyPatchHttpForPython_3x()


def _MonkeyPatchHttpForPython_3x():
  # We generally have to do all sorts of gross things when applying runtime
  # patches (dynamic imports, invalid names to resolve symbols in copy/pasted
  # methods, invalid spacing from copy/pasted methods, etc.), so we just disable
  # pylint warnings for this whole method.
  # pylint: disable=all

  # This fixes https://bugs.python.org/issue33365. A fix was applied in
  # https://github.com/python/cpython/commit/936f03e7fafc28fd6fdfba11d162c776b89c0167
  # but to apply that at runtime would mean patching the entire begin() method.
  # Rather, we just override begin() to call its old self, followed by printing
  # the HTTP headers afterward. This prevents us from overriding more behavior
  # than we have to.
  import http
  old_begin = http.client.HTTPResponse.begin

  def PatchedBegin(self):
    old_begin(self)
    if self.debuglevel > 0:
      for hdr, val in self.headers.items():
        print("header:", hdr + ":", val)

  http.client.HTTPResponse.begin = PatchedBegin


def StdinIterator():
  """A generator function that returns lines from stdin."""
  for line in sys.stdin:
    # Strip CRLF.
    yield line.rstrip()


class StdinIteratorCls(six.Iterator):
  """An iterator that returns lines from stdin.
     This is needed because Python 3 balks at pickling the
     generator version above.
  """

  def __iter__(self):
    return self

  def __next__(self):
    line = sys.stdin.readline()
    if not line:
      raise StopIteration()
    return line.rstrip()
