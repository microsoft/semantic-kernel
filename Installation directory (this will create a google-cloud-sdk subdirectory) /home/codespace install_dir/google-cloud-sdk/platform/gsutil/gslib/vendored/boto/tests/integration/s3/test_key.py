# -*- coding: utf-8 -*-
# Copyright (c) 2012 Mitch Garnaat http://garnaat.org/
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
Some unit tests for S3 Key
"""

from tests.unit import unittest
import time
import random

import boto.s3
from boto.compat import six, StringIO, urllib
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.exception import S3ResponseError


class S3KeyTest(unittest.TestCase):
    s3 = True

    def setUp(self):
        self.conn = S3Connection()
        random.seed()
        self.bucket_name = 'keytest-%d-%d' % (
            time.time(), random.randint(1, 99999999))
        self.bucket = self.conn.create_bucket(self.bucket_name)

    def tearDown(self):
        for key in self.bucket:
            key.delete()
        self.bucket.delete()

    def test_set_contents_from_file_dataloss(self):
        # Create an empty stringio and write to it.
        content = "abcde"
        sfp = StringIO()
        sfp.write(content)
        # Try set_contents_from_file() without rewinding sfp
        k = self.bucket.new_key("k")
        try:
            k.set_contents_from_file(sfp)
            self.fail("forgot to rewind so should fail.")
        except AttributeError:
            pass
        # call with rewind and check if we wrote 5 bytes
        k.set_contents_from_file(sfp, rewind=True)
        self.assertEqual(k.size, 5)
        # check actual contents by getting it.
        kn = self.bucket.new_key("k")
        ks = kn.get_contents_as_string().decode('utf-8')
        self.assertEqual(ks, content)

        # finally, try with a 0 length string
        sfp = StringIO()
        k = self.bucket.new_key("k")
        k.set_contents_from_file(sfp)
        self.assertEqual(k.size, 0)
        # check actual contents by getting it.
        kn = self.bucket.new_key("k")
        ks = kn.get_contents_as_string().decode('utf-8')
        self.assertEqual(ks, "")

    def test_set_contents_as_file(self):
        content="01234567890123456789"
        sfp = StringIO(content)

        # fp is set at 0 for just opened (for read) files.
        # set_contents should write full content to key.
        k = self.bucket.new_key("k")
        k.set_contents_from_file(sfp)
        self.assertEqual(k.size, 20)
        kn = self.bucket.new_key("k")
        ks = kn.get_contents_as_string().decode('utf-8')
        self.assertEqual(ks, content)

        # set fp to 5 and set contents. this should
        # set "567890123456789" to the key
        sfp.seek(5)
        k = self.bucket.new_key("k")
        k.set_contents_from_file(sfp)
        self.assertEqual(k.size, 15)
        kn = self.bucket.new_key("k")
        ks = kn.get_contents_as_string().decode('utf-8')
        self.assertEqual(ks, content[5:])

        # set fp to 5 and only set 5 bytes. this should
        # write the value "56789" to the key.
        sfp.seek(5)
        k = self.bucket.new_key("k")
        k.set_contents_from_file(sfp, size=5)
        self.assertEqual(k.size, 5)
        self.assertEqual(sfp.tell(), 10)
        kn = self.bucket.new_key("k")
        ks = kn.get_contents_as_string().decode('utf-8')
        self.assertEqual(ks, content[5:10])

    def test_set_contents_with_md5(self):
        content="01234567890123456789"
        sfp = StringIO(content)

        # fp is set at 0 for just opened (for read) files.
        # set_contents should write full content to key.
        k = self.bucket.new_key("k")
        good_md5 = k.compute_md5(sfp)
        k.set_contents_from_file(sfp, md5=good_md5)
        kn = self.bucket.new_key("k")
        ks = kn.get_contents_as_string().decode('utf-8')
        self.assertEqual(ks, content)

        # set fp to 5 and only set 5 bytes. this should
        # write the value "56789" to the key.
        sfp.seek(5)
        k = self.bucket.new_key("k")
        good_md5 = k.compute_md5(sfp, size=5)
        k.set_contents_from_file(sfp, size=5, md5=good_md5)
        self.assertEqual(sfp.tell(), 10)
        kn = self.bucket.new_key("k")
        ks = kn.get_contents_as_string().decode('utf-8')
        self.assertEqual(ks, content[5:10])

        # let's try a wrong md5 by just altering it.
        k = self.bucket.new_key("k")
        sfp.seek(0)
        hexdig, base64 = k.compute_md5(sfp)
        bad_md5 = (hexdig, base64[3:])
        try:
            k.set_contents_from_file(sfp, md5=bad_md5)
            self.fail("should fail with bad md5")
        except S3ResponseError:
            pass

    def test_get_contents_with_md5(self):
        content="01234567890123456789"
        sfp = StringIO(content)

        k = self.bucket.new_key("k")
        k.set_contents_from_file(sfp)
        kn = self.bucket.new_key("k")
        s = kn.get_contents_as_string().decode('utf-8')
        self.assertEqual(kn.md5, k.md5)
        self.assertEqual(s, content)

    def test_file_callback(self):
        def callback(wrote, total):
            self.my_cb_cnt += 1
            self.assertNotEqual(wrote, self.my_cb_last, "called twice with same value")
            self.my_cb_last = wrote

        # Zero bytes written => 1 call
        self.my_cb_cnt = 0
        self.my_cb_last = None
        k = self.bucket.new_key("k")
        k.BufferSize = 2
        sfp = StringIO("")
        k.set_contents_from_file(sfp, cb=callback, num_cb=10)
        self.assertEqual(self.my_cb_cnt, 1)
        self.assertEqual(self.my_cb_last, 0)
        sfp.close()

        # Read back zero bytes => 1 call
        self.my_cb_cnt = 0
        self.my_cb_last = None
        s = k.get_contents_as_string(cb=callback)
        self.assertEqual(self.my_cb_cnt, 1)
        self.assertEqual(self.my_cb_last, 0)

        content="01234567890123456789"
        sfp = StringIO(content)

        # expect 2 calls due start/finish
        self.my_cb_cnt = 0
        self.my_cb_last = None
        k = self.bucket.new_key("k")
        k.set_contents_from_file(sfp, cb=callback, num_cb=10)
        self.assertEqual(self.my_cb_cnt, 2)
        self.assertEqual(self.my_cb_last, 20)

        # Read back all bytes => 2 calls
        self.my_cb_cnt = 0
        self.my_cb_last = None
        s = k.get_contents_as_string(cb=callback).decode('utf-8')
        self.assertEqual(self.my_cb_cnt, 2)
        self.assertEqual(self.my_cb_last, 20)
        self.assertEqual(s, content)

        # rewind sfp and try upload again. -1 should call
        # for every read/write so that should make 11 when bs=2
        sfp.seek(0)
        self.my_cb_cnt = 0
        self.my_cb_last = None
        k = self.bucket.new_key("k")
        k.BufferSize = 2
        k.set_contents_from_file(sfp, cb=callback, num_cb=-1)
        self.assertEqual(self.my_cb_cnt, 11)
        self.assertEqual(self.my_cb_last, 20)

        # Read back all bytes => 11 calls
        self.my_cb_cnt = 0
        self.my_cb_last = None
        s = k.get_contents_as_string(cb=callback, num_cb=-1).decode('utf-8')
        self.assertEqual(self.my_cb_cnt, 11)
        self.assertEqual(self.my_cb_last, 20)
        self.assertEqual(s, content)

        # no more than 1 times => 2 times
        # last time always 20 bytes
        sfp.seek(0)
        self.my_cb_cnt = 0
        self.my_cb_last = None
        k = self.bucket.new_key("k")
        k.BufferSize = 2
        k.set_contents_from_file(sfp, cb=callback, num_cb=1)
        self.assertTrue(self.my_cb_cnt <= 2)
        self.assertEqual(self.my_cb_last, 20)

        # no more than 1 times => 2 times
        self.my_cb_cnt = 0
        self.my_cb_last = None
        s = k.get_contents_as_string(cb=callback, num_cb=1).decode('utf-8')
        self.assertTrue(self.my_cb_cnt <= 2)
        self.assertEqual(self.my_cb_last, 20)
        self.assertEqual(s, content)

        # no more than 2 times
        # last time always 20 bytes
        sfp.seek(0)
        self.my_cb_cnt = 0
        self.my_cb_last = None
        k = self.bucket.new_key("k")
        k.BufferSize = 2
        k.set_contents_from_file(sfp, cb=callback, num_cb=2)
        self.assertTrue(self.my_cb_cnt <= 2)
        self.assertEqual(self.my_cb_last, 20)

        # no more than 2 times
        self.my_cb_cnt = 0
        self.my_cb_last = None
        s = k.get_contents_as_string(cb=callback, num_cb=2).decode('utf-8')
        self.assertTrue(self.my_cb_cnt <= 2)
        self.assertEqual(self.my_cb_last, 20)
        self.assertEqual(s, content)

        # no more than 3 times
        # last time always 20 bytes
        sfp.seek(0)
        self.my_cb_cnt = 0
        self.my_cb_last = None
        k = self.bucket.new_key("k")
        k.BufferSize = 2
        k.set_contents_from_file(sfp, cb=callback, num_cb=3)
        self.assertTrue(self.my_cb_cnt <= 3)
        self.assertEqual(self.my_cb_last, 20)

        # no more than 3 times
        self.my_cb_cnt = 0
        self.my_cb_last = None
        s = k.get_contents_as_string(cb=callback, num_cb=3).decode('utf-8')
        self.assertTrue(self.my_cb_cnt <= 3)
        self.assertEqual(self.my_cb_last, 20)
        self.assertEqual(s, content)

        # no more than 4 times
        # last time always 20 bytes
        sfp.seek(0)
        self.my_cb_cnt = 0
        self.my_cb_last = None
        k = self.bucket.new_key("k")
        k.BufferSize = 2
        k.set_contents_from_file(sfp, cb=callback, num_cb=4)
        self.assertTrue(self.my_cb_cnt <= 4)
        self.assertEqual(self.my_cb_last, 20)

        # no more than 4 times
        self.my_cb_cnt = 0
        self.my_cb_last = None
        s = k.get_contents_as_string(cb=callback, num_cb=4).decode('utf-8')
        self.assertTrue(self.my_cb_cnt <= 4)
        self.assertEqual(self.my_cb_last, 20)
        self.assertEqual(s, content)

        # no more than 6 times
        # last time always 20 bytes
        sfp.seek(0)
        self.my_cb_cnt = 0
        self.my_cb_last = None
        k = self.bucket.new_key("k")
        k.BufferSize = 2
        k.set_contents_from_file(sfp, cb=callback, num_cb=6)
        self.assertTrue(self.my_cb_cnt <= 6)
        self.assertEqual(self.my_cb_last, 20)

        # no more than 6 times
        self.my_cb_cnt = 0
        self.my_cb_last = None
        s = k.get_contents_as_string(cb=callback, num_cb=6).decode('utf-8')
        self.assertTrue(self.my_cb_cnt <= 6)
        self.assertEqual(self.my_cb_last, 20)
        self.assertEqual(s, content)

        # no more than 10 times
        # last time always 20 bytes
        sfp.seek(0)
        self.my_cb_cnt = 0
        self.my_cb_last = None
        k = self.bucket.new_key("k")
        k.BufferSize = 2
        k.set_contents_from_file(sfp, cb=callback, num_cb=10)
        self.assertTrue(self.my_cb_cnt <= 10)
        self.assertEqual(self.my_cb_last, 20)

        # no more than 10 times
        self.my_cb_cnt = 0
        self.my_cb_last = None
        s = k.get_contents_as_string(cb=callback, num_cb=10).decode('utf-8')
        self.assertTrue(self.my_cb_cnt <= 10)
        self.assertEqual(self.my_cb_last, 20)
        self.assertEqual(s, content)

        # no more than 1000 times
        # last time always 20 bytes
        sfp.seek(0)
        self.my_cb_cnt = 0
        self.my_cb_last = None
        k = self.bucket.new_key("k")
        k.BufferSize = 2
        k.set_contents_from_file(sfp, cb=callback, num_cb=1000)
        self.assertTrue(self.my_cb_cnt <= 1000)
        self.assertEqual(self.my_cb_last, 20)

        # no more than 1000 times
        self.my_cb_cnt = 0
        self.my_cb_last = None
        s = k.get_contents_as_string(cb=callback, num_cb=1000).decode('utf-8')
        self.assertTrue(self.my_cb_cnt <= 1000)
        self.assertEqual(self.my_cb_last, 20)
        self.assertEqual(s, content)

    def test_website_redirects(self):
        self.bucket.configure_website('index.html')
        key = self.bucket.new_key('redirect-key')
        self.assertTrue(key.set_redirect('http://www.amazon.com/'))
        self.assertEqual(key.get_redirect(), 'http://www.amazon.com/')

        self.assertTrue(key.set_redirect('http://aws.amazon.com/'))
        self.assertEqual(key.get_redirect(), 'http://aws.amazon.com/')

    def test_website_redirect_none_configured(self):
        key = self.bucket.new_key('redirect-key')
        key.set_contents_from_string('')
        self.assertEqual(key.get_redirect(), None)

    def test_website_redirect_with_bad_value(self):
        self.bucket.configure_website('index.html')
        key = self.bucket.new_key('redirect-key')
        with self.assertRaises(key.provider.storage_response_error):
            # Must start with a / or http
            key.set_redirect('ftp://ftp.example.org')
        with self.assertRaises(key.provider.storage_response_error):
            # Must start with a / or http
            key.set_redirect('')

    def test_setting_date(self):
        key = self.bucket.new_key('test_date')
        # This should actually set x-amz-meta-date & not fail miserably.
        key.set_metadata('date', '20130524T155935Z')
        key.set_contents_from_string('Some text here.')

        check = self.bucket.get_key('test_date')
        self.assertEqual(check.get_metadata('date'), u'20130524T155935Z')
        self.assertTrue('x-amz-meta-date' in check._get_remote_metadata())

    def test_header_casing(self):
        key = self.bucket.new_key('test_header_case')
        # Using anything but CamelCase on ``Content-Type`` or ``Content-MD5``
        # used to cause a signature error (when using ``s3`` for signing).
        key.set_metadata('Content-type', 'application/json')
        key.set_metadata('Content-md5', 'XmUKnus7svY1frWsVskxXg==')
        key.set_contents_from_string('{"abc": 123}')

        check = self.bucket.get_key('test_header_case')
        self.assertEqual(check.content_type, 'application/json')

    def test_header_encoding(self):
        key = self.bucket.new_key('test_header_encoding')

        key.set_metadata('Cache-control', u'public, max-age=500')
        key.set_metadata('Test-Plus', u'A plus (+)')
        key.set_metadata('Content-disposition', u'filename=Schöne Zeit.txt')
        key.set_metadata('Content-Encoding', 'gzip')
        key.set_metadata('Content-Language', 'de')
        key.set_metadata('Content-Type', 'application/pdf')
        self.assertEqual(key.content_type, 'application/pdf')
        key.set_metadata('X-Robots-Tag', 'all')
        key.set_metadata('Expires', u'Thu, 01 Dec 1994 16:00:00 GMT')
        key.set_contents_from_string('foo')

        check = self.bucket.get_key('test_header_encoding')
        remote_metadata = check._get_remote_metadata()

        # TODO: investigate whether encoding ' ' as '%20' makes sense
        self.assertIn(
            check.cache_control,
            ('public,%20max-age=500', 'public, max-age=500')
        )
        self.assertIn(remote_metadata['cache-control'],
                      ('public,%20max-age=500', 'public, max-age=500'))
        self.assertEqual(check.get_metadata('test-plus'), 'A plus (+)')
        self.assertEqual(check.content_disposition, 'filename=Sch%C3%B6ne Zeit.txt')
        self.assertEqual(remote_metadata['content-disposition'], 'filename=Sch%C3%B6ne Zeit.txt')
        self.assertEqual(check.content_encoding, 'gzip')
        self.assertEqual(remote_metadata['content-encoding'], 'gzip')
        self.assertEqual(check.content_language, 'de')
        self.assertEqual(remote_metadata['content-language'], 'de')
        self.assertEqual(check.content_type, 'application/pdf')
        self.assertEqual(remote_metadata['content-type'], 'application/pdf')
        self.assertEqual(check.x_robots_tag, 'all')
        self.assertEqual(remote_metadata['x-robots-tag'], 'all')
        self.assertEqual(check.expires, 'Thu, 01 Dec 1994 16:00:00 GMT')
        self.assertEqual(remote_metadata['expires'], 'Thu, 01 Dec 1994 16:00:00 GMT')

        expected = u'filename=Schöne Zeit.txt'
        if six.PY2:
            # Newer versions of python default to unicode strings, but python 2
            # requires encoding to UTF-8 to compare the two properly
            expected = expected.encode('utf-8')

        self.assertEqual(
            urllib.parse.unquote(check.content_disposition),
            expected
        )

    def test_set_contents_with_sse_c(self):
        content="01234567890123456789"
        # the plain text of customer key is "01testKeyToSSEC!"
        header = {
            "x-amz-server-side-encryption-customer-algorithm" :
             "AES256",
            "x-amz-server-side-encryption-customer-key" :
             "MAAxAHQAZQBzAHQASwBlAHkAVABvAFMAUwBFAEMAIQA=",
            "x-amz-server-side-encryption-customer-key-MD5" :
             "fUgCZDDh6bfEMuP2bN38mg==",
        }
        # upload and download content with AWS specified headers
        k = self.bucket.new_key("testkey_for_sse_c")
        k.set_contents_from_string(content, headers=header)
        kn = self.bucket.new_key("testkey_for_sse_c")
        ks = kn.get_contents_as_string(headers=header)
        self.assertEqual(ks, content.encode('utf-8'))


class S3KeySigV4Test(unittest.TestCase):
    def setUp(self):
        self.conn = boto.s3.connect_to_region('eu-central-1')
        self.bucket_name = 'boto-sigv4-key-%d' % int(time.time())
        self.bucket = self.conn.create_bucket(self.bucket_name,
                                              location='eu-central-1')

    def tearDown(self):
        for key in self.bucket:
            key.delete()
        self.bucket.delete()

    def test_put_get_with_non_string_headers_key(self):
        k = Key(self.bucket)
        k.key = 'foobar'
        body = 'This is a test of S3'
        # A content-length header will be added to this request since it
        # has a body.
        k.set_contents_from_string(body)
        # Set a header that has an integer. This checks for a bug where
        # the sigv4 signer assumes that all of the headers are strings.
        headers = {'Content-Length': 0}
        from_s3_key = self.bucket.get_key('foobar', headers=headers)
        self.assertEqual(from_s3_key.get_contents_as_string().decode('utf-8'),
                         body)

    def test_head_put_get_with_non_ascii_key(self):
        k = Key(self.bucket)
        k.key = u'''pt-Olá_ch-你好_ko-안녕_ru-Здравствуйте%20,.<>~`!@#$%^&()_-+='"'''
        body = 'This is a test of S3'

        k.set_contents_from_string(body)
        from_s3_key = self.bucket.get_key(k.key, validate=True)
        self.assertEqual(from_s3_key.get_contents_as_string().decode('utf-8'),
                         body)

        keys = self.bucket.get_all_keys(prefix=k.key, max_keys=1)
        self.assertEqual(1, len(keys))


class S3KeyVersionCopyTest(unittest.TestCase):
    def setUp(self):
        self.conn = S3Connection()
        self.bucket_name = 'boto-key-version-copy-%d' % int(time.time())
        self.bucket = self.conn.create_bucket(self.bucket_name)
        self.bucket.configure_versioning(True)

    def tearDown(self):
        for key in self.bucket.list_versions():
            key.delete()
        self.bucket.delete()

    def test_key_overwrite_and_copy(self):
        first_content = b"abcdefghijklm"
        second_content = b"nopqrstuvwxyz"
        k = Key(self.bucket, 'testkey')
        k.set_contents_from_string(first_content)
        # Wait for S3's eventual consistency (may not be necessary)
        while self.bucket.get_key('testkey') is None:
            time.sleep(5)
        # Get the first version_id
        first_key = self.bucket.get_key('testkey')
        first_version_id = first_key.version_id
        # Overwrite the key
        k = Key(self.bucket, 'testkey')
        k.set_contents_from_string(second_content)
        # Wait for eventual consistency
        while True:
            second_key = self.bucket.get_key('testkey')
            if second_key is None or second_key.version_id == first_version_id:
                time.sleep(5)
            else:
                break
        # Copy first key (no longer the current version) to a new key
        source_key = self.bucket.get_key('testkey',
                                          version_id=first_version_id)
        source_key.copy(self.bucket, 'copiedkey')
        while self.bucket.get_key('copiedkey') is None:
            time.sleep(5)
        copied_key = self.bucket.get_key('copiedkey')
        copied_key_contents = copied_key.get_contents_as_string()
        self.assertEqual(first_content, copied_key_contents)

