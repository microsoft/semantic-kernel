# Copyright 2010 Google Inc.
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

"""
Tests of resumable downloads.
"""

import errno
import os
import re

import boto
from boto.s3.resumable_download_handler import get_cur_file_size
from boto.s3.resumable_download_handler import ResumableDownloadHandler
from boto.exception import ResumableTransferDisposition
from boto.exception import ResumableDownloadException
from .cb_test_harness import CallbackTestHarness
from tests.integration.gs.testcase import GSTestCase


SMALL_KEY_SIZE = 2 * 1024 # 2 KB.
LARGE_KEY_SIZE = 500 * 1024 # 500 KB.


class ResumableDownloadTests(GSTestCase):
    """Resumable download test suite."""

    def make_small_key(self):
        small_src_key_as_string = os.urandom(SMALL_KEY_SIZE)
        small_src_key = self._MakeKey(data=small_src_key_as_string)
        return small_src_key_as_string, small_src_key

    def make_tracker_file(self, tmpdir=None):
        if not tmpdir:
            tmpdir = self._MakeTempDir()
        tracker_file = os.path.join(tmpdir, 'tracker')
        return tracker_file

    def make_dst_fp(self, tmpdir=None):
        if not tmpdir:
            tmpdir = self._MakeTempDir()
        dst_file = os.path.join(tmpdir, 'dstfile')
        return open(dst_file, 'w')

    def test_non_resumable_download(self):
        """
        Tests that non-resumable downloads work
        """
        dst_fp = self.make_dst_fp()
        small_src_key_as_string, small_src_key = self.make_small_key()
        small_src_key.get_contents_to_file(dst_fp)
        self.assertEqual(SMALL_KEY_SIZE,
                         get_cur_file_size(dst_fp))
        self.assertEqual(small_src_key_as_string,
                         small_src_key.get_contents_as_string())

    def test_download_without_persistent_tracker(self):
        """
        Tests a single resumable download, with no tracker persistence
        """
        res_download_handler = ResumableDownloadHandler()
        dst_fp = self.make_dst_fp()
        small_src_key_as_string, small_src_key = self.make_small_key()
        small_src_key.get_contents_to_file(
            dst_fp, res_download_handler=res_download_handler)
        self.assertEqual(SMALL_KEY_SIZE,
                         get_cur_file_size(dst_fp))
        self.assertEqual(small_src_key_as_string,
                         small_src_key.get_contents_as_string())

    def test_failed_download_with_persistent_tracker(self):
        """
        Tests that failed resumable download leaves a correct tracker file
        """
        harness = CallbackTestHarness()
        tmpdir = self._MakeTempDir()
        tracker_file_name = self.make_tracker_file(tmpdir)
        dst_fp = self.make_dst_fp(tmpdir)
        res_download_handler = ResumableDownloadHandler(
            tracker_file_name=tracker_file_name, num_retries=0)
        small_src_key_as_string, small_src_key = self.make_small_key()
        try:
            small_src_key.get_contents_to_file(
                dst_fp, cb=harness.call,
                res_download_handler=res_download_handler)
            self.fail('Did not get expected ResumableDownloadException')
        except ResumableDownloadException as e:
            # We'll get a ResumableDownloadException at this point because
            # of CallbackTestHarness (above). Check that the tracker file was
            # created correctly.
            self.assertEqual(e.disposition,
                             ResumableTransferDisposition.ABORT_CUR_PROCESS)
            self.assertTrue(os.path.exists(tracker_file_name))
            f = open(tracker_file_name)
            etag_line = f.readline()
            self.assertEquals(etag_line.rstrip('\n'), small_src_key.etag.strip('"\''))

    def test_retryable_exception_recovery(self):
        """
        Tests handling of a retryable exception
        """
        # Test one of the RETRYABLE_EXCEPTIONS.
        exception = ResumableDownloadHandler.RETRYABLE_EXCEPTIONS[0]
        harness = CallbackTestHarness(exception=exception)
        res_download_handler = ResumableDownloadHandler(num_retries=1)
        dst_fp = self.make_dst_fp()
        small_src_key_as_string, small_src_key = self.make_small_key()
        small_src_key.get_contents_to_file(
            dst_fp, cb=harness.call,
            res_download_handler=res_download_handler)
        # Ensure downloaded object has correct content.
        self.assertEqual(SMALL_KEY_SIZE,
                         get_cur_file_size(dst_fp))
        self.assertEqual(small_src_key_as_string,
                         small_src_key.get_contents_as_string())

    def test_broken_pipe_recovery(self):
        """
        Tests handling of a Broken Pipe (which interacts with an httplib bug)
        """
        exception = IOError(errno.EPIPE, "Broken pipe")
        harness = CallbackTestHarness(exception=exception)
        res_download_handler = ResumableDownloadHandler(num_retries=1)
        dst_fp = self.make_dst_fp()
        small_src_key_as_string, small_src_key = self.make_small_key()
        small_src_key.get_contents_to_file(
            dst_fp, cb=harness.call,
            res_download_handler=res_download_handler)
        # Ensure downloaded object has correct content.
        self.assertEqual(SMALL_KEY_SIZE,
                         get_cur_file_size(dst_fp))
        self.assertEqual(small_src_key_as_string,
                         small_src_key.get_contents_as_string())

    def test_non_retryable_exception_handling(self):
        """
        Tests resumable download that fails with a non-retryable exception
        """
        harness = CallbackTestHarness(
            exception=OSError(errno.EACCES, 'Permission denied'))
        res_download_handler = ResumableDownloadHandler(num_retries=1)
        dst_fp = self.make_dst_fp()
        small_src_key_as_string, small_src_key = self.make_small_key()
        try:
            small_src_key.get_contents_to_file(
                dst_fp, cb=harness.call,
                res_download_handler=res_download_handler)
            self.fail('Did not get expected OSError')
        except OSError as e:
            # Ensure the error was re-raised.
            self.assertEqual(e.errno, 13)

    def test_failed_and_restarted_download_with_persistent_tracker(self):
        """
        Tests resumable download that fails once and then completes,
        with tracker file
        """
        harness = CallbackTestHarness()
        tmpdir = self._MakeTempDir()
        tracker_file_name = self.make_tracker_file(tmpdir)
        dst_fp = self.make_dst_fp(tmpdir)
        small_src_key_as_string, small_src_key = self.make_small_key()
        res_download_handler = ResumableDownloadHandler(
            tracker_file_name=tracker_file_name, num_retries=1)
        small_src_key.get_contents_to_file(
            dst_fp, cb=harness.call,
            res_download_handler=res_download_handler)
        # Ensure downloaded object has correct content.
        self.assertEqual(SMALL_KEY_SIZE,
                         get_cur_file_size(dst_fp))
        self.assertEqual(small_src_key_as_string,
                         small_src_key.get_contents_as_string())
        # Ensure tracker file deleted.
        self.assertFalse(os.path.exists(tracker_file_name))

    def test_multiple_in_process_failures_then_succeed(self):
        """
        Tests resumable download that fails twice in one process, then completes
        """
        res_download_handler = ResumableDownloadHandler(num_retries=3)
        dst_fp = self.make_dst_fp()
        small_src_key_as_string, small_src_key = self.make_small_key()
        small_src_key.get_contents_to_file(
            dst_fp, res_download_handler=res_download_handler)
        # Ensure downloaded object has correct content.
        self.assertEqual(SMALL_KEY_SIZE,
                         get_cur_file_size(dst_fp))
        self.assertEqual(small_src_key_as_string,
                         small_src_key.get_contents_as_string())

    def test_multiple_in_process_failures_then_succeed_with_tracker_file(self):
        """
        Tests resumable download that fails completely in one process,
        then when restarted completes, using a tracker file
        """
        # Set up test harness that causes more failures than a single
        # ResumableDownloadHandler instance will handle, writing enough data
        # before the first failure that some of it survives that process run.
        harness = CallbackTestHarness(
            fail_after_n_bytes=LARGE_KEY_SIZE/2, num_times_to_fail=2)
        larger_src_key_as_string = os.urandom(LARGE_KEY_SIZE)
        larger_src_key = self._MakeKey(data=larger_src_key_as_string)
        tmpdir = self._MakeTempDir()
        tracker_file_name = self.make_tracker_file(tmpdir)
        dst_fp = self.make_dst_fp(tmpdir)
        res_download_handler = ResumableDownloadHandler(
            tracker_file_name=tracker_file_name, num_retries=0)
        try:
            larger_src_key.get_contents_to_file(
                dst_fp, cb=harness.call,
                res_download_handler=res_download_handler)
            self.fail('Did not get expected ResumableDownloadException')
        except ResumableDownloadException as e:
            self.assertEqual(e.disposition,
                             ResumableTransferDisposition.ABORT_CUR_PROCESS)
            # Ensure a tracker file survived.
            self.assertTrue(os.path.exists(tracker_file_name))
        # Try it one more time; this time should succeed.
        larger_src_key.get_contents_to_file(
            dst_fp, cb=harness.call,
            res_download_handler=res_download_handler)
        self.assertEqual(LARGE_KEY_SIZE,
                         get_cur_file_size(dst_fp))
        self.assertEqual(larger_src_key_as_string,
                         larger_src_key.get_contents_as_string())
        self.assertFalse(os.path.exists(tracker_file_name))
        # Ensure some of the file was downloaded both before and after failure.
        self.assertTrue(
            len(harness.transferred_seq_before_first_failure) > 1 and
            len(harness.transferred_seq_after_first_failure) > 1)

    def test_download_with_inital_partial_download_before_failure(self):
        """
        Tests resumable download that successfully downloads some content
        before it fails, then restarts and completes
        """
        # Set up harness to fail download after several hundred KB so download
        # server will have saved something before we retry.
        harness = CallbackTestHarness(
            fail_after_n_bytes=LARGE_KEY_SIZE/2)
        larger_src_key_as_string = os.urandom(LARGE_KEY_SIZE)
        larger_src_key = self._MakeKey(data=larger_src_key_as_string)
        res_download_handler = ResumableDownloadHandler(num_retries=1)
        dst_fp = self.make_dst_fp()
        larger_src_key.get_contents_to_file(
            dst_fp, cb=harness.call,
            res_download_handler=res_download_handler)
        # Ensure downloaded object has correct content.
        self.assertEqual(LARGE_KEY_SIZE,
                         get_cur_file_size(dst_fp))
        self.assertEqual(larger_src_key_as_string,
                         larger_src_key.get_contents_as_string())
        # Ensure some of the file was downloaded both before and after failure.
        self.assertTrue(
            len(harness.transferred_seq_before_first_failure) > 1 and
            len(harness.transferred_seq_after_first_failure) > 1)

    def test_zero_length_object_download(self):
        """
        Tests downloading a zero-length object (exercises boundary conditions).
        """
        res_download_handler = ResumableDownloadHandler()
        dst_fp = self.make_dst_fp()
        k = self._MakeKey()
        k.get_contents_to_file(dst_fp,
                               res_download_handler=res_download_handler)
        self.assertEqual(0, get_cur_file_size(dst_fp))

    def test_download_with_invalid_tracker_etag(self):
        """
        Tests resumable download with a tracker file containing an invalid etag
        """
        tmp_dir = self._MakeTempDir()
        dst_fp = self.make_dst_fp(tmp_dir)
        small_src_key_as_string, small_src_key = self.make_small_key()
        invalid_etag_tracker_file_name = os.path.join(tmp_dir,
                                                      'invalid_etag_tracker')
        f = open(invalid_etag_tracker_file_name, 'w')
        f.write('3.14159\n')
        f.close()
        res_download_handler = ResumableDownloadHandler(
            tracker_file_name=invalid_etag_tracker_file_name)
        # An error should be printed about the invalid tracker, but then it
        # should run the update successfully.
        small_src_key.get_contents_to_file(
            dst_fp, res_download_handler=res_download_handler)
        self.assertEqual(SMALL_KEY_SIZE, get_cur_file_size(dst_fp))
        self.assertEqual(small_src_key_as_string,
                         small_src_key.get_contents_as_string())

    def test_download_with_inconsistent_etag_in_tracker(self):
        """
        Tests resumable download with an inconsistent etag in tracker file
        """
        tmp_dir = self._MakeTempDir()
        dst_fp = self.make_dst_fp(tmp_dir)
        small_src_key_as_string, small_src_key = self.make_small_key()
        inconsistent_etag_tracker_file_name = os.path.join(tmp_dir,
            'inconsistent_etag_tracker')
        f = open(inconsistent_etag_tracker_file_name, 'w')
        good_etag = small_src_key.etag.strip('"\'')
        new_val_as_list = []
        for c in reversed(good_etag):
            new_val_as_list.append(c)
        f.write('%s\n' % ''.join(new_val_as_list))
        f.close()
        res_download_handler = ResumableDownloadHandler(
            tracker_file_name=inconsistent_etag_tracker_file_name)
        # An error should be printed about the expired tracker, but then it
        # should run the update successfully.
        small_src_key.get_contents_to_file(
            dst_fp, res_download_handler=res_download_handler)
        self.assertEqual(SMALL_KEY_SIZE,
                         get_cur_file_size(dst_fp))
        self.assertEqual(small_src_key_as_string,
                         small_src_key.get_contents_as_string())

    def test_download_with_unwritable_tracker_file(self):
        """
        Tests resumable download with an unwritable tracker file
        """
        # Make dir where tracker_file lives temporarily unwritable.
        tmp_dir = self._MakeTempDir()
        tracker_file_name = os.path.join(tmp_dir, 'tracker')
        save_mod = os.stat(tmp_dir).st_mode
        try:
            os.chmod(tmp_dir, 0)
            res_download_handler = ResumableDownloadHandler(
                tracker_file_name=tracker_file_name)
        except ResumableDownloadException as e:
            self.assertEqual(e.disposition, ResumableTransferDisposition.ABORT)
            self.assertNotEqual(
                e.message.find('Couldn\'t write URI tracker file'), -1)
        finally:
            # Restore original protection of dir where tracker_file lives.
            os.chmod(tmp_dir, save_mod)
