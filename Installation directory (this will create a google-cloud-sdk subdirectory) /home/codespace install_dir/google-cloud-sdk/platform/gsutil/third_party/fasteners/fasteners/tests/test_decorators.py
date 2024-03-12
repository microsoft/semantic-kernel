# -*- coding: utf-8 -*-

#    Copyright (C) 2015 Yahoo! Inc. All Rights Reserved.
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

import threading

import fasteners
from fasteners import test


class Locked(object):
    def __init__(self):
        self._lock = threading.Lock()

    @fasteners.locked
    def i_am_locked(self, cb):
        cb(self._lock.locked())

    def i_am_not_locked(self, cb):
        cb(self._lock.locked())


class ManyLocks(object):
    def __init__(self, amount):
        self._lock = []
        for _i in range(0, amount):
            self._lock.append(threading.Lock())

    @fasteners.locked
    def i_am_locked(self, cb):
        gotten = [lock.locked() for lock in self._lock]
        cb(gotten)

    def i_am_not_locked(self, cb):
        gotten = [lock.locked() for lock in self._lock]
        cb(gotten)


class RWLocked(object):
    def __init__(self):
        self._lock = fasteners.ReaderWriterLock()

    @fasteners.read_locked
    def i_am_read_locked(self, cb):
        cb(self._lock.owner)

    @fasteners.write_locked
    def i_am_write_locked(self, cb):
        cb(self._lock.owner)

    def i_am_not_locked(self, cb):
        cb(self._lock.owner)


class DecoratorsTest(test.TestCase):
    def test_locked(self):
        obj = Locked()
        obj.i_am_locked(lambda is_locked: self.assertTrue(is_locked))
        obj.i_am_not_locked(lambda is_locked: self.assertFalse(is_locked))

    def test_many_locked(self):
        obj = ManyLocks(10)
        obj.i_am_locked(lambda gotten: self.assertTrue(all(gotten)))
        obj.i_am_not_locked(lambda gotten: self.assertEqual(0, sum(gotten)))

    def test_read_write_locked(self):
        reader = fasteners.ReaderWriterLock.READER
        writer = fasteners.ReaderWriterLock.WRITER
        obj = RWLocked()
        obj.i_am_write_locked(lambda owner: self.assertEqual(owner, writer))
        obj.i_am_read_locked(lambda owner: self.assertEqual(owner, reader))
        obj.i_am_not_locked(lambda owner: self.assertIsNone(owner))
