# -*- coding: utf-8 -*-
# Copyright (c) 2006-2011 Mitch Garnaat http://garnaat.org/
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
Some unit tests for the S3Connection
"""
import unittest
import time
import os
import socket

from boto.s3.connection import S3Connection
from boto.s3.bucket import Bucket
from boto.exception import S3PermissionsError, S3ResponseError
from boto.compat import http_client, six, urlopen, urlsplit


class S3ConnectionTest (unittest.TestCase):
    s3 = True

    def test_1_basic(self):
        print('--- running S3Connection tests ---')
        c = S3Connection()
        # create a new, empty bucket
        bucket_name = 'test-%d' % int(time.time())
        bucket = c.create_bucket(bucket_name)
        # now try a get_bucket call and see if it's really there
        bucket = c.get_bucket(bucket_name)
        # test logging
        logging_bucket = c.create_bucket(bucket_name + '-log')
        logging_bucket.set_as_logging_target()
        bucket.enable_logging(target_bucket=logging_bucket, target_prefix=bucket.name)
        bucket.disable_logging()
        c.delete_bucket(logging_bucket)
        k = bucket.new_key('foobar')
        s1 = 'This is a test of file upload and download'
        s2 = 'This is a second string to test file upload and download'
        k.set_contents_from_string(s1)
        fp = open('foobar', 'wb')
        # now get the contents from s3 to a local file
        k.get_contents_to_file(fp)
        fp.close()
        fp = open('foobar')
        # check to make sure content read from s3 is identical to original
        assert s1 == fp.read(), 'corrupted file'
        fp.close()
        # test generated URLs
        url = k.generate_url(3600)
        file = urlopen(url)
        assert s1 == file.read().decode('utf-8'), 'invalid URL %s' % url
        url = k.generate_url(3600, force_http=True)
        file = urlopen(url)
        assert s1 == file.read().decode('utf-8'), 'invalid URL %s' % url
        url = k.generate_url(3600, force_http=True, headers={'x-amz-x-token': 'XYZ'})
        file = urlopen(url)
        assert s1 == file.read().decode('utf-8'), 'invalid URL %s' % url
        rh = {'response-content-disposition': 'attachment; filename="foo.txt"'}
        url = k.generate_url(60, response_headers=rh)
        file = urlopen(url)
        assert s1 == file.read().decode('utf-8'), 'invalid URL %s' % url
        #test whether amperands and to-be-escaped characters work in header filename
        rh = {'response-content-disposition': 'attachment; filename="foo&z%20ar&ar&zar&bar.txt"'}
        url = k.generate_url(60, response_headers=rh, force_http=True)
        file = urlopen(url)
        assert s1 == file.read().decode('utf-8'), 'invalid URL %s' % url
        # overwrite foobar contents with a PUT
        url = k.generate_url(3600, 'PUT', force_http=True, policy='private', reduced_redundancy=True)
        up = urlsplit(url)
        con = http_client.HTTPConnection(up.hostname, up.port)
        con.request("PUT", up.path + '?' + up.query, body="hello there")
        resp = con.getresponse()
        self.assertEqual(200, resp.status)
        assert b"hello there" == k.get_contents_as_string()
        bucket.delete_key(k)
        # test a few variations on get_all_keys - first load some data
        # for the first one, let's override the content type
        phony_mimetype = 'application/x-boto-test'
        headers = {'Content-Type': phony_mimetype}
        k.name = 'foo/bar'
        k.set_contents_from_string(s1, headers)
        k.name = 'foo/bas'
        size = k.set_contents_from_filename('foobar')
        assert size == 42
        k.name = 'foo/bat'
        k.set_contents_from_string(s1)
        k.name = 'fie/bar'
        k.set_contents_from_string(s1)
        k.name = 'fie/bas'
        k.set_contents_from_string(s1)
        k.name = 'fie/bat'
        k.set_contents_from_string(s1)
        # try resetting the contents to another value
        md5 = k.md5
        k.set_contents_from_string(s2)
        assert k.md5 != md5
        os.unlink('foobar')
        all = bucket.get_all_keys()
        assert len(all) == 6
        rs = bucket.get_all_keys(prefix='foo')
        assert len(rs) == 3
        rs = bucket.get_all_keys(prefix='', delimiter='/')
        assert len(rs) == 2
        rs = bucket.get_all_keys(maxkeys=5)
        assert len(rs) == 5
        # test the lookup method
        k = bucket.lookup('foo/bar')
        assert isinstance(k, bucket.key_class)
        assert k.content_type == phony_mimetype
        k = bucket.lookup('notthere')
        assert k == None
        # try some metadata stuff
        k = bucket.new_key('has_metadata')
        mdkey1 = 'meta1'
        mdval1 = 'This is the first metadata value'
        k.set_metadata(mdkey1, mdval1)
        mdkey2 = 'meta2'
        mdval2 = 'This is the second metadata value'
        k.set_metadata(mdkey2, mdval2)
        # try a unicode metadata value
        mdval3 = u'föö'
        mdkey3 = 'meta3'
        k.set_metadata(mdkey3, mdval3)
        k.set_contents_from_string(s1)
        k = bucket.lookup('has_metadata')
        assert k.get_metadata(mdkey1) == mdval1
        assert k.get_metadata(mdkey2) == mdval2
        assert k.get_metadata(mdkey3) == mdval3
        k = bucket.new_key('has_metadata')
        k.get_contents_as_string()
        assert k.get_metadata(mdkey1) == mdval1
        assert k.get_metadata(mdkey2) == mdval2
        assert k.get_metadata(mdkey3) == mdval3
        bucket.delete_key(k)
        # test list and iterator
        rs1 = bucket.list()
        num_iter = 0
        for r in rs1:
            num_iter = num_iter + 1
        rs = bucket.get_all_keys()
        num_keys = len(rs)
        assert num_iter == num_keys
        # try a key with a funny character
        k = bucket.new_key('testnewline\n')
        k.set_contents_from_string('This is a test')
        rs = bucket.get_all_keys()
        assert len(rs) == num_keys + 1
        bucket.delete_key(k)
        rs = bucket.get_all_keys()
        assert len(rs) == num_keys
        # try some acl stuff
        bucket.set_acl('public-read')
        policy = bucket.get_acl()
        assert len(policy.acl.grants) == 2
        bucket.set_acl('private')
        policy = bucket.get_acl()
        assert len(policy.acl.grants) == 1
        k = bucket.lookup('foo/bar')
        k.set_acl('public-read')
        policy = k.get_acl()
        assert len(policy.acl.grants) == 2
        k.set_acl('private')
        policy = k.get_acl()
        assert len(policy.acl.grants) == 1
        # try the convenience methods for grants
        bucket.add_user_grant('FULL_CONTROL',
                              'c1e724fbfa0979a4448393c59a8c055011f739b6d102fb37a65f26414653cd67')
        try:
            bucket.add_email_grant('foobar', 'foo@bar.com')
        except S3PermissionsError:
            pass
        # now try to create an RRS key
        k = bucket.new_key('reduced_redundancy')
        k.set_contents_from_string('This key has reduced redundancy',
                                   reduced_redundancy=True)

        # now try to inject a response header
        data = k.get_contents_as_string(response_headers={'response-content-type' : 'foo/bar'})
        assert k.content_type == 'foo/bar'

        # now delete all keys in bucket
        for k in bucket:
            if k.name == 'reduced_redundancy':
                assert k.storage_class == 'REDUCED_REDUNDANCY'
            bucket.delete_key(k)
        # now delete bucket
        time.sleep(5)
        c.delete_bucket(bucket)
        print('--- tests completed ---')

    def test_basic_anon(self):
        auth_con = S3Connection()
        # create a new, empty bucket
        bucket_name = 'test-%d' % int(time.time())
        auth_bucket = auth_con.create_bucket(bucket_name)

        # try read the bucket anonymously
        anon_con = S3Connection(anon=True)
        anon_bucket = Bucket(anon_con, bucket_name)
        try:
            next(iter(anon_bucket.list()))
            self.fail("anon bucket list should fail")
        except S3ResponseError:
            pass

        # give bucket anon user access and anon read again
        auth_bucket.set_acl('public-read')
        time.sleep(10)  # Was 5 secondes, turns out not enough
        try:
            next(iter(anon_bucket.list()))
            self.fail("not expecting contents")
        except S3ResponseError as e:
            self.fail("We should have public-read access, but received "
                      "an error: %s" % e)
        except StopIteration:
            pass

        # cleanup
        auth_con.delete_bucket(auth_bucket)

    def test_error_code_populated(self):
        c = S3Connection()
        try:
            c.create_bucket('bad$bucket$name')
        except S3ResponseError as e:
            self.assertEqual(e.error_code, 'InvalidBucketName')
        except socket.gaierror:
            pass  # This is also a possible result for an invalid bucket name
        else:
            self.fail("S3ResponseError not raised.")
