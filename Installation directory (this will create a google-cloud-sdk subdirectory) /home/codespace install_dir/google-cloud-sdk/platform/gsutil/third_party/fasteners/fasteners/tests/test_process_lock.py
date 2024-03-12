# -*- coding: utf-8 -*-

# Copyright 2011 OpenStack Foundation.
# Copyright 2011 Justin Santa Barbara
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
import fcntl
import multiprocessing
import os
import shutil
import signal
import tempfile
import threading
import time

from fasteners import process_lock as pl
from fasteners import test


class BrokenLock(pl.InterProcessLock):
    def __init__(self, name, errno_code):
        super(BrokenLock, self).__init__(name)
        self.errno_code = errno_code

    def unlock(self):
        pass

    def trylock(self):
        err = IOError()
        err.errno = self.errno_code
        raise err


class ProcessLockTest(test.TestCase):
    def setUp(self):
        super(ProcessLockTest, self).setUp()
        self.lock_dir = tempfile.mkdtemp()
        self.tmp_dirs = [self.lock_dir]

    def tearDown(self):
        super(ProcessLockTest, self).tearDown()
        for a_dir in reversed(self.tmp_dirs):
            if os.path.exists(a_dir):
                shutil.rmtree(a_dir, ignore_errors=True)

    def test_lock_acquire_release_file_lock(self):
        lock_file = os.path.join(self.lock_dir, 'lock')
        lock = pl.InterProcessLock(lock_file)

        def try_lock():
            try:
                my_lock = pl.InterProcessLock(lock_file)
                my_lock.lockfile = open(lock_file, 'w')
                my_lock.trylock()
                my_lock.unlock()
                os._exit(1)
            except IOError:
                os._exit(0)

        def attempt_acquire(count):
            children = []
            for i in range(count):
                child = multiprocessing.Process(target=try_lock)
                child.start()
                children.append(child)
            exit_codes = []
            for child in children:
                child.join()
                exit_codes.append(child.exitcode)
            return sum(exit_codes)

        self.assertTrue(lock.acquire())
        try:
            acquired_children = attempt_acquire(10)
            self.assertEqual(0, acquired_children)
        finally:
            lock.release()

        acquired_children = attempt_acquire(5)
        self.assertNotEqual(0, acquired_children)

    def test_nested_synchronized_external_works(self):
        sentinel = object()

        @pl.interprocess_locked(os.path.join(self.lock_dir, 'test-lock-1'))
        def outer_lock():

            @pl.interprocess_locked(os.path.join(self.lock_dir, 'test-lock-2'))
            def inner_lock():
                return sentinel

            return inner_lock()

        self.assertEqual(sentinel, outer_lock())

    def _do_test_lock_externally(self, lock_dir):
        lock_path = os.path.join(lock_dir, "lock")

        def lock_files(handles_dir):
            with pl.InterProcessLock(lock_path):

                # Open some files we can use for locking
                handles = []
                for n in range(50):
                    path = os.path.join(handles_dir, ('file-%s' % n))
                    handles.append(open(path, 'w'))

                # Loop over all the handles and try locking the file
                # without blocking, keep a count of how many files we
                # were able to lock and then unlock. If the lock fails
                # we get an IOError and bail out with bad exit code
                count = 0
                for handle in handles:
                    try:
                        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        count += 1
                        fcntl.flock(handle, fcntl.LOCK_UN)
                    except IOError:
                        os._exit(2)
                    finally:
                        handle.close()

                # Check if we were able to open all files
                self.assertEqual(50, count)

        handles_dir = tempfile.mkdtemp()
        self.tmp_dirs.append(handles_dir)
        children = []
        for n in range(50):
            pid = os.fork()
            if pid:
                children.append(pid)
            else:
                try:
                    lock_files(handles_dir)
                finally:
                    os._exit(0)
        for child in children:
            (pid, status) = os.waitpid(child, 0)
            if pid:
                self.assertEqual(0, status)

    def test_lock_externally(self):
        self._do_test_lock_externally(self.lock_dir)

    def test_lock_externally_lock_dir_not_exist(self):
        os.rmdir(self.lock_dir)
        self._do_test_lock_externally(self.lock_dir)

    def test_lock_file_exists(self):
        lock_file = os.path.join(self.lock_dir, 'lock')

        @pl.interprocess_locked(lock_file)
        def foo():
            self.assertTrue(os.path.exists(lock_file))

        foo()

    def test_bad_acquire(self):
        lock_file = os.path.join(self.lock_dir, 'lock')
        lock = BrokenLock(lock_file, errno.EBUSY)
        self.assertRaises(threading.ThreadError, lock.acquire)

    def test_bad_release(self):
        lock_file = os.path.join(self.lock_dir, 'lock')
        lock = pl.InterProcessLock(lock_file)
        self.assertRaises(threading.ThreadError, lock.release)

    def test_interprocess_lock(self):
        lock_file = os.path.join(self.lock_dir, 'lock')

        pid = os.fork()
        if pid:
            # Make sure the child grabs the lock first
            start = time.time()
            while not os.path.exists(lock_file):
                if time.time() - start > 5:
                    self.fail('Timed out waiting for child to grab lock')
                time.sleep(0)
            lock1 = pl.InterProcessLock('foo')
            lock1.lockfile = open(lock_file, 'w')
            # NOTE(bnemec): There is a brief window between when the lock file
            # is created and when it actually becomes locked.  If we happen to
            # context switch in that window we may succeed in locking the
            # file. Keep retrying until we either get the expected exception
            # or timeout waiting.
            while time.time() - start < 5:
                try:
                    lock1.trylock()
                    lock1.unlock()
                    time.sleep(0)
                except IOError:
                    # This is what we expect to happen
                    break
            else:
                self.fail('Never caught expected lock exception')
            # We don't need to wait for the full sleep in the child here
            os.kill(pid, signal.SIGKILL)
        else:
            try:
                lock2 = pl.InterProcessLock('foo')
                lock2.lockfile = open(lock_file, 'w')
                have_lock = False
                while not have_lock:
                    try:
                        lock2.trylock()
                        have_lock = True
                    except IOError:
                        pass
            finally:
                # NOTE(bnemec): This is racy, but I don't want to add any
                # synchronization primitives that might mask a problem
                # with the one we're trying to test here.
                time.sleep(.5)
                os._exit(0)

    def test_non_destructive(self):
        lock_file = os.path.join(self.lock_dir, 'not-destroyed')
        with open(lock_file, 'w') as f:
            f.write('test')
        with pl.InterProcessLock(lock_file):
            with open(lock_file) as f:
                self.assertEqual(f.read(), 'test')
