# Copyright 2016 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import errno
import time

import pywintypes
import win32con
import win32file

from oauth2client.contrib import locked_file


class _Win32Opener(locked_file._Opener):
    """Open, lock, and unlock a file using windows primitives."""

    # Error #33:
    #  'The process cannot access the file because another process'
    FILE_IN_USE_ERROR = 33

    # Error #158:
    #  'The segment is already unlocked.'
    FILE_ALREADY_UNLOCKED_ERROR = 158

    def open_and_lock(self, timeout, delay):
        """Open the file and lock it.

        Args:
            timeout: float, How long to try to lock for.
            delay: float, How long to wait between retries

        Raises:
            AlreadyLockedException: if the lock is already acquired.
            IOError: if the open fails.
            CredentialsFileSymbolicLinkError: if the file is a symbolic
                                              link.
        """
        if self._locked:
            raise locked_file.AlreadyLockedException(
                'File {0} is already locked'.format(self._filename))
        start_time = time.time()

        locked_file.validate_file(self._filename)
        try:
            self._fh = open(self._filename, self._mode)
        except IOError as e:
            # If we can't access with _mode, try _fallback_mode
            # and don't lock.
            if e.errno == errno.EACCES:
                self._fh = open(self._filename, self._fallback_mode)
                return

        # We opened in _mode, try to lock the file.
        while True:
            try:
                hfile = win32file._get_osfhandle(self._fh.fileno())
                win32file.LockFileEx(
                    hfile,
                    (win32con.LOCKFILE_FAIL_IMMEDIATELY |
                     win32con.LOCKFILE_EXCLUSIVE_LOCK), 0, -0x10000,
                    pywintypes.OVERLAPPED())
                self._locked = True
                return
            except pywintypes.error as e:
                if timeout == 0:
                    raise

                # If the error is not that the file is already
                # in use, raise.
                if e[0] != _Win32Opener.FILE_IN_USE_ERROR:
                    raise

                # We could not acquire the lock. Try again.
                if (time.time() - start_time) >= timeout:
                    locked_file.logger.warn('Could not lock %s in %s seconds',
                                            self._filename, timeout)
                    if self._fh:
                        self._fh.close()
                    self._fh = open(self._filename, self._fallback_mode)
                    return
                time.sleep(delay)

    def unlock_and_close(self):
        """Close and unlock the file using the win32 primitive."""
        if self._locked:
            try:
                hfile = win32file._get_osfhandle(self._fh.fileno())
                win32file.UnlockFileEx(hfile, 0, -0x10000,
                                       pywintypes.OVERLAPPED())
            except pywintypes.error as e:
                if e[0] != _Win32Opener.FILE_ALREADY_UNLOCKED_ERROR:
                    raise
        self._locked = False
        if self._fh:
            self._fh.close()
