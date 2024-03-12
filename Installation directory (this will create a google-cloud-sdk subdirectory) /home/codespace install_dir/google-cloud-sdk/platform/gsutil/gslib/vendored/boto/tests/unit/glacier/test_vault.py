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
from boto.compat import StringIO
from tests.compat import mock, unittest

ANY = mock.ANY

from boto.glacier import vault
from boto.glacier.job import Job
from boto.glacier.response import GlacierResponse


class TestVault(unittest.TestCase):
    def setUp(self):
        self.size_patch = mock.patch('os.path.getsize')
        self.getsize = self.size_patch.start()
        self.api = mock.Mock()
        self.vault = vault.Vault(self.api, None)
        self.vault.name = 'myvault'
        self.mock_open = mock.mock_open()
        stringio = StringIO('content')
        self.mock_open.return_value.read = stringio.read

    def tearDown(self):
        self.size_patch.stop()

    @mock.patch('boto.glacier.vault.compute_hashes_from_fileobj',
                return_value=[b'abc', b'123'])
    def test_upload_archive_small_file(self, compute_hashes):
        self.getsize.return_value = 1

        self.api.upload_archive.return_value = {'ArchiveId': 'archive_id'}
        with mock.patch('boto.glacier.vault.open', self.mock_open,
                        create=True):
            archive_id = self.vault.upload_archive(
                'filename', 'my description')
        self.assertEqual(archive_id, 'archive_id')
        self.api.upload_archive.assert_called_with(
            'myvault', self.mock_open.return_value,
            mock.ANY, mock.ANY, 'my description')

    def test_small_part_size_is_obeyed(self):
        self.vault.DefaultPartSize = 2 * 1024 * 1024
        self.vault.create_archive_writer = mock.Mock()

        self.getsize.return_value = 1

        with mock.patch('boto.glacier.vault.open', self.mock_open,
                        create=True):
            self.vault.create_archive_from_file('myfile')
        # The write should be created with the default part size of the
        # instance (2 MB).
        self.vault.create_archive_writer.assert_called_with(
            description=mock.ANY, part_size=self.vault.DefaultPartSize)

    def test_large_part_size_is_obeyed(self):
        self.vault.DefaultPartSize = 8 * 1024 * 1024
        self.vault.create_archive_writer = mock.Mock()
        self.getsize.return_value = 1
        with mock.patch('boto.glacier.vault.open', self.mock_open,
                        create=True):
            self.vault.create_archive_from_file('myfile')
        # The write should be created with the default part size of the
        # instance (8 MB).
        self.vault.create_archive_writer.assert_called_with(
            description=mock.ANY, part_size=self.vault.DefaultPartSize)

    def test_part_size_needs_to_be_adjusted(self):
        # If we have a large file (400 GB)
        self.getsize.return_value = 400 * 1024 * 1024 * 1024
        self.vault.create_archive_writer = mock.Mock()
        # When we try to upload the file.
        with mock.patch('boto.glacier.vault.open', self.mock_open,
                        create=True):
            self.vault.create_archive_from_file('myfile')
        # We should automatically bump up the part size used to
        # 64 MB.
        expected_part_size = 64 * 1024 * 1024
        self.vault.create_archive_writer.assert_called_with(
            description=mock.ANY, part_size=expected_part_size)

    def test_retrieve_inventory(self):
        class FakeResponse(object):
            status = 202

            def getheader(self, key, default=None):
                if key == 'x-amz-job-id':
                    return 'HkF9p6'
                elif key == 'Content-Type':
                    return 'application/json'

                return 'something'

            def read(self, amt=None):
                return b"""{
  "Action": "ArchiveRetrieval",
  "ArchiveId": "NkbByEejwEggmBz2fTHgJrg0XBoDfjP4q6iu87-EXAMPLEArchiveId",
  "ArchiveSizeInBytes": 16777216,
  "ArchiveSHA256TreeHash": "beb0fe31a1c7ca8c6c04d574ea906e3f97",
  "Completed": false,
  "CreationDate": "2012-05-15T17:21:39.339Z",
  "CompletionDate": "2012-05-15T17:21:43.561Z",
  "InventorySizeInBytes": null,
  "JobDescription": "My ArchiveRetrieval Job",
  "JobId": "HkF9p6",
  "RetrievalByteRange": "0-16777215",
  "SHA256TreeHash": "beb0fe31a1c7ca8c6c04d574ea906e3f97b31fd",
  "SNSTopic": "arn:aws:sns:us-east-1:012345678901:mytopic",
  "StatusCode": "InProgress",
  "StatusMessage": "Operation in progress.",
  "VaultARN": "arn:aws:glacier:us-east-1:012345678901:vaults/examplevault"
}"""

        raw_resp = FakeResponse()
        init_resp = GlacierResponse(raw_resp, [('x-amz-job-id', 'JobId')])
        raw_resp_2 = FakeResponse()
        desc_resp = GlacierResponse(raw_resp_2, [])

        with mock.patch.object(self.vault.layer1, 'initiate_job',
                               return_value=init_resp):
            with mock.patch.object(self.vault.layer1, 'describe_job',
                                   return_value=desc_resp):
                # The old/back-compat variant of the call.
                self.assertEqual(self.vault.retrieve_inventory(), 'HkF9p6')

                # The variant the returns a full ``Job`` object.
                job = self.vault.retrieve_inventory_job()
                self.assertTrue(isinstance(job, Job))
                self.assertEqual(job.id, 'HkF9p6')


class TestConcurrentUploads(unittest.TestCase):

    def test_concurrent_upload_file(self):
        v = vault.Vault(None, None)
        with mock.patch('boto.glacier.vault.ConcurrentUploader') as c:
            c.return_value.upload.return_value = 'archive_id'
            archive_id = v.concurrent_create_archive_from_file(
                'filename', 'my description')
            c.return_value.upload.assert_called_with('filename',
                                                     'my description')
        self.assertEqual(archive_id, 'archive_id')

    def test_concurrent_upload_forwards_kwargs(self):
        v = vault.Vault(None, None)
        with mock.patch('boto.glacier.vault.ConcurrentUploader') as c:
            c.return_value.upload.return_value = 'archive_id'
            archive_id = v.concurrent_create_archive_from_file(
                'filename', 'my description', num_threads=10,
                part_size=1024 * 1024 * 1024 * 8)
            c.assert_called_with(None, None, num_threads=10,
                                 part_size=1024 * 1024 * 1024 * 8)


if __name__ == '__main__':
    unittest.main()
