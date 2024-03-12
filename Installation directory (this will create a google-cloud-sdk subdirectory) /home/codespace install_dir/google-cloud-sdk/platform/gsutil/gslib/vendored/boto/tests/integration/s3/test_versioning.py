# Copyright (c) 2010 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010, Eucalyptus Systems, Inc.
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
Some unit tests for the S3 Versioning.
"""

import unittest
import time
from boto.s3.connection import S3Connection
from boto.exception import S3ResponseError
from boto.s3.deletemarker import DeleteMarker
from boto.compat import six

class S3VersionTest (unittest.TestCase):

    def setUp(self):
        self.conn = S3Connection()
        self.bucket_name = 'version-%d' % int(time.time())
        self.bucket = self.conn.create_bucket(self.bucket_name)

    def tearDown(self):
        for k in self.bucket.list_versions():
            self.bucket.delete_key(k.name, version_id=k.version_id)
        self.bucket.delete()

    def test_1_versions(self):
        # check versioning off
        d = self.bucket.get_versioning_status()
        self.assertFalse('Versioning' in d)

        # enable versioning
        self.bucket.configure_versioning(versioning=True)
        d = self.bucket.get_versioning_status()
        self.assertEqual('Enabled', d['Versioning'])
        
        # create a new key in the versioned bucket
        k = self.bucket.new_key("foobar")
        s1 = 'This is v1'
        k.set_contents_from_string(s1)
        
        # remember the version id of this object
        v1 = k.version_id
        
        # now get the contents from s3 
        o1 = k.get_contents_as_string().decode('utf-8')
        
        # check to make sure content read from k is identical to original
        self.assertEqual(s1, o1)
        
        # now overwrite that same key with new data
        s2 = 'This is v2'
        k.set_contents_from_string(s2)
        v2 = k.version_id
        
        # now retrieve latest contents as a string and compare
        k2 = self.bucket.new_key("foobar")
        o2 = k2.get_contents_as_string().decode('utf-8')
        self.assertEqual(s2, o2)

        # next retrieve explicit versions and compare
        o1 = k.get_contents_as_string(version_id=v1).decode('utf-8')
        o2 = k.get_contents_as_string(version_id=v2).decode('utf-8')
        self.assertEqual(s1, o1)
        self.assertEqual(s2, o2)
        
        # Now list all versions and compare to what we have
        rs = self.bucket.get_all_versions()
        self.assertEqual(v2, rs[0].version_id)
        self.assertEqual(v1, rs[1].version_id)
        
        # Now do a regular list command and make sure only the new key shows up
        rs = self.bucket.get_all_keys()
        self.assertEqual(1, len(rs))
        
        # Now do regular delete
        self.bucket.delete_key('foobar')
        
        # Now list versions and make sure old versions are there
        # plus the DeleteMarker which is latest.
        rs = self.bucket.get_all_versions()
        self.assertEqual(3, len(rs))
        self.assertTrue(isinstance(rs[0], DeleteMarker))
        
        # Now delete v1 of the key
        self.bucket.delete_key('foobar', version_id=v1)
        
        # Now list versions again and make sure v1 is not there
        rs = self.bucket.get_all_versions()
        versions = [k.version_id for k in rs]
        self.assertTrue(v1 not in versions)
        self.assertTrue(v2 in versions)
        
        # Now suspend Versioning on the bucket
        self.bucket.configure_versioning(False)
        # Allow time for the change to fully propagate.
        time.sleep(3)
        d = self.bucket.get_versioning_status()
        self.assertEqual('Suspended', d['Versioning'])
        
    def test_latest_version(self):
        self.bucket.configure_versioning(versioning=True)
        
        # add v1 of an object
        key_name = "key"
        kv1 = self.bucket.new_key(key_name)
        kv1.set_contents_from_string("v1")
        
        # read list which should contain latest v1
        listed_kv1 = next(iter(self.bucket.get_all_versions()))
        self.assertEqual(listed_kv1.name, key_name)
        self.assertEqual(listed_kv1.version_id, kv1.version_id)
        self.assertEqual(listed_kv1.is_latest, True)

        # add v2 of the object
        kv2 = self.bucket.new_key(key_name)
        kv2.set_contents_from_string("v2")

        # read 2 versions, confirm v2 is latest
        i = iter(self.bucket.get_all_versions())
        listed_kv2 = next(i)
        listed_kv1 = next(i)
        self.assertEqual(listed_kv2.version_id, kv2.version_id)
        self.assertEqual(listed_kv1.version_id, kv1.version_id)
        self.assertEqual(listed_kv2.is_latest, True)
        self.assertEqual(listed_kv1.is_latest, False)

        # delete key, which creates a delete marker as latest
        self.bucket.delete_key(key_name)
        i = iter(self.bucket.get_all_versions())
        listed_kv3 = next(i)
        listed_kv2 = next(i)
        listed_kv1 = next(i)
        self.assertNotEqual(listed_kv3.version_id, None)
        self.assertEqual(listed_kv2.version_id, kv2.version_id)
        self.assertEqual(listed_kv1.version_id, kv1.version_id)
        self.assertEqual(listed_kv3.is_latest, True)
        self.assertEqual(listed_kv2.is_latest, False)
        self.assertEqual(listed_kv1.is_latest, False)
