# -*- coding: utf-8 -*-

# Copyright (c) 2016 Mitch Garnaat http://garnaat.org/
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

from mock import patch, Mock
import unittest

from boto.s3.bucket import ResultSet
from boto.s3.bucketlistresultset import multipart_upload_lister
from boto.s3.bucketlistresultset import versioned_bucket_lister


class S3BucketListResultSetTest (unittest.TestCase):
    def _test_patched_lister_encoding(self, inner_method, outer_method):
        bucket = Mock()
        call_args = []
        first = ResultSet()
        first.append('foo')
        first.next_key_marker = 'a+b'
        first.is_truncated = True
        second = ResultSet()
        second.append('bar')
        second.is_truncated = False
        pages = [first, second]

        def return_pages(**kwargs):
            call_args.append(kwargs)
            return pages.pop(0)

        setattr(bucket, inner_method, return_pages)
        results = list(outer_method(bucket, encoding_type='url'))
        self.assertEqual(['foo', 'bar'], results)
        self.assertEqual('a b', call_args[1]['key_marker'])

    def test_list_object_versions_with_url_encoding(self):
        self._test_patched_lister_encoding(
            'get_all_versions', versioned_bucket_lister)

    def test_list_multipart_upload_with_url_encoding(self):
        self._test_patched_lister_encoding(
            'get_all_multipart_uploads', multipart_upload_lister)
