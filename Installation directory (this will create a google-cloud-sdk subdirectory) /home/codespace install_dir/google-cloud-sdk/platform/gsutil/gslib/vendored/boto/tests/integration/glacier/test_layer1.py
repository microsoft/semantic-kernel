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
from tests.unit import unittest

from boto.glacier.layer1 import Layer1


class TestGlacierLayer1(unittest.TestCase):
    glacier = True

    def delete_vault(self, vault_name):
        pass

    def test_initialiate_multipart_upload(self):
        # Create a vault, initiate a multipart upload,
        # then cancel it.
        glacier = Layer1()
        glacier.create_vault('l1testvault')
        self.addCleanup(glacier.delete_vault, 'l1testvault')
        upload_id = glacier.initiate_multipart_upload('l1testvault', 4 * 1024 * 1024,
                                                      'double  spaces  here')['UploadId']
        self.addCleanup(glacier.abort_multipart_upload, 'l1testvault', upload_id)
        response = glacier.list_multipart_uploads('l1testvault')['UploadsList']
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['MultipartUploadId'], upload_id)
