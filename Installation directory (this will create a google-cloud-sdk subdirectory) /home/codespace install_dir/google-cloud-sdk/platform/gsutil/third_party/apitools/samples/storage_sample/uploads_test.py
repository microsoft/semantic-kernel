#
# Copyright 2015 Google Inc.
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

"""Integration tests for uploading and downloading to GCS.

These tests exercise most of the corner cases for upload/download of
files in apitools, via GCS. There are no performance tests here yet.
"""

import json
import os
import random
import string
import unittest

import six

from apitools.base.py import transfer
import storage

_CLIENT = None


def _GetClient():
    global _CLIENT  # pylint: disable=global-statement
    if _CLIENT is None:
        _CLIENT = storage.StorageV1()
    return _CLIENT


class UploadsTest(unittest.TestCase):
    _DEFAULT_BUCKET = 'apitools'
    _TESTDATA_PREFIX = 'uploads'

    def setUp(self):
        self.__client = _GetClient()
        self.__files = []
        self.__content = ''
        self.__buffer = None
        self.__upload = None

    def tearDown(self):
        self.__DeleteFiles()

    def __ResetUpload(self, size, auto_transfer=True):
        self.__content = ''.join(
            random.choice(string.ascii_letters) for _ in range(size))
        self.__buffer = six.StringIO(self.__content)
        self.__upload = storage.Upload.FromStream(
            self.__buffer, 'text/plain', auto_transfer=auto_transfer)

    def __DeleteFiles(self):
        for filename in self.__files:
            self.__DeleteFile(filename)

    def __DeleteFile(self, filename):
        object_name = os.path.join(self._TESTDATA_PREFIX, filename)
        req = storage.StorageObjectsDeleteRequest(
            bucket=self._DEFAULT_BUCKET, object=object_name)
        self.__client.objects.Delete(req)

    def __InsertRequest(self, filename):
        object_name = os.path.join(self._TESTDATA_PREFIX, filename)
        return storage.StorageObjectsInsertRequest(
            name=object_name, bucket=self._DEFAULT_BUCKET)

    def __GetRequest(self, filename):
        object_name = os.path.join(self._TESTDATA_PREFIX, filename)
        return storage.StorageObjectsGetRequest(
            object=object_name, bucket=self._DEFAULT_BUCKET)

    def __InsertFile(self, filename, request=None):
        if request is None:
            request = self.__InsertRequest(filename)
        response = self.__client.objects.Insert(request, upload=self.__upload)
        self.assertIsNotNone(response)
        self.__files.append(filename)
        return response

    def testZeroBytes(self):
        filename = 'zero_byte_file'
        self.__ResetUpload(0)
        response = self.__InsertFile(filename)
        self.assertEqual(0, response.size)

    def testSimpleUpload(self):
        filename = 'fifteen_byte_file'
        self.__ResetUpload(15)
        response = self.__InsertFile(filename)
        self.assertEqual(15, response.size)

    def testMultipartUpload(self):
        filename = 'fifteen_byte_file'
        self.__ResetUpload(15)
        request = self.__InsertRequest(filename)
        request.object = storage.Object(contentLanguage='en')
        response = self.__InsertFile(filename, request=request)
        self.assertEqual(15, response.size)
        self.assertEqual('en', response.contentLanguage)

    def testAutoUpload(self):
        filename = 'ten_meg_file'
        size = 10 << 20
        self.__ResetUpload(size)
        request = self.__InsertRequest(filename)
        response = self.__InsertFile(filename, request=request)
        self.assertEqual(size, response.size)

    def testStreamMedia(self):
        filename = 'ten_meg_file'
        size = 10 << 20
        self.__ResetUpload(size, auto_transfer=False)
        self.__upload.strategy = 'resumable'
        self.__upload.total_size = size
        request = self.__InsertRequest(filename)
        initial_response = self.__client.objects.Insert(
            request, upload=self.__upload)
        self.assertIsNotNone(initial_response)
        self.assertEqual(0, self.__buffer.tell())
        self.__upload.StreamMedia()
        self.assertEqual(size, self.__buffer.tell())

    def testBreakAndResumeUpload(self):
        filename = ('ten_meg_file_' +
                    ''.join(random.sample(string.ascii_letters, 5)))
        size = 10 << 20
        self.__ResetUpload(size, auto_transfer=False)
        self.__upload.strategy = 'resumable'
        self.__upload.total_size = size
        # Start the upload
        request = self.__InsertRequest(filename)
        initial_response = self.__client.objects.Insert(
            request, upload=self.__upload)
        self.assertIsNotNone(initial_response)
        self.assertEqual(0, self.__buffer.tell())
        # Pretend the process died, and resume with a new attempt at the
        # same upload.
        upload_data = json.dumps(self.__upload.serialization_data)
        second_upload_attempt = transfer.Upload.FromData(
            self.__buffer, upload_data, self.__upload.http)
        second_upload_attempt._Upload__SendChunk(0)
        self.assertEqual(second_upload_attempt.chunksize, self.__buffer.tell())
        # Simulate a third try, and stream from there.
        final_upload_attempt = transfer.Upload.FromData(
            self.__buffer, upload_data, self.__upload.http)
        final_upload_attempt.StreamInChunks()
        self.assertEqual(size, self.__buffer.tell())
        # Verify the upload
        object_info = self.__client.objects.Get(self.__GetRequest(filename))
        self.assertEqual(size, object_info.size)
        # Confirm that a new attempt successfully does nothing.
        completed_upload_attempt = transfer.Upload.FromData(
            self.__buffer, upload_data, self.__upload.http)
        self.assertTrue(completed_upload_attempt.complete)
        completed_upload_attempt.StreamInChunks()
        # Verify the upload didn't pick up extra bytes.
        object_info = self.__client.objects.Get(self.__GetRequest(filename))
        self.assertEqual(size, object_info.size)
        # TODO(craigcitro): Add tests for callbacks (especially around
        # finish callback).

if __name__ == '__main__':
    unittest.main()
