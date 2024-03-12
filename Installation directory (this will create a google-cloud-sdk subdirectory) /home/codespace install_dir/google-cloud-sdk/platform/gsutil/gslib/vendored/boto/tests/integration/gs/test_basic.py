# -*- coding: utf-8 -*-
# Copyright (c) 2006-2011 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010, Eucalyptus Systems, Inc.
# Copyright (c) 2011, Nexenta Systems, Inc.
# Copyright (c) 2012, Google, Inc.
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
Some integration tests for the GSConnection
"""

import os
import re
import urllib
import xml.sax

from six import StringIO

from boto import handler
from boto import storage_uri
from boto.gs.acl import ACL
from boto.gs.cors import Cors
from boto.gs.lifecycle import LifecycleConfig
from tests.integration.gs.testcase import GSTestCase


CORS_EMPTY = '<CorsConfig></CorsConfig>'
CORS_DOC = ('<CorsConfig><Cors><Origins><Origin>origin1.example.com'
            '</Origin><Origin>origin2.example.com</Origin></Origins>'
            '<Methods><Method>GET</Method><Method>PUT</Method>'
            '<Method>POST</Method></Methods><ResponseHeaders>'
            '<ResponseHeader>foo</ResponseHeader>'
            '<ResponseHeader>bar</ResponseHeader></ResponseHeaders>'
            '</Cors></CorsConfig>')

ENCRYPTION_CONFIG_WITH_KEY = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<EncryptionConfiguration>'
    '<DefaultKmsKeyName>%s</DefaultKmsKeyName>'
    '</EncryptionConfiguration>')

LIFECYCLE_EMPTY = ('<?xml version="1.0" encoding="UTF-8"?>'
                   '<LifecycleConfiguration></LifecycleConfiguration>')
LIFECYCLE_DOC = ('<?xml version="1.0" encoding="UTF-8"?>'
                 '<LifecycleConfiguration><Rule>'
                 '<Action><Delete/></Action>'
                 '<Condition>''<IsLive>true</IsLive>'
                 '<MatchesStorageClass>STANDARD</MatchesStorageClass>'
                 '<Age>365</Age>'
                 '<CreatedBefore>2013-01-15</CreatedBefore>'
                 '<NumberOfNewerVersions>3</NumberOfNewerVersions>'
                 '</Condition></Rule><Rule>'
                 '<Action><SetStorageClass>NEARLINE</SetStorageClass></Action>'
                 '<Condition><Age>366</Age>'
                 '</Condition></Rule></LifecycleConfiguration>')
LIFECYCLE_CONDITIONS_FOR_DELETE_RULE = {
    'Age': '365',
    'CreatedBefore': '2013-01-15',
    'NumberOfNewerVersions': '3',
    'IsLive': 'true',
    'MatchesStorageClass': ['STANDARD']}
LIFECYCLE_CONDITIONS_FOR_SET_STORAGE_CLASS_RULE = {'Age': '366'}

BILLING_EMPTY = {'BillingConfiguration': {}}
BILLING_ENABLED = {'BillingConfiguration': {'RequesterPays': 'Enabled'}}
BILLING_DISABLED = {'BillingConfiguration': {'RequesterPays': 'Disabled'}}

# Regexp for matching project-private default object ACL.
PROJECT_PRIVATE_RE = ('\s*<AccessControlList>\s*<Entries>\s*<Entry>'
  '\s*<Scope type="GroupById">\s*<ID>[-a-zA-Z0-9]+</ID>'
  '\s*(<Name>[^<]+</Name>)?\s*</Scope>'
  '\s*<Permission>FULL_CONTROL</Permission>\s*</Entry>\s*<Entry>'
  '\s*<Scope type="GroupById">\s*<ID>[-a-zA-Z0-9]+</ID>'
  '\s*(<Name>[^<]+</Name>)?\s*</Scope>'
  '\s*<Permission>FULL_CONTROL</Permission>\s*</Entry>\s*<Entry>'
  '\s*<Scope type="GroupById">\s*<ID>[-a-zA-Z0-9]+</ID>'
  '\s*(<Name>[^<]+</Name>)?\s*</Scope>'
  '\s*<Permission>READ</Permission>\s*</Entry>\s*</Entries>'
  '\s*</AccessControlList>\s*')


class GSBasicTest(GSTestCase):
    """Tests some basic GCS functionality."""

    def test_read_write(self):
        """Tests basic read/write to keys."""
        bucket = self._MakeBucket()
        bucket_name = bucket.name
        # now try a get_bucket call and see if it's really there
        bucket = self._GetConnection().get_bucket(bucket_name)
        key_name = 'foobar'
        k = bucket.new_key(key_name)
        s1 = 'This is a test of file upload and download'
        k.set_contents_from_string(s1)
        tmpdir = self._MakeTempDir()
        fpath = os.path.join(tmpdir, key_name)
        fp = open(fpath, 'wb')
        # now get the contents from gcs to a local file
        k.get_contents_to_file(fp)
        fp.close()
        fp = open(fpath)
        # check to make sure content read from gcs is identical to original
        self.assertEqual(s1, fp.read())
        fp.close()
        # Use generate_url to get the contents
        url = self._conn.generate_url(900, 'GET', bucket=bucket.name, key=key_name)
        f = urllib.urlopen(url)
        self.assertEqual(s1, f.read())
        f.close()
        # check to make sure set_contents_from_file is working
        sfp = StringIO.StringIO('foo')
        k.set_contents_from_file(sfp)
        self.assertEqual(k.get_contents_as_string(), 'foo')
        sfp2 = StringIO.StringIO('foo2')
        k.set_contents_from_file(sfp2)
        self.assertEqual(k.get_contents_as_string(), 'foo2')

    def test_get_all_keys(self):
        """Tests get_all_keys."""
        phony_mimetype = 'application/x-boto-test'
        headers = {'Content-Type': phony_mimetype}
        tmpdir = self._MakeTempDir()
        fpath = os.path.join(tmpdir, 'foobar1')
        fpath2 = os.path.join(tmpdir, 'foobar')
        with open(fpath2, 'w') as f:
            f.write('test-data')
        bucket = self._MakeBucket()

        # First load some data for the first one, overriding content type.
        k = bucket.new_key('foobar')
        s1 = 'test-contents'
        s2 = 'test-contents2'
        k.name = 'foo/bar'
        k.set_contents_from_string(s1, headers)
        k.name = 'foo/bas'
        k.set_contents_from_filename(fpath2)
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
        self.assertNotEqual(k.md5, md5)

        fp2 = open(fpath2, 'rb')
        k.md5 = None
        k.base64md5 = None
        k.set_contents_from_stream(fp2)
        fp = open(fpath, 'wb')
        k.get_contents_to_file(fp)
        fp.close()
        fp2.seek(0, 0)
        fp = open(fpath, 'rb')
        self.assertEqual(fp2.read(), fp.read())
        fp.close()
        fp2.close()
        all = bucket.get_all_keys()
        self.assertEqual(len(all), 6)
        rs = bucket.get_all_keys(prefix='foo')
        self.assertEqual(len(rs), 3)
        rs = bucket.get_all_keys(prefix='', delimiter='/')
        self.assertEqual(len(rs), 2)
        rs = bucket.get_all_keys(maxkeys=5)
        self.assertEqual(len(rs), 5)

    def test_bucket_lookup(self):
        """Test the bucket lookup method."""
        bucket = self._MakeBucket()
        k = bucket.new_key('foo/bar')
        phony_mimetype = 'application/x-boto-test'
        headers = {'Content-Type': phony_mimetype}
        k.set_contents_from_string('testdata', headers)

        k = bucket.lookup('foo/bar')
        self.assertIsInstance(k, bucket.key_class)
        self.assertEqual(k.content_type, phony_mimetype)
        k = bucket.lookup('notthere')
        self.assertIsNone(k)

    def test_metadata(self):
        """Test key metadata operations."""
        bucket = self._MakeBucket()
        k = self._MakeKey(bucket=bucket)
        key_name = k.name
        s1 = 'This is a test of file upload and download'

        mdkey1 = 'meta1'
        mdval1 = 'This is the first metadata value'
        k.set_metadata(mdkey1, mdval1)
        mdkey2 = 'meta2'
        mdval2 = 'This is the second metadata value'
        k.set_metadata(mdkey2, mdval2)

        # Test unicode character.
        mdval3 = u'föö'
        mdkey3 = 'meta3'
        k.set_metadata(mdkey3, mdval3)
        k.set_contents_from_string(s1)

        k = bucket.lookup(key_name)
        self.assertEqual(k.get_metadata(mdkey1), mdval1)
        self.assertEqual(k.get_metadata(mdkey2), mdval2)
        self.assertEqual(k.get_metadata(mdkey3), mdval3)
        k = bucket.new_key(key_name)
        k.get_contents_as_string()
        self.assertEqual(k.get_metadata(mdkey1), mdval1)
        self.assertEqual(k.get_metadata(mdkey2), mdval2)
        self.assertEqual(k.get_metadata(mdkey3), mdval3)

    def test_list_iterator(self):
        """Test list and iterator."""
        bucket = self._MakeBucket()
        num_iter = len([k for k in bucket.list()])
        rs = bucket.get_all_keys()
        num_keys = len(rs)
        self.assertEqual(num_iter, num_keys)

    def test_acl(self):
        """Test bucket and key ACLs."""
        bucket = self._MakeBucket()

        # try some acl stuff
        bucket.set_acl('public-read')
        acl = bucket.get_acl()
        self.assertEqual(len(acl.entries.entry_list), 2)
        bucket.set_acl('private')
        acl = bucket.get_acl()
        self.assertEqual(len(acl.entries.entry_list), 1)
        k = self._MakeKey(bucket=bucket)
        k.set_acl('public-read')
        acl = k.get_acl()
        self.assertEqual(len(acl.entries.entry_list), 2)
        k.set_acl('private')
        acl = k.get_acl()
        self.assertEqual(len(acl.entries.entry_list), 1)

        # Test case-insensitivity of XML ACL parsing.
        acl_xml = (
            '<ACCESSControlList><EntrIes><Entry>'    +
            '<Scope type="AllUsers"></Scope><Permission>READ</Permission>' +
            '</Entry></EntrIes></ACCESSControlList>')
        acl = ACL()
        h = handler.XmlHandler(acl, bucket)
        xml.sax.parseString(acl_xml, h)
        bucket.set_acl(acl)
        self.assertEqual(len(acl.entries.entry_list), 1)
        aclstr = k.get_xml_acl()
        self.assertGreater(aclstr.count('/Entry', 1), 0)

    def test_logging(self):
        """Test set/get raw logging subresource."""
        bucket = self._MakeBucket()
        empty_logging_str="<?xml version='1.0' encoding='UTF-8'?><Logging/>"
        logging_str = (
            "<?xml version='1.0' encoding='UTF-8'?><Logging>"
            "<LogBucket>log-bucket</LogBucket>" +
            "<LogObjectPrefix>example</LogObjectPrefix>" +
            "</Logging>")
        bucket.set_subresource('logging', logging_str)
        self.assertEqual(bucket.get_subresource('logging'), logging_str)
        # try disable/enable logging
        bucket.disable_logging()
        self.assertEqual(bucket.get_subresource('logging'), empty_logging_str)
        bucket.enable_logging('log-bucket', 'example')
        self.assertEqual(bucket.get_subresource('logging'), logging_str)

    def test_copy_key(self):
        """Test copying a key from one bucket to another."""
        # create two new, empty buckets
        bucket1 = self._MakeBucket()
        bucket2 = self._MakeBucket()
        bucket_name_1 = bucket1.name
        bucket_name_2 = bucket2.name
        # verify buckets got created
        bucket1 = self._GetConnection().get_bucket(bucket_name_1)
        bucket2 = self._GetConnection().get_bucket(bucket_name_2)
        # create a key in bucket1 and give it some content
        key_name = 'foobar'
        k1 = bucket1.new_key(key_name)
        self.assertIsInstance(k1, bucket1.key_class)
        k1.name = key_name
        s = 'This is a test.'
        k1.set_contents_from_string(s)
        # copy the new key from bucket1 to bucket2
        k1.copy(bucket_name_2, key_name)
        # now copy the contents from bucket2 to a local file
        k2 = bucket2.lookup(key_name)
        self.assertIsInstance(k2, bucket2.key_class)
        tmpdir = self._MakeTempDir()
        fpath = os.path.join(tmpdir, 'foobar')
        fp = open(fpath, 'wb')
        k2.get_contents_to_file(fp)
        fp.close()
        fp = open(fpath)
        # check to make sure content read is identical to original
        self.assertEqual(s, fp.read())
        fp.close()
        # delete keys
        bucket1.delete_key(k1)
        bucket2.delete_key(k2)

    def test_default_object_acls(self):
        """Test default object acls."""
        # create a new bucket
        bucket = self._MakeBucket()
        # get default acl and make sure it's project-private
        acl = bucket.get_def_acl()
        self.assertIsNotNone(re.search(PROJECT_PRIVATE_RE, acl.to_xml()))
        # set default acl to a canned acl and verify it gets set
        bucket.set_def_acl('public-read')
        acl = bucket.get_def_acl()
        # save public-read acl for later test
        public_read_acl = acl
        self.assertEqual(acl.to_xml(), ('<AccessControlList><Entries><Entry>'
          '<Scope type="AllUsers"></Scope><Permission>READ</Permission>'
          '</Entry></Entries></AccessControlList>'))
        # back to private acl
        bucket.set_def_acl('private')
        acl = bucket.get_def_acl()
        self.assertEqual(acl.to_xml(),
                         '<AccessControlList></AccessControlList>')
        # set default acl to an xml acl and verify it gets set
        bucket.set_def_acl(public_read_acl)
        acl = bucket.get_def_acl()
        self.assertEqual(acl.to_xml(), ('<AccessControlList><Entries><Entry>'
          '<Scope type="AllUsers"></Scope><Permission>READ</Permission>'
          '</Entry></Entries></AccessControlList>'))
        # back to private acl
        bucket.set_def_acl('private')
        acl = bucket.get_def_acl()
        self.assertEqual(acl.to_xml(),
                         '<AccessControlList></AccessControlList>')

    def test_default_object_acls_storage_uri(self):
        """Test default object acls using storage_uri."""
        # create a new bucket
        bucket = self._MakeBucket()
        bucket_name = bucket.name
        uri = storage_uri('gs://' + bucket_name)
        # get default acl and make sure it's project-private
        acl = uri.get_def_acl()
        self.assertIsNotNone(
            re.search(PROJECT_PRIVATE_RE, acl.to_xml()),
            'PROJECT_PRIVATE_RE not found in ACL XML:\n' + acl.to_xml())
        # set default acl to a canned acl and verify it gets set
        uri.set_def_acl('public-read')
        acl = uri.get_def_acl()
        # save public-read acl for later test
        public_read_acl = acl
        self.assertEqual(acl.to_xml(), ('<AccessControlList><Entries><Entry>'
          '<Scope type="AllUsers"></Scope><Permission>READ</Permission>'
          '</Entry></Entries></AccessControlList>'))
        # back to private acl
        uri.set_def_acl('private')
        acl = uri.get_def_acl()
        self.assertEqual(acl.to_xml(),
                         '<AccessControlList></AccessControlList>')
        # set default acl to an xml acl and verify it gets set
        uri.set_def_acl(public_read_acl)
        acl = uri.get_def_acl()
        self.assertEqual(acl.to_xml(), ('<AccessControlList><Entries><Entry>'
          '<Scope type="AllUsers"></Scope><Permission>READ</Permission>'
          '</Entry></Entries></AccessControlList>'))
        # back to private acl
        uri.set_def_acl('private')
        acl = uri.get_def_acl()
        self.assertEqual(acl.to_xml(),
                         '<AccessControlList></AccessControlList>')

    def test_cors_xml_bucket(self):
        """Test setting and getting of CORS XML documents on Bucket."""
        # create a new bucket
        bucket = self._MakeBucket()
        bucket_name = bucket.name
        # now call get_bucket to see if it's really there
        bucket = self._GetConnection().get_bucket(bucket_name)
        # get new bucket cors and make sure it's empty
        cors = re.sub(r'\s', '', bucket.get_cors().to_xml())
        self.assertEqual(cors, CORS_EMPTY)
        # set cors document on new bucket
        bucket.set_cors(CORS_DOC)
        cors = re.sub(r'\s', '', bucket.get_cors().to_xml())
        self.assertEqual(cors, CORS_DOC)

    def test_cors_xml_storage_uri(self):
        """Test setting and getting of CORS XML documents with storage_uri."""
        # create a new bucket
        bucket = self._MakeBucket()
        bucket_name = bucket.name
        uri = storage_uri('gs://' + bucket_name)
        # get new bucket cors and make sure it's empty
        cors = re.sub(r'\s', '', uri.get_cors().to_xml())
        self.assertEqual(cors, CORS_EMPTY)
        # set cors document on new bucket
        cors_obj = Cors()
        h = handler.XmlHandler(cors_obj, None)
        xml.sax.parseString(CORS_DOC, h)
        uri.set_cors(cors_obj)
        cors = re.sub(r'\s', '', uri.get_cors().to_xml())
        self.assertEqual(cors, CORS_DOC)

    def test_lifecycle_config_bucket(self):
        """Test setting and getting of lifecycle config on Bucket."""
        # create a new bucket
        bucket = self._MakeBucket()
        bucket_name = bucket.name
        # now call get_bucket to see if it's really there
        bucket = self._GetConnection().get_bucket(bucket_name)
        # get lifecycle config and make sure it's empty
        xml = bucket.get_lifecycle_config().to_xml()
        self.assertEqual(xml, LIFECYCLE_EMPTY)
        # set lifecycle config
        lifecycle_config = LifecycleConfig()
        lifecycle_config.add_rule(
            'Delete', None, LIFECYCLE_CONDITIONS_FOR_DELETE_RULE)
        lifecycle_config.add_rule(
            'SetStorageClass', 'NEARLINE',
            LIFECYCLE_CONDITIONS_FOR_SET_STORAGE_CLASS_RULE)
        bucket.configure_lifecycle(lifecycle_config)
        xml = bucket.get_lifecycle_config().to_xml()
        self.assertEqual(xml, LIFECYCLE_DOC)

    def test_lifecycle_config_storage_uri(self):
        """Test setting and getting of lifecycle config with storage_uri."""
        # create a new bucket
        bucket = self._MakeBucket()
        bucket_name = bucket.name
        uri = storage_uri('gs://' + bucket_name)
        # get lifecycle config and make sure it's empty
        xml = uri.get_lifecycle_config().to_xml()
        self.assertEqual(xml, LIFECYCLE_EMPTY)
        # set lifecycle config
        lifecycle_config = LifecycleConfig()
        lifecycle_config.add_rule(
            'Delete', None, LIFECYCLE_CONDITIONS_FOR_DELETE_RULE)
        lifecycle_config.add_rule(
            'SetStorageClass', 'NEARLINE',
            LIFECYCLE_CONDITIONS_FOR_SET_STORAGE_CLASS_RULE)
        uri.configure_lifecycle(lifecycle_config)
        xml = uri.get_lifecycle_config().to_xml()
        self.assertEqual(xml, LIFECYCLE_DOC)

    def test_billing_config_bucket(self):
        """Test setting and getting of billing config on Bucket."""
        # create a new bucket
        bucket = self._MakeBucket()
        bucket_name = bucket.name
        # get billing config and make sure it's empty
        billing = bucket.get_billing_config()
        self.assertEqual(billing, BILLING_EMPTY)
        # set requester pays to enabled
        bucket.configure_billing(requester_pays=True)
        billing = bucket.get_billing_config()
        self.assertEqual(billing, BILLING_ENABLED)
        # set requester pays to disabled
        bucket.configure_billing(requester_pays=False)
        billing = bucket.get_billing_config()
        self.assertEqual(billing, BILLING_DISABLED)

    def test_billing_config_storage_uri(self):
        """Test setting and getting of billing config with storage_uri."""
        # create a new bucket
        bucket = self._MakeBucket()
        bucket_name = bucket.name
        uri = storage_uri('gs://' + bucket_name)
        # get billing config and make sure it's empty
        billing = uri.get_billing_config()
        self.assertEqual(billing, BILLING_EMPTY)
        # set requester pays to enabled
        uri.configure_billing(requester_pays=True)
        billing = uri.get_billing_config()
        self.assertEqual(billing, BILLING_ENABLED)
        # set requester pays to disabled
        uri.configure_billing(requester_pays=False)
        billing = uri.get_billing_config()
        self.assertEqual(billing, BILLING_DISABLED)

    def test_encryption_config_bucket(self):
        """Test setting and getting of EncryptionConfig on gs Bucket objects."""
        # Create a new bucket.
        bucket = self._MakeBucket()
        bucket_name = bucket.name
        # Get EncryptionConfig and make sure it's empty.
        encryption_config = bucket.get_encryption_config()
        self.assertIsNone(encryption_config.default_kms_key_name)
        # Testing set functionality would require having an existing Cloud KMS
        # key. Since we can't hardcode a key name or dynamically create one, we
        # only test here that we're creating the correct XML document to send to
        # GCS.
        xmldoc = bucket._construct_encryption_config_xml(
            default_kms_key_name='dummykey')
        self.assertEqual(xmldoc, ENCRYPTION_CONFIG_WITH_KEY % 'dummykey')
        # Test that setting an empty encryption config works.
        bucket.set_encryption_config()

    def test_encryption_config_storage_uri(self):
        """Test setting and getting of EncryptionConfig with storage_uri."""
        # Create a new bucket.
        bucket = self._MakeBucket()
        bucket_name = bucket.name
        uri = storage_uri('gs://' + bucket_name)
        # Get EncryptionConfig and make sure it's empty.
        encryption_config = uri.get_encryption_config()
        self.assertIsNone(encryption_config.default_kms_key_name)

        # Test that setting an empty encryption config works.
        uri.set_encryption_config()
