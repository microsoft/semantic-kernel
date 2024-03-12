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
Some unit tests for the S3 Encryption
"""
import unittest
import time
from boto.s3.connection import S3Connection
from boto.exception import S3ResponseError

json_policy = """{
   "Version":"2008-10-17",
   "Id":"PutObjPolicy",
   "Statement":[{
         "Sid":"DenyUnEncryptedObjectUploads",
         "Effect":"Deny",
         "Principal":{
            "AWS":"*"
         },
         "Action":"s3:PutObject",
         "Resource":"arn:aws:s3:::%s/*",
         "Condition":{
            "StringNotEquals":{
               "s3:x-amz-server-side-encryption":"AES256"
            }
         }
      }
   ]
}"""

class S3EncryptionTest (unittest.TestCase):
    s3 = True

    def test_1_versions(self):
        print('--- running S3Encryption tests ---')
        c = S3Connection()
        # create a new, empty bucket
        bucket_name = 'encryption-%d' % int(time.time())
        bucket = c.create_bucket(bucket_name)
        
        # now try a get_bucket call and see if it's really there
        bucket = c.get_bucket(bucket_name)
        
        # create an unencrypted key
        k = bucket.new_key('foobar')
        s1 = 'This is unencrypted data'
        s2 = 'This is encrypted data'
        k.set_contents_from_string(s1)
        time.sleep(5)
        
        # now get the contents from s3 
        o = k.get_contents_as_string().decode('utf-8')
        
        # check to make sure content read from s3 is identical to original
        assert o == s1
        
        # now overwrite that same key with encrypted data
        k.set_contents_from_string(s2, encrypt_key=True)
        time.sleep(5)
        
        # now retrieve the contents as a string and compare
        o = k.get_contents_as_string().decode('utf-8')
        assert o == s2
        
        # now set bucket policy to require encrypted objects
        bucket.set_policy(json_policy % bucket.name)
        time.sleep(5)
        
        # now try to write unencrypted key
        write_failed = False
        try:
            k.set_contents_from_string(s1)
        except S3ResponseError:
            write_failed = True

        assert write_failed
        
        # now try to write unencrypted key
        write_failed = False
        try:
            k.set_contents_from_string(s1, encrypt_key=True)
        except S3ResponseError:
            write_failed = True

        assert not write_failed
        
        # Now do regular delete
        k.delete()
        time.sleep(5)

        # now delete bucket
        bucket.delete()
        print('--- tests completed ---')
