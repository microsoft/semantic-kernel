# -*- coding: utf-8 -*-
# Copyright 2010 Google Inc. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
"""Tests for parallel uploads ported from gsutil naming tests.

Currently, the mock storage service is not thread-safe and therefore not
suitable for multiprocess/multithreaded testing. Since parallel composite
uploads necessarily create at least one worker thread outside of main,
these tests are present in this file as temporary (slower) integration tests
to provide validation for parallel composite uploads until a thread-safe
mock storage service rewrite.

Tests for relative paths are not included as integration_testcase does not
support modifying the current working directory.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os

import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import SequentialAndParallelTransfer
from gslib.utils.retry_util import Retry


class TestParallelCp(testcase.GsUtilIntegrationTestCase):
  """Unit tests for gsutil naming logic."""

  @SequentialAndParallelTransfer
  def testCopyingTopLevelFileToBucket(self):
    """Tests copying one top-level file to a bucket."""
    src_file = self.CreateTempFile(file_name='f0')
    dst_bucket_uri = self.CreateBucket()
    self.RunGsUtil(['cp', src_file, suri(dst_bucket_uri)])

    lines = self.AssertNObjectsInBucket(dst_bucket_uri, 1)
    self.assertEqual(suri(dst_bucket_uri, 'f0'), lines[0])

  @SequentialAndParallelTransfer
  def testCopyingMultipleFilesToBucket(self):
    """Tests copying multiple files to a bucket."""
    src_file0 = self.CreateTempFile(file_name='f0')
    src_file1 = self.CreateTempFile(file_name='f1')
    dst_bucket_uri = self.CreateBucket()
    self.RunGsUtil(['cp', src_file0, src_file1, suri(dst_bucket_uri)])

    lines = self.AssertNObjectsInBucket(dst_bucket_uri, 2)
    self.assertEqual(suri(dst_bucket_uri, 'f0'), lines[0])
    self.assertEqual(suri(dst_bucket_uri, 'f1'), lines[1])

  @SequentialAndParallelTransfer
  def testCopyingNestedFileToBucketSubdir(self):
    """Tests copying a nested file to a bucket subdir.

    Tests that we correctly translate local FS-specific delimiters ('\' on
    Windows) to bucket delimiter (/).
    """
    tmpdir = self.CreateTempDir()
    subdir = os.path.join(tmpdir, 'subdir')
    os.mkdir(subdir)
    src_file = self.CreateTempFile(tmpdir=tmpdir, file_name='obj', contents=b'')
    dst_bucket_uri = self.CreateBucket()
    # Make an object under subdir so next copy will treat subdir as a subdir.
    self.RunGsUtil(['cp', src_file, suri(dst_bucket_uri, 'subdir/a')])
    self.RunGsUtil(['cp', src_file, suri(dst_bucket_uri, 'subdir')])

    lines = self.AssertNObjectsInBucket(dst_bucket_uri, 2)
    self.assertEqual(suri(dst_bucket_uri, 'subdir/a'), lines[0])
    self.assertEqual(suri(dst_bucket_uri, 'subdir/obj'), lines[1])

  @SequentialAndParallelTransfer
  def testCopyingAbsolutePathDirToBucket(self):
    """Tests recursively copying absolute path directory to a bucket."""
    dst_bucket_uri = self.CreateBucket()
    src_dir_root = self.CreateTempDir(
        test_files=['f0', 'f1', 'f2.txt', ('dir0', 'dir1', 'nested')])
    self.RunGsUtil(['cp', '-R', src_dir_root, suri(dst_bucket_uri)])
    src_tmpdir = os.path.split(src_dir_root)[1]

    lines = self.AssertNObjectsInBucket(dst_bucket_uri, 4)
    self.assertEqual(suri(dst_bucket_uri, src_tmpdir, 'dir0', 'dir1', 'nested'),
                     lines[0])
    self.assertEqual(suri(dst_bucket_uri, src_tmpdir, 'f0'), lines[1])
    self.assertEqual(suri(dst_bucket_uri, src_tmpdir, 'f1'), lines[2])
    self.assertEqual(suri(dst_bucket_uri, src_tmpdir, 'f2.txt'), lines[3])

  @SequentialAndParallelTransfer
  def testCopyingDirContainingOneFileToBucket(self):
    """Tests copying a directory containing 1 file to a bucket.

    We test this case to ensure that correct bucket handling isn't dependent
    on the copy being treated as a multi-source copy.
    """
    dst_bucket_uri = self.CreateBucket()
    src_dir = self.CreateTempDir(test_files=[('dir0', 'dir1', 'foo')])
    self.RunGsUtil([
        'cp', '-R',
        os.path.join(src_dir, 'dir0', 'dir1'),
        suri(dst_bucket_uri)
    ])

    lines = self.AssertNObjectsInBucket(dst_bucket_uri, 1)
    self.assertEqual(suri(dst_bucket_uri, 'dir1', 'foo'), lines[0])

  @SkipForS3('The boto lib used for S3 does not handle objects '
             'starting with slashes if we use V4 signature')
  @SequentialAndParallelTransfer
  def testCopyingFileToObjectWithConsecutiveSlashes(self):
    """Tests copying a file to an object containing consecutive slashes."""
    src_file = self.CreateTempFile(file_name='f0')
    dst_bucket_uri = self.CreateBucket()
    self.RunGsUtil(['cp', src_file, suri(dst_bucket_uri) + '//obj'])

    lines = self.AssertNObjectsInBucket(dst_bucket_uri, 1)
    self.assertEqual(suri(dst_bucket_uri) + '//obj', lines[0])

  @SequentialAndParallelTransfer
  def testCopyingObjsAndFilesToBucket(self):
    """Tests copying objects and files to a bucket."""
    src_bucket_uri = self.CreateBucket()
    self.CreateObject(src_bucket_uri, object_name='f1', contents=b'foo')
    src_dir = self.CreateTempDir(test_files=['f2'])
    dst_bucket_uri = self.CreateBucket()
    self.RunGsUtil([
        'cp', '-R',
        suri(src_bucket_uri, '**'),
        '%s%s**' % (src_dir, os.sep),
        suri(dst_bucket_uri)
    ])

    lines = self.AssertNObjectsInBucket(dst_bucket_uri, 2)
    self.assertEqual(suri(dst_bucket_uri, 'f1'), lines[0])
    self.assertEqual(suri(dst_bucket_uri, 'f2'), lines[1])

  @SequentialAndParallelTransfer
  def testCopyingSubdirRecursiveToNonexistentSubdir(self):
    """Tests copying a directory with a single file recursively to a bucket.

    The file should end up in a new bucket subdirectory with the file's
    directory structure starting below the recursive copy point, as in Unix cp.

    Example:
      filepath: dir1/dir2/foo
      cp -r dir1 dir3
      Results in dir3/dir2/foo being created.
    """
    src_dir = self.CreateTempDir()
    self.CreateTempFile(tmpdir=src_dir + '/dir1/dir2', file_name='foo')
    dst_bucket_uri = self.CreateBucket()
    self.RunGsUtil(
        ['cp', '-R', src_dir + '/dir1',
         suri(dst_bucket_uri, 'dir3')])

    lines = self.AssertNObjectsInBucket(dst_bucket_uri, 1)
    self.assertEqual(suri(dst_bucket_uri, 'dir3/dir2/foo'), lines[0])

  @SequentialAndParallelTransfer
  def testCopyingWildcardedFilesToBucketSubDir(self):
    """Tests copying wildcarded files to a bucket subdir."""
    # Test with and without final slash on dest subdir.
    for final_dst_char in ('', '/'):
      dst_bucket_uri = self.CreateBucket()
      self.CreateObject(dst_bucket_uri,
                        object_name='subdir0/existing',
                        contents=b'foo')
      self.CreateObject(dst_bucket_uri,
                        object_name='subdir1/existing',
                        contents=b'foo')
      src_dir = self.CreateTempDir(test_files=['f0', 'f1', 'f2'])

      for i in range(2):
        self.RunGsUtil([
            'cp',
            os.path.join(src_dir, 'f?'),
            suri(dst_bucket_uri, 'subdir%d' % i) + final_dst_char
        ])

        @Retry(AssertionError, tries=3, timeout_secs=1)
        def _Check1():
          """Validate files were copied to the correct destinations."""
          stdout = self.RunGsUtil(
              ['ls', suri(dst_bucket_uri, 'subdir%d' % i, '**')],
              return_stdout=True)
          lines = stdout.split('\n')
          self.assertEqual(5, len(lines))
          self.assertEqual(suri(dst_bucket_uri, 'subdir%d' % i, 'existing'),
                           lines[0])
          self.assertEqual(suri(dst_bucket_uri, 'subdir%d' % i, 'f0'), lines[1])
          self.assertEqual(suri(dst_bucket_uri, 'subdir%d' % i, 'f1'), lines[2])
          self.assertEqual(suri(dst_bucket_uri, 'subdir%d' % i, 'f2'), lines[3])

        _Check1()

  @SequentialAndParallelTransfer
  def testCopyingOneNestedFileToBucketSubDir(self):
    """Tests copying one nested file to a bucket subdir."""
    # Test with and without final slash on dest subdir.
    for final_dst_char in ('', '/'):

      dst_bucket_uri = self.CreateBucket()
      self.CreateObject(dst_bucket_uri,
                        object_name='d0/placeholder',
                        contents=b'foo')
      self.CreateObject(dst_bucket_uri,
                        object_name='d1/placeholder',
                        contents=b'foo')

      for i in range(2):
        src_dir = self.CreateTempDir(test_files=[('d3', 'd4', 'nested', 'f1')])
        self.RunGsUtil([
            'cp', '-r',
            suri(src_dir, 'd3'),
            suri(dst_bucket_uri, 'd%d' % i) + final_dst_char
        ])

      lines = self.AssertNObjectsInBucket(dst_bucket_uri, 4)
      self.assertEqual(suri(dst_bucket_uri, 'd0', 'd3', 'd4', 'nested', 'f1'),
                       lines[0])
      self.assertEqual(suri(dst_bucket_uri, 'd0', 'placeholder'), lines[1])
      self.assertEqual(suri(dst_bucket_uri, 'd1', 'd3', 'd4', 'nested', 'f1'),
                       lines[2])
      self.assertEqual(suri(dst_bucket_uri, 'd1', 'placeholder'), lines[3])
