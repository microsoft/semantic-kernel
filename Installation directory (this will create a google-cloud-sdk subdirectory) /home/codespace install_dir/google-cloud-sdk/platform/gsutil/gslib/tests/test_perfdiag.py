# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
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
"""Integration tests for perfdiag command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import socket
import sys

import six

import boto
from gslib.commands.perfdiag import _GenerateFileData
import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForXML
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import RUN_S3_TESTS
from gslib.tests.util import unittest
from gslib.utils.system_util import IS_WINDOWS

from six import add_move, MovedModule

add_move(MovedModule('mock', 'mock', 'unittest.mock'))
from six.moves import mock


class TestPerfDiag(testcase.GsUtilIntegrationTestCase):
  """Integration tests for perfdiag command."""

  @classmethod
  def setUpClass(cls):
    super(TestPerfDiag, cls).setUpClass()
    # We want to test that perfdiag works both when connecting to the standard
    # gs endpoint, and when connecting to a specific IP or host while setting
    # the host header. For the 2nd case we resolve gs_host (normally
    # storage.googleapis.com) to a specific IP and connect to that explicitly.
    gs_host = boto.config.get('Credentials', 'gs_host',
                              boto.gs.connection.GSConnection.DefaultHost)
    gs_ip = None
    for address_tuple in socket.getaddrinfo(gs_host, None):
      # Index 0 holds IP version. AF_INET = IPv4.
      if address_tuple[0].name in ('AF_INET', 'AF_INET6'):
        # Index 4 holds IP tuple, where first item is IP.
        gs_ip = address_tuple[4][0]
        break
    if not gs_ip:
      raise ConnectionError('Count not find IP for ' + gs_host)

    cls._custom_endpoint_flags = [
        '-o', 'Credentials:gs_host=' + gs_ip, '-o',
        'Credentials:gs_host_header=' + gs_host, '-o',
        'Boto:https_validate_certificates=False'
    ]

  def _should_run_with_custom_endpoints(self):
    # Host headers are only supported for XML, and not when
    # using environment variables for proxies.
    # TODO: Currently this is disabled for Python versions
    # >= 2.7.9 which cause certificate errors due to validation
    # added in https://www.python.org/dev/peps/pep-0466/
    # If https://github.com/boto/boto/pull/2857 or its analog
    # is accepted in boto, set https_validate_certificates to False
    # in these tests and re-enable them.
    python_version_less_than_2_7_9 = (sys.version_info[0] == 2 and (
        (sys.version_info[1] < 7) or
        (sys.version_info[1] == 7 and sys.version_info[2] < 9)))
    return (self.test_api == 'XML' and not RUN_S3_TESTS and
            python_version_less_than_2_7_9 and
            not (os.environ.get('http_proxy') or os.environ.get('https_proxy')
                 or os.environ.get('HTTPS_PROXY')))

  def test_latency(self):
    bucket_uri = self.CreateBucket()
    cmd = ['perfdiag', '-n', '1', '-t', 'lat', suri(bucket_uri)]
    self.RunGsUtil(cmd)
    if self._should_run_with_custom_endpoints():
      self.RunGsUtil(self._custom_endpoint_flags + cmd)
    self.AssertNObjectsInBucket(bucket_uri, 0, versioned=True)

  def _run_throughput_test(self,
                           test_name,
                           num_processes,
                           num_threads,
                           parallelism_strategy=None,
                           compression_ratio=None):
    bucket_uri = self.CreateBucket()

    cmd = [
        'perfdiag', '-n',
        str(num_processes * num_threads), '-s', '1024', '-c',
        str(num_processes), '-k',
        str(num_threads), '-t', test_name
    ]
    if compression_ratio is not None:
      cmd += ['-j', str(compression_ratio)]
    if parallelism_strategy is not None:
      cmd += ['-p', parallelism_strategy]
    cmd += [suri(bucket_uri)]

    stderr_default = self.RunGsUtil(cmd, return_stderr=True)
    stderr_custom = None
    if self._should_run_with_custom_endpoints():
      stderr_custom = self.RunGsUtil(self._custom_endpoint_flags + cmd,
                                     return_stderr=True)
    self.AssertNObjectsInBucket(bucket_uri, 0, versioned=True)
    return (stderr_default, stderr_custom)

  def _run_each_parallel_throughput_test(self,
                                         test_name,
                                         num_processes,
                                         num_threads,
                                         compression_ratio=None):
    self._run_throughput_test(test_name,
                              num_processes,
                              num_threads,
                              'fan',
                              compression_ratio=compression_ratio)
    if not RUN_S3_TESTS:
      self._run_throughput_test(test_name,
                                num_processes,
                                num_threads,
                                'slice',
                                compression_ratio=compression_ratio)
      self._run_throughput_test(test_name,
                                num_processes,
                                num_threads,
                                'both',
                                compression_ratio=compression_ratio)

  def test_write_throughput_single_process_single_thread(self):
    self._run_throughput_test('wthru', 1, 1)
    self._run_throughput_test('wthru_file', 1, 1)

  def test_write_throughput_single_process_multi_thread(self):
    self._run_each_parallel_throughput_test('wthru', 1, 2)
    self._run_each_parallel_throughput_test('wthru_file', 1, 2)

  @unittest.skipIf(IS_WINDOWS, 'Multiprocessing is not supported on Windows')
  def test_write_throughput_multi_process_single_thread(self):
    self._run_each_parallel_throughput_test('wthru', 2, 1)
    self._run_each_parallel_throughput_test('wthru_file', 2, 1)

  @unittest.skipIf(IS_WINDOWS, 'Multiprocessing is not supported on Windows')
  def test_write_throughput_multi_process_multi_thread(self):
    self._run_each_parallel_throughput_test('wthru', 2, 2)
    self._run_each_parallel_throughput_test('wthru_file', 2, 2)

  def test_read_throughput_single_process_single_thread(self):
    self._run_throughput_test('rthru', 1, 1)
    self._run_throughput_test('rthru_file', 1, 1)

  def test_read_throughput_single_process_multi_thread(self):
    self._run_each_parallel_throughput_test('rthru', 1, 2)
    self._run_each_parallel_throughput_test('rthru_file', 1, 2)

  @unittest.skipIf(IS_WINDOWS, 'Multiprocessing is not supported on Windows')
  def test_read_throughput_multi_process_single_thread(self):
    self._run_each_parallel_throughput_test('rthru', 2, 1)
    self._run_each_parallel_throughput_test('rthru_file', 2, 1)

  @unittest.skipIf(IS_WINDOWS, 'Multiprocessing is not supported on Windows')
  def test_read_throughput_multi_process_multi_thread(self):
    self._run_each_parallel_throughput_test('rthru', 2, 2)
    self._run_each_parallel_throughput_test('rthru_file', 2, 2)

  @unittest.skipIf(IS_WINDOWS, 'Multiprocessing is not supported on Windows')
  def test_read_and_write_file_ordering(self):
    """Tests that rthru_file and wthru_file work when run together."""
    self._run_throughput_test('rthru_file,wthru_file', 1, 1)
    self._run_throughput_test('rthru_file,wthru_file', 2, 2, 'fan')
    if not RUN_S3_TESTS:
      self._run_throughput_test('rthru_file,wthru_file', 2, 2, 'slice')
      self._run_throughput_test('rthru_file,wthru_file', 2, 2, 'both')

  def test_input_output(self):
    outpath = self.CreateTempFile()
    bucket_uri = self.CreateBucket()
    self.RunGsUtil(
        ['perfdiag', '-o', outpath, '-n', '1', '-t', 'lat',
         suri(bucket_uri)])
    self.RunGsUtil(['perfdiag', '-i', outpath])

  def test_invalid_size(self):
    stderr = self.RunGsUtil(
        ['perfdiag', '-n', '1', '-s', 'foo', '-t', 'wthru', 'gs://foobar'],
        expected_status=1,
        return_stderr=True)
    self.assertIn('Invalid -s', stderr)

  def test_toobig_size(self):
    stderr = self.RunGsUtil(
        ['perfdiag', '-n', '1', '-s', '3pb', '-t', 'wthru', 'gs://foobar'],
        expected_status=1,
        return_stderr=True)
    self.assertIn('in-memory tests maximum file size', stderr)

  def test_listing(self):
    bucket_uri = self.CreateBucket()
    stdout = self.RunGsUtil(
        ['perfdiag', '-n', '1', '-t', 'list',
         suri(bucket_uri)],
        return_stdout=True)
    self.assertIn('Number of listing calls made:', stdout)
    self.AssertNObjectsInBucket(bucket_uri, 0, versioned=True)

  @SkipForXML('No compressed transport encoding support for the XML API.')
  def test_gzip_write_throughput_single_process_single_thread(self):
    (stderr_default, _) = self._run_throughput_test('wthru',
                                                    1,
                                                    1,
                                                    compression_ratio=50)
    self.assertIn('Gzip compression ratio: 50', stderr_default)
    self.assertIn('Gzip transport encoding writes: True', stderr_default)
    (stderr_default, _) = self._run_throughput_test('wthru_file',
                                                    1,
                                                    1,
                                                    compression_ratio=50)
    self.assertIn('Gzip compression ratio: 50', stderr_default)
    self.assertIn('Gzip transport encoding writes: True', stderr_default)

  @SkipForXML('No compressed transport encoding support for the XML API.')
  def test_gzip_write_throughput_single_process_multi_thread(self):
    self._run_each_parallel_throughput_test('wthru', 1, 2, compression_ratio=50)
    self._run_each_parallel_throughput_test('wthru_file',
                                            1,
                                            2,
                                            compression_ratio=50)

  @unittest.skipIf(IS_WINDOWS, 'Multiprocessing is not supported on Windows')
  @SkipForXML('No compressed transport encoding support for the XML API.')
  def test_gzip_write_throughput_multi_process_multi_thread(self):
    self._run_each_parallel_throughput_test('wthru', 2, 2, compression_ratio=50)
    self._run_each_parallel_throughput_test('wthru_file',
                                            2,
                                            2,
                                            compression_ratio=50)


class TestPerfDiagUnitTests(testcase.GsUtilUnitTestCase):
  """Unit tests for perfdiag command."""

  def test_listing_does_not_list_preexisting_objects(self):
    test_objects = 1
    bucket_uri = self.CreateBucket()
    # Create two objects in the bucket before executing perfdiag.
    self.CreateObject(bucket_uri=bucket_uri, contents=b'foo')
    self.CreateObject(bucket_uri=bucket_uri, contents=b'bar')
    mock_log_handler = self.RunCommand(
        'perfdiag',
        ['-n', str(test_objects), '-t', 'list',
         suri(bucket_uri)],
        return_log_handler=True)
    self.assertNotIn(
        'Listing produced more than the expected %d object(s).' % test_objects,
        mock_log_handler.messages['warning'])

  @mock.patch('os.urandom')
  def test_generate_file_data(self, mock_urandom):
    """Test the right amount of random and sequential data is generated."""

    def urandom(length):
      return b'a' * length

    mock_urandom.side_effect = urandom

    fp = six.BytesIO()
    _GenerateFileData(fp, 1000, 100, 1000)
    self.assertEqual(b'a' * 1000, fp.getvalue())
    self.assertEqual(1000, fp.tell())

    fp = six.BytesIO()
    _GenerateFileData(fp, 1000, 50, 1000)
    self.assertIn(b'a' * 500, fp.getvalue())
    self.assertIn(b'x' * 500, fp.getvalue())
    self.assertEqual(1000, fp.tell())

    fp = six.BytesIO()
    _GenerateFileData(fp, 1001, 50, 1001)
    self.assertIn(b'a' * 501, fp.getvalue())
    self.assertIn(b'x' * 500, fp.getvalue())
    self.assertEqual(1001, fp.tell())

  @mock.patch('os.urandom')
  def test_generate_file_data_repeat(self, mock_urandom):
    """Test that random data repeats when exhausted."""

    def urandom(length):
      return b'a' * length

    mock_urandom.side_effect = urandom

    fp = six.BytesIO()
    _GenerateFileData(fp, 8, 50, 4)
    self.assertEqual(b'aaxxaaxx', fp.getvalue())
    self.assertEqual(8, fp.tell())
