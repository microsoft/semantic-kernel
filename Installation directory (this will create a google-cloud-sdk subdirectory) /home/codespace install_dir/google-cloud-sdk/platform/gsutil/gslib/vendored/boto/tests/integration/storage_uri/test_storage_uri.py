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
Some unit tests for StorageUri
"""

from tests.unit import unittest
import time
import boto
from boto.s3.connection import S3Connection, Location


class StorageUriTest(unittest.TestCase):
    s3 = True

    def nuke_bucket(self, bucket):
        for key in bucket:
            key.delete()

        bucket.delete()

    def test_storage_uri_regionless(self):
        # First, create a bucket in a different region.
        conn = S3Connection(
            host='s3-us-west-2.amazonaws.com'
        )
        bucket_name = 'keytest-%d' % int(time.time())
        bucket = conn.create_bucket(bucket_name, location=Location.USWest2)
        self.addCleanup(self.nuke_bucket, bucket)

        # Now use ``storage_uri`` to try to make a new key.
        # This would throw a 301 exception.
        suri = boto.storage_uri('s3://%s/test' % bucket_name)
        the_key = suri.new_key()
        the_key.key = 'Test301'
        the_key.set_contents_from_string(
            'This should store in a different region.'
        )

        # Check it a different way.
        alt_conn = boto.connect_s3(host='s3-us-west-2.amazonaws.com')
        alt_bucket = alt_conn.get_bucket(bucket_name)
        alt_key = alt_bucket.get_key('Test301')
