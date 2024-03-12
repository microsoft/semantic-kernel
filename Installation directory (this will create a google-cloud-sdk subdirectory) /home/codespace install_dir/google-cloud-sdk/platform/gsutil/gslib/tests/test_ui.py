# -*- coding: utf-8 -*-
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for gsutil UI functions."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import pickle

import crcmod
import six
from six.moves import queue as Queue

from gslib.cs_api_map import ApiSelector
from gslib.parallel_tracker_file import ObjectFromTracker
from gslib.parallel_tracker_file import WriteParallelUploadTrackerFile
from gslib.storage_url import StorageUrlFromString
import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.util import HaltingCopyCallbackHandler
from gslib.tests.util import HaltOneComponentCopyCallbackHandler
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import TailSet
from gslib.tests.util import TEST_ENCRYPTION_KEY1
from gslib.tests.util import TEST_ENCRYPTION_KEY2
from gslib.tests.util import unittest
from gslib.thread_message import FileMessage
from gslib.thread_message import FinalMessage
from gslib.thread_message import MetadataMessage
from gslib.thread_message import ProducerThreadMessage
from gslib.thread_message import ProgressMessage
from gslib.thread_message import SeekAheadMessage
from gslib.tracker_file import DeleteTrackerFile
from gslib.tracker_file import GetSlicedDownloadTrackerFilePaths
from gslib.tracker_file import GetTrackerFilePath
from gslib.tracker_file import TrackerFileType
from gslib.ui_controller import BytesToFixedWidthString
from gslib.ui_controller import DataManager
from gslib.ui_controller import MainThreadUIQueue
from gslib.ui_controller import MetadataManager
from gslib.ui_controller import UIController
from gslib.ui_controller import UIThread
from gslib.utils.boto_util import UsingCrcmodExtension
from gslib.utils.constants import START_CALLBACK_PER_BYTES
from gslib.utils.constants import UTF8
from gslib.utils.copy_helper import PARALLEL_UPLOAD_STATIC_SALT
from gslib.utils.copy_helper import PARALLEL_UPLOAD_TEMP_NAMESPACE
from gslib.utils.hashing_helper import GetMd5
from gslib.utils.parallelism_framework_util import PutToQueueWithTimeout
from gslib.utils.parallelism_framework_util import ZERO_TASKS_TO_DO_ARGUMENT
from gslib.utils.retry_util import Retry
from gslib.utils.unit_util import HumanReadableWithDecimalPlaces
from gslib.utils.unit_util import MakeHumanReadable
from gslib.utils.unit_util import ONE_KIB

DOWNLOAD_SIZE = 300
UPLOAD_SIZE = 400
# Ensures at least one progress callback is made
HALT_SIZE = START_CALLBACK_PER_BYTES * 2
# After waiting this long, assume the UIThread is hung.
THREAD_WAIT_TIME = 5


def JoinThreadAndRaiseOnTimeout(ui_thread, thread_wait_time=THREAD_WAIT_TIME):
  """Joins the ui_thread and ensures it has not timed out.

  Args:
    ui_thread: the UIThread to be joined.
    thread_wait_time: the time to wait to join
  Raises:
    Exception: Warns UIThread is still alive.
  """
  ui_thread.join(thread_wait_time)
  if ui_thread.is_alive():
    raise Exception('UIThread is still alive')


def _FindAppropriateDescriptionString(metadata):
  """Returns the correspondent string (objects or files) for the operation type.

  Args:
    metadata: Describes whether this is a metadata operation.
  Returns:
    ' objects' if a metadata operation; ' files' otherwise.
  """
  return ' objects' if metadata else ' files'


# TODO: migrate CheckUiOutput functions to integration_testcase
# and call them directly from the adapted tests so we do not have to duplicate
# code.
def CheckUiOutputWithMFlag(test_case,
                           content,
                           num_objects,
                           total_size=0,
                           metadata=False):
  """Checks if the UI output works as expected with the -m flag enabled.

  Args:
    test_case: Testcase used to maintain the same assert structure.
    content: The output provided by the UI.
    num_objects: The number of objects processed.
    total_size: The total size transferred in the operation. Used for data
                operations only.
    metadata: Indicates whether this is a metadata operation.
  """
  description_string = _FindAppropriateDescriptionString(metadata)
  # We must have transferred 100% of our data.
  test_case.assertIn('100% Done', content)
  # All files should be completed.
  files_completed_string = str(num_objects) + '/' + str(num_objects)
  test_case.assertIn(files_completed_string + description_string, content)
  final_message = 'Operation completed over %s objects' % num_objects
  if not metadata:
    # The total_size must also been successfully transferred.
    total_size_string = BytesToFixedWidthString(total_size)
    test_case.assertIn(total_size_string + '/' + total_size_string, content)
    final_message += '/%s' % HumanReadableWithDecimalPlaces(total_size)
  test_case.assertIn(final_message, content)


def CheckUiOutputWithNoMFlag(test_case,
                             content,
                             num_objects,
                             total_size=0,
                             metadata=False):
  """Checks if the UI output works as expected with the -m flag not enabled.

  Args:
    test_case: Testcase used to maintain the same assert structure.
    content: The output provided by the UI.
    num_objects: The number of objects processed.
    total_size: The total size transferred in the operation. Used for data
                operations only.
    metadata: Indicates whether this is a metadata operation.
  """
  description_string = _FindAppropriateDescriptionString(metadata)
  # All files should be completed.
  files_completed_string = str(num_objects)
  test_case.assertIn(files_completed_string + description_string, content)
  final_message = 'Operation completed over %s objects' % num_objects
  if not metadata:
    # The total_size must also been successfully transferred.
    total_size_string = BytesToFixedWidthString(total_size)
    test_case.assertIn(total_size_string + '/' + total_size_string, content)
    final_message += '/%s' % HumanReadableWithDecimalPlaces(total_size)
  test_case.assertIn(final_message, content)


def CheckBrokenUiOutputWithMFlag(test_case,
                                 content,
                                 num_objects,
                                 total_size=0,
                                 metadata=False):
  """Checks if the UI output fails as expected with the -m flag enabled.

  Args:
    test_case: Testcase used to maintain the same assert structure.
    content: The output provided by the UI.
    num_objects: The number of objects processed.
    total_size: The total size transferred in the operation. Used for data
                operations only.
    metadata: Indicates whether this is a metadata operation.
  """
  description_string = _FindAppropriateDescriptionString(metadata)
  # We must not have transferred 100% of our data.
  test_case.assertNotIn('100% Done', content)
  # We cannot have completed a file.
  files_completed_string = str(num_objects) + '/' + str(num_objects)
  test_case.assertNotIn(files_completed_string + description_string, content)
  if not metadata:
    total_size_string = BytesToFixedWidthString(total_size)
    zero = BytesToFixedWidthString(0)
    # Zero bytes must have been transferred in the beginning.
    test_case.assertIn(zero + '/' + total_size_string, content)
    # The total_size must have not been successfully transferred.
    test_case.assertNotIn(total_size_string + '/' + total_size_string, content)
  final_message_prefix = 'Operation completed over'
  test_case.assertNotIn(final_message_prefix, content)


def CheckBrokenUiOutputWithNoMFlag(test_case,
                                   content,
                                   num_objects,
                                   total_size=0,
                                   metadata=False):
  """Checks if the UI output fails as expected with the -m flag not enabled.

  Args:
    test_case: Testcase used to maintain the same assert structure.
    content: The output provided by the UI.
    num_objects: The number of objects processed.
    total_size: The total size transferred in the operation. Used for data
                operations only.
    metadata: Indicates whether this is a metadata operation.
  """
  description_string = _FindAppropriateDescriptionString(metadata)
  # 0 files should be completed.
  no_files_string = str(0)
  test_case.assertIn(no_files_string + description_string, content)
  # We cannot have completed a file.
  files_completed_string = str(num_objects)
  test_case.assertNotIn(files_completed_string + description_string, content)
  if not metadata:
    total_size_string = BytesToFixedWidthString(total_size)
    zero = BytesToFixedWidthString(0)
    # Zero bytes must have been transferred in the beginning.
    test_case.assertIn(zero + '/' + total_size_string, content)
    # The total_size must have not been successfully transferred.
    test_case.assertNotIn(total_size_string + '/' + total_size_string, content)
  final_message_prefix = 'Operation completed over'
  test_case.assertNotIn(final_message_prefix, content)


