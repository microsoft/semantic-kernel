# -*- coding: utf-8 -*-

#    Copyright (C) 2014 Yahoo! Inc. All Rights Reserved.
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

import collections
import random
import threading
import time

from concurrent import futures

import fasteners
from fasteners import test

from fasteners import _utils


# NOTE(harlowja): Sleep a little so now() can not be the same (which will
# cause false positives when our overlap detection code runs). If there are
# real overlaps then they will still exist.
NAPPY_TIME = 0.05

# We will spend this amount of time doing some "fake" work.
WORK_TIMES = [(0.01 + x / 100.0) for x in range(0, 5)]

# If latches/events take longer than this to become empty/set, something is
# usually wrong and should be debugged instead of deadlocking...
WAIT_TIMEOUT = 300


def _find_overlaps(times, start, end):
    overlaps = 0
    for (s, e) in times:
        if s >= start and e <= end:
            overlaps += 1
    return overlaps


def _spawn_variation(readers, writers, max_workers=None):
    start_stops = collections.deque()
    lock = fasteners.ReaderWriterLock()

    def read_func(ident):
        with lock.read_lock():
            # TODO(harlowja): sometime in the future use a monotonic clock here
            # to avoid problems that can be caused by ntpd resyncing the clock
            # while we are actively running.
            enter_time = _utils.now()
            time.sleep(WORK_TIMES[ident % len(WORK_TIMES)])
            exit_time = _utils.now()
            start_stops.append((lock.READER, enter_time, exit_time))
            time.sleep(NAPPY_TIME)

    def write_func(ident):
        with lock.write_lock():
            enter_time = _utils.now()
            time.sleep(WORK_TIMES[ident % len(WORK_TIMES)])
            exit_time = _utils.now()
            start_stops.append((lock.WRITER, enter_time, exit_time))
            time.sleep(NAPPY_TIME)

    if max_workers is None:
        max_workers = max(0, readers) + max(0, writers)
    if max_workers > 0:
        with futures.ThreadPoolExecutor(max_workers=max_workers) as e:
            count = 0
            for _i in range(0, readers):
                e.submit(read_func, count)
                count += 1
            for _i in range(0, writers):
                e.submit(write_func, count)
                count += 1

    writer_times = []
    reader_times = []
    for (lock_type, start, stop) in list(start_stops):
        if lock_type == lock.WRITER:
            writer_times.append((start, stop))
        else:
            reader_times.append((start, stop))
    return (writer_times, reader_times)


def _daemon_thread(target):
    t = threading.Thread(target=target)
    t.daemon = True
    return t


