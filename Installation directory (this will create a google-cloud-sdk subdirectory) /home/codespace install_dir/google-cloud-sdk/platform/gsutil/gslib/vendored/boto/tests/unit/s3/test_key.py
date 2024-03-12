#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import io

from tests.compat import mock, unittest
from tests.unit import AWSMockServiceTestCase

from boto.compat import StringIO
from boto.exception import BotoServerError
from boto.exception import ResumableDownloadException
from boto.exception import ResumableTransferDisposition
from boto.s3.connection import S3Connection
from boto.s3.bucket import Bucket
from boto.s3.key import Key


class TestS3Key(AWSMockServiceTestCase):
    connection_class = S3Connection

    def setUp(self):
        super(TestS3Key, self).setUp()

    def default_body(self):
        return "default body"

    def test_unicode_name(self):
        k = Key()
        k.name = u'Österreich'
        print(repr(k))

    def test_when_no_restore_header_present(self):
        self.set_http_response(status_code=200)
        b = Bucket(self.service_connection, 'mybucket')
        k = b.get_key('myglacierkey')
        self.assertIsNone(k.ongoing_restore)
        self.assertIsNone(k.expiry_date)

    def test_restore_header_with_ongoing_restore(self):
        self.set_http_response(
            status_code=200,
            header=[('x-amz-restore', 'ongoing-request="true"')])
        b = Bucket(self.service_connection, 'mybucket')
        k = b.get_key('myglacierkey')
        self.assertTrue(k.ongoing_restore)
        self.assertIsNone(k.expiry_date)

    def test_restore_completed(self):
        self.set_http_response(
            status_code=200,
            header=[('x-amz-restore',
                     'ongoing-request="false", '
                     'expiry-date="Fri, 21 Dec 2012 00:00:00 GMT"')])
        b = Bucket(self.service_connection, 'mybucket')
        k = b.get_key('myglacierkey')
        self.assertFalse(k.ongoing_restore)
        self.assertEqual(k.expiry_date, 'Fri, 21 Dec 2012 00:00:00 GMT')

    def test_delete_key_return_key(self):
        self.set_http_response(status_code=204, body='')
        b = Bucket(self.service_connection, 'mybucket')
        key = b.delete_key('fookey')
        self.assertIsNotNone(key)

    def test_storage_class(self):
        self.set_http_response(status_code=200)
        b = Bucket(self.service_connection, 'mybucket')
        k = b.get_key('fookey')

        # Mock out the bucket object - we really only care about calls
        # to list.
        k.bucket = mock.MagicMock()

        # Default behavior doesn't call list
        k.set_contents_from_string('test')
        k.bucket.list.assert_not_called()

        # Direct access calls list to get the real value if unset,
        # and still defaults to STANDARD if unavailable.
        sc_value = k.storage_class
        self.assertEqual(sc_value, 'STANDARD')
        k.bucket.list.assert_called_with(k.name.encode('utf-8'))
        k.bucket.list.reset_mock()

        # Setting manually doesn't call list
        k.storage_class = 'GLACIER'
        k.set_contents_from_string('test')
        k.bucket.list.assert_not_called()

    def test_change_storage_class(self):
        self.set_http_response(status_code=200)
        b = Bucket(self.service_connection, 'mybucket')
        k = b.get_key('fookey')

        # Mock out Key.copy so we can record calls to it
        k.copy = mock.MagicMock()
        # Mock out the bucket so we don't actually need to have fake responses
        k.bucket = mock.MagicMock()
        k.bucket.name = 'mybucket'

        self.assertEqual(k.storage_class, 'STANDARD')

        # The default change_storage_class call should result in a copy to our
        # bucket
        k.change_storage_class('REDUCED_REDUNDANCY')
        k.copy.assert_called_with(
            'mybucket',
            'fookey',
            reduced_redundancy=True,
            preserve_acl=True,
            validate_dst_bucket=True,
        )

    def test_change_storage_class_new_bucket(self):
        self.set_http_response(status_code=200)
        b = Bucket(self.service_connection, 'mybucket')
        k = b.get_key('fookey')

        # Mock out Key.copy so we can record calls to it
        k.copy = mock.MagicMock()
        # Mock out the bucket so we don't actually need to have fake responses
        k.bucket = mock.MagicMock()
        k.bucket.name = 'mybucket'

        self.assertEqual(k.storage_class, 'STANDARD')
        # Specifying a different dst_bucket should result in a copy to the new
        # bucket
        k.copy.reset_mock()
        k.change_storage_class('REDUCED_REDUNDANCY', dst_bucket='yourbucket')
        k.copy.assert_called_with(
            'yourbucket',
            'fookey',
            reduced_redundancy=True,
            preserve_acl=True,
            validate_dst_bucket=True,
        )
    
    def test_download_succeeds(self):
        test_case_headers = [
            [('Content-Length', '5')],
            [('Content-Range', 'bytes 15-19/100')],
        ]
        for headers in test_case_headers:
            with self.subTest(headers=headers):
                head_object_response = self.create_response(
                    status_code=200, header=headers)

                media_response = self.create_response(
                    status_code=200, header=headers)
                media_response.read.side_effect = [
                    b'12345',
                    b'',
                    b'',  # Key.close calls read an additional time.
                ]

                self.https_connection.getresponse.side_effect = [
                    head_object_response,
                    media_response
                ]

                bucket = Bucket(self.service_connection, 'bucket')
                key = bucket.get_key('object')

                output_stream = io.BytesIO()
                key.get_file(output_stream)

                output_stream.seek(0)
                self.assertEqual(output_stream.read(), b'12345')
    
    def test_download_raises_retriable_error_with_truncated_stream(self):
        test_case_headers = [
            [('Content-Length', '5')],
            [('Content-Range', 'bytes 15-19/100')],
        ]
        for headers in test_case_headers:
            with self.subTest(headers=headers):
                head_object_response = self.create_response(
                    status_code=200, header=headers)

                media_response = self.create_response(
                    status_code=200, header=headers)
                media_response.read.side_effect = [
                    # Stream is truncated and returns < 5 bytes.
                    b'1234',
                    b'',
                ]

                self.https_connection.getresponse.side_effect = [
                    head_object_response,
                    media_response
                ]

                bucket = Bucket(self.service_connection, 'bucket')
                key = bucket.get_key('object')

                with self.assertRaisesRegex(
                    ResumableDownloadException,
                    'Download stream truncated. Received 4 of 5 bytes.'
                ) as context:
                    key.get_file(io.BytesIO())
                    self.assertEqual(
                        context.exception.disposition,
                        ResumableTransferDisposition.WAIT_BEFORE_RETRY)


