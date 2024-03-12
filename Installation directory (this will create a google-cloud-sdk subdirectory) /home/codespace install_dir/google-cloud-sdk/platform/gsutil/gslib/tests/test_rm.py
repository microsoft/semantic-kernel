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
"""Integration tests for rm command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import re
import sys
from unittest import mock

from gslib.exception import NO_URLS_MATCHED_PREFIX
from gslib.exception import NO_URLS_MATCHED_TARGET
import gslib.tests.testcase as testcase
from gslib.tests.testcase.base import MAX_BUCKET_LENGTH
from gslib.tests.testcase.integration_testcase import SkipForS3
import gslib.tests.util as util
from gslib.tests.util import GenerationFromURI as urigen
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import SetEnvironmentForTest
from gslib.utils import shim_util
from gslib.utils.retry_util import Retry

MACOS_WARNING = (
    'If you experience problems with multiprocessing on MacOS, they might be '
    'related to https://bugs.python.org/issue33725. You can disable '
    'multiprocessing by editing your .boto config or by adding the following '
    'flag to your command: `-o "GSUtil:parallel_process_count=1"`. Note that '
    'multithreading is still available even if you disable multiprocessing.')


class TestRm(testcase.GsUtilIntegrationTestCase):
  """Integration tests for rm command."""

  def _CleanRmUiOutputBeforeChecking(self, stderr):
    """Excludes everything coming from the UI to avoid assert errors.

    Args:
      stderr: The cumulative stderr output.
    Returns:
      The cumulative stderr output without the expected UI output.
    """
    if self._use_gcloud_storage:
      return self._CleanOutputLinesForGcloudStorage(stderr)
    ui_output_pattern = '[^\n\r]*objects][^\n\r]*[\n\r]'
    final_message_pattern = 'Operation completed over[^\n]*'
    ui_spinner_list = ['\\\r', '|\r', '/\r', '-\r']
    ui_lines_list = (re.findall(ui_output_pattern, stderr) +
                     re.findall(final_message_pattern, stderr) +
                     ui_spinner_list)
    for ui_line in ui_lines_list:
      stderr = stderr.replace(ui_line, '')
    return stderr

  def _CleanOutputLinesForGcloudStorage(self, stderr):
    """Remove irrelevant lines from the output lines."""
    stderr_lines = stderr.splitlines()
    valid_lines = []
    strings_to_remove = set(['Removing objects:', 'Removing Buckets:', '  '])
    for line in stderr_lines:
      if line in strings_to_remove:
        continue
      # Gcloud storage logs a '.' for each resource in non-interactive mode.
      # This might get added to the start of a valid line.
      # e.g. ".Removing gs://bucket/obj"
      cleaned_line = line.lstrip('.')
      if cleaned_line:
        valid_lines.append(cleaned_line)
    return os.linesep.join(valid_lines)

  def _RunRemoveCommandAndCheck(self,
                                command_and_args,
                                objects_to_remove=None,
                                buckets_to_remove=None,
                                stdin=None):
    """Tests a remove command in the presence of eventual listing consistency.

    Eventual listing consistency means that a remove command may not see all
    of the objects to be removed at once. When removing multiple objects
    (or buckets via -r), some calls may return no matches and multiple calls
    to the rm command may be necessary to reach the desired state. This function
    retries the rm command, incrementally tracking what has been removed and
    ensuring that the exact set of objects/buckets are removed across all
    retried calls.

    The caller is responsible for confirming the existence of buckets/objects
    prior to calling this function.

    Args:
      command_and_args: List of strings representing the rm command+args to run.
      objects_to_remove: List of object URL strings (optionally including
          generation) that should be removed by the command, if any.
      buckets_to_remove: List of bucket URL strings that should be removed by
         the command, if any.
      stdin: String of data to pipe to the process as standard input (for
         testing -I option).
    """
    bucket_strings = []
    for bucket_to_remove in buckets_to_remove or []:
      bucket_strings.append('Removing %s/...' % bucket_to_remove)
    object_strings = []
    for object_to_remove in objects_to_remove or []:
      object_strings.append('Removing %s...' % object_to_remove)
    expected_stderr_lines = set(object_strings + bucket_strings)

    if not self.multiregional_buckets and self.default_provider == 'gs':
      stderr = self.RunGsUtil(command_and_args,
                              return_stderr=True,
                              expected_status=None,
                              stdin=stdin)
      num_objects = len(object_strings)
      # Asserting for operation completion
      if '-q' not in command_and_args and not self._use_gcloud_storage:
        if '-m' in command_and_args:
          self.assertIn('[%d/%d objects]' % (num_objects, num_objects), stderr)
        else:
          self.assertIn('[%d objects]' % num_objects, stderr)

      stderr = self._CleanRmUiOutputBeforeChecking(stderr)
      stderr_set = set(stderr.splitlines())
      if '' in stderr_set:
        stderr_set.remove('')  # Avoid groups represented by an empty string.
      if MACOS_WARNING in stderr_set:
        stderr_set.remove(MACOS_WARNING)
      self.assertEqual(stderr_set, expected_stderr_lines)
    else:
      cumulative_stderr_lines = set()

      @Retry(AssertionError, tries=5, timeout_secs=1)
      def _RunRmCommandAndCheck():
        """Runs/retries the command updating+checking cumulative output."""
        stderr = self.RunGsUtil(command_and_args,
                                return_stderr=True,
                                expected_status=None,
                                stdin=stdin)
        stderr = self._CleanRmUiOutputBeforeChecking(stderr)
        update_lines = True
        # Retry 404's and 409's due to eventual listing consistency, but don't
        # add the output to the set.
        if (NO_URLS_MATCHED_PREFIX in stderr or
            '409 BucketNotEmpty' in stderr or
            '409 VersionedBucketNotEmpty' in stderr):
          update_lines = False

        # For recursive deletes of buckets, it is possible that the bucket is
        # deleted before the objects are all present in the listing, in which
        # case we will never see all of the expected "Removing object..."
        # messages. Since this is still a successful outcome, just return
        # successfully.
        if self._use_gcloud_storage:
          bucket_not_found_string = 'not found'
        else:
          bucket_not_found_string = 'bucket does not exist'
        if '-r' in command_and_args and 'bucket does not exist' in stderr:
          for bucket_to_remove in buckets_to_remove:
            matching_bucket = re.match(
                r'.*404\s+%s\s+bucket does not exist' %
                re.escape(bucket_to_remove), stderr)
            if matching_bucket:
              for line in cumulative_stderr_lines:
                if 'Removing %s/...' % bucket_to_remove in line:
                  return
              if 'Removing %s/...' % bucket_to_remove in stderr:
                return

        if update_lines:
          cumulative_stderr_lines.update(
              set([s for s in stderr.splitlines() if s]))

        # Ensure all of the expected strings are present.
        self.assertEqual(cumulative_stderr_lines, expected_stderr_lines)

      _RunRmCommandAndCheck()

  def test_all_versions_current(self):
    """Test that 'rm -a' for an object with a current version works."""
    bucket_uri = self.CreateVersionedBucket()
    key_uri = self.StorageUriCloneReplaceName(bucket_uri, 'foo')
    self.StorageUriSetContentsFromString(key_uri, 'bar')
    g1 = urigen(key_uri)
    self.StorageUriSetContentsFromString(key_uri, 'baz')
    g2 = urigen(key_uri)

    def _Check1(stderr_lines):
      stderr = self.RunGsUtil(
          ['-m', 'rm', '-a', suri(key_uri)], return_stderr=True)
      stderr_lines.update(set(stderr.splitlines()))
      stderr = '\n'.join(stderr_lines)
      self.assertEqual(stderr.count('Removing %s://' % self.default_provider),
                       2)
      self.assertIn('Removing %s#%s...' % (suri(key_uri), g1), stderr)
      self.assertIn('Removing %s#%s...' % (suri(key_uri), g2), stderr)

    all_stderr_lines = set()
    if self.multiregional_buckets:
      self.AssertNObjectsInBucket(bucket_uri, 2, versioned=True)

      @Retry(AssertionError, tries=3, timeout_secs=1)
      # Use @Retry as hedge against bucket listing eventual consistency.
      def _CheckWithRetries(stderr_lines):
        _Check1(stderr_lines)

      _CheckWithRetries(all_stderr_lines)
    else:
      _Check1(all_stderr_lines)

    self.AssertNObjectsInBucket(bucket_uri, 0, versioned=True)

  def test_all_versions_no_current(self):
    """Test that 'rm -a' for an object without a current version works."""
    bucket_uri = self.CreateVersionedBucket()
    key_uri = self.StorageUriCloneReplaceName(bucket_uri, 'foo')
    self.StorageUriSetContentsFromString(key_uri, 'bar')
    g1 = urigen(key_uri)
    self.StorageUriSetContentsFromString(key_uri, 'baz')
    g2 = urigen(key_uri)
    self._RunRemoveCommandAndCheck(
        ['-m', 'rm', '-a', suri(key_uri)],
        objects_to_remove=[
            '%s#%s' % (suri(key_uri), g1),
            '%s#%s' % (suri(key_uri), g2)
        ])
    self.AssertNObjectsInBucket(bucket_uri, 0, versioned=True)

  def test_fails_for_missing_obj(self):
    bucket_uri = self.CreateVersionedBucket()
    stderr = self.RunGsUtil(
        ['rm', '-a', '%s' % suri(bucket_uri, 'foo')],
        return_stderr=True,
        expected_status=1)
    if self._use_gcloud_storage:
      no_url_matched_target = no_url_matched_target = (
          'The following URLs matched no objects or files:\n-%s')
    else:
      no_url_matched_target = NO_URLS_MATCHED_TARGET
    self.assertIn(no_url_matched_target % suri(bucket_uri, 'foo'), stderr)

  def test_remove_recursive_prefix(self):
    bucket_uri = self.CreateBucket()
    obj_uri = self.CreateObject(bucket_uri=bucket_uri,
                                object_name='a/b/c',
                                contents=b'foo')
    if self.multiregional_buckets:
      self.AssertNObjectsInBucket(bucket_uri, 1)

    stderr = self.RunGsUtil(['rm', '-r', suri(bucket_uri, 'a')],
                            return_stderr=True)
    self.assertIn('Removing %s' % suri(obj_uri), stderr)

  def test_remove_all_versions_recursive_on_bucket(self):
    """Test that 'rm -r' works on bucket."""
    bucket_uri = self.CreateVersionedBucket()
    k1_uri = self.StorageUriCloneReplaceName(bucket_uri, 'foo')
    k2_uri = self.StorageUriCloneReplaceName(bucket_uri, 'foo2')
    self.StorageUriSetContentsFromString(k1_uri, 'bar')
    self.StorageUriSetContentsFromString(k2_uri, 'bar2')
    k1g1 = urigen(k1_uri)
    k2g1 = urigen(k2_uri)
    self.StorageUriSetContentsFromString(k1_uri, 'baz')
    self.StorageUriSetContentsFromString(k2_uri, 'baz2')
    k1g2 = urigen(k1_uri)
    k2g2 = urigen(k2_uri)

    if self.multiregional_buckets:
      self.AssertNObjectsInBucket(bucket_uri, 4, versioned=True)

    self._RunRemoveCommandAndCheck(['rm', '-r', suri(bucket_uri)],
                                   objects_to_remove=[
                                       '%s#%s' % (suri(k1_uri), k1g1),
                                       '%s#%s' % (suri(k1_uri), k1g2),
                                       '%s#%s' % (suri(k2_uri), k2g1),
                                       '%s#%s' % (suri(k2_uri), k2g2)
                                   ],
                                   buckets_to_remove=[suri(bucket_uri)])

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check():
      # Bucket should no longer exist.
      stderr = self.RunGsUtil(['ls', '-a', suri(bucket_uri)],
                              return_stderr=True,
                              expected_status=1)
      if self._use_gcloud_storage:
        if self._use_gcloud_storage:
          # GCS and S3 responses.
          self.assertTrue('not found: 404' in stderr or
                          'NoSuchBucket' in stderr)
      else:
        self.assertIn('bucket does not exist', stderr)

    _Check()

  def test_remove_all_versions_recursive_on_subdir(self):
    """Test that 'rm -r' works on subdir."""
    bucket_uri = self.CreateVersionedBucket()
    k1_uri = self.StorageUriCloneReplaceName(bucket_uri, 'dir/foo')
    k2_uri = self.StorageUriCloneReplaceName(bucket_uri, 'dir/foo2')
    self.StorageUriSetContentsFromString(k1_uri, 'bar')
    self.StorageUriSetContentsFromString(k2_uri, 'bar2')
    k1g1 = urigen(k1_uri)
    k2g1 = urigen(k2_uri)
    self.StorageUriSetContentsFromString(k1_uri, 'baz')
    self.StorageUriSetContentsFromString(k2_uri, 'baz2')
    k1g2 = urigen(k1_uri)
    k2g2 = urigen(k2_uri)

    if self.multiregional_buckets:
      self.AssertNObjectsInBucket(bucket_uri, 4, versioned=True)

    self._RunRemoveCommandAndCheck(
        ['rm', '-r', '%s' % suri(bucket_uri, 'dir')],
        objects_to_remove=[
            '%s#%s' % (suri(k1_uri), k1g1),
            '%s#%s' % (suri(k1_uri), k1g2),
            '%s#%s' % (suri(k2_uri), k2g1),
            '%s#%s' % (suri(k2_uri), k2g2)
        ])
    self.AssertNObjectsInBucket(bucket_uri, 0, versioned=True)

  def test_rm_seek_ahead(self):
    object_uri = self.CreateObject(contents=b'foo')
    with SetBotoConfigForTest([('GSUtil', 'task_estimation_threshold', '1'),
                               ('GSUtil', 'task_estimation_force', 'True')]):
      stderr = self.RunGsUtil(['-m', 'rm', suri(object_uri)],
                              return_stderr=True)
      self.assertIn('Estimated work for this command: objects: 1\n', stderr)

  def test_rm_seek_ahead_stdin_args(self):
    object_uri = self.CreateObject(contents=b'foo')
    with SetBotoConfigForTest([('GSUtil', 'task_estimation_threshold', '1'),
                               ('GSUtil', 'task_estimation_force', 'True')]):
      stderr = self.RunGsUtil(['-m', 'rm', '-I'],
                              stdin=suri(object_uri),
                              return_stderr=True)
      self.assertNotIn('Estimated work', stderr)

  def test_missing_first_force(self):
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='present',
                                   contents=b'foo')
    if self.multiregional_buckets:
      self.AssertNObjectsInBucket(bucket_uri, 1)
    if not self._use_gcloud_storage:
      # Gcloud storage continues on missing objects by default.
      # So we will skip running this for gcloud storage.
      self.RunGsUtil(
          ['rm', '%s' % suri(bucket_uri, 'missing'),
           suri(object_uri)],
          expected_status=1)
    stderr = self.RunGsUtil(
        ['rm', '-f',
         '%s' % suri(bucket_uri, 'missing'),
         suri(object_uri)],
        return_stderr=True,
        expected_status=1)
    self.assertEqual(stderr.count('Removing %s://' % self.default_provider), 1)
    self.RunGsUtil(['stat', suri(object_uri)], expected_status=1)

  def test_some_missing(self):
    """Test that 'rm -a' fails when some but not all uris don't exist."""
    bucket_uri = self.CreateVersionedBucket()
    key_uri = self.StorageUriCloneReplaceName(bucket_uri, 'foo')
    self.StorageUriSetContentsFromString(key_uri, 'bar')
    if self.multiregional_buckets:
      self.AssertNObjectsInBucket(bucket_uri, 1, versioned=True)
    stderr = self.RunGsUtil(
        ['rm', '-a',
         suri(key_uri),
         '%s' % suri(bucket_uri, 'missing')],
        return_stderr=True,
        expected_status=1)
    self.assertEqual(stderr.count('Removing %s://' % self.default_provider), 1)
    if self._use_gcloud_storage:
      self.assertIn(
          'The following URLs matched no objects or files:\n-%s' %
          suri(bucket_uri, 'missing'), stderr)
    else:
      self.assertIn(NO_URLS_MATCHED_TARGET % suri(bucket_uri, 'missing'),
                    stderr)

  def test_some_missing_force(self):
    """Test that 'rm -af' succeeds despite hidden first uri."""
    bucket_uri = self.CreateVersionedBucket()
    key_uri = self.StorageUriCloneReplaceName(bucket_uri, 'foo')
    self.StorageUriSetContentsFromString(key_uri, 'bar')
    if self.multiregional_buckets:
      self.AssertNObjectsInBucket(bucket_uri, 1, versioned=True)
    stderr = self.RunGsUtil(
        ['rm', '-af',
         suri(key_uri),
         '%s' % suri(bucket_uri, 'missing')],
        return_stderr=True,
        expected_status=1)
    self.assertEqual(stderr.count('Removing %s://' % self.default_provider), 1)
    self.AssertNObjectsInBucket(bucket_uri, 0)

  def test_folder_objects_deleted(self):
    """Test for 'rm -r' of a folder with a dir_$folder$ marker."""
    bucket_uri = self.CreateVersionedBucket()
    key_uri = self.StorageUriCloneReplaceName(bucket_uri, 'abc/o1')
    self.StorageUriSetContentsFromString(key_uri, 'foobar')
    folder_uri = self.StorageUriCloneReplaceName(bucket_uri, 'abc_$folder$')
    self.StorageUriSetContentsFromString(folder_uri, '')

    def _RemoveAndCheck():
      self.RunGsUtil(['rm', '-r', '%s' % suri(bucket_uri, 'abc')],
                     expected_status=None)
      self.AssertNObjectsInBucket(bucket_uri, 0, versioned=True)

    if self.multiregional_buckets:
      self.AssertNObjectsInBucket(bucket_uri, 2, versioned=True)
      # This could fail due to eventual listing consistency, so use retry and
      # expected_status=None to guard against No URLs matched exceptions.
      @Retry(AssertionError, tries=3, timeout_secs=1)
      def _RemoveAndCheckWrapper():
        _RemoveAndCheck()

      _RemoveAndCheckWrapper()
    else:
      _RemoveAndCheck()
    # Bucket should not be deleted (Should not get ServiceException).
    bucket_uri.get_location(validate=False)

  def test_folder_objects_deleted_with_wildcard(self):
    """Test for 'rm -r' of a folder with a dir_$folder$ marker."""
    bucket_uri = self.CreateVersionedBucket()
    key_uri = self.StorageUriCloneReplaceName(bucket_uri, 'abc/o1')
    self.StorageUriSetContentsFromString(key_uri, 'foobar')
    folder_uri = self.StorageUriCloneReplaceName(bucket_uri, 'abc_$folder$')
    self.StorageUriSetContentsFromString(folder_uri, '')

    if self.multiregional_buckets:
      self.AssertNObjectsInBucket(bucket_uri, 2, versioned=True)
    self._RunRemoveCommandAndCheck(
        ['rm', '-r', '%s' % suri(bucket_uri, '*')],
        objects_to_remove=[
            '%s#%s' % (suri(key_uri), urigen(key_uri)),
            '%s#%s' % (suri(folder_uri), urigen(folder_uri))
        ])
    self.AssertNObjectsInBucket(bucket_uri, 0, versioned=True)
    # Bucket should not be deleted (Should not get ServiceException).
    bucket_uri.get_location(validate=False)

  def test_folder_objects_deleted_with_double_wildcard(self):
    """Test for 'rm -r' of a folder with a dir_$folder$ marker."""
    bucket_uri = self.CreateVersionedBucket()
    key_uri = self.StorageUriCloneReplaceName(bucket_uri, 'abc/o1')
    self.StorageUriSetContentsFromString(key_uri, 'foobar')
    folder_uri = self.StorageUriCloneReplaceName(bucket_uri, 'abc_$folder$')
    self.StorageUriSetContentsFromString(folder_uri, '')

    if self.multiregional_buckets:
      self.AssertNObjectsInBucket(bucket_uri, 2, versioned=True)
    self._RunRemoveCommandAndCheck(
        ['rm', '-r', '%s' % suri(bucket_uri, '**')],
        objects_to_remove=[
            '%s#%s' % (suri(key_uri), urigen(key_uri)),
            '%s#%s' % (suri(folder_uri), urigen(folder_uri))
        ])
    self.AssertNObjectsInBucket(bucket_uri, 0, versioned=True)
    # Bucket should not be deleted (Should not get ServiceException).
    bucket_uri.get_location(validate=False)

  @SkipForS3('Listing/removing S3 DeleteMarkers is not supported')
  def test_recursive_bucket_rm(self):
    """Test for 'rm -r' of a bucket."""
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri, contents=b'foo')
    if self.multiregional_buckets:
      self.AssertNObjectsInBucket(bucket_uri, 1)
    self._RunRemoveCommandAndCheck(
        ['rm', '-r', suri(bucket_uri)],
        objects_to_remove=['%s#%s' % (suri(object_uri), urigen(object_uri))],
        buckets_to_remove=[suri(bucket_uri)])

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      # Bucket should be deleted.
      stderr = self.RunGsUtil(['ls', '-Lb', suri(bucket_uri)],
                              return_stderr=True,
                              expected_status=1,
                              force_gsutil=True)
      self.assertIn('bucket does not exist', stderr)

    _Check1()

    # Now try same thing, but for a versioned bucket with multiple versions of
    # an object present.
    bucket_uri = self.CreateVersionedBucket()
    self.CreateObject(bucket_uri, 'obj', contents=b'z')
    self.CreateObject(bucket_uri, 'obj', contents=b'z')
    final_uri = self.CreateObject(bucket_uri, 'obj', contents=b'z')
    if self.multiregional_buckets:
      self.AssertNObjectsInBucket(bucket_uri, 3, versioned=True)
    self._RunRemoveCommandAndCheck(['rm', suri(bucket_uri, '**')],
                                   objects_to_remove=['%s' % final_uri])

    stderr = self.RunGsUtil(['rb', suri(bucket_uri)],
                            return_stderr=True,
                            expected_status=1,
                            force_gsutil=True)
    self.assertIn('not empty', stderr)

    # Now try with rm -r.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check2():
      self.RunGsUtil(['rm', '-r', suri(bucket_uri)])
      # Bucket should be deleted.
      stderr = self.RunGsUtil(['ls', '-Lb', suri(bucket_uri)],
                              return_stderr=True,
                              expected_status=1,
                              force_gsutil=True)
      self.assertIn('bucket does not exist', stderr)

    _Check2()

  def test_recursive_bucket_rm_with_wildcarding(self):
    """Tests removing all objects and buckets matching a bucket wildcard."""
    buri_base = 'gsutil-test-%s' % self.GetTestMethodName()
    buri_base = buri_base[:MAX_BUCKET_LENGTH - 20]
    buri_base = '%s-%s' % (buri_base, self.MakeRandomTestString())
    buri_base = 'aaa-' + buri_base
    buri_base = util.MakeBucketNameValid(buri_base)
    buri1 = self.CreateBucket(bucket_name='%s-tbuck1' % buri_base)
    buri2 = self.CreateBucket(bucket_name='%s-tbuck2' % buri_base)
    buri3 = self.CreateBucket(bucket_name='%s-tb3' % buri_base)
    ouri1 = self.CreateObject(bucket_uri=buri1, object_name='o1', contents=b'z')
    ouri2 = self.CreateObject(bucket_uri=buri2, object_name='o2', contents=b'z')
    self.CreateObject(bucket_uri=buri3, object_name='o3', contents=b'z')

    if self.multiregional_buckets:
      self.AssertNObjectsInBucket(buri1, 1)
      self.AssertNObjectsInBucket(buri2, 1)
      self.AssertNObjectsInBucket(buri3, 1)

    self._RunRemoveCommandAndCheck(
        ['rm', '-r',
         '%s://%s-tbu*' % (self.default_provider, buri_base)],
        objects_to_remove=[
            '%s#%s' % (suri(ouri1), urigen(ouri1)),
            '%s#%s' % (suri(ouri2), urigen(ouri2))
        ],
        buckets_to_remove=[suri(buri1), suri(buri2)])

    self.AssertNObjectsInBucket(buri3, 1)

  def test_rm_quiet(self):
    """Test that 'rm -q' outputs no progress indications."""
    bucket_uri = self.CreateBucket()
    key_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'foo')
    if self.multiregional_buckets:
      self.AssertNObjectsInBucket(bucket_uri, 1)
    self._RunRemoveCommandAndCheck(['-q', 'rm', suri(key_uri)], [])
    self.AssertNObjectsInBucket(bucket_uri, 0)

  @SkipForS3('The boto lib used for S3 does not handle objects '
             'starting with slashes if we use V4 signature')
  def test_rm_object_with_prefix_slash(self):
    """Tests removing a bucket that has an object starting with slash.

    The boto lib used for S3 does not handle objects starting with slashes
    if we use V4 signature. Hence we are testing objects with prefix
    slashes separately.
    """
    bucket_uri = self.CreateVersionedBucket()
    ouri1 = self.CreateObject(bucket_uri=bucket_uri,
                              object_name='/dirwithslash/foo',
                              contents=b'z')
    if self.multiregional_buckets:
      self.AssertNObjectsInBucket(bucket_uri, 1, versioned=True)

    self._RunRemoveCommandAndCheck(
        ['rm', '-r', suri(bucket_uri)],
        objects_to_remove=['%s#%s' % (suri(ouri1), urigen(ouri1))],
        buckets_to_remove=[suri(bucket_uri)])

  def test_rm_object_with_slashes(self):
    """Tests removing a bucket that has objects with slashes."""
    bucket_uri = self.CreateVersionedBucket()
    ouri1 = self.CreateObject(bucket_uri=bucket_uri,
                              object_name='h/e/l//lo',
                              contents=b'z')
    ouri2 = self.CreateObject(bucket_uri=bucket_uri,
                              object_name='dirnoslash/foo',
                              contents=b'z')
    ouri3 = self.CreateObject(bucket_uri=bucket_uri,
                              object_name='dirnoslash/foo2',
                              contents=b'z')
    if self.multiregional_buckets:
      self.AssertNObjectsInBucket(bucket_uri, 3, versioned=True)

    self._RunRemoveCommandAndCheck(['rm', '-r', suri(bucket_uri)],
                                   objects_to_remove=[
                                       '%s#%s' % (suri(ouri1), urigen(ouri1)),
                                       '%s#%s' % (suri(ouri2), urigen(ouri2)),
                                       '%s#%s' % (suri(ouri3), urigen(ouri3))
                                   ],
                                   buckets_to_remove=[suri(bucket_uri)])

  @SkipForS3('The boto lib used for S3 does not handle objects '
             'starting with slashes if we use V4 signature')
  def test_slasher_horror_film(self):
    """Tests removing a bucket with objects that are filled with slashes."""
    bucket_uri = self.CreateVersionedBucket()
    ouri1 = self.CreateObject(bucket_uri=bucket_uri,
                              object_name='h/e/l//lo',
                              contents=b'Halloween')
    ouri2 = self.CreateObject(bucket_uri=bucket_uri,
                              object_name='/h/e/l/l/o',
                              contents=b'A Nightmare on Elm Street')
    ouri3 = self.CreateObject(bucket_uri=bucket_uri,
                              object_name='//h//e/l//l/o',
                              contents=b'Friday the 13th')
    ouri4 = self.CreateObject(bucket_uri=bucket_uri,
                              object_name='//h//e//l//l//o',
                              contents=b'I Know What You Did Last Summer')
    ouri5 = self.CreateObject(bucket_uri=bucket_uri,
                              object_name='/',
                              contents=b'Scream')
    ouri6 = self.CreateObject(bucket_uri=bucket_uri,
                              object_name='//',
                              contents=b'Child\'s Play')
    ouri7 = self.CreateObject(bucket_uri=bucket_uri,
                              object_name='///',
                              contents=b'The Prowler')
    ouri8 = self.CreateObject(bucket_uri=bucket_uri,
                              object_name='////',
                              contents=b'Black Christmas')
    ouri9 = self.CreateObject(
        bucket_uri=bucket_uri,
        object_name='everything/is/better/with/slashes///////',
        contents=b'Maniac')

    if self.multiregional_buckets:
      self.AssertNObjectsInBucket(bucket_uri, 9, versioned=True)

    # We add a slash to URIs with a trailing slash,
    # because ObjectToURI (suri) removes one trailing slash.
    objects_to_remove = [
        '%s#%s' % (suri(ouri1), urigen(ouri1)),
        '%s#%s' % (suri(ouri2), urigen(ouri2)),
        '%s#%s' % (suri(ouri3), urigen(ouri3)),
        '%s#%s' % (suri(ouri4), urigen(ouri4)),
        '%s#%s' % (suri(ouri5) + '/', urigen(ouri5)),
        '%s#%s' % (suri(ouri6) + '/', urigen(ouri6)),
        '%s#%s' % (suri(ouri7) + '/', urigen(ouri7)),
        '%s#%s' % (suri(ouri8) + '/', urigen(ouri8)),
        '%s#%s' % (suri(ouri9) + '/', urigen(ouri9))
    ]

    self._RunRemoveCommandAndCheck(
        ['-m', 'rm', '-r', suri(bucket_uri)],
        objects_to_remove=objects_to_remove,
        buckets_to_remove=[suri(bucket_uri)])

  @SkipForS3('GCS versioning headers not supported by S3')
  def test_rm_failing_precondition(self):
    """Test for '-h x-goog-if-generation-match:value rm' of an object."""
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri, contents=b'foo')
    stderr = self.RunGsUtil(
        ['-h', 'x-goog-if-generation-match:12345', 'rm',
         suri(object_uri)],
        return_stderr=True,
        expected_status=1)
    if self._use_gcloud_storage:
      self.assertRegex(stderr, r'pre-conditions you specified did not hold')
    else:
      self.assertRegex(stderr, r'PreconditionException: 412')

  def test_stdin_args(self):
    """Tests rm with the -I option."""
    buri1 = self.CreateVersionedBucket()
    ouri1 = self.CreateObject(bucket_uri=buri1,
                              object_name='foo',
                              contents=b'foocontents')
    self.CreateObject(bucket_uri=buri1,
                      object_name='bar',
                      contents=b'barcontents')
    ouri3 = self.CreateObject(bucket_uri=buri1,
                              object_name='baz',
                              contents=b'bazcontents')
    buri2 = self.CreateVersionedBucket()
    ouri4 = self.CreateObject(bucket_uri=buri2,
                              object_name='moo',
                              contents=b'moocontents')
    if self.multiregional_buckets:
      self.AssertNObjectsInBucket(buri1, 3, versioned=True)
      self.AssertNObjectsInBucket(buri2, 1, versioned=True)

    objects_to_remove = [
        '%s#%s' % (suri(ouri1), urigen(ouri1)),
        '%s#%s' % (suri(ouri3), urigen(ouri3)),
        '%s#%s' % (suri(ouri4), urigen(ouri4))
    ]
    stdin = '\n'.join(objects_to_remove)
    self._RunRemoveCommandAndCheck(['rm', '-I'],
                                   objects_to_remove=objects_to_remove,
                                   stdin=stdin)
    self.AssertNObjectsInBucket(buri1, 1, versioned=True)
    self.AssertNObjectsInBucket(buri2, 0, versioned=True)

  def test_rm_nonexistent_bucket_recursive(self):
    stderr = self.RunGsUtil([
        'rm', '-rf',
        '%s://%s' % (self.default_provider, self.nonexistent_bucket_name)
    ],
                            return_stderr=True,
                            expected_status=1)
    if self._use_gcloud_storage:
      # GCS and S3 responses.
      self.assertTrue('not found: 404' in stderr or 'NoSuchBucket' in stderr)
    else:
      self.assertIn('Encountered non-existent bucket', stderr)

  def test_rm_multiple_nonexistent_objects(self):
    bucket_uri = self.CreateBucket()
    nonexistent_object1 = suri(bucket_uri, 'nonexistent1')
    nonexistent_object2 = suri(bucket_uri, 'nonexistent2')
    stderr = self.RunGsUtil(
        ['rm', '-rf', nonexistent_object1, nonexistent_object2],
        return_stderr=True,
        expected_status=1)
    if self._use_gcloud_storage:
      self.assertIn(
          'The following URLs matched no objects or files:\n-{}\n-{}'.format(
              nonexistent_object1, nonexistent_object2), stderr)
    else:
      self.assertIn('2 files/objects could not be removed.', stderr)


class TestRmUnitTests(testcase.GsUtilUnitTestCase):
  """Unit tests for gsutil rm."""

  def test_shim_translates_flags(self):
    bucket_uri = self.CreateBucket()
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand(
            'rm',
            ['-r', '-R', '-a', '-f', suri(bucket_uri)],
            return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            'Gcloud Storage Command: {} storage rm'
            ' -r -r -a --continue-on-error {}'.format(
                shim_util._get_gcloud_binary_path('fake_dir'),
                suri(bucket_uri)), info_lines)

  @mock.patch.object(sys, 'stdin')
  def test_shim_translates_stdin_flag(self, mock_stdin):
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri, 'foo', 'abcd')
    mock_stdin.__iter__.return_value = [suri(object_uri)]
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):

        mock_log_handler = self.RunCommand('rm', ['-I'],
                                           return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            'Gcloud Storage Command: {} storage rm'
            ' -I'.format(shim_util._get_gcloud_binary_path('fake_dir')),
            info_lines)
