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
"""Integration tests for gsutil -D option."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import platform
import re

import six
import gslib
from gslib.cs_api_map import ApiSelector
import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import SetBotoConfigForTest
from gslib.utils.unit_util import ONE_KIB


@SkipForS3('-D output is implementation-specific.')
class TestDOption(testcase.GsUtilIntegrationTestCase):
  """Integration tests for gsutil -D option."""

  def assert_header_in_output(self, name, value, output):
    """Asserts that httplib2's debug logger printed out a specified header.

    This method is fairly primitive and uses assertIn statements, and thus is
    case-sensitive. Values should be normalized (e.g. to lowercase) if
    capitalization of the expected characters may vary.

    Args:
      name: (str) The header name, e.g. "Content-Length".
      value: (Union[str, None]) The header value, e.g. "4096". If no value is
          expected for the header or the value is unknown, this argument should
          be `None`.
      output: (str) The string in which to search for the specified header.
    """
    expected = 'header: %s:' % name
    if value:
      # Only append a space and then the header value if a value was expected.
      expected += ' %s' % value
    if expected in output:
      return

    # Try the other format - when sending requests via the XML API, headers are
    # printed in a list of 2-tuples (by Boto), so we test for that output style
    # as well.  The above style is generally preferred, but Python's http client
    # doesn't print all values in scenarios where a header is sent multiple
    # times with different values, e.g. in this case:
    #   x-goog-hash: md5=blah2
    #   x-goog-hash: crc32c=blah1
    # the debug logger would just print the last one to occur (the crc32c hash).
    alt_expected = "('%s'" % name
    if value:
      # Only check for the second part of the tuple if a value was expected.
      alt_expected += ", '%s')" % value
    if not alt_expected in output:
      self.fail('Neither of these two header formats were found in the output:'
                '\n1) %s\n2) %s\nOutput string: %s' %
                (expected, alt_expected, output))

  def test_minus_D_multipart_upload(self):
    """Tests that debug option does not output upload media body."""
    # We want to ensure it works with and without a trailing newline.
    for file_contents in (b'a1b2c3d4', b'a1b2c3d4\n'):
      fpath = self.CreateTempFile(contents=file_contents)
      bucket_uri = self.CreateBucket()
      with SetBotoConfigForTest([('GSUtil', 'resumable_threshold', str(ONE_KIB))
                                ]):
        stderr = self.RunGsUtil(
            ['-D', 'cp', fpath, suri(bucket_uri)], return_stderr=True)
        print('command line:' + ' '.join(['-D', 'cp', fpath, suri(bucket_uri)]))
        if self.test_api == ApiSelector.JSON:
          self.assertIn('media body', stderr)
        self.assertNotIn('a1b2c3d4', stderr)
        self.assertIn('Comparing local vs cloud md5-checksum for', stderr)
        self.assertIn('total_bytes_transferred: %d' % len(file_contents),
                      stderr)

  def test_minus_D_perf_trace_cp(self):
    """Test upload and download with a sample perf trace token."""
    file_name = 'bar'
    fpath = self.CreateTempFile(file_name=file_name, contents=b'foo')
    bucket_uri = self.CreateBucket()
    stderr = self.RunGsUtil(
        ['-D', '--perf-trace-token=123', 'cp', fpath,
         suri(bucket_uri)],
        return_stderr=True)
    self.assertIn('\'cookie\': \'123\'', stderr)
    stderr2 = self.RunGsUtil([
        '-D', '--perf-trace-token=123', 'cp',
        suri(bucket_uri, file_name), fpath
    ],
                             return_stderr=True)
    self.assertIn('\'cookie\': \'123\'', stderr2)

  def test_minus_D_arbitrary_header_cp(self):
    """Test upload and download with a sample perf trace token."""
    file_name = 'bar'
    fpath = self.CreateTempFile(file_name=file_name, contents=b'foo')
    bucket_uri = self.CreateBucket()
    stderr = self.RunGsUtil(
        ['-D', '-h', 'custom-header:asdf', 'cp', fpath,
         suri(bucket_uri)],
        return_stderr=True)
    self.assertRegex(stderr,
                     r"Headers: \{[\s\S]*'custom-header': 'asdf'[\s\S]*\}")
    stderr2 = self.RunGsUtil([
        '-D', '-h', 'custom-header:asdf', 'cp',
        suri(bucket_uri, file_name), fpath
    ],
                             return_stderr=True)
    self.assertRegex(stderr2,
                     r"Headers: \{[\s\S]*'custom-header': 'asdf'[\s\S]*\}")

    # Ensure the header wasn't set in metadata somehow:
    stdout = self.RunGsUtil(
        ['ls', '-L', suri(bucket_uri, file_name)], return_stdout=True)
    self.assertNotIn('custom', stdout)
    self.assertNotIn('asdf', stdout)

  def test_minus_D_resumable_upload(self):
    fpath = self.CreateTempFile(contents=b'a1b2c3d4')
    bucket_uri = self.CreateBucket()
    with SetBotoConfigForTest([('GSUtil', 'resumable_threshold', '4')]):
      stderr = self.RunGsUtil(
          ['-D', 'cp', fpath, suri(bucket_uri)], return_stderr=True)
      self.assertNotIn('a1b2c3d4', stderr)
      self.assertIn('Comparing local vs cloud md5-checksum for', stderr)
      self.assertIn('total_bytes_transferred: 8', stderr)

  def test_minus_D_cat(self):
    """Tests cat command with debug option."""
    key_uri = self.CreateObject(contents=b'0123456789')
    with SetBotoConfigForTest([('Boto', 'proxy_pass', 'secret')]):
      (stdout,
       stderr) = self.RunGsUtil(['-D', 'cat', suri(key_uri)],
                                return_stdout=True,
                                return_stderr=True)
    # Check for log messages we output.
    self.assertIn('You are running gsutil with debug output enabled.', stderr)
    self.assertIn('config:', stderr)
    if six.PY2:
      self.assertIn("('proxy_pass', u'REDACTED')", stderr)
    else:
      self.assertIn("('proxy_pass', 'REDACTED')", stderr)
    # Check for log messages from httplib2 / http_client.
    self.assertIn("reply: 'HTTP/1.1 200 OK", stderr)
    self.assert_header_in_output('Expires', None, stderr)
    self.assert_header_in_output('Date', None, stderr)
    self.assert_header_in_output('Content-Type', 'application/octet-stream',
                                 stderr)
    self.assert_header_in_output('Content-Length', '10', stderr)

    if self.test_api == ApiSelector.XML:
      self.assert_header_in_output('Cache-Control', None, stderr)
      self.assert_header_in_output('ETag', '"781e5e245d69b566979b86e28d23f2c7"',
                                   stderr)
      self.assert_header_in_output('Last-Modified', None, stderr)
      self.assert_header_in_output('x-goog-generation', None, stderr)
      self.assert_header_in_output('x-goog-metageneration', '1', stderr)
      self.assert_header_in_output('x-goog-hash', 'crc32c=KAwGng==', stderr)
      self.assert_header_in_output('x-goog-hash',
                                   'md5=eB5eJF1ptWaXm4bijSPyxw==', stderr)
      # Check request fields show correct segments.
      regex_str = r'''send:\s+([b|u]')?HEAD /%s/%s HTTP/[^\\]*\\r\\n(.*)''' % (
          key_uri.bucket_name, key_uri.object_name)
      regex = re.compile(regex_str)
      match = regex.search(stderr)
      if not match:
        self.fail('Did not find this regex in stderr:\nRegex: %s\nStderr: %s' %
                  (regex_str, stderr))
      request_fields_str = match.group(2)
      self.assertIn('Content-Length: 0', request_fields_str)
      self.assertRegex(
          request_fields_str,
          'User-Agent: .*gsutil/%s.*interactive/False command/cat' %
          gslib.VERSION)
    elif self.test_api == ApiSelector.JSON:
      if six.PY2:
        self.assertIn("md5Hash: u'eB5eJF1ptWaXm4bijSPyxw=='", stderr)
      else:
        self.assertIn("md5Hash: 'eB5eJF1ptWaXm4bijSPyxw=='", stderr)
      self.assert_header_in_output(
          'Cache-Control', 'no-cache, no-store, max-age=0, must-revalidate',
          stderr)
      self.assertRegex(
          stderr,
          '.*GET.*b/%s/o/%s' % (key_uri.bucket_name, key_uri.object_name))
      self.assertRegex(
          stderr, 'Python/%s.gsutil/%s.*interactive/False command/cat' %
          (platform.python_version(), gslib.VERSION))

    if gslib.IS_PACKAGE_INSTALL:
      self.assertIn('PACKAGED_GSUTIL_INSTALLS_DO_NOT_HAVE_CHECKSUMS', stdout)
    else:
      self.assertRegex(stdout, r'.*checksum: [0-9a-f]{32}.*')
    self.assertIn('gsutil version: %s' % gslib.VERSION, stdout)
    self.assertIn('boto version: ', stdout)
    self.assertIn('python version: ', stdout)
    self.assertIn('OS: ', stdout)
    self.assertIn('multiprocessing available: ', stdout)
    self.assertIn('using cloud sdk: ', stdout)
    self.assertIn('pass cloud sdk credentials to gsutil: ', stdout)
    self.assertIn('config path(s): ', stdout)
    self.assertIn('gsutil path: ', stdout)
    self.assertIn('compiled crcmod: ', stdout)
    self.assertIn('installed via package manager: ', stdout)
    self.assertIn('editable install: ', stdout)
