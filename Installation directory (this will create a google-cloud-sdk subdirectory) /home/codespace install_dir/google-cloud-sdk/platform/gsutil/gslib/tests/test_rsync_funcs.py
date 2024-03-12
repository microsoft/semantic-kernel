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
"""Unit tests for functions in rsync command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import logging
import os

from gslib.commands.rsync import _ComputeNeededFileChecksums
from gslib.commands.rsync import _NA
from gslib.tests.testcase.unit_testcase import GsUtilUnitTestCase
from gslib.utils.hashing_helper import CalculateB64EncodedCrc32cFromContents
from gslib.utils.hashing_helper import CalculateB64EncodedMd5FromContents


class TestRsyncFuncs(GsUtilUnitTestCase):

  def test_compute_needed_file_checksums(self):
    """Tests that we compute all/only needed file checksums."""
    size = 4
    logger = logging.getLogger()
    tmpdir = self.CreateTempDir()
    file_url_str = 'file://%s' % os.path.join(tmpdir, 'obj1')
    self.CreateTempFile(tmpdir=tmpdir, file_name='obj1', contents=b'obj1')
    cloud_url_str = 'gs://whatever'
    with open(os.path.join(tmpdir, 'obj1'), 'rb') as fp:
      crc32c = CalculateB64EncodedCrc32cFromContents(fp)
      fp.seek(0)
      md5 = CalculateB64EncodedMd5FromContents(fp)

    # Test case where source is a file and dest has CRC32C.
    (src_crc32c, src_md5, dst_crc32c,
     dst_md5) = _ComputeNeededFileChecksums(logger, file_url_str, size, _NA,
                                            _NA, cloud_url_str, size, crc32c,
                                            _NA)
    self.assertEqual(crc32c, src_crc32c)
    self.assertEqual(_NA, src_md5)
    self.assertEqual(crc32c, dst_crc32c)
    self.assertEqual(_NA, dst_md5)

    # Test case where source is a file and dest has MD5 but not CRC32C.
    (src_crc32c, src_md5, dst_crc32c,
     dst_md5) = _ComputeNeededFileChecksums(logger, file_url_str, size, _NA,
                                            _NA, cloud_url_str, size, _NA, md5)
    self.assertEqual(_NA, src_crc32c)
    self.assertEqual(md5, src_md5)
    self.assertEqual(_NA, dst_crc32c)
    self.assertEqual(md5, dst_md5)

    # Test case where dest is a file and src has CRC32C.
    (src_crc32c, src_md5, dst_crc32c,
     dst_md5) = _ComputeNeededFileChecksums(logger, cloud_url_str, size, crc32c,
                                            _NA, file_url_str, size, _NA, _NA)
    self.assertEqual(crc32c, dst_crc32c)
    self.assertEqual(_NA, src_md5)
    self.assertEqual(crc32c, src_crc32c)
    self.assertEqual(_NA, src_md5)

    # Test case where dest is a file and src has MD5 but not CRC32C.
    (src_crc32c, src_md5, dst_crc32c,
     dst_md5) = _ComputeNeededFileChecksums(logger, cloud_url_str, size, _NA,
                                            md5, file_url_str, size, _NA, _NA)
    self.assertEqual(_NA, dst_crc32c)
    self.assertEqual(md5, src_md5)
    self.assertEqual(_NA, src_crc32c)
    self.assertEqual(md5, src_md5)
