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
"""Unit tests for tracker_file and parallel_tracker_file."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import stat

from gslib.exception import CommandException
from gslib.parallel_tracker_file import ObjectFromTracker
from gslib.parallel_tracker_file import ReadParallelUploadTrackerFile
from gslib.parallel_tracker_file import ValidateParallelCompositeTrackerData
from gslib.parallel_tracker_file import WriteComponentToParallelUploadTrackerFile
from gslib.parallel_tracker_file import WriteParallelUploadTrackerFile
from gslib.storage_url import StorageUrlFromString
from gslib.tests.testcase.unit_testcase import GsUtilUnitTestCase
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.tracker_file import _HashFilename
from gslib.tracker_file import DeleteTrackerFile
from gslib.tracker_file import GetRewriteTrackerFilePath
from gslib.tracker_file import HashRewriteParameters
from gslib.tracker_file import ReadRewriteTrackerFile
from gslib.tracker_file import WriteRewriteTrackerFile
from gslib.utils import parallelism_framework_util
from gslib.utils.constants import UTF8


class TestTrackerFile(GsUtilUnitTestCase):
  """Unit tests for parallel upload functions in cp command."""

  def test_HashFilename(self):
    # Tests that _HashFilename function works for both string and unicode
    # filenames (without raising any Unicode encode/decode errors).
    _HashFilename(b'file1')
    _HashFilename('file1')

  def test_RewriteTrackerFile(self):
    """Tests Rewrite tracker file functions."""
    tracker_file_name = GetRewriteTrackerFilePath('bk1', 'obj1', 'bk2', 'obj2',
                                                  self.test_api)
    # Should succeed regardless of whether it exists.
    DeleteTrackerFile(tracker_file_name)
    src_obj_metadata = apitools_messages.Object(bucket='bk1',
                                                name='obj1',
                                                etag='etag1',
                                                md5Hash='12345')
    src_obj2_metadata = apitools_messages.Object(bucket='bk1',
                                                 name='obj1',
                                                 etag='etag2',
                                                 md5Hash='67890')
    dst_obj_metadata = apitools_messages.Object(bucket='bk2', name='obj2')
    rewrite_token = 'token1'
    self.assertIsNone(
        ReadRewriteTrackerFile(tracker_file_name, src_obj_metadata))
    rewrite_params_hash = HashRewriteParameters(src_obj_metadata,
                                                dst_obj_metadata, 'full')
    WriteRewriteTrackerFile(tracker_file_name, rewrite_params_hash,
                            rewrite_token)
    self.assertEqual(
        ReadRewriteTrackerFile(tracker_file_name, rewrite_params_hash),
        rewrite_token)

    # Tracker file for an updated source object (with non-matching etag/md5)
    # should return None.
    rewrite_params_hash2 = HashRewriteParameters(src_obj2_metadata,
                                                 dst_obj_metadata, 'full')

    self.assertIsNone(
        ReadRewriteTrackerFile(tracker_file_name, rewrite_params_hash2))
    DeleteTrackerFile(tracker_file_name)

  def testReadGsutil416ParallelUploadTrackerFile(self):
    """Tests the parallel upload tracker file format prior to gsutil 4.17."""
    random_prefix = '123'
    objects = ['obj1', '42', 'obj2', '314159']
    contents = '\n'.join([random_prefix] + objects) + '\n'
    fpath = self.CreateTempFile(file_name='foo', contents=contents.encode(UTF8))
    expected_objects = [
        ObjectFromTracker(objects[2 * i], objects[2 * i + 1])
        for i in range(0,
                       len(objects) // 2)
    ]
    (_, actual_prefix,
     actual_objects) = ReadParallelUploadTrackerFile(fpath, self.logger)
    self.assertEqual(random_prefix, actual_prefix)
    self.assertEqual(expected_objects, actual_objects)

  def testReadEmptyGsutil416ParallelUploadTrackerFile(self):
    """Tests reading an empty pre-gsutil 4.17 parallel upload tracker file."""
    fpath = self.CreateTempFile(file_name='foo', contents=b'')
    (_, actual_prefix,
     actual_objects) = ReadParallelUploadTrackerFile(fpath, self.logger)
    self.assertEqual(None, actual_prefix)
    self.assertEqual([], actual_objects)

  def testParallelUploadTrackerFileNoEncryption(self):
    fpath = self.CreateTempFile(file_name='foo')
    random_prefix = '123'
    objects = [
        ObjectFromTracker('obj1', '42'),
        ObjectFromTracker('obj2', '314159')
    ]
    WriteParallelUploadTrackerFile(fpath, random_prefix, objects)
    (enc_key, actual_prefix,
     actual_objects) = ReadParallelUploadTrackerFile(fpath, self.logger)
    self.assertEqual(random_prefix, actual_prefix)
    self.assertEqual(None, enc_key)
    self.assertEqual(objects, actual_objects)

  def testParallelUploadTrackerFileWithEncryption(self):
    fpath = self.CreateTempFile(file_name='foo')
    random_prefix = '123'
    enc_key = '456'
    objects = [
        ObjectFromTracker('obj1', '42'),
        ObjectFromTracker('obj2', '314159')
    ]
    WriteParallelUploadTrackerFile(fpath,
                                   random_prefix,
                                   objects,
                                   encryption_key_sha256=enc_key)
    (actual_key, actual_prefix,
     actual_objects) = ReadParallelUploadTrackerFile(fpath, self.logger)
    self.assertEqual(enc_key, actual_key)
    self.assertEqual(random_prefix, actual_prefix)
    self.assertEqual(objects, actual_objects)

  def testWriteComponentToParallelUploadTrackerFile(self):
    tracker_file_lock = parallelism_framework_util.CreateLock()
    fpath = self.CreateTempFile(file_name='foo')
    random_prefix = '123'
    enc_key = '456'
    objects = [
        ObjectFromTracker('obj1', '42'),
        ObjectFromTracker('obj2', '314159')
    ]
    WriteParallelUploadTrackerFile(fpath,
                                   random_prefix,
                                   objects,
                                   encryption_key_sha256=enc_key)
    new_object = ObjectFromTracker('obj3', '43')
    try:
      WriteComponentToParallelUploadTrackerFile(fpath,
                                                tracker_file_lock,
                                                new_object,
                                                self.logger,
                                                encryption_key_sha256=None)
      self.fail('Expected CommandException due to different encryption key')
    except CommandException as e:
      self.assertIn('does not match encryption key', str(e))

    WriteComponentToParallelUploadTrackerFile(fpath,
                                              tracker_file_lock,
                                              new_object,
                                              self.logger,
                                              encryption_key_sha256='456')

    (actual_key, actual_prefix,
     actual_objects) = ReadParallelUploadTrackerFile(fpath, self.logger)
    self.assertEqual(enc_key, actual_key)
    self.assertEqual(random_prefix, actual_prefix)
    self.assertEqual(objects + [new_object], actual_objects)

  def testValidateParallelCompositeTrackerData(self):
    tempdir = self.CreateTempDir()
    fpath = os.path.join(tempdir, 'foo')
    random_prefix = '123'
    old_enc_key = '456'
    bucket_url = StorageUrlFromString('gs://foo')
    objects = [
        ObjectFromTracker('obj1', '42'),
        ObjectFromTracker('obj2', '314159')
    ]
    WriteParallelUploadTrackerFile(fpath,
                                   random_prefix,
                                   objects,
                                   encryption_key_sha256=old_enc_key)
    # Test the permissions
    if os.name == 'posix':
      mode = oct(stat.S_IMODE(os.stat(fpath).st_mode))
      # Assert that only user has read/write permission
      self.assertEqual(oct(0o600), mode)

    # Mock command object since Valdiate will call Apply() to delete the
    # existing components.
    class MockCommandObject(object):
      delete_called = False

      # We call Apply with parallel_operations_override, which expects this enum
      # class to exist.
      class ParallelOverrideReason(object):
        SPEED = 'speed'

      def Apply(self, *unused_args, **unused_kwargs):
        self.delete_called = True

    def MockDeleteFunc():
      pass

    def MockDeleteExceptionHandler():
      pass

    command_obj = MockCommandObject()
    # Validate with correct key should succeed.
    (actual_prefix, actual_objects) = ValidateParallelCompositeTrackerData(
        fpath, old_enc_key, random_prefix, objects, old_enc_key, bucket_url,
        command_obj, self.logger, MockDeleteFunc, MockDeleteExceptionHandler)
    self.assertEqual(False, command_obj.delete_called)
    self.assertEqual(random_prefix, actual_prefix)
    self.assertEqual(objects, actual_objects)

    new_enc_key = '789'
    command_obj = MockCommandObject()

    (actual_prefix, actual_objects) = ValidateParallelCompositeTrackerData(
        fpath, old_enc_key, random_prefix, objects, new_enc_key, bucket_url,
        command_obj, self.logger, MockDeleteFunc, MockDeleteExceptionHandler)

    self.assertEqual(True, command_obj.delete_called)
    self.assertEqual(None, actual_prefix)
    self.assertEqual([], actual_objects)