def counter(fn):
    def _wrapper(*args, **kwargs):
        _wrapper.count += 1
        return fn(*args, **kwargs)
    _wrapper.count = 0
    return _wrapper


class TestS3KeyRetries(AWSMockServiceTestCase):
    connection_class = S3Connection

    @mock.patch('time.sleep')
    def test_500_retry(self, sleep_mock):
        self.set_http_response(status_code=500)
        b = Bucket(self.service_connection, 'mybucket')
        k = b.new_key('test_failure')
        fail_file = StringIO('This will attempt to retry.')

        with self.assertRaises(BotoServerError):
            k.send_file(fail_file)

    @mock.patch('time.sleep')
    def test_400_timeout(self, sleep_mock):
        weird_timeout_body = "<Error><Code>RequestTimeout</Code></Error>"
        self.set_http_response(status_code=400, body=weird_timeout_body)
        b = Bucket(self.service_connection, 'mybucket')
        k = b.new_key('test_failure')
        fail_file = StringIO('This will pretend to be chunk-able.')

        k.should_retry = counter(k.should_retry)
        self.assertEqual(k.should_retry.count, 0)

        with self.assertRaises(BotoServerError):
            k.send_file(fail_file)

        self.assertTrue(k.should_retry.count, 1)

    @mock.patch('time.sleep')
    def test_502_bad_gateway(self, sleep_mock):
        weird_timeout_body = "<Error><Code>BadGateway</Code></Error>"
        self.set_http_response(status_code=502, body=weird_timeout_body)
        b = Bucket(self.service_connection, 'mybucket')
        k = b.new_key('test_failure')
        fail_file = StringIO('This will pretend to be chunk-able.')

        k.should_retry = counter(k.should_retry)
        self.assertEqual(k.should_retry.count, 0)

        with self.assertRaises(BotoServerError):
            k.send_file(fail_file)

        self.assertTrue(k.should_retry.count, 1)

    @mock.patch('time.sleep')
    def test_504_gateway_timeout(self, sleep_mock):
        weird_timeout_body = "<Error><Code>GatewayTimeout</Code></Error>"
        self.set_http_response(status_code=504, body=weird_timeout_body)
        b = Bucket(self.service_connection, 'mybucket')
        k = b.new_key('test_failure')
        fail_file = StringIO('This will pretend to be chunk-able.')

        k.should_retry = counter(k.should_retry)
        self.assertEqual(k.should_retry.count, 0)

        with self.assertRaises(BotoServerError):
            k.send_file(fail_file)

        self.assertTrue(k.should_retry.count, 1)

    def test_should_not_raise_kms_related_integrity_errors(self):
        self.set_http_response(status_code=200, header=[
            ('x-amz-server-side-encryption-aws-kms-key-id', 'key'),
            ('etag', 'not equal to key.md5')])
        bucket = Bucket(self.service_connection, 'mybucket')
        key = bucket.new_key('test_kms')
        file_content = StringIO('Some content to upload.')

        # Should not raise errors related to integrity checks:
        key.send_file(file_content)

class TestFileError(unittest.TestCase):
    def test_file_error(self):
        key = Key()

        class CustomException(Exception): pass

        key.get_contents_to_file = mock.Mock(
            side_effect=CustomException('File blew up!'))

        # Ensure our exception gets raised instead of a file or IO error
        with self.assertRaises(CustomException):
            key.get_contents_to_filename('foo.txt')

if __name__ == '__main__':
    unittest.main()
