# -*- coding: utf-8 -*-
# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Unit tests for resumable streaming upload functions and classes."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import pkgutil

from six.moves import range

from gslib.exception import CommandException
from gslib.resumable_streaming_upload import ResumableStreamingJsonUploadWrapper
import gslib.tests.testcase as testcase
from gslib.utils.boto_util import GetJsonResumableChunkSize
from gslib.utils.constants import TRANSFER_BUFFER_SIZE
from gslib.utils.hashing_helper import CalculateHashesFromContents
from gslib.utils.hashing_helper import CalculateMd5FromContents
from gslib.utils.hashing_helper import GetMd5

_TEST_FILE = 'test.txt'


class TestResumableStreamingJsonUploadWrapper(testcase.GsUtilUnitTestCase):
  """Unit tests for the TestResumableStreamingJsonUploadWrapper class."""

  _temp_test_file = None
  _temp_test_file_contents = None
  _temp_test_file_len = None

  def _GetTestFile(self):
    if not self._temp_test_file:
      self._temp_test_file_contents = pkgutil.get_data(
          'gslib', 'tests/test_data/%s' % _TEST_FILE)
      self._temp_test_file = self.CreateTempFile(
          file_name=_TEST_FILE, contents=self._temp_test_file_contents)
      self._temp_test_file_len = len(self._temp_test_file_contents)
    return self._temp_test_file

  def testReadInChunks(self):
    tmp_file = self._GetTestFile()
    with open(tmp_file, 'rb') as stream:
      wrapper = ResumableStreamingJsonUploadWrapper(stream,
                                                    TRANSFER_BUFFER_SIZE,
                                                    test_small_buffer=True)
      hash_dict = {'md5': GetMd5()}
      # CalculateHashesFromContents reads in chunks, but does not seek.
      CalculateHashesFromContents(wrapper, hash_dict)
    with open(tmp_file, 'rb') as stream:
      actual = CalculateMd5FromContents(stream)
    self.assertEqual(actual, hash_dict['md5'].hexdigest())

  def testReadInChunksWithSeekToBeginning(self):
    """Reads one buffer, then seeks to 0 and reads chunks until the end."""
    tmp_file = self._GetTestFile()
    for initial_read in (TRANSFER_BUFFER_SIZE - 1, TRANSFER_BUFFER_SIZE,
                         TRANSFER_BUFFER_SIZE + 1, TRANSFER_BUFFER_SIZE * 2 - 1,
                         TRANSFER_BUFFER_SIZE * 2, TRANSFER_BUFFER_SIZE * 2 + 1,
                         TRANSFER_BUFFER_SIZE * 3 - 1, TRANSFER_BUFFER_SIZE * 3,
                         TRANSFER_BUFFER_SIZE * 3 + 1):
      for buffer_size in (TRANSFER_BUFFER_SIZE - 1, TRANSFER_BUFFER_SIZE,
                          TRANSFER_BUFFER_SIZE + 1, self._temp_test_file_len -
                          1, self._temp_test_file_len,
                          self._temp_test_file_len + 1):
        # Can't seek to 0 if the buffer is too small, so we expect an
        # exception.
        expect_exception = buffer_size < self._temp_test_file_len
        with open(tmp_file, 'rb') as stream:
          wrapper = ResumableStreamingJsonUploadWrapper(stream,
                                                        buffer_size,
                                                        test_small_buffer=True)
          wrapper.read(initial_read)
          # CalculateMd5FromContents seeks to 0, reads in chunks, then seeks
          # to 0 again.
          try:
            hex_digest = CalculateMd5FromContents(wrapper)
            if expect_exception:
              self.fail('Did not get expected CommandException for '
                        'initial read size %s, buffer size %s' %
                        (initial_read, buffer_size))
          except CommandException as e:
            if not expect_exception:
              self.fail('Got unexpected CommandException "%s" for '
                        'initial read size %s, buffer size %s' %
                        (str(e), initial_read, buffer_size))
        if not expect_exception:
          with open(tmp_file, 'rb') as stream:
            actual = CalculateMd5FromContents(stream)
          self.assertEqual(
              actual, hex_digest,
              'Digests not equal for initial read size %s, buffer size %s' %
              (initial_read, buffer_size))

  def _testSeekBack(self, initial_reads, buffer_size, seek_back_amount):
    """Tests reading then seeking backwards.

    This function simulates an upload that is resumed after a connection break.
    It reads one transfer buffer at a time until it reaches initial_position,
    then seeks backwards (as if the server did not receive some of the bytes)
    and reads to the end of the file, ensuring the data read after the seek
    matches the original file.

    Args:
      initial_reads: List of integers containing read sizes to perform
          before seek.
      buffer_size: Maximum buffer size for the wrapper.
      seek_back_amount: Number of bytes to seek backward.

    Raises:
      AssertionError on wrong data returned by the wrapper.
    """
    tmp_file = self._GetTestFile()
    initial_position = 0
    for read_size in initial_reads:
      initial_position += read_size
    self.assertGreaterEqual(
        buffer_size, seek_back_amount,
        'seek_back_amount must be less than initial position %s '
        '(but was actually: %s)' % (buffer_size, seek_back_amount))
    self.assertLess(
        initial_position, self._temp_test_file_len,
        'initial_position must be less than test file size %s '
        '(but was actually: %s)' % (self._temp_test_file_len, initial_position))

    with open(tmp_file, 'rb') as stream:
      wrapper = ResumableStreamingJsonUploadWrapper(stream,
                                                    buffer_size,
                                                    test_small_buffer=True)
      position = 0
      for read_size in initial_reads:
        data = wrapper.read(read_size)
        self.assertEqual(
            self._temp_test_file_contents[position:position + read_size], data,
            'Data from position %s to %s did not match file contents.' %
            (position, position + read_size))
        position += len(data)
      wrapper.seek(initial_position - seek_back_amount)
      self.assertEqual(wrapper.tell(), initial_position - seek_back_amount)
      data = wrapper.read()
      self.assertEqual(
          self._temp_test_file_len - (initial_position - seek_back_amount),
          len(data),
          'Unexpected data length with initial pos %s seek_back_amount %s. '
          'Expected: %s, actual: %s.' %
          (initial_position, seek_back_amount, self._temp_test_file_len -
           (initial_position - seek_back_amount), len(data)))
      self.assertEqual(
          self._temp_test_file_contents[-len(data):], data,
          'Data from position %s to EOF did not match file contents.' %
          position)

  def testReadSeekAndReadToEOF(self):
    """Tests performing reads on the wrapper, seeking, then reading to EOF."""
    for initial_reads in ([1], [TRANSFER_BUFFER_SIZE - 1], [
        TRANSFER_BUFFER_SIZE
    ], [TRANSFER_BUFFER_SIZE + 1], [1, TRANSFER_BUFFER_SIZE - 1], [
        1, TRANSFER_BUFFER_SIZE
    ], [1, TRANSFER_BUFFER_SIZE + 1
       ], [TRANSFER_BUFFER_SIZE - 1,
           1], [TRANSFER_BUFFER_SIZE,
                1], [TRANSFER_BUFFER_SIZE + 1,
                     1], [TRANSFER_BUFFER_SIZE - 1, TRANSFER_BUFFER_SIZE - 1
                         ], [TRANSFER_BUFFER_SIZE - 1, TRANSFER_BUFFER_SIZE],
                          [TRANSFER_BUFFER_SIZE - 1, TRANSFER_BUFFER_SIZE + 1
                          ], [TRANSFER_BUFFER_SIZE, TRANSFER_BUFFER_SIZE - 1
                             ], [TRANSFER_BUFFER_SIZE, TRANSFER_BUFFER_SIZE],
                          [TRANSFER_BUFFER_SIZE, TRANSFER_BUFFER_SIZE + 1],
                          [TRANSFER_BUFFER_SIZE + 1, TRANSFER_BUFFER_SIZE - 1
                          ], [TRANSFER_BUFFER_SIZE + 1, TRANSFER_BUFFER_SIZE],
                          [TRANSFER_BUFFER_SIZE + 1,
                           TRANSFER_BUFFER_SIZE + 1], [
                               TRANSFER_BUFFER_SIZE, TRANSFER_BUFFER_SIZE,
                               TRANSFER_BUFFER_SIZE
                           ]):
      initial_position = 0
      for read_size in initial_reads:
        initial_position += read_size
      for buffer_size in (initial_position, initial_position + 1,
                          initial_position * 2 - 1, initial_position * 2):
        for seek_back_amount in (min(TRANSFER_BUFFER_SIZE - 1,
                                     initial_position),
                                 min(TRANSFER_BUFFER_SIZE, initial_position),
                                 min(TRANSFER_BUFFER_SIZE + 1,
                                     initial_position),
                                 min(TRANSFER_BUFFER_SIZE * 2 - 1,
                                     initial_position),
                                 min(TRANSFER_BUFFER_SIZE * 2,
                                     initial_position),
                                 min(TRANSFER_BUFFER_SIZE * 2 + 1,
                                     initial_position)):
          self._testSeekBack(initial_reads, buffer_size, seek_back_amount)

  def testBufferSizeLessThanChunkSize(self):
    ResumableStreamingJsonUploadWrapper(None, GetJsonResumableChunkSize())
    try:
      ResumableStreamingJsonUploadWrapper(None, GetJsonResumableChunkSize() - 1)
      self.fail('Did not get expected CommandException')
    except CommandException as e:
      self.assertIn('Buffer size must be >= JSON resumable upload', str(e))

  def testSeekPartialBuffer(self):
    """Tests seeking back partially within the buffer."""
    tmp_file = self._GetTestFile()
    read_size = TRANSFER_BUFFER_SIZE
    with open(tmp_file, 'rb') as stream:
      wrapper = ResumableStreamingJsonUploadWrapper(stream,
                                                    TRANSFER_BUFFER_SIZE * 3,
                                                    test_small_buffer=True)
      position = 0
      for _ in range(3):
        data = wrapper.read(read_size)
        self.assertEqual(
            self._temp_test_file_contents[position:position + read_size], data,
            'Data from position %s to %s did not match file contents.' %
            (position, position + read_size))
        position += len(data)

      data = wrapper.read(read_size // 2)
      # Buffer contents should now be have contents from:
      # read_size/2 through 7*read_size/2.
      position = read_size // 2
      wrapper.seek(position)
      data = wrapper.read()
      self.assertEqual(
          self._temp_test_file_contents[-len(data):], data,
          'Data from position %s to EOF did not match file contents.' %
          position)

  def testSeekEnd(self):
    tmp_file = self._GetTestFile()
    for buffer_size in (TRANSFER_BUFFER_SIZE - 1, TRANSFER_BUFFER_SIZE,
                        TRANSFER_BUFFER_SIZE + 1):
      for seek_back in (TRANSFER_BUFFER_SIZE - 1, TRANSFER_BUFFER_SIZE,
                        TRANSFER_BUFFER_SIZE + 1):
        expect_exception = seek_back > buffer_size
        with open(tmp_file, 'rb') as stream:
          wrapper = ResumableStreamingJsonUploadWrapper(stream,
                                                        buffer_size,
                                                        test_small_buffer=True)
          # Read to the end.
          while wrapper.read(TRANSFER_BUFFER_SIZE):
            pass
          try:
            wrapper.seek(seek_back, whence=os.SEEK_END)
            if expect_exception:
              self.fail('Did not get expected CommandException for '
                        'seek_back size %s, buffer size %s' %
                        (seek_back, buffer_size))
          except CommandException as e:
            if not expect_exception:
              self.fail('Got unexpected CommandException "%s" for '
                        'seek_back size %s, buffer size %s' %
                        (str(e), seek_back, buffer_size))
