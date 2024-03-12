#!/usr/bin/env python

# Copyright (c) 2006,2007 Mitch Garnaat http://garnaat.org/
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

import time
import os
import urllib

from boto.s3.connection import S3Connection
from boto.exception import S3PermissionsError

# this test requires a devpay product and user token to run:

AMAZON_USER_TOKEN = '{UserToken}...your token here...'
DEVPAY_HEADERS = { 'x-amz-security-token': AMAZON_USER_TOKEN }

def test():
    print('--- running S3Connection tests (DevPay) ---')
    c = S3Connection()
    # create a new, empty bucket
    bucket_name = 'test-%d' % int(time.time())
    bucket = c.create_bucket(bucket_name, headers=DEVPAY_HEADERS)
    # now try a get_bucket call and see if it's really there
    bucket = c.get_bucket(bucket_name, headers=DEVPAY_HEADERS)
    # test logging
    logging_bucket = c.create_bucket(bucket_name + '-log', headers=DEVPAY_HEADERS)
    logging_bucket.set_as_logging_target(headers=DEVPAY_HEADERS)
    bucket.enable_logging(target_bucket=logging_bucket, target_prefix=bucket.name, headers=DEVPAY_HEADERS)
    bucket.disable_logging(headers=DEVPAY_HEADERS)
    c.delete_bucket(logging_bucket, headers=DEVPAY_HEADERS)
    # create a new key and store it's content from a string
    k = bucket.new_key()
    k.name = 'foobar'
    s1 = 'This is a test of file upload and download'
    s2 = 'This is a second string to test file upload and download'
    k.set_contents_from_string(s1, headers=DEVPAY_HEADERS)
    fp = open('foobar', 'wb')
    # now get the contents from s3 to a local file
    k.get_contents_to_file(fp, headers=DEVPAY_HEADERS)
    fp.close()
    fp = open('foobar')
    # check to make sure content read from s3 is identical to original
    assert s1 == fp.read(), 'corrupted file'
    fp.close()
    # test generated URLs
    url = k.generate_url(3600, headers=DEVPAY_HEADERS)
    file = urllib.urlopen(url)
    assert s1 == file.read(), 'invalid URL %s' % url
    url = k.generate_url(3600, force_http=True, headers=DEVPAY_HEADERS)
    file = urllib.urlopen(url)
    assert s1 == file.read(), 'invalid URL %s' % url
    bucket.delete_key(k, headers=DEVPAY_HEADERS)
    # test a few variations on get_all_keys - first load some data
    # for the first one, let's override the content type
    phony_mimetype = 'application/x-boto-test'
    headers = {'Content-Type': phony_mimetype}
    headers.update(DEVPAY_HEADERS)
    k.name = 'foo/bar'
    k.set_contents_from_string(s1, headers)
    k.name = 'foo/bas'
    k.set_contents_from_filename('foobar', headers=DEVPAY_HEADERS)
    k.name = 'foo/bat'
    k.set_contents_from_string(s1, headers=DEVPAY_HEADERS)
    k.name = 'fie/bar'
    k.set_contents_from_string(s1, headers=DEVPAY_HEADERS)
    k.name = 'fie/bas'
    k.set_contents_from_string(s1, headers=DEVPAY_HEADERS)
    k.name = 'fie/bat'
    k.set_contents_from_string(s1, headers=DEVPAY_HEADERS)
    # try resetting the contents to another value
    md5 = k.md5
    k.set_contents_from_string(s2, headers=DEVPAY_HEADERS)
    assert k.md5 != md5
    os.unlink('foobar')
    all = bucket.get_all_keys(headers=DEVPAY_HEADERS)
    assert len(all) == 6
    rs = bucket.get_all_keys(prefix='foo', headers=DEVPAY_HEADERS)
    assert len(rs) == 3
    rs = bucket.get_all_keys(prefix='', delimiter='/', headers=DEVPAY_HEADERS)
    assert len(rs) == 2
    rs = bucket.get_all_keys(maxkeys=5, headers=DEVPAY_HEADERS)
    assert len(rs) == 5
    # test the lookup method
    k = bucket.lookup('foo/bar', headers=DEVPAY_HEADERS)
    assert isinstance(k, bucket.key_class)
    assert k.content_type == phony_mimetype
    k = bucket.lookup('notthere', headers=DEVPAY_HEADERS)
    assert k == None
    # try some metadata stuff
    k = bucket.new_key()
    k.name = 'has_metadata'
    mdkey1 = 'meta1'
    mdval1 = 'This is the first metadata value'
    k.set_metadata(mdkey1, mdval1)
    mdkey2 = 'meta2'
    mdval2 = 'This is the second metadata value'
    k.set_metadata(mdkey2, mdval2)
    k.set_contents_from_string(s1, headers=DEVPAY_HEADERS)
    k = bucket.lookup('has_metadata', headers=DEVPAY_HEADERS)
    assert k.get_metadata(mdkey1) == mdval1
    assert k.get_metadata(mdkey2) == mdval2
    k = bucket.new_key()
    k.name = 'has_metadata'
    k.get_contents_as_string(headers=DEVPAY_HEADERS)
    assert k.get_metadata(mdkey1) == mdval1
    assert k.get_metadata(mdkey2) == mdval2
    bucket.delete_key(k, headers=DEVPAY_HEADERS)
    # test list and iterator
    rs1 = bucket.list(headers=DEVPAY_HEADERS)
    num_iter = 0
    for r in rs1:
        num_iter = num_iter + 1
    rs = bucket.get_all_keys(headers=DEVPAY_HEADERS)
    num_keys = len(rs)
    assert num_iter == num_keys
    # try a key with a funny character
    k = bucket.new_key()
    k.name = 'testnewline\n'
    k.set_contents_from_string('This is a test', headers=DEVPAY_HEADERS)
    rs = bucket.get_all_keys(headers=DEVPAY_HEADERS)
    assert len(rs) == num_keys + 1
    bucket.delete_key(k, headers=DEVPAY_HEADERS)
    rs = bucket.get_all_keys(headers=DEVPAY_HEADERS)
    assert len(rs) == num_keys
    # try some acl stuff
    bucket.set_acl('public-read', headers=DEVPAY_HEADERS)
    policy = bucket.get_acl(headers=DEVPAY_HEADERS)
    assert len(policy.acl.grants) == 2
    bucket.set_acl('private', headers=DEVPAY_HEADERS)
    policy = bucket.get_acl(headers=DEVPAY_HEADERS)
    assert len(policy.acl.grants) == 1
    k = bucket.lookup('foo/bar', headers=DEVPAY_HEADERS)
    k.set_acl('public-read', headers=DEVPAY_HEADERS)
    policy = k.get_acl(headers=DEVPAY_HEADERS)
    assert len(policy.acl.grants) == 2
    k.set_acl('private', headers=DEVPAY_HEADERS)
    policy = k.get_acl(headers=DEVPAY_HEADERS)
    assert len(policy.acl.grants) == 1
    # try the convenience methods for grants
    # this doesn't work with devpay
    #bucket.add_user_grant('FULL_CONTROL',
    #                      'c1e724fbfa0979a4448393c59a8c055011f739b6d102fb37a65f26414653cd67',
    #                      headers=DEVPAY_HEADERS)
    try:
        bucket.add_email_grant('foobar', 'foo@bar.com', headers=DEVPAY_HEADERS)
    except S3PermissionsError:
        pass
    # now delete all keys in bucket
    for k in all:
        bucket.delete_key(k, headers=DEVPAY_HEADERS)
    # now delete bucket

    c.delete_bucket(bucket, headers=DEVPAY_HEADERS)

    print('--- tests completed ---')

if __name__ == '__main__':
    test()