class TestUi(testcase.GsUtilIntegrationTestCase):
  """Integration tests for UI functions."""

  def test_ui_download_single_objects_with_m_flag(self):
    """Tests UI for a single object download with the -m flag enabled.

    This test indirectly tests the correctness of ProducerThreadMessage in the
    UIController.
    """
    bucket_uri = self.CreateBucket()
    file_contents = b'd' * DOWNLOAD_SIZE
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=file_contents)
    fpath = self.CreateTempFile()
    stderr = self.RunGsUtil(['-m', 'cp', suri(object_uri), fpath],
                            return_stderr=True)
    CheckUiOutputWithMFlag(self, stderr, 1, total_size=DOWNLOAD_SIZE)

  def test_ui_download_single_objects_with_no_m_flag(self):
    """Tests UI for a single object download with the -m flag not enabled.

    The UI should behave differently from the -m flag option because in the
    latter we have a ProducerThreadMessage that allows us to know our progress
    percentage and total number of files.
    """
    bucket_uri = self.CreateBucket()
    file_contents = b'd' * DOWNLOAD_SIZE
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=file_contents)
    fpath = self.CreateTempFile()
    stderr = self.RunGsUtil(['cp', suri(object_uri), fpath], return_stderr=True)
    CheckUiOutputWithNoMFlag(self, stderr, 1, total_size=DOWNLOAD_SIZE)

  def test_ui_upload_single_object_with_m_flag(self):
    """Tests UI for a single object upload with -m flag enabled.

    This test indirectly tests the correctness of ProducerThreadMessage in the
    UIController.
    """
    bucket_uri = self.CreateBucket()
    file_contents = b'u' * UPLOAD_SIZE
    fpath = self.CreateTempFile(file_name='sample-file.txt',
                                contents=file_contents)
    stderr = self.RunGsUtil(
        ['-m', 'cp', suri(fpath), suri(bucket_uri)], return_stderr=True)

    CheckUiOutputWithMFlag(self, stderr, 1, total_size=UPLOAD_SIZE)

  def test_ui_upload_single_object_with_no_m_flag(self):
    """Tests UI for a single object upload with -m flag not enabled.

    The UI should behave differently from the -m flag option because in the
    latter we have a ProducerThreadMessage that allows us to know our progress
    percentage and total number of files.
    """
    bucket_uri = self.CreateBucket()
    file_contents = b'u' * UPLOAD_SIZE
    fpath = self.CreateTempFile(file_name='sample-file.txt',
                                contents=file_contents)
    stderr = self.RunGsUtil(
        ['cp', suri(fpath), suri(bucket_uri)], return_stderr=True)

    CheckUiOutputWithNoMFlag(self, stderr, 1, total_size=UPLOAD_SIZE)

  def test_ui_download_multiple_objects_with_m_flag(self):
    """Tests UI for a multiple object download with the -m flag enabled.

    This test indirectly tests the correctness of ProducerThreadMessage in the
    UIController.
    """
    bucket_uri = self.CreateBucket()
    num_objects = 7
    argument_list = ['-m', 'cp']
    total_size = 0
    for i in range(num_objects):
      file_size = DOWNLOAD_SIZE // 3
      file_contents = b'd' * file_size
      object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                     object_name='foo' + str(i),
                                     contents=file_contents)
      total_size += file_size
      argument_list.append(suri(object_uri))

    fpath = self.CreateTempDir()
    argument_list.append(fpath)
    stderr = self.RunGsUtil(argument_list, return_stderr=True)

    CheckUiOutputWithMFlag(self, stderr, num_objects, total_size=total_size)

  def test_ui_download_multiple_objects_with_no_m_flag(self):
    """Tests UI for a multiple object download with the -m flag not enabled.

    The UI should behave differently from the -m flag option because in the
    latter we have a ProducerThreadMessage that allows us to know our progress
    percentage and total number of files.
    """
    bucket_uri = self.CreateBucket()
    num_objects = 7
    argument_list = ['cp']
    total_size = 0
    for i in range(num_objects):
      file_size = DOWNLOAD_SIZE // 3
      file_contents = b'd' * file_size
      object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                     object_name='foo' + str(i),
                                     contents=file_contents)
      total_size += file_size
      argument_list.append(suri(object_uri))

    fpath = self.CreateTempDir()
    argument_list.append(fpath)
    stderr = self.RunGsUtil(argument_list, return_stderr=True)

    CheckUiOutputWithNoMFlag(self, stderr, num_objects, total_size=total_size)

  def test_ui_upload_mutliple_objects_with_m_flag(self):
    """Tests UI for a multiple object upload with -m flag enabled.

    This test indirectly tests the correctness of ProducerThreadMessage in the
    UIController.
    """
    bucket_uri = self.CreateBucket()
    num_objects = 7
    argument_list = ['-m', 'cp']
    total_size = 0
    for i in range(num_objects):
      file_size = UPLOAD_SIZE // 3
      file_contents = b'u' * file_size
      fpath = self.CreateTempFile(file_name='foo' + str(i),
                                  contents=file_contents)
      total_size += file_size
      argument_list.append(suri(fpath))

    argument_list.append(suri(bucket_uri))
    stderr = self.RunGsUtil(argument_list, return_stderr=True)

    CheckUiOutputWithMFlag(self, stderr, num_objects, total_size=total_size)

  def test_ui_upload_mutliple_objects_with_no_m_flag(self):
    """Tests UI for a multiple object upload with -m flag not enabled.

    The UI should behave differently from the -m flag option because in the
    latter we have a ProducerThreadMessage that allows us to know our progress
    percentage and total number of files.
    """
    bucket_uri = self.CreateBucket()
    num_objects = 7
    argument_list = ['cp']
    total_size = 0
    for i in range(num_objects):
      file_size = UPLOAD_SIZE // 3
      file_contents = b'u' * file_size
      fpath = self.CreateTempFile(file_name='foo' + str(i),
                                  contents=file_contents)
      total_size += file_size
      argument_list.append(suri(fpath))

    argument_list.append(suri(bucket_uri))
    stderr = self.RunGsUtil(argument_list, return_stderr=True)

    CheckUiOutputWithNoMFlag(self, stderr, num_objects, total_size=total_size)

  @SkipForS3('No resumable upload support for S3.')
  def test_ui_resumable_upload_break_with_m_flag(self):
    """Tests UI for upload resumed after a connection break with -m flag.

    This was adapted from test_cp_resumable_upload_break.
    """
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=b'a' * HALT_SIZE)
    boto_config_for_test = [
        ('GSUtil', 'resumable_threshold', str(ONE_KIB)),
        ('GSUtil', 'parallel_composite_upload_component_size', str(ONE_KIB))
    ]
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(True, 5)))

    with SetBotoConfigForTest(boto_config_for_test):
      stderr = self.RunGsUtil([
          '-m', 'cp', '--testcallbackfile', test_callback_file, fpath,
          suri(bucket_uri)
      ],
                              expected_status=1,
                              return_stderr=True)
      self.assertIn('Artifically halting upload', stderr)
      CheckBrokenUiOutputWithMFlag(self, stderr, 1, total_size=HALT_SIZE)
      stderr = self.RunGsUtil(
          ['-m', 'cp', fpath, suri(bucket_uri)], return_stderr=True)
      self.assertIn('Resuming upload', stderr)
      CheckUiOutputWithMFlag(self, stderr, 1, total_size=HALT_SIZE)

  @SkipForS3('No resumable upload support for S3.')
  def test_ui_resumable_upload_break_with_no_m_flag(self):
    """Tests UI for upload resumed after a connection break with no -m flag.

    This was adapted from test_cp_resumable_upload_break.
    """
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=b'a' * HALT_SIZE)
    boto_config_for_test = [
        ('GSUtil', 'resumable_threshold', str(ONE_KIB)),
        ('GSUtil', 'parallel_composite_upload_component_size', str(ONE_KIB))
    ]
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(True, 5)))

    with SetBotoConfigForTest(boto_config_for_test):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file, fpath,
          suri(bucket_uri)
      ],
                              expected_status=1,
                              return_stderr=True)
      self.assertIn('Artifically halting upload', stderr)
      CheckBrokenUiOutputWithNoMFlag(self, stderr, 1, total_size=HALT_SIZE)
      stderr = self.RunGsUtil(['cp', fpath, suri(bucket_uri)],
                              return_stderr=True)
      self.assertIn('Resuming upload', stderr)
      CheckUiOutputWithNoMFlag(self, stderr, 1, total_size=HALT_SIZE)

  def _test_ui_resumable_download_break_helper(self,
                                               boto_config,
                                               gsutil_flags=None):
    """Helper function for testing UI on a resumable download break.

    This was adapted from _test_cp_resumable_download_break_helper.

    Args:
      boto_config: List of boto configuration tuples for use with
          SetBotoConfigForTest.
      gsutil_flags: List of flags to run gsutil with, or None.
    """
    if not gsutil_flags:
      gsutil_flags = []
    bucket_uri = self.CreateBucket()
    file_contents = b'a' * HALT_SIZE
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=file_contents)
    fpath = self.CreateTempFile()
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(False, 5)))

    with SetBotoConfigForTest(boto_config):
      gsutil_args = (gsutil_flags + [
          'cp', '--testcallbackfile', test_callback_file,
          suri(object_uri), fpath
      ])
      stderr = self.RunGsUtil(gsutil_args,
                              expected_status=1,
                              return_stderr=True)
      self.assertIn('Artifically halting download.', stderr)
      if '-q' not in gsutil_flags:
        if '-m' in gsutil_flags:
          CheckBrokenUiOutputWithMFlag(self, stderr, 1, total_size=HALT_SIZE)
        else:
          CheckBrokenUiOutputWithNoMFlag(self, stderr, 1, total_size=HALT_SIZE)
      tracker_filename = GetTrackerFilePath(StorageUrlFromString(fpath),
                                            TrackerFileType.DOWNLOAD,
                                            self.test_api)
      self.assertTrue(os.path.isfile(tracker_filename))
      gsutil_args = gsutil_flags + ['cp', suri(object_uri), fpath]
      stderr = self.RunGsUtil(gsutil_args, return_stderr=True)
      if '-q' not in gsutil_args:
        self.assertIn('Resuming download', stderr)

    with open(fpath, 'rb') as f:
      self.assertEqual(f.read(), file_contents, 'File contents differ')
    if '-q' in gsutil_flags:
      self.assertEqual('', stderr)
    elif '-m' in gsutil_flags:
      CheckUiOutputWithMFlag(self, stderr, 1, total_size=HALT_SIZE)
    else:
      CheckUiOutputWithNoMFlag(self, stderr, 1, total_size=HALT_SIZE)

  def test_ui_resumable_download_break_with_m_flag(self):
    """Tests UI on a resumable download break with -m flag.

    This was adapted from test_cp_resumable_download_break.
    """
    self._test_ui_resumable_download_break_helper(
        [('GSUtil', 'resumable_threshold', str(ONE_KIB))], gsutil_flags=['-m'])

  def test_ui_resumable_download_break_with_no_m_flag(self):
    """Tests UI on a resumable download break with no -m flag.

    This was adapted from test_cp_resumable_download_break.
    """
    self._test_ui_resumable_download_break_helper([
        ('GSUtil', 'resumable_threshold', str(ONE_KIB))
    ])

  def test_ui_resumable_download_break_with_q_flag(self):
    """Tests UI on a resumable download break with -q flag but no -m flag.

    This was adapted from test_cp_resumable_download_break, and the UI output
    should be empty.
    """
    self._test_ui_resumable_download_break_helper(
        [('GSUtil', 'resumable_threshold', str(ONE_KIB))], gsutil_flags=['-q'])

  def test_ui_resumable_download_break_with_q_and_m_flags(self):
    """Tests UI on a resumable download break with -q and -m flags.

    This was adapted from test_cp_resumable_download_break, and the UI output
    should be empty.
    """
    self._test_ui_resumable_download_break_helper(
        [('GSUtil', 'resumable_threshold', str(ONE_KIB))],
        gsutil_flags=['-m', '-q'])

  def _test_ui_composite_upload_resume_helper(self, gsutil_flags=None):
    """Helps testing UI on a resumable upload with finished components.

    Args:
      gsutil_flags: List of flags to run gsutil with, or None.
    """
    if not gsutil_flags:
      gsutil_flags = []
    bucket_uri = self.CreateBucket()
    dst_url = StorageUrlFromString(suri(bucket_uri, 'foo'))

    file_contents = b'foobar'
    file_name = 'foobar'
    source_file = self.CreateTempFile(contents=file_contents,
                                      file_name=file_name)
    src_url = StorageUrlFromString(source_file)

    # Simulate an upload that had occurred by writing a tracker file
    # that points to a previously uploaded component.
    tracker_file_name = GetTrackerFilePath(dst_url,
                                           TrackerFileType.PARALLEL_UPLOAD,
                                           self.test_api, src_url)
    tracker_prefix = '123'

    # Create component 0 to be used in the resume; it must match the name
    # that will be generated in copy_helper, so we use the same scheme.
    encoded_name = (PARALLEL_UPLOAD_STATIC_SALT + source_file).encode(UTF8)
    content_md5 = GetMd5()
    content_md5.update(encoded_name)
    digest = content_md5.hexdigest()
    component_object_name = (tracker_prefix + PARALLEL_UPLOAD_TEMP_NAMESPACE +
                             digest + '_0')

    component_size = 3
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name=component_object_name,
                                   contents=file_contents[:component_size])
    existing_component = ObjectFromTracker(component_object_name,
                                           str(object_uri.generation))
    existing_components = [existing_component]

    WriteParallelUploadTrackerFile(tracker_file_name, tracker_prefix,
                                   existing_components)

    try:
      # Now "resume" the upload.
      with SetBotoConfigForTest([
          ('GSUtil', 'parallel_composite_upload_threshold', '1'),
          ('GSUtil', 'parallel_composite_upload_component_size',
           str(component_size))
      ]):
        gsutil_args = (
            gsutil_flags +
            ['cp', source_file, suri(bucket_uri, 'foo')])
        stderr = self.RunGsUtil(gsutil_args, return_stderr=True)
        self.assertIn('Found 1 existing temporary components to reuse.', stderr)
        self.assertFalse(
            os.path.exists(tracker_file_name),
            'Tracker file %s should have been deleted.' % tracker_file_name)
        read_contents = self.RunGsUtil(['cat', suri(bucket_uri, 'foo')],
                                       return_stdout=True)
        self.assertEqual(read_contents.encode(UTF8), file_contents)
        if '-m' in gsutil_flags:
          CheckUiOutputWithMFlag(self, stderr, 1, total_size=len(file_contents))
        else:
          CheckUiOutputWithNoMFlag(self,
                                   stderr,
                                   1,
                                   total_size=len(file_contents))
    finally:
      # Clean up if something went wrong.
      DeleteTrackerFile(tracker_file_name)

  @SkipForS3('No resumable upload support for S3.')
  def test_ui_composite_upload_resume_with_m_flag(self):
    """Tests UI on a resumable upload with finished components and -m flag."""
    self._test_ui_composite_upload_resume_helper(gsutil_flags=['-m'])

  @SkipForS3('No resumable upload support for S3.')
  def test_ui_composite_upload_resume_with_no_m_flag(self):
    """Tests UI on a resumable upload with finished components and no -m flag.
    """
    self._test_ui_composite_upload_resume_helper()

  @unittest.skipUnless(UsingCrcmodExtension(),
                       'Sliced download requires fast crcmod.')
  @SkipForS3('No sliced download support for S3.')
  def _test_ui_sliced_download_partial_resume_helper(self, gsutil_flags=None):
    """Helps testing UI for sliced download with some finished components.

    This was adapted from test_sliced_download_partial_resume_helper.

    Args:
      gsutil_flags: List of flags to run gsutil with, or None.
    """
    if not gsutil_flags:
      gsutil_flags = []
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=b'abc' * HALT_SIZE)
    fpath = self.CreateTempFile()
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltOneComponentCopyCallbackHandler(5)))

    boto_config_for_test = [
        ('GSUtil', 'resumable_threshold', str(HALT_SIZE)),
        ('GSUtil', 'sliced_object_download_threshold', str(HALT_SIZE)),
        ('GSUtil', 'sliced_object_download_max_components', '3')
    ]

    with SetBotoConfigForTest(boto_config_for_test):
      gsutil_args = gsutil_flags + [
          'cp', '--testcallbackfile', test_callback_file,
          suri(object_uri),
          suri(fpath)
      ]

      stderr = self.RunGsUtil(gsutil_args,
                              return_stderr=True,
                              expected_status=1)
      if '-m' in gsutil_args:
        CheckBrokenUiOutputWithMFlag(self,
                                     stderr,
                                     1,
                                     total_size=(len('abc') * HALT_SIZE))
      else:
        CheckBrokenUiOutputWithNoMFlag(self,
                                       stderr,
                                       1,
                                       total_size=(len('abc') * HALT_SIZE))
      # Each tracker file should exist.
      tracker_filenames = GetSlicedDownloadTrackerFilePaths(
          StorageUrlFromString(fpath), self.test_api)
      for tracker_filename in tracker_filenames:
        self.assertTrue(os.path.isfile(tracker_filename))
      gsutil_args = gsutil_flags + ['cp', suri(object_uri), fpath]

      stderr = self.RunGsUtil(gsutil_args, return_stderr=True)
      self.assertIn('Resuming download', stderr)
      self.assertIn('Download already complete', stderr)

      # Each tracker file should have been deleted.
      tracker_filenames = GetSlicedDownloadTrackerFilePaths(
          StorageUrlFromString(fpath), self.test_api)
      for tracker_filename in tracker_filenames:
        self.assertFalse(os.path.isfile(tracker_filename))

      with open(fpath, 'r') as f:
        self.assertEqual(f.read(), 'abc' * HALT_SIZE, 'File contents differ')
      if '-m' in gsutil_args:
        CheckUiOutputWithMFlag(self,
                               stderr,
                               1,
                               total_size=(len('abc') * HALT_SIZE))
      else:
        CheckUiOutputWithNoMFlag(self,
                                 stderr,
                                 1,
                                 total_size=(len('abc') * HALT_SIZE))

  @SkipForS3('No resumable upload support for S3.')
  def test_ui_sliced_download_partial_resume_helper_with_m_flag(self):
    """Tests UI on a resumable download with finished components and -m flag.
    """
    self._test_ui_sliced_download_partial_resume_helper(gsutil_flags=['-m'])

  @SkipForS3('No resumable upload support for S3.')
  def _test_ui_sliced_download_partial_resume_helper_with_no_m_flag(self):
    """Tests UI on a resumable upload with finished components and no -m flag.
    """
    self._test_ui_sliced_download_partial_resume_helper()

  def test_ui_hash_mutliple_objects_with_no_m_flag(self):
    """Tests UI for a multiple object hashing with no -m flag enabled.

    This test indirectly tests the correctness of ProducerThreadMessage in the
    UIController.
    """
    num_objects = 7
    argument_list = ['hash']
    total_size = 0
    for i in range(num_objects):
      file_size = UPLOAD_SIZE // 3
      file_contents = b'u' * file_size
      fpath = self.CreateTempFile(file_name='foo' + str(i),
                                  contents=file_contents)
      total_size += file_size
      argument_list.append(suri(fpath))

    stderr = self.RunGsUtil(argument_list, return_stderr=True)
    CheckUiOutputWithNoMFlag(self, stderr, num_objects, total_size)

  def test_ui_rewrite_with_m_flag(self):
    """Tests UI output for rewrite and -m flag.

    Adapted from test_rewrite_stdin_args.
    """
    if self.test_api == ApiSelector.XML:
      return unittest.skip('Rewrite API is only supported in JSON.')
    object_uri = self.CreateObject(contents=b'bar',
                                   encryption_key=TEST_ENCRYPTION_KEY1)
    stdin_arg = suri(object_uri)

    boto_config_for_test = [('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY2),
                            ('GSUtil', 'decryption_key1', TEST_ENCRYPTION_KEY1)]
    with SetBotoConfigForTest(boto_config_for_test):
      stderr = self.RunGsUtil(['-m', 'rewrite', '-k', '-I'],
                              stdin=stdin_arg,
                              return_stderr=True)
    self.AssertObjectUsesCSEK(stdin_arg, TEST_ENCRYPTION_KEY2)
    num_objects = 1
    total_size = len(b'bar')
    CheckUiOutputWithMFlag(self, stderr, num_objects, total_size)

  def test_ui_rewrite_with_no_m_flag(self):
    """Tests UI output for rewrite and -m flag not enabled.

    Adapted from test_rewrite_stdin_args.
    """
    if self.test_api == ApiSelector.XML:
      return unittest.skip('Rewrite API is only supported in JSON.')
    object_uri = self.CreateObject(contents=b'bar',
                                   encryption_key=TEST_ENCRYPTION_KEY1)
    stdin_arg = suri(object_uri)

    boto_config_for_test = [('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY2),
                            ('GSUtil', 'decryption_key1', TEST_ENCRYPTION_KEY1)]
    with SetBotoConfigForTest(boto_config_for_test):
      stderr = self.RunGsUtil(['rewrite', '-k', '-I'],
                              stdin=stdin_arg,
                              return_stderr=True)
    self.AssertObjectUsesCSEK(stdin_arg, TEST_ENCRYPTION_KEY2)
    num_objects = 1
    total_size = len(b'bar')
    CheckUiOutputWithNoMFlag(self, stderr, num_objects, total_size)

  def test_ui_setmeta_with_m_flag(self):
    """Tests a recursive setmeta command with m flag has expected UI output.

    Adapted from test_recursion_works on test_setmeta.
    """
    bucket_uri = self.CreateBucket()
    object1_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'foo')
    object2_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'foo')
    stderr = self.RunGsUtil([
        '-m', 'setmeta', '-h', 'content-type:footype',
        suri(object1_uri),
        suri(object2_uri)
    ],
                            return_stderr=True)

    for obj_uri in [object1_uri, object2_uri]:
      stdout = self.RunGsUtil(['stat', suri(obj_uri)], return_stdout=True)
      self.assertIn('footype', stdout)
    CheckUiOutputWithMFlag(self, stderr, 2, metadata=True)

  def test_ui_setmeta_with_no_m_flag(self):
    """Tests a recursive setmeta command with no m flag has expected UI output.

    Adapted from test_recursion_works on test_setmeta.
    """
    bucket_uri = self.CreateBucket()
    object1_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'foo')
    object2_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'foo')
    stderr = self.RunGsUtil([
        'setmeta', '-h', 'content-type:footype',
        suri(object1_uri),
        suri(object2_uri)
    ],
                            return_stderr=True)

    for obj_uri in [object1_uri, object2_uri]:
      stdout = self.RunGsUtil(['stat', suri(obj_uri)], return_stdout=True)
      self.assertIn('footype', stdout)
    CheckUiOutputWithNoMFlag(self, stderr, 2, metadata=True)

  def test_ui_acl_with_m_flag(self):
    """Tests UI output for an ACL command with m flag enabled.

    Adapted from test_set_valid_acl_object.
    """
    get_acl_prefix = ['-m', 'acl', 'get']
    set_acl_prefix = ['-m', 'acl', 'set']
    obj_uri = suri(self.CreateObject(contents=b'foo'))
    acl_string = self.RunGsUtil(get_acl_prefix + [obj_uri], return_stdout=True)
    inpath = self.CreateTempFile(contents=acl_string.encode(UTF8))
    stderr = self.RunGsUtil(set_acl_prefix + ['public-read', obj_uri],
                            return_stderr=True)
    CheckUiOutputWithMFlag(self, stderr, 1, metadata=True)
    acl_string2 = self.RunGsUtil(get_acl_prefix + [obj_uri], return_stdout=True)
    stderr = self.RunGsUtil(set_acl_prefix + [inpath, obj_uri],
                            return_stderr=True)
    CheckUiOutputWithMFlag(self, stderr, 1, metadata=True)
    acl_string3 = self.RunGsUtil(get_acl_prefix + [obj_uri], return_stdout=True)

    self.assertNotEqual(acl_string, acl_string2)
    self.assertEqual(acl_string, acl_string3)

  def test_ui_acl_with_no_m_flag(self):
    """Tests UI output for an ACL command with m flag not enabled.

    Adapted from test_set_valid_acl_object.
    """
    get_acl_prefix = ['acl', 'get']
    set_acl_prefix = ['acl', 'set']
    obj_uri = suri(self.CreateObject(contents=b'foo'))
    acl_string = self.RunGsUtil(get_acl_prefix + [obj_uri], return_stdout=True)
    inpath = self.CreateTempFile(contents=acl_string.encode(UTF8))
    stderr = self.RunGsUtil(set_acl_prefix + ['public-read', obj_uri],
                            return_stderr=True)
    CheckUiOutputWithNoMFlag(self, stderr, 1, metadata=True)
    acl_string2 = self.RunGsUtil(get_acl_prefix + [obj_uri], return_stdout=True)
    stderr = self.RunGsUtil(set_acl_prefix + [inpath, obj_uri],
                            return_stderr=True)
    CheckUiOutputWithNoMFlag(self, stderr, 1, metadata=True)
    acl_string3 = self.RunGsUtil(get_acl_prefix + [obj_uri], return_stdout=True)

    self.assertNotEqual(acl_string, acl_string2)
    self.assertEqual(acl_string, acl_string3)

  def _test_ui_rsync_bucket_to_bucket_helper(self, gsutil_flags=None):
    """Helper class to test UI output for rsync command.

    Args:
      gsutil_flags: List of flags to run gsutil with, or None.

    Adapted from test_bucket_to_bucket in test_rsync.
    """
    if not gsutil_flags:
      gsutil_flags = []
    # Create 2 buckets with 1 overlapping object, 1 extra object at root level
    # in each, and 1 extra object 1 level down in each, where one of the objects
    # starts with "." to test that we don't skip those objects. Make the
    # overlapping objects named the same but with different content, to test
    # that we detect and properly copy in that case.
    bucket1_uri = self.CreateBucket()
    bucket2_uri = self.CreateBucket()
    self.CreateObject(bucket_uri=bucket1_uri,
                      object_name='obj1',
                      contents=b'obj1')
    self.CreateObject(bucket_uri=bucket1_uri,
                      object_name='.obj2',
                      contents=b'.obj2',
                      mtime=10)
    self.CreateObject(bucket_uri=bucket1_uri,
                      object_name='subdir/obj3',
                      contents=b'subdir/obj3')
    self.CreateObject(bucket_uri=bucket1_uri,
                      object_name='obj6',
                      contents=b'obj6_',
                      mtime=100)
    # .obj2 will be replaced and have mtime of 10
    self.CreateObject(bucket_uri=bucket2_uri,
                      object_name='.obj2',
                      contents=b'.OBJ2')
    self.CreateObject(bucket_uri=bucket2_uri,
                      object_name='obj4',
                      contents=b'obj4')
    self.CreateObject(bucket_uri=bucket2_uri,
                      object_name='subdir/obj5',
                      contents=b'subdir/obj5')
    self.CreateObject(bucket_uri=bucket2_uri,
                      object_name='obj6',
                      contents=b'obj6',
                      mtime=100)

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      """Tests rsync works as expected."""
      gsutil_args = (gsutil_flags +
                     ['rsync', suri(bucket1_uri),
                      suri(bucket2_uri)])
      stderr = self.RunGsUtil(gsutil_args, return_stderr=True)
      num_objects = 3
      total_size = len('obj1') + len('.obj2') + len('obj6_')
      CheckUiOutputWithNoMFlag(self, stderr, num_objects, total_size)
      listing1 = TailSet(suri(bucket1_uri), self.FlatListBucket(bucket1_uri))
      listing2 = TailSet(suri(bucket2_uri), self.FlatListBucket(bucket2_uri))
      # First bucket should have un-altered content.
      self.assertEqual(listing1,
                        set(['/obj1', '/.obj2', '/subdir/obj3', '/obj6']))
      # Second bucket should have new objects added from source bucket (without
      # removing extraneeous object found in dest bucket), and without the
      # subdir objects synchronized.
      self.assertEqual(
          listing2, set(['/obj1', '/.obj2', '/obj4', '/subdir/obj5', '/obj6']))
      # Assert that the src/dest objects that had same length but different
      # content were correctly synchronized (bucket to bucket rsync uses
      # checksums).
      self.assertEqual(
          '.obj2',
          self.RunGsUtil(['cat', suri(bucket1_uri, '.obj2')],
                         return_stdout=True))
      self.assertEqual(
          '.obj2',
          self.RunGsUtil(['cat', suri(bucket2_uri, '.obj2')],
                         return_stdout=True))
      self.assertEqual(
          'obj6_',
          self.RunGsUtil(['cat', suri(bucket2_uri, 'obj6')],
                         return_stdout=True))

    _Check1()

  def test_ui_rsync_bucket_to_bucket_with_m_flag(self):
    """Tests UI output for rsync with -m flag enabled works as expected."""
    self._test_ui_rsync_bucket_to_bucket_helper(gsutil_flags=['-m'])

  def test_ui_rsync_bucket_to_bucket_with_no_m_flag(self):
    """Tests UI output for rsync with -m flag not enabled works as expected."""
    self._test_ui_rsync_bucket_to_bucket_helper()


