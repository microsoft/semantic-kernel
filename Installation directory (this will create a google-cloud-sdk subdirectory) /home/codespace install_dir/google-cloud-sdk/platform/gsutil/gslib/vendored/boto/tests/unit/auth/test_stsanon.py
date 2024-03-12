# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
#
import copy
from mock import Mock
from tests.unit import unittest

from boto.auth import STSAnonHandler
from boto.connection import HTTPRequest


class TestSTSAnonHandler(unittest.TestCase):
    def setUp(self):
        self.provider = Mock()
        self.provider.access_key = 'access_key'
        self.provider.secret_key = 'secret_key'
        self.request = HTTPRequest(
            method='GET',
            protocol='https',
            host='sts.amazonaws.com',
            port=443,
            path='/',
            auth_path=None,
            params={
                'Action': 'AssumeRoleWithWebIdentity',
                'Version': '2011-06-15',
                'RoleSessionName': 'web-identity-federation',
                'ProviderId': '2012-06-01',
                'WebIdentityToken': 'Atza|IQEBLjAsAhRkcxQ',
            },
            headers={},
            body=''
        )

    def test_escape_value(self):
        auth = STSAnonHandler('sts.amazonaws.com',
                              Mock(), self.provider)
        # This is changed from a previous version because this string is
        # being passed to the query string and query strings must
        # be url encoded.
        value = auth._escape_value('Atza|IQEBLjAsAhRkcxQ')
        self.assertEqual(value, 'Atza%7CIQEBLjAsAhRkcxQ')

    def test_build_query_string(self):
        auth = STSAnonHandler('sts.amazonaws.com',
                              Mock(), self.provider)
        query_string = auth._build_query_string(self.request.params)
        self.assertEqual(query_string, 'Action=AssumeRoleWithWebIdentity' + \
            '&ProviderId=2012-06-01&RoleSessionName=web-identity-federation' + \
            '&Version=2011-06-15&WebIdentityToken=Atza%7CIQEBLjAsAhRkcxQ')

    def test_add_auth(self):
        auth = STSAnonHandler('sts.amazonaws.com',
                              Mock(), self.provider)
        req = copy.copy(self.request)
        auth.add_auth(req)
        self.assertEqual(req.body,
            'Action=AssumeRoleWithWebIdentity' + \
            '&ProviderId=2012-06-01&RoleSessionName=web-identity-federation' + \
            '&Version=2011-06-15&WebIdentityToken=Atza%7CIQEBLjAsAhRkcxQ')
