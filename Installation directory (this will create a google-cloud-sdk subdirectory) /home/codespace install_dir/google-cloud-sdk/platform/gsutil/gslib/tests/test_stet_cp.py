# -*- coding: utf-8 -*-
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Integration tests for cp STET binary integration.

Could go with cp tests but that file is bulky."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import stat

from gslib import storage_url
from gslib.tests import testcase
from gslib.tests import util
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import unittest
from gslib.utils import system_util
from gslib.utils import temporary_file_util

FAKE_STET_BINARY = """\
#!/bin/sh
if [ "$#" -ne 5 ]; then
  echo "Expected 5 arguments. Got $#."
  exit 1
fi

echo "subcommand: $1
config file: $2
blob id: $3
in file: $4
out file: $5" > $5
"""


@unittest.skipIf(not system_util.IS_LINUX, 'STET binary supports only Linux.')
class TestStetCp(testcase.GsUtilIntegrationTestCase):
  """Integration tests for cp integration with STET binary."""

  def setUp(self):
    super(TestStetCp, self).setUp()
    # Substitute for actual binary.
    self.stet_binary_path = self.CreateTempFile(contents=FAKE_STET_BINARY)
    # Make shell script executable in addition to current permissions.
    current_stat = os.stat(self.stet_binary_path)
    os.chmod(self.stet_binary_path, current_stat.st_mode | stat.S_IEXEC)
    # Fake config.
    self.stet_config_path = self.CreateTempFile()

  def test_encrypts_upload_if_stet_is_enabled(self):
    object_uri = self.CreateObject()
    test_file = self.CreateTempFile(contents='will be rewritten')

    stderr = self.RunGsUtil([
        '-o', 'GSUtil:stet_binary_path={}'.format(self.stet_binary_path), '-o',
        'GSUtil:stet_config_path={}'.format(
            self.stet_config_path), 'cp', '--stet', test_file,
        suri(object_uri)
    ],
                            return_stderr=True)

    # Progress indicator should show transformed file size (variable based on
    # random string generation above). 4.0 B is the pre-transform size.
    self.assertNotIn('/4.0 B]', stderr)

    stdout = self.RunGsUtil(['cat', suri(object_uri)], return_stdout=True)
    self.assertIn('subcommand: encrypt', stdout)
    self.assertIn('config file: --config-file={}'.format(self.stet_config_path),
                  stdout)
    self.assertIn('blob id: --blob-id={}'.format(suri(object_uri)), stdout)
    self.assertIn('in file: {}'.format(test_file), stdout)
    self.assertIn('out file: {}_.stet_tmp'.format(test_file), stdout)

    self.assertFalse(
        os.path.exists(
            temporary_file_util.GetStetTempFileName(
                storage_url.StorageUrlFromString(test_file))))

  def test_decrypts_download_if_stet_is_enabled(self):
    object_uri = self.CreateObject(contents='abc')
    test_file = self.CreateTempFile()

    stderr = self.RunGsUtil([
        '-o', 'GSUtil:stet_binary_path={}'.format(self.stet_binary_path), '-o',
        'GSUtil:stet_config_path={}'.format(
            self.stet_config_path), 'cp', '--stet',
        suri(object_uri), test_file
    ],
                            return_stderr=True)

    # Progress indicator should show transformed file size (variable based on
    # random string generation above). 4.0 B is the pre-transform size.
    self.assertNotIn('/4.0 B]', stderr)

    with open(test_file) as file_reader:
      downloaded_text = file_reader.read()
    self.assertIn('subcommand: decrypt', downloaded_text)
    self.assertIn('config file: --config-file={}'.format(self.stet_config_path),
                  downloaded_text)
    self.assertIn('blob id: --blob-id={}'.format(suri(object_uri)),
                  downloaded_text)
    self.assertIn('in file: {}'.format(test_file), downloaded_text)
    self.assertIn('out file: {}_.stet_tmp'.format(test_file), downloaded_text)

    self.assertFalse(
        os.path.exists(
            temporary_file_util.GetStetTempFileName(
                storage_url.StorageUrlFromString(test_file))))

  def test_does_not_seek_ahead_for_bytes_if_stet_transform(self):
    """Tests that cp does not seek-ahead for bytes if file size will change."""
    tmpdir = self.CreateTempDir()
    for _ in range(3):
      self.CreateTempFile(tmpdir=tmpdir, contents=b'123456')

    bucket_uri = self.CreateBucket()

    with util.SetBotoConfigForTest([
        ('GSUtil', 'task_estimation_threshold', '1'),
        ('GSUtil', 'task_estimation_force', 'True')
    ]):
      stderr = self.RunGsUtil([
          '-m', '-o', 'GSUtil:stet_binary_path={}'.format(
              self.stet_binary_path), '-o', 'GSUtil:stet_config_path={}'.format(
                  self.stet_config_path), 'cp', '-r', '--stet', tmpdir,
          suri(bucket_uri)
      ],
                              return_stderr=True)

      # Check the denominator of the progress indicator to see if the
      # correct total file size is shown. This is a proxy for if the seek-ahead
      # thread ran because if seak-ahead runs before STET encryption, an
      # incorrect, smaller file size will show. The full progress string looks
      # something like: "[3 files][   2.0 KiB/   2.0 KiB]"
      # Pre-encryption total file size:
      self.assertNotIn('18.0 B]', stderr)
      # Post-encryption total file size:
      # +-0.1 KiB b/c of rounding and different platforms.
      self.assertRegex(stderr, r'2\.\d KiB]')
