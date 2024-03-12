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
Tests for Session Tokens
"""

import unittest
import os
from boto.exception import BotoServerError
from boto.sts.connection import STSConnection
from boto.sts.credentials import Credentials
from boto.s3.connection import S3Connection


class SessionTokenTest(unittest.TestCase):
    sts = True

    def test_session_token(self):
        print('--- running Session Token tests ---')
        c = STSConnection()

        # Create a session token
        token = c.get_session_token()

        # Save session token to a file
        token.save('token.json')

        # Now load up a copy of that token
        token_copy = Credentials.load('token.json')
        assert token_copy.access_key == token.access_key
        assert token_copy.secret_key == token.secret_key
        assert token_copy.session_token == token.session_token
        assert token_copy.expiration == token.expiration
        assert token_copy.request_id == token.request_id

        os.unlink('token.json')

        assert not token.is_expired()

        # Try using the session token with S3
        s3 = S3Connection(aws_access_key_id=token.access_key,
                          aws_secret_access_key=token.secret_key,
                          security_token=token.session_token)
        buckets = s3.get_all_buckets()

        print('--- tests completed ---')

    def test_assume_role_with_web_identity(self):
        c = STSConnection(anon=True)
        arn = 'arn:aws:iam::000240903217:role/FederatedWebIdentityRole'
        wit = 'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'

        try:
            creds = c.assume_role_with_web_identity(
                role_arn=arn,
                role_session_name='guestuser',
                web_identity_token=wit,
                provider_id='www.amazon.com',
            )
        except BotoServerError as err:
            self.assertEqual(err.status, 403)
            self.assertTrue('Not authorized' in err.body)

    def test_decode_authorization_message(self):
        c = STSConnection()

        try:
            creds = c.decode_authorization_message('b94d27b9934')
        except BotoServerError as err:
            self.assertEqual(err.status, 400)
            self.assertIn('InvalidAuthorizationMessageException', err.body)
