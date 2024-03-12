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
import unittest

import six

from apitools.base.py import exceptions
import storage

_CLIENT = None


def _GetClient():
    global _CLIENT  # pylint: disable=global-statement
    if _CLIENT is None:
        _CLIENT = storage.StorageV1()
    return _CLIENT


class DownloadsTest(unittest.TestCase):
    _DEFAULT_BUCKET = 'apitools'
    _TESTDATA_PREFIX = 'testdata'

    def setUp(self):
        self.__client = _GetClient()
        self.__ResetDownload()

    def __ResetDownload(self, auto_transfer=False):
        self.__buffer = six.StringIO()
        self.__download = storage.Download.FromStream(
            self.__buffer, auto_transfer=auto_transfer)

    def __GetTestdataFileContents(self, filename):
        file_path = os.path.join(
            os.path.dirname(__file__), self._TESTDATA_PREFIX, filename)
        file_contents = open(file_path).read()
        self.assertIsNotNone(
            file_contents, msg=('Could not read file %s' % filename))
        return file_contents

    @classmethod
    def __GetRequest(cls, filename):
        object_name = os.path.join(cls._TESTDATA_PREFIX, filename)
        return storage.StorageObjectsGetRequest(
            bucket=cls._DEFAULT_BUCKET, object=object_name)

    def __GetFile(self, request):
        response = self.__client.objects.Get(request, download=self.__download)
        self.assertIsNone(response, msg=(
            'Unexpected nonempty response for file download: %s' % response))

    def __GetAndStream(self, request):
        self.__GetFile(request)
        self.__download.StreamInChunks()

    def testZeroBytes(self):
        request = self.__GetRequest('zero_byte_file')
        self.__GetAndStream(request)
        self.assertEqual(0, self.__buffer.tell())

    def testObjectDoesNotExist(self):
        self.__ResetDownload(auto_transfer=True)
        with self.assertRaises(exceptions.HttpError):
            self.__GetFile(self.__GetRequest('nonexistent_file'))

    def testAutoTransfer(self):
        self.__ResetDownload(auto_transfer=True)
        self.__GetFile(self.__GetRequest('fifteen_byte_file'))
        file_contents = self.__GetTestdataFileContents('fifteen_byte_file')
        self.assertEqual(15, self.__buffer.tell())
        self.__buffer.seek(0)
        self.assertEqual(file_contents, self.__buffer.read())

    def testFilenameWithSpaces(self):
        self.__ResetDownload(auto_transfer=True)
        self.__GetFile(self.__GetRequest('filename with spaces'))
        # NOTE(craigcitro): We add _ here to make this play nice with blaze.
        file_contents = self.__GetTestdataFileContents('filename_with_spaces')
        self.assertEqual(15, self.__buffer.tell())
        self.__buffer.seek(0)
        self.assertEqual(file_contents, self.__buffer.read())

    def testGetRange(self):
        # TODO(craigcitro): Test about a thousand more corner cases.
        file_contents = self.__GetTestdataFileContents('fifteen_byte_file')
        self.__GetFile(self.__GetRequest('fifteen_byte_file'))
        self.__download.GetRange(5, 10)
        self.assertEqual(6, self.__buffer.tell())
        self.__buffer.seek(0)
        self.assertEqual(file_contents[5:11], self.__buffer.read())

    def testGetRangeWithNegativeStart(self):
        file_contents = self.__GetTestdataFileContents('fifteen_byte_file')
        self.__GetFile(self.__GetRequest('fifteen_byte_file'))
        self.__download.GetRange(-3)
        self.assertEqual(3, self.__buffer.tell())
        self.__buffer.seek(0)
        self.assertEqual(file_contents[-3:], self.__buffer.read())

    def testGetRangeWithPositiveStart(self):
        file_contents = self.__GetTestdataFileContents('fifteen_byte_file')
        self.__GetFile(self.__GetRequest('fifteen_byte_file'))
        self.__download.GetRange(2)
        self.assertEqual(13, self.__buffer.tell())
        self.__buffer.seek(0)
        self.assertEqual(file_contents[2:15], self.__buffer.read())

    def testSmallChunksizes(self):
        file_contents = self.__GetTestdataFileContents('fifteen_byte_file')
        request = self.__GetRequest('fifteen_byte_file')
        for chunksize in (2, 3, 15, 100):
            self.__ResetDownload()
            self.__download.chunksize = chunksize
            self.__GetAndStream(request)
            self.assertEqual(15, self.__buffer.tell())
            self.__buffer.seek(0)
            self.assertEqual(file_contents, self.__buffer.read(15))

    def testLargeFileChunksizes(self):
        request = self.__GetRequest('thirty_meg_file')
        for chunksize in (1048576, 40 * 1048576):
            self.__ResetDownload()
            self.__download.chunksize = chunksize
            self.__GetAndStream(request)
            self.__buffer.seek(0)

    def testAutoGzipObject(self):
        # TODO(craigcitro): Move this to a new object once we have a more
        # permanent one, see: http://b/12250275
        request = storage.StorageObjectsGetRequest(
            bucket='ottenl-gzip', object='50K.txt')
        # First, try without auto-transfer.
        self.__GetFile(request)
        self.assertEqual(0, self.__buffer.tell())
        self.__download.StreamInChunks()
        self.assertEqual(50000, self.__buffer.tell())
        # Next, try with auto-transfer.
        self.__ResetDownload(auto_transfer=True)
        self.__GetFile(request)
        self.assertEqual(50000, self.__buffer.tell())

    def testSmallGzipObject(self):
        request = self.__GetRequest('zero-gzipd.html')
        self.__GetFile(request)
        self.assertEqual(0, self.__buffer.tell())
        additional_headers = {'accept-encoding': 'gzip, deflate'}
        self.__download.StreamInChunks(additional_headers=additional_headers)
        self.assertEqual(0, self.__buffer.tell())

    def testSerializedDownload(self):

        def _ProgressCallback(unused_response, download_object):
            print('Progress %s' % download_object.progress)

        file_contents = self.__GetTestdataFileContents('fifteen_byte_file')
        object_name = os.path.join(self._TESTDATA_PREFIX, 'fifteen_byte_file')
        request = storage.StorageObjectsGetRequest(
            bucket=self._DEFAULT_BUCKET, object=object_name)
        response = self.__client.objects.Get(request)
        # pylint: disable=attribute-defined-outside-init
        self.__buffer = six.StringIO()
        download_data = json.dumps({
            'auto_transfer': False,
            'progress': 0,
            'total_size': response.size,
            'url': response.mediaLink,
        })
        self.__download = storage.Download.FromData(
            self.__buffer, download_data, http=self.__client.http)
        self.__download.StreamInChunks(callback=_ProgressCallback)
        self.assertEqual(15, self.__buffer.tell())
        self.__buffer.seek(0)
        self.assertEqual(file_contents, self.__buffer.read(15))

if __name__ == '__main__':
    unittest.main()
