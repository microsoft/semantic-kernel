# Copyright (c) 2014 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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

import boto
from tests.compat import unittest


class CognitoTest(unittest.TestCase):
    def setUp(self):
        self.cognito_identity = boto.connect_cognito_identity()
        self.cognito_sync = boto.connect_cognito_sync()
        self.identity_pool_name = 'myIdentityPool'
        response = self.cognito_identity.create_identity_pool(
            identity_pool_name=self.identity_pool_name,
            allow_unauthenticated_identities=False
        )
        self.identity_pool_id = response['IdentityPoolId']

    def tearDown(self):
        self.cognito_identity.delete_identity_pool(
            identity_pool_id=self.identity_pool_id
        )