class TestUiUnitTests(testcase.GsUtilUnitTestCase):
  """Unit tests for UI functions."""

  upload_size = UPLOAD_SIZE
  start_time = 10000

  def test_ui_seek_ahead_message(self):
    """Tests if a seek ahead message is correctly printed."""
    status_queue = Queue.Queue()
    stream = six.StringIO()
    # No time constraints for displaying messages.
    start_time = self.start_time
    ui_controller = UIController(0, 0, 0, 0, custom_time=start_time)
    ui_thread = UIThread(status_queue, stream, ui_controller)
    num_objects = 10
    total_size = 1024**3
    PutToQueueWithTimeout(status_queue,
                          SeekAheadMessage(num_objects, total_size, start_time))

    # Adds a file. Because this message was already theoretically processed
    # by the SeekAheadThread, the number of files reported by the UIController
    # should not change.
    fpath = self.CreateTempFile(file_name='sample-file.txt', contents=b'foo')
    PutToQueueWithTimeout(
        status_queue,
        FileMessage(StorageUrlFromString(suri(fpath)),
                    None,
                    start_time + 10,
                    size=UPLOAD_SIZE,
                    message_type=FileMessage.FILE_UPLOAD,
                    finished=False))
    PutToQueueWithTimeout(
        status_queue,
        FileMessage(StorageUrlFromString(suri(fpath)),
                    None,
                    start_time + 20,
                    size=UPLOAD_SIZE,
                    message_type=FileMessage.FILE_UPLOAD,
                    finished=True))

    PutToQueueWithTimeout(status_queue, ZERO_TASKS_TO_DO_ARGUMENT)
    JoinThreadAndRaiseOnTimeout(ui_thread)
    content = stream.getvalue()
    expected_message = (
        'Estimated work for this command: objects: %s, total size: %s\n' %
        (num_objects, MakeHumanReadable(total_size)))
    self.assertIn(expected_message, content)
    # This ensures the SeekAheadMessage did its job.
    self.assertIn('/' + str(num_objects), content)
    # This ensures a FileMessage did not affect the total number of files
    # obtained by the SeekAheadMessage.
    self.assertNotIn('/' + str(num_objects + 1), content)

  def test_ui_seek_ahead_zero_size(self):
    """Tests the case where the SeekAheadThread returns total size of 0."""
    current_time_ms = self.start_time
    status_queue = Queue.Queue()
    stream = six.StringIO()
    ui_controller = UIController(custom_time=current_time_ms)
    ui_thread = UIThread(status_queue, stream, ui_controller)
    PutToQueueWithTimeout(status_queue,
                          SeekAheadMessage(100, 0, current_time_ms))
    for i in range(100):
      current_time_ms += 200
      PutToQueueWithTimeout(
          status_queue,
          FileMessage(StorageUrlFromString('gs://foo%s' % i),
                      StorageUrlFromString('bar%s' % i),
                      current_time_ms,
                      message_type=FileMessage.FILE_DOWNLOAD))
    for i in range(100):
      current_time_ms += 200
      PutToQueueWithTimeout(
          status_queue,
          FileMessage(StorageUrlFromString('gs://foo%s' % i),
                      StorageUrlFromString('bar%s' % i),
                      current_time_ms,
                      finished=True,
                      message_type=FileMessage.FILE_DOWNLOAD))
    PutToQueueWithTimeout(
        status_queue,
        ProducerThreadMessage(100, 0, current_time_ms, finished=True))
    PutToQueueWithTimeout(status_queue, FinalMessage(current_time_ms))
    PutToQueueWithTimeout(status_queue, ZERO_TASKS_TO_DO_ARGUMENT)
    JoinThreadAndRaiseOnTimeout(ui_thread)
    self.assertIn('100/100', stream.getvalue())

  def test_ui_empty_list(self):
    """Tests if status queue is empty after processed by UIThread."""
    status_queue = Queue.Queue()
    stream = six.StringIO()
    ui_controller = UIController()
    ui_thread = UIThread(status_queue, stream, ui_controller)
    for i in range(10000):  # pylint: disable=unused-variable
      PutToQueueWithTimeout(status_queue, 'foo')
    PutToQueueWithTimeout(status_queue, ZERO_TASKS_TO_DO_ARGUMENT)
    JoinThreadAndRaiseOnTimeout(ui_thread)
    self.assertEqual(0, status_queue.qsize())

  def test_ui_controller_shared_states(self):
    """Tests that UIController correctly integrates messages.

    This test ensures UIController correctly shares its state, which is used by
    both UIThread and MainThreadUIQueue. There are multiple ways of checking
    that. One such way is to create a ProducerThreadMessage on the
    MainThreadUIQueue, simulate a upload with messages coming from the UIThread,
    and check if the output has the percentage done and number of files
    (both happen only when a ProducerThreadMessage or SeekAheadMessage is
    called).
    """
    ui_thread_status_queue = Queue.Queue()
    stream = six.StringIO()
    # No time constraints for displaying messages.
    start_time = self.start_time
    ui_controller = UIController(0, 0, 0, 0, custom_time=start_time)
    main_thread_ui_queue = MainThreadUIQueue(stream, ui_controller)
    ui_thread = UIThread(ui_thread_status_queue, stream, ui_controller)
    PutToQueueWithTimeout(
        main_thread_ui_queue,
        ProducerThreadMessage(1, UPLOAD_SIZE, start_time, finished=True))
    fpath = self.CreateTempFile(file_name='sample-file.txt', contents=b'foo')
    PutToQueueWithTimeout(
        ui_thread_status_queue,
        FileMessage(StorageUrlFromString(suri(fpath)),
                    None,
                    start_time + 10,
                    size=UPLOAD_SIZE,
                    message_type=FileMessage.FILE_UPLOAD,
                    finished=False))
    PutToQueueWithTimeout(
        ui_thread_status_queue,
        FileMessage(StorageUrlFromString(suri(fpath)),
                    None,
                    start_time + 20,
                    size=UPLOAD_SIZE,
                    message_type=FileMessage.FILE_UPLOAD,
                    finished=True))
    PutToQueueWithTimeout(ui_thread_status_queue, FinalMessage(start_time + 50))
    PutToQueueWithTimeout(ui_thread_status_queue, ZERO_TASKS_TO_DO_ARGUMENT)
    JoinThreadAndRaiseOnTimeout(ui_thread)
    content = stream.getvalue()
    CheckUiOutputWithMFlag(self, content, 1, UPLOAD_SIZE)

  def test_ui_throughput_calculation_with_components(self):
    """Tests throughput calculation in the UI.

    This test takes two different values, both with a different size and
    different number of components, and see if throughput behaves as expected.
    """
    status_queue = Queue.Queue()
    stream = six.StringIO()
    # Creates a UIController that has no time constraints for updating info,
    # except for having to wait at least 2 seconds (considering the time
    # informed by the messages) to update the throughput. We use a value
    # slightly smaller than 2 to ensure messages that are 2 seconds apart from
    # one another will be enough to calculate throughput.
    start_time = self.start_time
    ui_controller = UIController(sliding_throughput_period=2,
                                 update_message_period=1,
                                 first_throughput_latency=0,
                                 custom_time=start_time)
    # We use start_time to have a reasonable set of values for the time messages
    # processed by the UIController. However, the start_time does not influence
    # this test, as the throughput is calculated based on the time
    # difference between two messages, which is fixed in this test.

    ui_thread = UIThread(status_queue, stream, ui_controller)
    fpath1 = self.CreateTempFile(file_name='sample-file.txt', contents=b'foo')
    fpath2 = self.CreateTempFile(file_name='sample-file2.txt', contents=b'FOO')

    def _CreateFileVariables(alpha, component_number, src_url):
      """Creates size and component_size for a given file."""
      size = 1024**2 * 60 * alpha  # this is 60*alpha MiB
      component_size = size / component_number
      return (size, component_number, component_size, src_url)

    # Note: size1 and size2 do not actually correspond to the actual sizes of
    # fpath1 and fpath2. However, the UIController only uses the size sent on
    # the message, so we should be able to pretend they are much larger on size.
    (size1, component_num_file1, component_size_file1,
     src_url1) = (_CreateFileVariables(1, 3,
                                       StorageUrlFromString(suri(fpath1))))

    (size2, component_num_file2, component_size_file2,
     src_url2) = (_CreateFileVariables(10, 4,
                                       StorageUrlFromString(suri(fpath2))))

    for file_message_type, component_message_type, operation_name in (
        (FileMessage.FILE_UPLOAD, FileMessage.COMPONENT_TO_UPLOAD,
         'Uploading'), (FileMessage.FILE_DOWNLOAD,
                        FileMessage.COMPONENT_TO_DOWNLOAD, 'Downloading')):
      # Testing for uploads and downloads
      PutToQueueWithTimeout(
          status_queue,
          FileMessage(src_url1,
                      None,
                      start_time + 100,
                      size=size1,
                      message_type=file_message_type))
      PutToQueueWithTimeout(
          status_queue,
          FileMessage(src_url2,
                      None,
                      start_time + 150,
                      size=size2,
                      message_type=file_message_type))

      for i in range(component_num_file1):
        PutToQueueWithTimeout(
            status_queue,
            FileMessage(src_url1,
                        None,
                        start_time + 200 + i,
                        size=component_size_file1,
                        component_num=i,
                        message_type=component_message_type))
      for i in range(component_num_file2):
        PutToQueueWithTimeout(
            status_queue,
            FileMessage(src_url2,
                        None,
                        start_time + 250 + i,
                        size=component_size_file2,
                        component_num=i,
                        message_type=component_message_type))

      progress_calls_number = 4
      for j in range(1, progress_calls_number + 1):
        # We will send progress_calls_number ProgressMessages for each
        # component.
        base_start_time = (start_time + 300 + (j - 1) *
                           (component_num_file1 + component_num_file2))

        for i in range(component_num_file1):
          # Each component has size equal to
          # component_size_file1/progress_calls_number
          PutToQueueWithTimeout(
              status_queue,
              ProgressMessage(size1,
                              j * component_size_file1 / progress_calls_number,
                              src_url1,
                              base_start_time + i,
                              component_num=i,
                              operation_name=operation_name))

        for i in range(component_num_file2):
          # Each component has size equal to
          # component_size_file2/progress_calls_number
          PutToQueueWithTimeout(
              status_queue,
              ProgressMessage(size2,
                              j * component_size_file2 / progress_calls_number,
                              src_url2,
                              base_start_time + component_num_file1 + i,
                              component_num=i,
                              operation_name=operation_name))

      # Time to finish the components and files.
      for i in range(component_num_file1):
        PutToQueueWithTimeout(
            status_queue,
            FileMessage(src_url1,
                        None,
                        start_time + 500 + i,
                        finished=True,
                        size=component_size_file1,
                        component_num=i,
                        message_type=component_message_type))
      for i in range(component_num_file2):
        PutToQueueWithTimeout(
            status_queue,
            FileMessage(src_url2,
                        None,
                        start_time + 600 + i,
                        finished=True,
                        size=component_size_file2,
                        component_num=i,
                        message_type=component_message_type))

      PutToQueueWithTimeout(
          status_queue,
          FileMessage(src_url1,
                      None,
                      start_time + 700,
                      size=size1,
                      finished=True,
                      message_type=file_message_type))
      PutToQueueWithTimeout(
          status_queue,
          FileMessage(src_url2,
                      None,
                      start_time + 800,
                      size=size2,
                      finished=True,
                      message_type=file_message_type))

      PutToQueueWithTimeout(status_queue, ZERO_TASKS_TO_DO_ARGUMENT)
      JoinThreadAndRaiseOnTimeout(ui_thread)
      content = stream.getvalue()
      # There were 2-second periods when no progress was reported. The
      # throughput here will be 0. We will use BytesToFixedWidthString(0)
      # to ensure that any changes to the function are applied here as well.
      zero = BytesToFixedWidthString(0)
      self.assertIn(zero + '/s', content)
      file1_progress = (size1 / (component_num_file1 * progress_calls_number))
      file2_progress = (size2 / (component_num_file2 * progress_calls_number))
      # There were 2-second periods when only two progresses from file1
      # were reported. The throughput here will be file1_progress.
      self.assertIn(BytesToFixedWidthString(file1_progress) + '/s', content)
      # There were 2-second periods when only two progresses from file2
      # were reported. The throughput here will be file2_progress.
      self.assertIn(BytesToFixedWidthString(file2_progress) + '/s', content)
      # For each loop iteration, there are two 2-second periods when
      # one progress from each file is reported: in the middle of the
      # iteration, and in the end of the iteration along with the beginning
      # of the following iteration, on a total of
      # 2 * progress_calls_number - 1 occurrences (-1 due to only 1 occurrence
      # on the last iteration).
      # The throughput here will be (file1_progress + file2_progress) / 2.
      average_progress = BytesToFixedWidthString(
          (file1_progress + file2_progress) / 2)
      self.assertEqual(content.count(average_progress + '/s'),
                        2 * progress_calls_number - 1)

  def test_ui_throughput_calculation_with_no_components(self):
    """Tests throughput calculation in the UI.

    This test takes two different values, both with a different size and
    different number of components, and see if throughput behaves as expected.
    """
    status_queue = Queue.Queue()
    stream = six.StringIO()
    # Creates a UIController that has no time constraints for updating info,
    # except for having to wait at least 2 seconds(considering the time informed
    # by the messages) to update the throughput. We use a value slightly smaller
    # than 2 to ensure messages that are 2 seconds apart from one another will
    # be enough to calculate throughput.
    start_time = self.start_time
    ui_controller = UIController(sliding_throughput_period=2,
                                 update_message_period=1,
                                 first_throughput_latency=0,
                                 custom_time=start_time)
    # We use start_time to have a reasonable set of values for the time messages
    # processed by the UIController. However, the start_time does not influence
    # much this test, as the throughput is calculated based on the time
    # difference between two messages, which is fixed in this text.

    ui_thread = UIThread(status_queue, stream, ui_controller)
    fpath1 = self.CreateTempFile(file_name='sample-file.txt', contents=b'foo')
    fpath2 = self.CreateTempFile(file_name='sample-file2.txt', contents=b'FOO')

    # Note: size1 and size2 do not actually correspond to the actual sizes of
    # fpath1 and fpath2. However, the UIController only uses the size sent on
    # the message, so we should be able to pretend they are much larger on size.
    size1 = 1024**2 * 60
    src_url1 = StorageUrlFromString(suri(fpath1))
    size2 = 1024**2 * 600
    src_url2 = StorageUrlFromString(suri(fpath2))

    for file_message_type, operation_name in ((FileMessage.FILE_UPLOAD,
                                               'Uploading'),
                                              (FileMessage.FILE_DOWNLOAD,
                                               'Downloading')):
      # Testing for uploads and downloads
      PutToQueueWithTimeout(
          status_queue,
          FileMessage(src_url1,
                      None,
                      start_time + 200,
                      size=size1,
                      message_type=file_message_type))
      PutToQueueWithTimeout(
          status_queue,
          FileMessage(src_url2,
                      None,
                      start_time + 301,
                      size=size2,
                      message_type=file_message_type))
      progress_calls_number = 4
      for j in range(1, progress_calls_number + 1):
        # We will send progress_calls_number ProgressMessages for each file.
        PutToQueueWithTimeout(
            status_queue,
            ProgressMessage(size1,
                            j * size1 / 4,
                            src_url1,
                            start_time + 300 + j * 2,
                            operation_name=operation_name))
        PutToQueueWithTimeout(
            status_queue,
            ProgressMessage(size2,
                            j * size2 / 4,
                            src_url2,
                            start_time + 300 + j * 2 + 1,
                            operation_name=operation_name))

      # Time to finish the files.
      PutToQueueWithTimeout(
          status_queue,
          FileMessage(src_url1,
                      None,
                      start_time + 700,
                      size=size1,
                      finished=True,
                      message_type=file_message_type))
      PutToQueueWithTimeout(
          status_queue,
          FileMessage(src_url2,
                      None,
                      start_time + 800,
                      size=size2,
                      finished=True,
                      message_type=file_message_type))

      PutToQueueWithTimeout(status_queue, ZERO_TASKS_TO_DO_ARGUMENT)
      JoinThreadAndRaiseOnTimeout(ui_thread)
      content = stream.getvalue()
      # There were 2-second periods when no progress was reported. The
      # throughput here will be 0. We will use BytesToFixedWidthString(0)
      # to ensure that any changes to the function are applied here as well.
      zero = BytesToFixedWidthString(0)
      self.assertIn(zero + '/s', content)
      file1_progress = (size1 / progress_calls_number)
      file2_progress = (size2 / progress_calls_number)
      # For each loop iteration, there are two 2-second periods when
      # one progress from each file is reported: in the middle of the
      # iteration, and in the end of the iteration along with the beginning
      # of the following iteration, on a total of
      # 2 * progress_calls_number - 1 occurrences (-1 due to only 1 occurrence
      # on the last iteration).
      # The throughput here will be (file1_progress + file2_progress) / 2.
      average_progress = BytesToFixedWidthString(
          (file1_progress + file2_progress) / 2)
      self.assertEqual(content.count(average_progress + '/s'),
                        2 * progress_calls_number - 1)

  def test_ui_metadata_message_passing(self):
    """Tests that MetadataMessages are being correctly received and processed.

    This also tests the relation and hierarchy between different estimation
    sources, as represented by the EstimationSource class.
    """
    status_queue = Queue.Queue()
    stream = six.StringIO()
    # Creates a UIController that has no time constraints for updating info,
    # except for having to wait at least 2 seconds(considering the time informed
    # by the messages) to update the throughput. We use a value slightly smaller
    # than 2 to ensure messages that are 2 seconds apart from one another will
    # be enough to calculate throughput.
    start_time = self.start_time
    ui_controller = UIController(sliding_throughput_period=2,
                                 update_message_period=1,
                                 first_throughput_latency=0,
                                 custom_time=start_time)
    num_objects = 200
    ui_thread = UIThread(status_queue, stream, ui_controller)
    for i in range(num_objects):
      if i < 100:
        PutToQueueWithTimeout(status_queue,
                              MetadataMessage(start_time + 0.1 * i))
      elif i < 130:
        if i == 100:
          # Sends an estimation message
          PutToQueueWithTimeout(
              status_queue,
              ProducerThreadMessage(130, 0, start_time + 0.1 + 0.1 * i))
        PutToQueueWithTimeout(
            status_queue, MetadataMessage(start_time + 10 + 0.2 * (i - 100)))
      elif i < 150:
        if i == 130:
          # Sends a SeekAheadMessage
          PutToQueueWithTimeout(
              status_queue,
              SeekAheadMessage(190, 0, start_time + 10.1 + 0.2 * (i - 100)))
        PutToQueueWithTimeout(
            status_queue, MetadataMessage(start_time + 16 + 0.5 * (i - 130)))
      elif i < num_objects:
        if i == 150:
          # Sends a final ProducerThreadMessage
          PutToQueueWithTimeout(
              status_queue,
              ProducerThreadMessage(200,
                                    0,
                                    start_time + 16.1 + 0.5 * (i - 130),
                                    finished=True))
        PutToQueueWithTimeout(status_queue,
                              MetadataMessage(start_time + 26 + (i - 150)))
    PutToQueueWithTimeout(status_queue, FinalMessage(start_time + 100))
    PutToQueueWithTimeout(status_queue, ZERO_TASKS_TO_DO_ARGUMENT)
    JoinThreadAndRaiseOnTimeout(ui_thread)
    content = stream.getvalue()
    # We should not have estimated the number of objects as 130 in the UI.
    self.assertNotIn('/130 objects', content)
    # We should have estimated the number of objects as 190 in the UI.
    self.assertIn('/190 objects', content)
    # We should have estimated the number of objects as 200 in the UI.
    self.assertIn('/200 objects', content)
    # We should have calculated the throughput at all moments.
    # First 100 elements.
    self.assertIn('10.00 objects/s', content)
    # At one exact point between first and second round of elements.
    self.assertEqual(content.count('7.50 objects/s'), 1)
    # Next 30 elements.
    self.assertIn('5.00 objects/s', content)
    # At one exact point between second and third round of elements.
    self.assertEqual(content.count('3.50 objects/s'), 1)
    # Next 20 elements.
    self.assertIn('2.00 objects/s', content)
    # At one exact point between third and fourth round of elements.
    self.assertEqual(content.count('1.50 objects/s'), 1)
    # Final 50 elements.
    self.assertIn('1.00 objects/s', content)
    CheckUiOutputWithMFlag(self, content, 200, metadata=True)

  def test_ui_manager(self):
    """Tests the correctness of the UI manager.

    This test ensures a DataManager is created whenever a data message appears,
    regardless of previous MetadataMessages.
    """
    stream = six.StringIO()
    start_time = self.start_time
    ui_controller = UIController(custom_time=start_time)
    status_queue = MainThreadUIQueue(stream, ui_controller)
    # No manager has been created.
    self.assertEqual(ui_controller.manager, None)
    PutToQueueWithTimeout(status_queue, ProducerThreadMessage(2, 0, start_time))
    # Still no manager has been created.
    self.assertEqual(ui_controller.manager, None)
    PutToQueueWithTimeout(status_queue, MetadataMessage(start_time + 1))
    # Now we have a MetadataManager.
    self.assertIsInstance(ui_controller.manager, MetadataManager)
    PutToQueueWithTimeout(
        status_queue,
        FileMessage(StorageUrlFromString('foo'), None, start_time + 2))
    # Now we have a DataManager since the DataManager overwrites the
    # MetadataManager.
    self.assertIsInstance(ui_controller.manager, DataManager)

  def test_ui_BytesToFixedWidthString(self):
    """Tests the correctness of BytesToFixedWidthString."""
    self.assertEqual('    0.0 B', BytesToFixedWidthString(0, decimal_places=1))
    self.assertEqual('   0.00 B', BytesToFixedWidthString(0, decimal_places=2))
    self.assertEqual('  2.3 KiB',
                      BytesToFixedWidthString(2.27 * 1024, decimal_places=1))
    self.assertEqual(' 1023 KiB',
                      BytesToFixedWidthString(1023.2 * 1024, decimal_places=1))
    self.assertEqual('  1.0 MiB',
                      BytesToFixedWidthString(1024**2, decimal_places=1))
    self.assertEqual(
        '999.1 MiB', BytesToFixedWidthString(999.1 * 1024**2, decimal_places=1))

  def test_ui_spinner(self):
    stream = six.StringIO()
    start_time = self.start_time
    ui_controller = UIController(update_spinner_period=1,
                                 custom_time=start_time)
    status_queue = MainThreadUIQueue(stream, ui_controller)
    PutToQueueWithTimeout(status_queue,
                          ProducerThreadMessage(1, len('foo'), start_time))
    PutToQueueWithTimeout(
        status_queue,
        FileMessage(StorageUrlFromString('foo'),
                    None,
                    start_time,
                    message_type=FileMessage.FILE_UPLOAD))
    current_spinner = ui_controller.manager.GetSpinner()
    PutToQueueWithTimeout(
        status_queue,
        ProgressMessage(1, len('foo'), StorageUrlFromString('foo'),
                        start_time + 1.2))
    old_spinner1 = current_spinner
    current_spinner = ui_controller.manager.GetSpinner()
    # Spinner must have changed since more than 1 second has passed.
    self.assertNotEqual(old_spinner1, current_spinner)
    PutToQueueWithTimeout(
        status_queue,
        ProgressMessage(2, len('foo'), StorageUrlFromString('foo'),
                        start_time + 2))
    old_spinner2 = current_spinner
    current_spinner = ui_controller.manager.GetSpinner()
    # Spinner must not have changed since less than 1 second has passed.
    self.assertEqual(old_spinner2, current_spinner)
    PutToQueueWithTimeout(
        status_queue,
        ProgressMessage(3, len('foo'), StorageUrlFromString('foo'),
                        start_time + 2.5))
    old_spinner3 = current_spinner
    current_spinner = ui_controller.manager.GetSpinner()
    # Spinner must have changed since more than 1 second has passed.
    self.assertNotEqual(old_spinner3, current_spinner)
    PutToQueueWithTimeout(
        status_queue,
        FileMessage(StorageUrlFromString('foo'),
                    None,
                    start_time + 5,
                    finished=True,
                    message_type=FileMessage.FILE_UPLOAD))
    old_spinner4 = current_spinner
    current_spinner = ui_controller.manager.GetSpinner()
    # Spinner must have changed since more than 1 second has passed.
    self.assertNotEqual(old_spinner4, current_spinner)
    # Moreover, since we have 4 spinner characters and were only supposed to
    # change it twice, current_spinner must be different from old_spinner1 and
    # old_spinner3.
    self.assertNotEqual(old_spinner3, current_spinner)
    self.assertNotEqual(old_spinner1, current_spinner)
