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
Some unit tests for S3 MfaDelete with versioning
"""

import unittest
import time
from nose.plugins.attrib import attr

from boto.s3.connection import S3Connection
from boto.exception import S3ResponseError
from boto.s3.deletemarker import DeleteMarker


@attr('notdefault', 's3mfa')
class S3MFATest (unittest.TestCase):

    def setUp(self):
        self.conn = S3Connection()
        self.bucket_name = 'mfa-%d' % int(time.time())
        self.bucket = self.conn.create_bucket(self.bucket_name)

    def tearDown(self):
        for k in self.bucket.list_versions():
            self.bucket.delete_key(k.name, version_id=k.version_id)
        self.bucket.delete()

    def test_mfadel(self):
        # Enable Versioning with MfaDelete
        mfa_sn = raw_input('MFA S/N: ')
        mfa_code = raw_input('MFA Code: ')
        self.bucket.configure_versioning(True, mfa_delete=True, mfa_token=(mfa_sn, mfa_code))

        # Check enabling mfa worked.
        i = 0
        for i in range(1, 8):
            time.sleep(2**i)
            d = self.bucket.get_versioning_status()
            if d['Versioning'] == 'Enabled' and d['MfaDelete'] == 'Enabled':
                break
        self.assertEqual('Enabled', d['Versioning'])
        self.assertEqual('Enabled', d['MfaDelete'])

        # Add a key to the bucket
        k = self.bucket.new_key('foobar')
        s1 = 'This is v1'
        k.set_contents_from_string(s1)
        v1 = k.version_id

        # Now try to delete v1 without the MFA token
        try:
            self.bucket.delete_key('foobar', version_id=v1)
            self.fail("Must fail if not using MFA token")
        except S3ResponseError:
            pass

        # Now try delete again with the MFA token
        mfa_code = raw_input('MFA Code: ')
        self.bucket.delete_key('foobar', version_id=v1, mfa_token=(mfa_sn, mfa_code))

        # Next suspend versioning and disable MfaDelete on the bucket
        mfa_code = raw_input('MFA Code: ')
        self.bucket.configure_versioning(False, mfa_delete=False, mfa_token=(mfa_sn, mfa_code))

        # Lastly, check disabling mfa worked.
        i = 0
        for i in range(1, 8):
            time.sleep(2**i)
            d = self.bucket.get_versioning_status()
            if d['Versioning'] == 'Suspended' and d['MfaDelete'] != 'Enabled':
                break
        self.assertEqual('Suspended', d['Versioning'])
        self.assertNotEqual('Enabled', d['MfaDelete'])
