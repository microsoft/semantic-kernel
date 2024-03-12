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
import fcntl
import time

from oauth2client.contrib import locked_file


class _FcntlOpener(locked_file._Opener):
    """Open, lock, and unlock a file using fcntl.lockf."""

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
            # If we can't access with _mode, try _fallback_mode and
            # don't lock.
            if e.errno in (errno.EPERM, errno.EACCES):
                self._fh = open(self._filename, self._fallback_mode)
                return

        # We opened in _mode, try to lock the file.
        while True:
            try:
                fcntl.lockf(self._fh.fileno(), fcntl.LOCK_EX)
                self._locked = True
                return
            except IOError as e:
                # If not retrying, then just pass on the error.
                if timeout == 0:
                    raise
                if e.errno != errno.EACCES:
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
        """Close and unlock the file using the fcntl.lockf primitive."""
        if self._locked:
            fcntl.lockf(self._fh.fileno(), fcntl.LOCK_UN)
        self._locked = False
        if self._fh:
            self._fh.close()
