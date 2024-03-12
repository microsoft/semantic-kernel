#
# Copyright 2015 Google Inc.
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

"""Tests for stream_slice."""

import string
import unittest

import six

from apitools.base.py import exceptions
from apitools.base.py import stream_slice


class StreamSliceTest(unittest.TestCase):

    def setUp(self):
        self.stream = six.StringIO(string.ascii_letters)
        self.value = self.stream.getvalue()
        self.stream.seek(0)

    def testSimpleSlice(self):
        ss = stream_slice.StreamSlice(self.stream, 10)
        self.assertEqual('', ss.read(0))
        self.assertEqual(self.value[0:3], ss.read(3))
        self.assertIn('7/10', str(ss))
        self.assertEqual(self.value[3:10], ss.read())
        self.assertEqual('', ss.read())
        self.assertEqual('', ss.read(10))
        self.assertEqual(10, self.stream.tell())

    def testEmptySlice(self):
        ss = stream_slice.StreamSlice(self.stream, 0)
        self.assertEqual('', ss.read(5))
        self.assertEqual('', ss.read())
        self.assertEqual(0, self.stream.tell())

    def testOffsetStream(self):
        self.stream.seek(26)
        ss = stream_slice.StreamSlice(self.stream, 26)
        self.assertEqual(self.value[26:36], ss.read(10))
        self.assertEqual(self.value[36:], ss.read())
        self.assertEqual('', ss.read())

    def testTooShortStream(self):
        ss = stream_slice.StreamSlice(self.stream, 1000)
        self.assertEqual(self.value, ss.read())
        self.assertEqual('', ss.read(0))
        with self.assertRaises(exceptions.StreamExhausted) as e:
            ss.read()
        with self.assertRaises(exceptions.StreamExhausted) as e:
            ss.read(10)
        self.assertIn('exhausted after %d' % len(self.value), str(e.exception))
