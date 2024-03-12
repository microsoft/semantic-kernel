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
"""Unit tests for FilePart class."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os

from gslib.file_part import FilePart
import gslib.tests.testcase as testcase


# pylint: disable=protected-access
class TestFilePart(testcase.GsUtilUnitTestCase):
  """Unit tests for FilePart class."""

  def test_tell(self):
    filename = 'test_tell'
    contents = 100 * b'x'
    fpath = self.CreateTempFile(file_name=filename, contents=contents)
    part_length = 23
    start_pos = 50
    fp = FilePart(fpath, start_pos, part_length)
    self.assertEqual(start_pos, fp._fp.tell())
    self.assertEqual(0, fp.tell())

  def test_seek(self):
    """Tests seeking in a FilePart."""
    filename = 'test_seek'
    contents = 100 * b'x'
    part_length = 23
    start_pos = 50
    fpath = self.CreateTempFile(file_name=filename, contents=contents)
    fp = FilePart(fpath, start_pos, part_length)
    offset = 10

    # Absolute positioning.
    fp.seek(offset)
    self.assertEqual(start_pos + offset, fp._fp.tell())
    self.assertEqual(offset, fp.tell())

    # Relative positioning.
    fp.seek(offset, whence=os.SEEK_CUR)
    self.assertEqual(start_pos + 2 * offset, fp._fp.tell())
    self.assertEqual(2 * offset, fp.tell())

    # Absolute positioning from EOF.
    fp.seek(-offset, whence=os.SEEK_END)
    self.assertEqual(start_pos + part_length - offset, fp._fp.tell())
    self.assertEqual(part_length - offset, fp.tell())

    # Seek past EOF.
    fp.seek(1, whence=os.SEEK_END)
    self.assertEqual(start_pos + part_length + 1, fp._fp.tell())
    self.assertEqual(part_length + 1, fp.tell())

  def test_read(self):
    """Tests various reaad operations with FilePart."""
    filename = 'test_read'
    contents = bytearray(range(256))
    part_length = 23
    start_pos = 50
    fpath = self.CreateTempFile(file_name=filename, contents=contents)

    # Read in the whole file.
    fp = FilePart(fpath, start_pos, part_length)
    whole_file = fp.read()
    self.assertEqual(contents[start_pos:(start_pos + part_length)], whole_file)

    # Read in a piece of the file from the beginning.
    fp.seek(0)
    offset = 10
    partial_file = fp.read(offset)
    self.assertEqual(contents[start_pos:(start_pos + offset)], partial_file)

    # Read in the rest of the file.
    remaining_file = fp.read(part_length - offset)
    self.assertEqual(contents[(start_pos + offset):(start_pos + part_length)],
                     remaining_file)
    self.assertEqual(contents[start_pos:(start_pos + part_length)],
                     partial_file + remaining_file)

    # Try to read after reaching EOF.
    empty_file = fp.read(100)
    self.assertEqual(b'', empty_file)

    empty_file = fp.read()
    self.assertEqual(b'', empty_file)
