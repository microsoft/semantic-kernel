#!/usr/bin/env python
#
# Copyright 2017 Google Inc.
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

"""Tests for compression."""

import unittest

from apitools.base.py import compression
from apitools.base.py import gzip

import six


class CompressionTest(unittest.TestCase):

    def setUp(self):
        # Sample highly compressible data (~50MB).
        self.sample_data = b'abc' * 16777216
        # Stream of the sample data.
        self.stream = six.BytesIO()
        self.stream.write(self.sample_data)
        self.length = self.stream.tell()
        self.stream.seek(0)

    def testCompressionExhausted(self):
        """Test full compression.

        Test that highly compressible data is actually compressed in entirety.
        """
        output, read, exhausted = compression.CompressStream(
            self.stream,
            self.length,
            9)
        # Ensure the compressed buffer is smaller than the input buffer.
        self.assertLess(output.length, self.length)
        # Ensure we read the entire input stream.
        self.assertEqual(read, self.length)
        # Ensure the input stream was exhausted.
        self.assertTrue(exhausted)

    def testCompressionUnbounded(self):
        """Test unbounded compression.

        Test that the input stream is exhausted when length is none.
        """
        output, read, exhausted = compression.CompressStream(
            self.stream,
            None,
            9)
        # Ensure the compressed buffer is smaller than the input buffer.
        self.assertLess(output.length, self.length)
        # Ensure we read the entire input stream.
        self.assertEqual(read, self.length)
        # Ensure the input stream was exhausted.
        self.assertTrue(exhausted)

    def testCompressionPartial(self):
        """Test partial compression.

        Test that the length parameter works correctly. The amount of data
        that's compressed can be greater than or equal to the requested length.
        """
        output_length = 40
        output, _, exhausted = compression.CompressStream(
            self.stream,
            output_length,
            9)
        # Ensure the requested read size is <= the compressed buffer size.
        self.assertLessEqual(output_length, output.length)
        # Ensure the input stream was not exhausted.
        self.assertFalse(exhausted)

    def testCompressionIntegrity(self):
        """Test that compressed data can be decompressed."""
        output, read, exhausted = compression.CompressStream(
            self.stream,
            self.length,
            9)
        # Ensure uncompressed data matches the sample data.
        with gzip.GzipFile(fileobj=output) as f:
            original = f.read()
            self.assertEqual(original, self.sample_data)
        # Ensure we read the entire input stream.
        self.assertEqual(read, self.length)
        # Ensure the input stream was exhausted.
        self.assertTrue(exhausted)


class StreamingBufferTest(unittest.TestCase):

    def setUp(self):
        self.stream = compression.StreamingBuffer()

    def testSimpleStream(self):
        """Test simple stream operations.

        Test that the stream can be written to and read from. Also test that
        reading from the stream consumes the bytes.
        """
        # Ensure the stream is empty.
        self.assertEqual(self.stream.length, 0)
        # Ensure data is correctly written.
        self.stream.write(b'Sample data')
        self.assertEqual(self.stream.length, 11)
        # Ensure data can be read and the read data is purged from the stream.
        data = self.stream.read(11)
        self.assertEqual(data, b'Sample data')
        self.assertEqual(self.stream.length, 0)

    def testPartialReads(self):
        """Test partial stream reads.

        Test that the stream can be read in chunks while perserving the
        consumption mechanics.
        """
        self.stream.write(b'Sample data')
        # Ensure data can be read and the read data is purged from the stream.
        data = self.stream.read(6)
        self.assertEqual(data, b'Sample')
        self.assertEqual(self.stream.length, 5)
        # Ensure the remaining data can be read.
        data = self.stream.read(5)
        self.assertEqual(data, b' data')
        self.assertEqual(self.stream.length, 0)

    def testTooShort(self):
        """Test excessive stream reads.

        Test that more data can be requested from the stream than available
        without raising an exception.
        """
        self.stream.write(b'Sample')
        # Ensure requesting more data than available does not raise an
        # exception.
        data = self.stream.read(100)
        self.assertEqual(data, b'Sample')
        self.assertEqual(self.stream.length, 0)
