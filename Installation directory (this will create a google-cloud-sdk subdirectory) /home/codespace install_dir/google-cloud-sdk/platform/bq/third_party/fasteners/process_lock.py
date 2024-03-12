#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2011 OpenStack Foundation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import errno
import logging
import os
import threading
import time

import six

from fasteners import _utils

LOG = logging.getLogger(__name__)


def _ensure_tree(path):
    """Create a directory (and any ancestor directories required).

    :param path: Directory to create
    """
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            if not os.path.isdir(path):
                raise
            else:
                return False
        elif e.errno == errno.EISDIR:
            return False
        else:
            raise
    else:
        return True


class _InterProcessLock(object):
    """An interprocess locking implementation.

    This is a lock implementation which allows multiple locks, working around
    issues like http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=632857 and
    does not require any cleanup. Since the lock is always held on a file
    descriptor rather than outside of the process, the lock gets dropped
    automatically if the process crashes, even if ``__exit__`` is not
    executed.

    There are no guarantees regarding usage by multiple threads in a
    single process here. This lock works only between processes.

    Note these locks are released when the descriptor is closed, so it's not
    safe to close the file descriptor while another thread holds the
    lock. Just opening and closing the lock file can break synchronization,
    so lock files must be accessed only using this abstraction.
    """

    MAX_DELAY = 0.1
    """
    Default maximum delay we will wait to try to acquire the lock (when
    it's busy/being held by another process).
    """

    DELAY_INCREMENT = 0.01
    """
    Default increment we will use (up to max delay) after each attempt before
    next attempt to acquire the lock. For example if 3 attempts have been made
    the calling thread will sleep (0.01 * 3) before the next attempt to
    acquire the lock (and repeat).
    """

    def __init__(self, path, sleep_func=time.sleep, logger=None):
        self.lockfile = None
        self.path = path
        self.acquired = False
        self.sleep_func = sleep_func
        self.logger = _utils.pick_first_not_none(logger, LOG)

    def _try_acquire(self, blocking, watch):
        try:
            self.trylock()
        except IOError as e:
            if e.errno in (errno.EACCES, errno.EAGAIN):
                if not blocking or watch.expired():
                    return False
                else:
                    raise _utils.RetryAgain()
            else:
                raise threading.ThreadError("Unable to acquire lock on"
                                            " `%(path)s` due to"
                                            " %(exception)s" %
                                            {
                                                'path': self.path,
                                                'exception': e,
                                            })
        else:
            return True

    def _do_open(self):
        basedir = os.path.dirname(self.path)
        if basedir:
            made_basedir = _ensure_tree(basedir)
            if made_basedir:
                self.logger.log(_utils.BLATHER,
                                'Created lock base path `%s`', basedir)
        # Open in append mode so we don't overwrite any potential contents of
        # the target file. This eliminates the possibility of an attacker
        # creating a symlink to an important file in our lock path.
        if self.lockfile is None or self.lockfile.closed:
            self.lockfile = open(self.path, 'a')

    def acquire(self, blocking=True,
                delay=DELAY_INCREMENT, max_delay=MAX_DELAY,
                timeout=None):
        """Attempt to acquire the given lock.

        :param blocking: whether to wait forever to try to acquire the lock
        :type blocking: bool
        :param delay: when blocking this is the delay time in seconds that
                      will be added after each failed acquisition
        :type delay: int/float
        :param max_delay: the maximum delay to have (this limits the
                          accumulated delay(s) added after each failed
                          acquisition)
        :type max_delay: int/float
        :param timeout: an optional timeout (limits how long blocking
                        will occur for)
        :type timeout: int/float
        :returns: whether or not the acquisition succeeded
        :rtype: bool
        """
        if delay < 0:
            raise ValueError("Delay must be greater than or equal to zero")
        if timeout is not None and timeout < 0:
            raise ValueError("Timeout must be greater than or equal to zero")
        if delay >= max_delay:
            max_delay = delay
        self._do_open()
        watch = _utils.StopWatch(duration=timeout)
        r = _utils.Retry(delay, max_delay,
                         sleep_func=self.sleep_func, watch=watch)
        with watch:
            gotten = r(self._try_acquire, blocking, watch)
        if not gotten:
            self.acquired = False
            return False
        else:
            self.acquired = True
            self.logger.log(_utils.BLATHER,
                            "Acquired file lock `%s` after waiting %0.3fs [%s"
                            " attempts were required]", self.path,
                            watch.elapsed(), r.attempts)
            return True

    def _do_close(self):
        if self.lockfile is not None:
            self.lockfile.close()
            self.lockfile = None

    def __enter__(self):
        self.acquire()
        return self

    def release(self):
        """Release the previously acquired lock."""
        if not self.acquired:
            raise threading.ThreadError("Unable to release an unacquired"
                                        " lock")
        try:
            self.unlock()
        except IOError:
            self.logger.exception("Could not unlock the acquired lock opened"
                                  " on `%s`", self.path)
        else:
            self.acquired = False
            try:
                self._do_close()
            except IOError:
                self.logger.exception("Could not close the file handle"
                                      " opened on `%s`", self.path)
            else:
                self.logger.log(_utils.BLATHER,
                                "Unlocked and closed file lock open on"
                                " `%s`", self.path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def exists(self):
        """Checks if the path that this lock exists at actually exists."""
        return os.path.exists(self.path)

    def trylock(self):
        raise NotImplementedError()

    def unlock(self):
        raise NotImplementedError()


class _WindowsLock(_InterProcessLock):
    """Interprocess lock implementation that works on windows systems."""

    def trylock(self):
        msvcrt.locking(self.lockfile.fileno(), msvcrt.LK_NBLCK, 1)

    def unlock(self):
        msvcrt.locking(self.lockfile.fileno(), msvcrt.LK_UNLCK, 1)


class _FcntlLock(_InterProcessLock):
    """Interprocess lock implementation that works on posix systems."""

    def trylock(self):
        fcntl.lockf(self.lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def unlock(self):
        fcntl.lockf(self.lockfile, fcntl.LOCK_UN)


if os.name == 'nt':
    import msvcrt
    InterProcessLock = _WindowsLock
else:
    import fcntl
    InterProcessLock = _FcntlLock


def interprocess_locked(path):
    """Acquires & releases a interprocess lock around call into
       decorated function."""

    lock = InterProcessLock(path)

    def decorator(f):

        @six.wraps(f)
        def wrapper(*args, **kwargs):
            with lock:
                return f(*args, **kwargs)

        return wrapper

    return decorator