class ReadWriteLockTest(test.TestCase):
    THREAD_COUNT = 20

    def test_no_double_writers(self):
        lock = fasteners.ReaderWriterLock()
        watch = _utils.StopWatch(duration=5)
        watch.start()
        dups = collections.deque()
        active = collections.deque()

        def acquire_check(me):
            with lock.write_lock():
                if len(active) >= 1:
                    dups.append(me)
                    dups.extend(active)
                active.append(me)
                try:
                    time.sleep(random.random() / 100)
                finally:
                    active.remove(me)

        def run():
            me = threading.current_thread()
            while not watch.expired():
                acquire_check(me)

        threads = []
        for i in range(0, self.THREAD_COUNT):
            t = _daemon_thread(run)
            threads.append(t)
            t.start()
        while threads:
            t = threads.pop()
            t.join()

        self.assertEqual([], list(dups))
        self.assertEqual([], list(active))

    def test_no_concurrent_readers_writers(self):
        lock = fasteners.ReaderWriterLock()
        watch = _utils.StopWatch(duration=5)
        watch.start()
        dups = collections.deque()
        active = collections.deque()

        def acquire_check(me, reader):
            if reader:
                lock_func = lock.read_lock
            else:
                lock_func = lock.write_lock
            with lock_func():
                if not reader:
                    # There should be no-one else currently active, if there
                    # is ensure we capture them so that we can later blow-up
                    # the test.
                    if len(active) >= 1:
                        dups.append(me)
                        dups.extend(active)
                active.append(me)
                try:
                    time.sleep(random.random() / 100)
                finally:
                    active.remove(me)

        def run():
            me = threading.current_thread()
            while not watch.expired():
                acquire_check(me, random.choice([True, False]))

        threads = []
        for i in range(0, self.THREAD_COUNT):
            t = _daemon_thread(run)
            threads.append(t)
            t.start()
        while threads:
            t = threads.pop()
            t.join()

        self.assertEqual([], list(dups))
        self.assertEqual([], list(active))

    def test_writer_abort(self):
        lock = fasteners.ReaderWriterLock()
        self.assertFalse(lock.owner)

        def blow_up():
            with lock.write_lock():
                self.assertEqual(lock.WRITER, lock.owner)
                raise RuntimeError("Broken")

        self.assertRaises(RuntimeError, blow_up)
        self.assertFalse(lock.owner)

    def test_reader_abort(self):
        lock = fasteners.ReaderWriterLock()
        self.assertFalse(lock.owner)

        def blow_up():
            with lock.read_lock():
                self.assertEqual(lock.READER, lock.owner)
                raise RuntimeError("Broken")

        self.assertRaises(RuntimeError, blow_up)
        self.assertFalse(lock.owner)

    def test_double_reader_abort(self):
        lock = fasteners.ReaderWriterLock()
        activated = collections.deque()

        def double_bad_reader():
            with lock.read_lock():
                with lock.read_lock():
                    raise RuntimeError("Broken")

        def happy_writer():
            with lock.write_lock():
                activated.append(lock.owner)

        with futures.ThreadPoolExecutor(max_workers=20) as e:
            for i in range(0, 20):
                if i % 2 == 0:
                    e.submit(double_bad_reader)
                else:
                    e.submit(happy_writer)

        self.assertEqual(10, len([a for a in activated if a == 'w']))

    def test_double_reader_writer(self):
        lock = fasteners.ReaderWriterLock()
        activated = collections.deque()
        active = threading.Event()

        def double_reader():
            with lock.read_lock():
                active.set()
                while not lock.has_pending_writers:
                    time.sleep(0.001)
                with lock.read_lock():
                    activated.append(lock.owner)

        def happy_writer():
            with lock.write_lock():
                activated.append(lock.owner)

        reader = _daemon_thread(double_reader)
        reader.start()
        active.wait(WAIT_TIMEOUT)
        self.assertTrue(active.is_set())

        writer = _daemon_thread(happy_writer)
        writer.start()

        reader.join()
        writer.join()
        self.assertEqual(2, len(activated))
        self.assertEqual(['r', 'w'], list(activated))

    def test_reader_chaotic(self):
        lock = fasteners.ReaderWriterLock()
        activated = collections.deque()

        def chaotic_reader(blow_up):
            with lock.read_lock():
                if blow_up:
                    raise RuntimeError("Broken")
                else:
                    activated.append(lock.owner)

        def happy_writer():
            with lock.write_lock():
                activated.append(lock.owner)

        with futures.ThreadPoolExecutor(max_workers=20) as e:
            for i in range(0, 20):
                if i % 2 == 0:
                    e.submit(chaotic_reader, blow_up=bool(i % 4 == 0))
                else:
                    e.submit(happy_writer)

        writers = [a for a in activated if a == 'w']
        readers = [a for a in activated if a == 'r']
        self.assertEqual(10, len(writers))
        self.assertEqual(5, len(readers))

    def test_writer_chaotic(self):
        lock = fasteners.ReaderWriterLock()
        activated = collections.deque()

        def chaotic_writer(blow_up):
            with lock.write_lock():
                if blow_up:
                    raise RuntimeError("Broken")
                else:
                    activated.append(lock.owner)

        def happy_reader():
            with lock.read_lock():
                activated.append(lock.owner)

        with futures.ThreadPoolExecutor(max_workers=20) as e:
            for i in range(0, 20):
                if i % 2 == 0:
                    e.submit(chaotic_writer, blow_up=bool(i % 4 == 0))
                else:
                    e.submit(happy_reader)

        writers = [a for a in activated if a == 'w']
        readers = [a for a in activated if a == 'r']
        self.assertEqual(5, len(writers))
        self.assertEqual(10, len(readers))

    def test_writer_reader_writer(self):
        lock = fasteners.ReaderWriterLock()
        with lock.write_lock():
            self.assertTrue(lock.is_writer())
            with lock.read_lock():
                self.assertTrue(lock.is_reader())
                with lock.write_lock():
                    self.assertTrue(lock.is_writer())

    def test_single_reader_writer(self):
        results = []
        lock = fasteners.ReaderWriterLock()
        with lock.read_lock():
            self.assertTrue(lock.is_reader())
            self.assertEqual(0, len(results))
        with lock.write_lock():
            results.append(1)
            self.assertTrue(lock.is_writer())
        with lock.read_lock():
            self.assertTrue(lock.is_reader())
            self.assertEqual(1, len(results))
        self.assertFalse(lock.is_reader())
        self.assertFalse(lock.is_writer())

    def test_reader_to_writer(self):
        lock = fasteners.ReaderWriterLock()

        def writer_func():
            with lock.write_lock():
                pass

        with lock.read_lock():
            self.assertRaises(RuntimeError, writer_func)
            self.assertFalse(lock.is_writer())

        self.assertFalse(lock.is_reader())
        self.assertFalse(lock.is_writer())

    def test_writer_to_reader(self):
        lock = fasteners.ReaderWriterLock()

        def reader_func():
            with lock.read_lock():
                self.assertTrue(lock.is_writer())
                self.assertTrue(lock.is_reader())

        with lock.write_lock():
            self.assertIsNone(reader_func())
            self.assertFalse(lock.is_reader())

        self.assertFalse(lock.is_reader())
        self.assertFalse(lock.is_writer())

    def test_double_writer(self):
        lock = fasteners.ReaderWriterLock()
        with lock.write_lock():
            self.assertFalse(lock.is_reader())
            self.assertTrue(lock.is_writer())
            with lock.write_lock():
                self.assertTrue(lock.is_writer())
            self.assertTrue(lock.is_writer())

        self.assertFalse(lock.is_reader())
        self.assertFalse(lock.is_writer())

    def test_double_reader(self):
        lock = fasteners.ReaderWriterLock()
        with lock.read_lock():
            self.assertTrue(lock.is_reader())
            self.assertFalse(lock.is_writer())
            with lock.read_lock():
                self.assertTrue(lock.is_reader())
            self.assertTrue(lock.is_reader())

        self.assertFalse(lock.is_reader())
        self.assertFalse(lock.is_writer())

    def test_multi_reader_multi_writer(self):
        writer_times, reader_times = _spawn_variation(10, 10)
        self.assertEqual(10, len(writer_times))
        self.assertEqual(10, len(reader_times))
        for (start, stop) in writer_times:
            self.assertEqual(0, _find_overlaps(reader_times, start, stop))
            self.assertEqual(1, _find_overlaps(writer_times, start, stop))
        for (start, stop) in reader_times:
            self.assertEqual(0, _find_overlaps(writer_times, start, stop))

    def test_multi_reader_single_writer(self):
        writer_times, reader_times = _spawn_variation(9, 1)
        self.assertEqual(1, len(writer_times))
        self.assertEqual(9, len(reader_times))
        start, stop = writer_times[0]
        self.assertEqual(0, _find_overlaps(reader_times, start, stop))

    def test_multi_writer(self):
        writer_times, reader_times = _spawn_variation(0, 10)
        self.assertEqual(10, len(writer_times))
        self.assertEqual(0, len(reader_times))
        for (start, stop) in writer_times:
            self.assertEqual(1, _find_overlaps(writer_times, start, stop))
