# -*- coding: utf-8 -*-

# Copyright (c) 2011 Mitch Garnaat http://garnaat.org/
# All rights reserved.
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
Some unit tests for the S3 MultiPartUpload
"""

# Note:
# Multipart uploads require at least one part. If you upload
# multiple parts then all parts except the last part has to be
# bigger than 5M. Hence we just use 1 part so we can keep
# things small and still test logic.

import os
import unittest
import time
from boto.compat import StringIO

import mock

import boto
from boto.s3.connection import S3Connection


class S3MultiPartUploadTest(unittest.TestCase):
    s3 = True

    def setUp(self):
        self.conn = S3Connection(is_secure=False)
        self.bucket_name = 'multipart-%d' % int(time.time())
        self.bucket = self.conn.create_bucket(self.bucket_name)

    def tearDown(self):
        for key in self.bucket:
            key.delete()
        self.bucket.delete()

    def test_abort(self):
        key_name = u"テスト"
        mpu = self.bucket.initiate_multipart_upload(key_name)
        mpu.cancel_upload()

    def test_complete_ascii(self):
        key_name = "test"
        mpu = self.bucket.initiate_multipart_upload(key_name)
        fp = StringIO("small file")
        mpu.upload_part_from_file(fp, part_num=1)
        fp.close()
        cmpu = mpu.complete_upload()
        self.assertEqual(cmpu.key_name, key_name)
        self.assertNotEqual(cmpu.etag, None)

    def test_complete_japanese(self):
        key_name = u"テスト"
        mpu = self.bucket.initiate_multipart_upload(key_name)
        fp = StringIO("small file")
        mpu.upload_part_from_file(fp, part_num=1)
        fp.close()
        cmpu = mpu.complete_upload()
        self.assertEqual(cmpu.key_name, key_name)
        self.assertNotEqual(cmpu.etag, None)

    def test_list_japanese(self):
        key_name = u"テスト"
        mpu = self.bucket.initiate_multipart_upload(key_name)
        rs = self.bucket.list_multipart_uploads()
        # New bucket, so only one upload expected
        lmpu = next(iter(rs))
        self.assertEqual(lmpu.id, mpu.id)
        self.assertEqual(lmpu.key_name, key_name)
        # Abort using the one returned in the list
        lmpu.cancel_upload()

    def test_list_multipart_uploads(self):
        key_name = u"テスト"
        mpus = []
        mpus.append(self.bucket.initiate_multipart_upload(key_name))
        mpus.append(self.bucket.initiate_multipart_upload(key_name))
        rs = self.bucket.list_multipart_uploads()
        # uploads (for a key) are returned in time initiated asc order
        for lmpu in rs:
            ompu = mpus.pop(0)
            self.assertEqual(lmpu.key_name, ompu.key_name)
            self.assertEqual(lmpu.id, ompu.id)
        self.assertEqual(0, len(mpus))

    def test_get_all_multipart_uploads(self):
        key1 = 'a'
        key2 = 'b/c'
        mpu1 = self.bucket.initiate_multipart_upload(key1)
        mpu2 = self.bucket.initiate_multipart_upload(key2)
        rs = self.bucket.get_all_multipart_uploads(prefix='b/', delimiter='/')
        for lmpu in rs:
            # only expect upload for key2 (mpu2) returned
            self.assertEqual(lmpu.key_name, mpu2.key_name)
            self.assertEqual(lmpu.id, mpu2.id)

    def test_four_part_file(self):
        key_name = "k"
        contents = "01234567890123456789"
        sfp = StringIO(contents)

        # upload 20 bytes in 4 parts of 5 bytes each
        mpu = self.bucket.initiate_multipart_upload(key_name)
        mpu.upload_part_from_file(sfp, part_num=1, size=5)
        mpu.upload_part_from_file(sfp, part_num=2, size=5)
        mpu.upload_part_from_file(sfp, part_num=3, size=5)
        mpu.upload_part_from_file(sfp, part_num=4, size=5)
        sfp.close()

        etags = {}
        pn = 0
        for part in mpu:
            pn += 1
            self.assertEqual(5, part.size)
            etags[pn] = part.etag
        self.assertEqual(pn, 4)
        # etags for 01234
        self.assertEqual(etags[1], etags[3])
        # etags for 56789
        self.assertEqual(etags[2], etags[4])
        # etag 01234 != etag 56789
        self.assertNotEqual(etags[1], etags[2])

        # parts are too small to compete as each part must
        # be a min of 5MB so so we'll assume that is enough
        # testing and abort the upload.
        mpu.cancel_upload()

    # mpu.upload_part_from_file() now returns the uploaded part
    # which makes the etag available. Confirm the etag is 
    # available and equal to the etag returned by the parts list.
    def test_etag_of_parts(self):
        key_name = "etagtest"
        mpu = self.bucket.initiate_multipart_upload(key_name)
        fp = StringIO("small file")
        # upload 2 parts and save each part
        uparts = []
        uparts.append(mpu.upload_part_from_file(fp, part_num=1, size=5))
        uparts.append(mpu.upload_part_from_file(fp, part_num=2))
        fp.close()
        # compare uploaded parts etag to listed parts
        pn = 0
        for lpart in mpu:
            self.assertEqual(uparts[pn].etag, lpart.etag)
            pn += 1
        # Can't complete 2 small parts so just clean up.
        mpu.cancel_upload()


class S3MultiPartUploadSigV4Test(unittest.TestCase):
    s3 = True

    def setUp(self):
        self.env_patch = mock.patch('os.environ', {'S3_USE_SIGV4': True})
        self.env_patch.start()
        self.conn = boto.s3.connect_to_region('us-west-2')
        self.bucket_name = 'multipart-%d' % int(time.time())
        self.bucket = self.conn.create_bucket(self.bucket_name,
                                              location='us-west-2')

    def tearDown(self):
        for key in self.bucket:
            key.delete()
        self.bucket.delete()
        self.env_patch.stop()

    def test_initiate_multipart(self):
        key_name = "multipart"
        multipart_upload = self.bucket.initiate_multipart_upload(key_name)
        multipart_uploads = self.bucket.get_all_multipart_uploads()
        for upload in multipart_uploads:
            # Check that the multipart upload was created.
            self.assertEqual(upload.key_name, multipart_upload.key_name)
            self.assertEqual(upload.id, multipart_upload.id)
        multipart_upload.cancel_upload()

    def test_upload_part_by_size(self):
        key_name = "k"
        contents = "01234567890123456789"
        sfp = StringIO(contents)

        # upload 20 bytes in 4 parts of 5 bytes each
        mpu = self.bucket.initiate_multipart_upload(key_name)
        mpu.upload_part_from_file(sfp, part_num=1, size=5)
        mpu.upload_part_from_file(sfp, part_num=2, size=5)
        mpu.upload_part_from_file(sfp, part_num=3, size=5)
        mpu.upload_part_from_file(sfp, part_num=4, size=5)
        sfp.close()

        etags = {}
        pn = 0
        for part in mpu:
            pn += 1
            self.assertEqual(5, part.size)
            etags[pn] = part.etag
        self.assertEqual(pn, 4)
        # etags for 01234
        self.assertEqual(etags[1], etags[3])
        # etags for 56789
        self.assertEqual(etags[2], etags[4])
        # etag 01234 != etag 56789
        self.assertNotEqual(etags[1], etags[2])

        # parts are too small to complete as each part must
        # be a min of 5MB so so we'll assume that is enough
        # testing and abort the upload.
        mpu.cancel_upload()
