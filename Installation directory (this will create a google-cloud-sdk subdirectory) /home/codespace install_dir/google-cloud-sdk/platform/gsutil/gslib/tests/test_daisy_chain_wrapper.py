# -*- coding: utf-8 -*-
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Unit tests for daisy chain wrapper class."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import math
import os
import pkgutil

import six
import gslib.cloud_api
from gslib.daisy_chain_wrapper import DaisyChainWrapper
from gslib.storage_url import StorageUrlFromString
import gslib.tests.testcase as testcase
from gslib.utils.constants import TRANSFER_BUFFER_SIZE

_TEST_FILE = 'test.txt'


class TestDaisyChainWrapper(testcase.GsUtilUnitTestCase):
  """Unit tests for the DaisyChainWrapper class."""

  _temp_test_file = None
  _dummy_url = StorageUrlFromString('gs://bucket/object')

  def setUp(self):
    super(TestDaisyChainWrapper, self).setUp()
    self.test_data_file = self._GetTestFile()
    self.test_data_file_len = os.path.getsize(self.test_data_file)

  def _GetTestFile(self):
    contents = pkgutil.get_data('gslib', 'tests/test_data/%s' % _TEST_FILE)
    if not self._temp_test_file:
      # Write to a temp file because pkgutil doesn't expose a stream interface.
      self._temp_test_file = self.CreateTempFile(file_name=_TEST_FILE,
                                                 contents=contents)
    return self._temp_test_file

  class MockDownloadCloudApi(gslib.cloud_api.CloudApi):
    """Mock CloudApi that implements GetObjectMedia for testing."""

    def __init__(self, write_values):
      """Initialize the mock that will be used by the download thread.

      Args:
        write_values: List of values that will be used for calls to write(),
            in order, by the download thread. An Exception class may be part of
            the list; if so, the Exception will be raised after previous
            values are consumed.
      """
      self._write_values = write_values
      self.get_calls = 0

    def GetObjectMedia(self,
                       unused_bucket_name,
                       unused_object_name,
                       download_stream,
                       start_byte=0,
                       end_byte=None,
                       **kwargs):
      """Writes self._write_values to the download_stream."""
      # Writes from start_byte up to, but not including end_byte (if not None).
      # Does not slice values;
      # self._write_values must line up with start/end_byte.
      self.get_calls += 1
      bytes_read = 0
      for write_value in self._write_values:
        if bytes_read < start_byte:
          bytes_read += len(write_value)
          continue
        if end_byte and bytes_read >= end_byte:
          break
        if isinstance(write_value, Exception):
          raise write_value
        download_stream.write(write_value)
        bytes_read += len(write_value)

  def _WriteFromWrapperToFile(self, daisy_chain_wrapper, file_path):
    """Writes all contents from the DaisyChainWrapper to the named file."""
    with open(file_path, 'wb') as upload_stream:
      while True:
        data = daisy_chain_wrapper.read(TRANSFER_BUFFER_SIZE)
        if not data:
          break
        upload_stream.write(data)

  def testDownloadSingleChunk(self):
    """Tests a single call to GetObjectMedia."""
    write_values = []
    with open(self.test_data_file, 'rb') as stream:
      while True:
        data = stream.read(TRANSFER_BUFFER_SIZE)
        if not data:
          break
        write_values.append(data)
    upload_file = self.CreateTempFile()
    # Test for a single call even if the chunk size is larger than the data.
    for chunk_size in (self.test_data_file_len, self.test_data_file_len + 1):
      mock_api = self.MockDownloadCloudApi(write_values)
      daisy_chain_wrapper = DaisyChainWrapper(self._dummy_url,
                                              self.test_data_file_len,
                                              mock_api,
                                              download_chunk_size=chunk_size)
      self._WriteFromWrapperToFile(daisy_chain_wrapper, upload_file)
      # Since the chunk size is >= the file size, only a single GetObjectMedia
      # call should be made.
      self.assertEqual(mock_api.get_calls, 1)
      with open(upload_file, 'rb') as upload_stream:
        with open(self.test_data_file, 'rb') as download_stream:
          self.assertEqual(upload_stream.read(), download_stream.read())

  def testDownloadMultiChunk(self):
    """Tests multiple calls to GetObjectMedia."""
    upload_file = self.CreateTempFile()
    write_values = []
    with open(self.test_data_file, 'rb') as stream:
      while True:
        data = stream.read(TRANSFER_BUFFER_SIZE)
        if not data:
          break
        write_values.append(data)
    mock_api = self.MockDownloadCloudApi(write_values)
    daisy_chain_wrapper = DaisyChainWrapper(
        self._dummy_url,
        self.test_data_file_len,
        mock_api,
        download_chunk_size=TRANSFER_BUFFER_SIZE)
    self._WriteFromWrapperToFile(daisy_chain_wrapper, upload_file)
    num_expected_calls = self.test_data_file_len // TRANSFER_BUFFER_SIZE
    if self.test_data_file_len % TRANSFER_BUFFER_SIZE:
      num_expected_calls += 1
    # Since the chunk size is < the file size, multiple calls to GetObjectMedia
    # should be made.
    self.assertEqual(mock_api.get_calls, num_expected_calls)
    with open(upload_file, 'rb') as upload_stream:
      with open(self.test_data_file, 'rb') as download_stream:
        self.assertEqual(upload_stream.read(), download_stream.read())

  def testDownloadWithDifferentChunkSize(self):
    """Tests multiple calls to GetObjectMedia."""
    upload_file = self.CreateTempFile()
    write_values = []
    with open(self.test_data_file, 'rb') as stream:
      # Use an arbitrary size greater than TRANSFER_BUFFER_SIZE for writing
      # data to the buffer. For reading from the buffer
      # WriteFromWrapperToFile will use TRANSFER_BUFFER_SIZE.
      buffer_write_size = TRANSFER_BUFFER_SIZE * 2 + 10
      while True:
        # Write data with size.
        data = stream.read(buffer_write_size)
        if not data:
          break
        write_values.append(data)
    mock_api = self.MockDownloadCloudApi(write_values)
    daisy_chain_wrapper = DaisyChainWrapper(
        self._dummy_url,
        self.test_data_file_len,
        mock_api,
        download_chunk_size=TRANSFER_BUFFER_SIZE)
    self._WriteFromWrapperToFile(daisy_chain_wrapper, upload_file)
    num_expected_calls = math.ceil(self.test_data_file_len /
                                   TRANSFER_BUFFER_SIZE)
    # Since the chunk size is < the file size, multiple calls to GetObjectMedia
    # should be made.
    self.assertEqual(mock_api.get_calls, num_expected_calls)
    with open(upload_file, 'rb') as upload_stream:
      with open(self.test_data_file, 'rb') as download_stream:
        self.assertEqual(upload_stream.read(), download_stream.read())

  def testDownloadWithZeroWrites(self):
    """Tests 0-byte writes to the download stream from GetObjectMedia."""
    write_values = []
    with open(self.test_data_file, 'rb') as stream:
      while True:
        write_values.append(b'')
        data = stream.read(TRANSFER_BUFFER_SIZE)
        write_values.append(b'')
        if not data:
          break
        write_values.append(data)
    upload_file = self.CreateTempFile()
    mock_api = self.MockDownloadCloudApi(write_values)
    daisy_chain_wrapper = DaisyChainWrapper(
        self._dummy_url,
        self.test_data_file_len,
        mock_api,
        download_chunk_size=self.test_data_file_len)
    self._WriteFromWrapperToFile(daisy_chain_wrapper, upload_file)
    self.assertEqual(mock_api.get_calls, 1)
    with open(upload_file, 'rb') as upload_stream:
      with open(self.test_data_file, 'rb') as download_stream:
        self.assertEqual(upload_stream.read(), download_stream.read())

  def testDownloadWithPartialWrite(self):
    """Tests unaligned writes to the download stream from GetObjectMedia."""
    with open(self.test_data_file, 'rb') as stream:
      chunk = stream.read(TRANSFER_BUFFER_SIZE)
    # Though it may seem equivalent, the `:1` is actually necessary, without
    # it in python 3, `one_byte` would be int(77) and with it, `one_byte` is
    # the expected value of b'M' (using case where start of chunk is b'MJoTM...')
    one_byte = chunk[0:1]
    chunk_minus_one_byte = chunk[1:TRANSFER_BUFFER_SIZE]
    half_chunk = chunk[0:TRANSFER_BUFFER_SIZE // 2]

    write_values_dict = {
        'First byte first chunk unaligned':
            (one_byte, chunk_minus_one_byte, chunk, chunk),
        'Last byte first chunk unaligned': (chunk_minus_one_byte, chunk, chunk),
        'First byte second chunk unaligned':
            (chunk, one_byte, chunk_minus_one_byte, chunk),
        'Last byte second chunk unaligned':
            (chunk, chunk_minus_one_byte, one_byte, chunk),
        'First byte final chunk unaligned':
            (chunk, chunk, one_byte, chunk_minus_one_byte),
        'Last byte final chunk unaligned':
            (chunk, chunk, chunk_minus_one_byte, one_byte),
        'Half chunks': (half_chunk, half_chunk, half_chunk),
        'Many unaligned':
            (one_byte, half_chunk, one_byte, half_chunk, chunk,
             chunk_minus_one_byte, chunk, one_byte, half_chunk, one_byte)
    }
    upload_file = self.CreateTempFile()
    for case_name, write_values in six.iteritems(write_values_dict):
      expected_contents = b''
      for write_value in write_values:
        expected_contents += write_value
      mock_api = self.MockDownloadCloudApi(write_values)
      daisy_chain_wrapper = DaisyChainWrapper(
          self._dummy_url,
          len(expected_contents),
          mock_api,
          download_chunk_size=self.test_data_file_len)
      self._WriteFromWrapperToFile(daisy_chain_wrapper, upload_file)
      with open(upload_file, 'rb') as upload_stream:
        self.assertEqual(
            upload_stream.read(), expected_contents,
            'Uploaded file contents for case %s did not match' % case_name)

  def testSeekAndReturn(self):
    """Tests seeking to the end of the wrapper (simulates getting size)."""
    write_values = []
    with open(self.test_data_file, 'rb') as stream:
      while True:
        data = stream.read(TRANSFER_BUFFER_SIZE)
        if not data:
          break
        write_values.append(data)
    upload_file = self.CreateTempFile()
    mock_api = self.MockDownloadCloudApi(write_values)
    daisy_chain_wrapper = DaisyChainWrapper(
        self._dummy_url,
        self.test_data_file_len,
        mock_api,
        download_chunk_size=self.test_data_file_len)
    with open(upload_file, 'wb') as upload_stream:
      current_position = 0
      daisy_chain_wrapper.seek(0, whence=os.SEEK_END)
      daisy_chain_wrapper.seek(current_position)
      while True:
        data = daisy_chain_wrapper.read(TRANSFER_BUFFER_SIZE)
        current_position += len(data)
        daisy_chain_wrapper.seek(0, whence=os.SEEK_END)
        daisy_chain_wrapper.seek(current_position)
        if not data:
          break
        upload_stream.write(data)
    self.assertEqual(mock_api.get_calls, 1)
    with open(upload_file, 'rb') as upload_stream:
      with open(self.test_data_file, 'rb') as download_stream:
        self.assertEqual(upload_stream.read(), download_stream.read())

  def testRestartDownloadThread(self):
    """Tests seek to non-stored position; this restarts the download thread."""
    write_values = []
    with open(self.test_data_file, 'rb') as stream:
      while True:
        data = stream.read(TRANSFER_BUFFER_SIZE)
        if not data:
          break
        write_values.append(data)
    upload_file = self.CreateTempFile()
    mock_api = self.MockDownloadCloudApi(write_values)
    daisy_chain_wrapper = DaisyChainWrapper(
        self._dummy_url,
        self.test_data_file_len,
        mock_api,
        download_chunk_size=self.test_data_file_len)
    daisy_chain_wrapper.read(TRANSFER_BUFFER_SIZE)
    daisy_chain_wrapper.read(TRANSFER_BUFFER_SIZE)
    daisy_chain_wrapper.seek(0)
    self._WriteFromWrapperToFile(daisy_chain_wrapper, upload_file)
    self.assertEqual(mock_api.get_calls, 2)
    with open(upload_file, 'rb') as upload_stream:
      with open(self.test_data_file, 'rb') as download_stream:
        self.assertEqual(upload_stream.read(), download_stream.read())

  def testDownloadThreadException(self):
    """Tests that an exception is propagated via the upload thread."""

    class DownloadException(Exception):
      pass

    write_values = [
        b'a', b'b',
        DownloadException('Download thread forces failure')
    ]
    upload_file = self.CreateTempFile()
    mock_api = self.MockDownloadCloudApi(write_values)
    daisy_chain_wrapper = DaisyChainWrapper(
        self._dummy_url,
        self.test_data_file_len,
        mock_api,
        download_chunk_size=self.test_data_file_len)
    try:
      self._WriteFromWrapperToFile(daisy_chain_wrapper, upload_file)
      self.fail('Expected exception')
    except DownloadException as e:
      self.assertIn('Download thread forces failure', str(e))

  def testInvalidSeek(self):
    """Tests that seeking fails for unsupported seek arguments."""
    daisy_chain_wrapper = DaisyChainWrapper(self._dummy_url,
                                            self.test_data_file_len,
                                            self.MockDownloadCloudApi([]))
    try:
      # SEEK_CUR is invalid.
      daisy_chain_wrapper.seek(0, whence=os.SEEK_CUR)
      self.fail('Expected exception')
    except IOError as e:
      self.assertIn('does not support seek mode', str(e))

    try:
      # Seeking from the end with an offset is invalid.
      daisy_chain_wrapper.seek(1, whence=os.SEEK_END)
      self.fail('Expected exception')
    except IOError as e:
      self.assertIn('Invalid seek during daisy chain', str(e))
