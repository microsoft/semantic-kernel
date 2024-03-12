#!/usr/bin/env python
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
#
import tempfile
from boto.compat import Queue

from tests.compat import mock, unittest
from tests.unit import AWSMockServiceTestCase

from boto.glacier.concurrent import ConcurrentUploader, ConcurrentDownloader
from boto.glacier.concurrent import UploadWorkerThread
from boto.glacier.concurrent import _END_SENTINEL


class FakeThreadedConcurrentUploader(ConcurrentUploader):
    def _start_upload_threads(self, results_queue, upload_id,
                              worker_queue, filename):
        self.results_queue = results_queue
        self.worker_queue = worker_queue
        self.upload_id = upload_id

    def _wait_for_upload_threads(self, hash_chunks, result_queue, total_parts):
        for i in range(total_parts):
            hash_chunks[i] = b'foo'


class FakeThreadedConcurrentDownloader(ConcurrentDownloader):
    def _start_download_threads(self, results_queue, worker_queue):
        self.results_queue = results_queue
        self.worker_queue = worker_queue

    def _wait_for_download_threads(self, filename, result_queue, total_parts):
        pass


class TestConcurrentUploader(unittest.TestCase):

    def setUp(self):
        super(TestConcurrentUploader, self).setUp()
        self.stat_patch = mock.patch('os.stat')
        self.addCleanup(self.stat_patch.stop)
        self.stat_mock = self.stat_patch.start()
        # Give a default value for tests that don't care
        # what the file size is.
        self.stat_mock.return_value.st_size = 1024 * 1024 * 8

    def test_calculate_required_part_size(self):
        self.stat_mock.return_value.st_size = 1024 * 1024 * 8
        uploader = ConcurrentUploader(mock.Mock(), 'vault_name')
        total_parts, part_size = uploader._calculate_required_part_size(
            1024 * 1024 * 8)
        self.assertEqual(total_parts, 2)
        self.assertEqual(part_size, 4 * 1024 * 1024)

    def test_calculate_required_part_size_too_small(self):
        too_small = 1 * 1024 * 1024
        self.stat_mock.return_value.st_size = 1024 * 1024 * 1024
        uploader = ConcurrentUploader(mock.Mock(), 'vault_name',
                                      part_size=too_small)
        total_parts, part_size = uploader._calculate_required_part_size(
            1024 * 1024 * 1024)
        self.assertEqual(total_parts, 256)
        # Part size if 4MB not the passed in 1MB.
        self.assertEqual(part_size, 4 * 1024 * 1024)

    def test_work_queue_is_correctly_populated(self):
        uploader = FakeThreadedConcurrentUploader(mock.MagicMock(),
                                                  'vault_name')
        uploader.upload('foofile')
        q = uploader.worker_queue
        items = [q.get() for i in range(q.qsize())]
        self.assertEqual(items[0], (0, 4 * 1024 * 1024))
        self.assertEqual(items[1], (1, 4 * 1024 * 1024))
        # 2 for the parts, 10 for the end sentinels (10 threads).
        self.assertEqual(len(items), 12)

    def test_correct_low_level_api_calls(self):
        api_mock = mock.MagicMock()
        upload_id = '0898d645-ea45-4548-9a67-578f507ead49'
        initiate_upload_mock = mock.Mock(
            return_value={'UploadId': upload_id})
        # initiate_multipart_upload must return a body containing an `UploadId`
        api_mock.attach_mock(initiate_upload_mock, 'initiate_multipart_upload')

        uploader = FakeThreadedConcurrentUploader(api_mock, 'vault_name')
        uploader.upload('foofile')
        # The threads call the upload_part, so we're just verifying the
        # initiate/complete multipart API calls.
        initiate_upload_mock.assert_called_with(
            'vault_name', 4 * 1024 * 1024, None)
        api_mock.complete_multipart_upload.assert_called_with(
            'vault_name', upload_id, mock.ANY, 8 * 1024 * 1024)

    def test_downloader_work_queue_is_correctly_populated(self):
        job = mock.MagicMock()
        job.archive_size = 8 * 1024 * 1024
        downloader = FakeThreadedConcurrentDownloader(job)
        downloader.download('foofile')
        q = downloader.worker_queue
        items = [q.get() for i in range(q.qsize())]
        self.assertEqual(items[0], (0, 4 * 1024 * 1024))
        self.assertEqual(items[1], (1, 4 * 1024 * 1024))
        # 2 for the parts, 10 for the end sentinels (10 threads).
        self.assertEqual(len(items), 12)


class TestUploaderThread(unittest.TestCase):
    def setUp(self):
        self.fileobj = tempfile.NamedTemporaryFile()
        self.filename = self.fileobj.name

    def test_fileobj_closed_when_thread_shuts_down(self):
        thread = UploadWorkerThread(mock.Mock(), 'vault_name',
                                    self.filename, 'upload_id',
                                    Queue(), Queue())
        fileobj = thread._fileobj
        self.assertFalse(fileobj.closed)
        # By settings should_continue to False, it should immediately
        # exit, and we can still verify cleanup behavior.
        thread.should_continue = False
        thread.run()
        self.assertTrue(fileobj.closed)

    def test_upload_errors_have_exception_messages(self):
        api = mock.Mock()
        job_queue = Queue()
        result_queue = Queue()
        upload_thread = UploadWorkerThread(
            api, 'vault_name', self.filename,
            'upload_id', job_queue, result_queue, num_retries=1,
            time_between_retries=0)
        api.upload_part.side_effect = Exception("exception message")
        job_queue.put((0, 1024))
        job_queue.put(_END_SENTINEL)

        upload_thread.run()
        result = result_queue.get(timeout=1)
        self.assertIn("exception message", str(result))

    def test_num_retries_is_obeyed(self):
        # total attempts is 1 + num_retries so if I have num_retries of 2,
        # I'll attempt the upload once, and if that fails I'll retry up to
        # 2 more times for a total of 3 attempts.
        api = mock.Mock()
        job_queue = Queue()
        result_queue = Queue()
        upload_thread = UploadWorkerThread(
            api, 'vault_name', self.filename,
            'upload_id', job_queue, result_queue, num_retries=2,
            time_between_retries=0)
        api.upload_part.side_effect = Exception()
        job_queue.put((0, 1024))
        job_queue.put(_END_SENTINEL)

        upload_thread.run()
        self.assertEqual(api.upload_part.call_count, 3)


if __name__ == '__main__':
    unittest.main()
