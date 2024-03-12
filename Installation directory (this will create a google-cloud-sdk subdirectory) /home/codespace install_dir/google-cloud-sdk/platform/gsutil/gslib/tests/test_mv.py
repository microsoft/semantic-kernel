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
"""Integration tests for mv command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os

from gslib.cs_api_map import ApiSelector
from gslib.tests.test_cp import TestCpMvPOSIXBucketToLocalErrors
from gslib.tests.test_cp import TestCpMvPOSIXBucketToLocalNoErrors
from gslib.tests.test_cp import TestCpMvPOSIXLocalToBucketNoErrors
import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import SequentialAndParallelTransfer
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import SetEnvironmentForTest
from gslib.tests.util import unittest
from gslib.utils.boto_util import UsingCrcmodExtension
from gslib.utils.retry_util import Retry
from gslib.utils.system_util import IS_WINDOWS
from gslib.utils import shim_util


class TestMvUnitTests(testcase.GsUtilUnitTestCase):
  """Unit tests for mv command."""

  def test_move_bucket_objects_with_duplicate_names_inter_bucket(self):
    """Tests moving multiple top-level items between buckets."""
    bucket1_uri = self.CreateBucket()
    self.CreateObject(bucket_uri=bucket1_uri,
                      object_name='dir1/file.txt',
                      contents=b'data')
    self.CreateObject(bucket_uri=bucket1_uri,
                      object_name='dir2/file.txt',
                      contents=b'data')
    bucket2_uri = self.CreateBucket()

    self.RunCommand('mv', [suri(bucket1_uri, '*'), suri(bucket2_uri)])

    actual = set(
        str(u)
        for u in self._test_wildcard_iterator(suri(bucket2_uri, '**')).IterAll(
            expand_top_level_buckets=True))
    expected = set([
        suri(bucket2_uri, 'dir1', 'file.txt'),
        suri(bucket2_uri, 'dir2', 'file.txt'),
    ])
    self.assertEqual(actual, expected)

  def test_move_bucket_objects_with_duplicate_names_to_bucket_subdir(self):
    """Tests moving multiple top-level items between buckets."""
    bucket1_uri = self.CreateBucket()
    self.CreateObject(bucket_uri=bucket1_uri,
                      object_name='dir1/file.txt',
                      contents=b'data')
    self.CreateObject(bucket_uri=bucket1_uri,
                      object_name='dir2/file.txt',
                      contents=b'data')
    bucket2_uri = self.CreateBucket()

    self.RunCommand('mv', [suri(bucket1_uri, '*'), suri(bucket2_uri, 'dir')])

    actual = set(
        str(u)
        for u in self._test_wildcard_iterator(suri(bucket2_uri, '**')).IterAll(
            expand_top_level_buckets=True))
    expected = set([
        suri(bucket2_uri, 'dir', 'dir1', 'file.txt'),
        suri(bucket2_uri, 'dir', 'dir2', 'file.txt'),
    ])
    self.assertEqual(actual, expected)

  def test_move_dirs_with_duplicate_file_names_to_bucket(self):
    """Tests moving multiple top-level items to a bucket."""
    bucket_uri = self.CreateBucket()
    dir_path = self.CreateTempDir(test_files=[
        ('dir1', 'file.txt'),
        ('dir2', 'file.txt'),
    ])

    self.RunCommand('mv', [dir_path + '/*', suri(bucket_uri)])

    actual = set(
        str(u)
        for u in self._test_wildcard_iterator(suri(bucket_uri, '**')).IterAll(
            expand_top_level_buckets=True))
    expected = set([
        suri(bucket_uri, 'dir1', 'file.txt'),
        suri(bucket_uri, 'dir2', 'file.txt'),
    ])
    self.assertEqual(actual, expected)

  def test_shim_translates_flags(self):
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=b'abcd')
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand(
            'mv', ['-a', 'public-read', fpath,
                   suri(bucket_uri)],
            return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            'Gcloud Storage Command: {} storage mv'
            ' --predefined-acl publicRead {} {}'.format(
                shim_util._get_gcloud_binary_path('fake_dir'), fpath,
                suri(bucket_uri)), info_lines)


class TestMvE2ETests(testcase.GsUtilIntegrationTestCase):
  """Integration tests for mv command."""

  def test_moving(self):
    """Tests moving two buckets, one with 2 objects and one with 0 objects."""
    bucket1_uri = self.CreateBucket(test_objects=2)
    self.AssertNObjectsInBucket(bucket1_uri, 2)
    bucket2_uri = self.CreateBucket()
    self.AssertNObjectsInBucket(bucket2_uri, 0)

    # Move two objects from bucket1 to bucket2.
    objs = [
        self.StorageUriCloneReplaceKey(bucket1_uri, key).versionless_uri
        for key in bucket1_uri.list_bucket()
    ]
    cmd = (['-m', 'mv'] + objs + [suri(bucket2_uri)])
    stderr = self.RunGsUtil(cmd, return_stderr=True)
    # Rewrite API may output an additional 'Copying' progress notification.
    self.assertGreaterEqual(
        stderr.count('Copying'), 2,
        'stderr did not contain 2 "Copying" lines:\n%s' % stderr)
    self.assertLessEqual(
        stderr.count('Copying'), 4,
        'stderr did not contain <= 4 "Copying" lines:\n%s' % stderr)
    self.assertEqual(
        stderr.count('Copying') % 2, 0,
        'stderr did not contain even number of "Copying" lines:\n%s' % stderr)
    self.assertEqual(stderr.count('Removing'), 2,
                     'stderr did not contain 2 "Removing" lines:\n%s' % stderr)

    self.AssertNObjectsInBucket(bucket1_uri, 0)
    self.AssertNObjectsInBucket(bucket2_uri, 2)

    # Remove one of the objects.
    objs = [
        self.StorageUriCloneReplaceKey(bucket2_uri, key).versionless_uri
        for key in bucket2_uri.list_bucket()
    ]
    obj1 = objs[0]
    self.RunGsUtil(['rm', obj1])

    self.AssertNObjectsInBucket(bucket1_uri, 0)
    self.AssertNObjectsInBucket(bucket2_uri, 1)

    # Move the 1 remaining object back.
    objs = [
        suri(self.StorageUriCloneReplaceKey(bucket2_uri, key))
        for key in bucket2_uri.list_bucket()
    ]
    cmd = (['-m', 'mv'] + objs + [suri(bucket1_uri)])
    stderr = self.RunGsUtil(cmd, return_stderr=True)
    # Rewrite API may output an additional 'Copying' progress notification.
    self.assertGreaterEqual(
        stderr.count('Copying'), 1,
        'stderr did not contain >= 1 "Copying" lines:\n%s' % stderr)
    self.assertLessEqual(
        stderr.count('Copying'), 2,
        'stderr did not contain <= 2 "Copying" lines:\n%s' % stderr)
    self.assertEqual(stderr.count('Removing'), 1)

    self.AssertNObjectsInBucket(bucket1_uri, 1)
    self.AssertNObjectsInBucket(bucket2_uri, 0)

  def test_move_bucket_to_dir(self):
    """Tests moving a local directory to a bucket."""
    bucket_uri = self.CreateBucket(test_objects=2)
    self.AssertNObjectsInBucket(bucket_uri, 2)
    tmpdir = self.CreateTempDir()
    self.RunGsUtil(['mv', suri(bucket_uri, '*'), tmpdir])
    dir_list = []
    for dirname, _, filenames in os.walk(tmpdir):
      for filename in filenames:
        dir_list.append(os.path.join(dirname, filename))
    self.assertEqual(len(dir_list), 2)
    self.AssertNObjectsInBucket(bucket_uri, 0)

  def test_move_dir_to_bucket(self):
    """Tests moving a local directory to a bucket."""
    bucket_uri = self.CreateBucket()
    dir_to_move = self.CreateTempDir(test_files=2)
    self.RunGsUtil(['mv', dir_to_move, suri(bucket_uri)])
    self.AssertNObjectsInBucket(bucket_uri, 2)

  @SequentialAndParallelTransfer
  def test_stdin_args(self):
    """Tests mv with the -I option."""
    tmpdir = self.CreateTempDir()
    fpath1 = self.CreateTempFile(tmpdir=tmpdir, contents=b'data1')
    fpath2 = self.CreateTempFile(tmpdir=tmpdir, contents=b'data2')
    bucket_uri = self.CreateBucket()
    self.RunGsUtil(['mv', '-I', suri(bucket_uri)],
                   stdin='\n'.join((fpath1, fpath2)))

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', suri(bucket_uri)], return_stdout=True)
      self.assertIn(os.path.basename(fpath1), stdout)
      self.assertIn(os.path.basename(fpath2), stdout)
      self.assertNumLines(stdout, 2)

    _Check1()

  def test_mv_no_clobber(self):
    """Tests mv with the -n option."""
    fpath1 = self.CreateTempFile(contents=b'data1')
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'data2')
    stderr = self.RunGsUtil(
        ['mv', '-n', fpath1, suri(object_uri)], return_stderr=True)
    # Copy should be skipped and source file should not be removed.
    if self._use_gcloud_storage:
      self.assertIn(
          'Skipping existing destination item (no-clobber): %s' %
          suri(object_uri), stderr)
    else:
      self.assertIn('Skipping existing item: %s' % suri(object_uri), stderr)
    self.assertNotIn('Removing %s' % suri(fpath1), stderr)
    # Object content should be unchanged.
    contents = self.RunGsUtil(['cat', suri(object_uri)], return_stdout=True)
    self.assertEqual(contents, 'data2')

  @unittest.skipIf(IS_WINDOWS, 'POSIX attributes not available on Windows.')
  @unittest.skipUnless(UsingCrcmodExtension(), 'Test requires fast crcmod.')
  def test_mv_preserve_posix_bucket_to_dir_no_errors(self):
    """Tests use of the -P flag with mv from a bucket to a local dir.

    Specifically tests combinations of POSIX attributes in metadata that will
    pass validation.
    """
    bucket_uri = self.CreateBucket()
    tmpdir = self.CreateTempDir()
    TestCpMvPOSIXBucketToLocalNoErrors(self, bucket_uri, tmpdir, is_cp=False)

  @unittest.skipIf(IS_WINDOWS, 'POSIX attributes not available on Windows.')
  def test_mv_preserve_posix_bucket_to_dir_errors(self):
    """Tests use of the -P flag with mv from a bucket to a local dir.

    Specifically, combinations of POSIX attributes in metadata that will fail
    validation.
    """
    bucket_uri = self.CreateBucket()
    tmpdir = self.CreateTempDir()

    obj = self.CreateObject(bucket_uri=bucket_uri,
                            object_name='obj',
                            contents=b'obj')
    TestCpMvPOSIXBucketToLocalErrors(self, bucket_uri, obj, tmpdir, is_cp=False)

  @unittest.skipIf(IS_WINDOWS, 'POSIX attributes not available on Windows.')
  def test_mv_preseve_posix_dir_to_bucket_no_errors(self):
    """Tests use of the -P flag with mv from a local dir to a bucket."""
    bucket_uri = self.CreateBucket()
    TestCpMvPOSIXLocalToBucketNoErrors(self, bucket_uri, is_cp=False)

  @SkipForS3('Test is only relevant for gs storage classes.')
  def test_mv_early_deletion_warning(self):
    """Tests that mv on a recent nearline object warns about early deletion."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip('boto does not return object storage class')

    bucket_uri = self.CreateBucket(storage_class='NEARLINE')
    object_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'obj')
    stderr = self.RunGsUtil(
        ['mv', suri(object_uri),
         suri(bucket_uri, 'foo')], return_stderr=True)
    self.assertIn(
        'Warning: moving nearline object %s may incur an early deletion '
        'charge, because the original object is less than 30 days old '
        'according to the local system time.' % suri(object_uri), stderr)

  def test_move_bucket_objects_with_duplicate_names_to_dir(self):
    """Tests moving multiple top-level items to a bucket."""
    bucket_uri = self.CreateBucket()
    self.CreateObject(bucket_uri=bucket_uri,
                      object_name='dir1/file.txt',
                      contents=b'data')
    self.CreateObject(bucket_uri=bucket_uri,
                      object_name='dir2/file.txt',
                      contents=b'data')
    self.AssertNObjectsInBucket(bucket_uri, 2)

    tmpdir = self.CreateTempDir()
    self.RunGsUtil(['mv', suri(bucket_uri, '*'), tmpdir])

    file_list = []
    for dirname, _, filenames in os.walk(tmpdir):
      for filename in filenames:
        file_list.append(os.path.join(dirname, filename))
    self.assertEqual(len(file_list), 2)
    self.assertIn('{}{}dir1{}file.txt'.format(tmpdir, os.sep, os.sep),
                  file_list)
    self.assertIn('{}{}dir2{}file.txt'.format(tmpdir, os.sep, os.sep),
                  file_list)
    self.AssertNObjectsInBucket(bucket_uri, 0)
