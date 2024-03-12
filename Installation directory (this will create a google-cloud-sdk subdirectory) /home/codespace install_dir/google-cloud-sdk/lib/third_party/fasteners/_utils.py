# -*- coding: utf-8 -*-

# Copyright (C) 2015 Yahoo! Inc. All Rights Reserved.
#
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

import logging
import time

from monotonic import monotonic as now  # noqa

# log level for low-level debugging
BLATHER = 5

LOG = logging.getLogger(__name__)


def pick_first_not_none(*values):
    """Returns first of values that is *not* None (or None if all are/were)."""
    for val in values:
        if val is not None:
            return val
    return None


class LockStack(object):
    """Simple lock stack to get and release many locks.

    An instance of this should **not** be used by many threads at the
    same time, as the stack that is maintained will be corrupted and
    invalid if that is attempted.
    """

    def __init__(self, logger=None):
        self._stack = []
        self._logger = pick_first_not_none(logger, LOG)

    def acquire_lock(self, lock):
        gotten = lock.acquire()
        if gotten:
            self._stack.append(lock)
        return gotten

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        am_left = len(self._stack)
        tot_am = am_left
        while self._stack:
            lock = self._stack.pop()
            try:
                lock.release()
            except Exception:
                self._logger.exception("Failed releasing lock %s from lock"
                                       " stack with %s locks", am_left, tot_am)
            am_left -= 1


class RetryAgain(Exception):
    """Exception to signal to retry helper to try again."""


class Retry(object):
    """A little retry helper object."""

    def __init__(self, delay, max_delay,
                 sleep_func=time.sleep, watch=None):
        self.delay = delay
        self.attempts = 0
        self.max_delay = max_delay
        self.sleep_func = sleep_func
        self.watch = watch

    def __call__(self, fn, *args, **kwargs):
        while True:
            self.attempts += 1
            try:
                return fn(*args, **kwargs)
            except RetryAgain:
                maybe_delay = self.attempts * self.delay
                if maybe_delay < self.max_delay:
                    actual_delay = maybe_delay
                else:
                    actual_delay = self.max_delay
                actual_delay = max(0.0, actual_delay)
                if self.watch is not None:
                    leftover = self.watch.leftover()
                    if leftover is not None and leftover < actual_delay:
                        actual_delay = leftover
                self.sleep_func(actual_delay)


class StopWatch(object):
    """A really basic stop watch."""

    def __init__(self, duration=None):
        self.duration = duration
        self.started_at = None
        self.stopped_at = None

    def leftover(self):
        if self.duration is None:
            return None
        return max(0.0, self.duration - self.elapsed())

    def elapsed(self):
        if self.stopped_at is not None:
            end_time = self.stopped_at
        else:
            end_time = now()
        return max(0.0, end_time - self.started_at)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.stopped_at = now()

    def start(self):
        self.started_at = now()
        self.stopped_at = None

    def expired(self):
        if self.duration is None:
            return False
        else:
            return self.elapsed() > self.duration
