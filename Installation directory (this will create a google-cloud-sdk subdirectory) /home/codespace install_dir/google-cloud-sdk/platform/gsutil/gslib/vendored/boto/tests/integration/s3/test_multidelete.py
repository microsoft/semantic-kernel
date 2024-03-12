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
Some unit tests for the S3 MultiDelete
"""

import unittest
import time
from boto.s3.key import Key
from boto.s3.deletemarker import DeleteMarker
from boto.s3.prefix import Prefix
from boto.s3.connection import S3Connection
from boto.exception import S3ResponseError

class S3MultiDeleteTest(unittest.TestCase):
    s3 = True

    def setUp(self):
        self.conn = S3Connection()
        self.bucket_name = 'multidelete-%d' % int(time.time())
        self.bucket = self.conn.create_bucket(self.bucket_name)

    def tearDown(self):
        for key in self.bucket:
            key.delete()
        self.bucket.delete_keys(self.bucket.list_versions())
        self.bucket.delete()

    def test_delete_nothing(self):
        result = self.bucket.delete_keys([])
        self.assertEqual(len(result.deleted), 0)
        self.assertEqual(len(result.errors), 0)

    def test_delete_illegal(self):
        result = self.bucket.delete_keys([{"dict":"notallowed"}])
        self.assertEqual(len(result.deleted), 0)
        self.assertEqual(len(result.errors), 1)

    def test_delete_mix(self):
        result = self.bucket.delete_keys(["king",
                                          ("mice", None),
                                          Key(name="regular"),
                                          Key(),
                                          Prefix(name="folder/"),
                                          DeleteMarker(name="deleted"),
                                          {"bad":"type"}])
        self.assertEqual(len(result.deleted), 4)
        self.assertEqual(len(result.errors), 3)

    def test_delete_quietly(self):
        result = self.bucket.delete_keys(["king"], quiet=True)
        self.assertEqual(len(result.deleted), 0)
        self.assertEqual(len(result.errors), 0)

    def test_delete_must_escape(self):
        result = self.bucket.delete_keys([Key(name=">_<;")])
        self.assertEqual(len(result.deleted), 1)
        self.assertEqual(len(result.errors), 0)

    def test_delete_unknown_version(self):
        no_ver = Key(name="no")
        no_ver.version_id = "version"
        result = self.bucket.delete_keys([no_ver])
        self.assertEqual(len(result.deleted), 0)
        self.assertEqual(len(result.errors), 1)

    def test_delete_kanji(self):
        result = self.bucket.delete_keys([u"漢字", Key(name=u"日本語")])
        self.assertEqual(len(result.deleted), 2)
        self.assertEqual(len(result.errors), 0)

    def test_delete_empty_by_list(self):
        result = self.bucket.delete_keys(self.bucket.list())
        self.assertEqual(len(result.deleted), 0)
        self.assertEqual(len(result.errors), 0)

    def test_delete_kanji_by_list(self):
        for key_name in [u"漢字", u"日本語", u"テスト"]:
            key = self.bucket.new_key(key_name)
            key.set_contents_from_string('this is a test')
        result = self.bucket.delete_keys(self.bucket.list())
        self.assertEqual(len(result.deleted), 3)
        self.assertEqual(len(result.errors), 0)

    def test_delete_with_prefixes(self):
        for key_name in ["a", "a/b", "b"]:
            key = self.bucket.new_key(key_name)
            key.set_contents_from_string('this is a test')

        # First delete all "files": "a" and "b"
        result = self.bucket.delete_keys(self.bucket.list(delimiter="/"))
        self.assertEqual(len(result.deleted), 2)
        # Using delimiter will cause 1 common prefix to be listed
        # which will be skipped as an error.
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].key, "a/")

        # Next delete any remaining objects: "a/b"
        result = self.bucket.delete_keys(self.bucket.list())
        self.assertEqual(len(result.deleted), 1)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(result.deleted[0].key, "a/b")

    def test_delete_too_many_versions(self):
        # configure versioning first
        self.bucket.configure_versioning(True)

        # Add 1000 initial versions as DMs by deleting them :-)
        # Adding 1000 objects is painful otherwise...
        key_names = ['key-%03d' % i for i in range(0, 1000)]
        result = self.bucket.delete_keys(key_names)
        self.assertEqual(len(result.deleted) + len(result.errors), 1000)

        # delete them again to create 1000 more delete markers
        result = self.bucket.delete_keys(key_names)
        self.assertEqual(len(result.deleted) + len(result.errors), 1000)

        # Sometimes takes AWS sometime to settle
        time.sleep(10)

        # delete all versions to delete 2000 objects.
        # this tests the 1000 limit.
        result = self.bucket.delete_keys(self.bucket.list_versions())
        self.assertEqual(len(result.deleted) + len(result.errors), 2000)

    def test_1(self):
        nkeys = 100

        # create a bunch of keynames
        key_names = ['key-%03d' % i for i in range(0, nkeys)]

        # create the corresponding keys
        for key_name in key_names:
            key = self.bucket.new_key(key_name)
            key.set_contents_from_string('this is a test')

        # now count keys in bucket
        n = 0
        for key in self.bucket:
            n += 1

        self.assertEqual(n, nkeys)

        # now delete them all
        result = self.bucket.delete_keys(key_names)

        self.assertEqual(len(result.deleted), nkeys)
        self.assertEqual(len(result.errors), 0)

        time.sleep(5)

        # now count keys in bucket
        n = 0
        for key in self.bucket:
            n += 1

        self.assertEqual(n, 0)
