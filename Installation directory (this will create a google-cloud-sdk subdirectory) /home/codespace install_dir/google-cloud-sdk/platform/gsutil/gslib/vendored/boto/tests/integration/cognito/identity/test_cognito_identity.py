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

from boto.cognito.identity.exceptions import ResourceNotFoundException
from tests.integration.cognito import CognitoTest


class TestCognitoIdentity(CognitoTest):
    """
    Test Cognitoy identity pools operations since individual Cognito identities
    require an AWS account ID.
    """
    def test_cognito_identity(self):
        # Ensure the identity pool is in the list of pools.
        response = self.cognito_identity.list_identity_pools(max_results=5)
        expected_identity = {'IdentityPoolId': self.identity_pool_id,
                             'IdentityPoolName': self.identity_pool_name}
        self.assertIn(expected_identity, response['IdentityPools'])

        # Ensure the pool's attributes are as expected.
        response = self.cognito_identity.describe_identity_pool(
            identity_pool_id=self.identity_pool_id
        )
        self.assertEqual(response['IdentityPoolName'], self.identity_pool_name)
        self.assertEqual(response['IdentityPoolId'], self.identity_pool_id)
        self.assertFalse(response['AllowUnauthenticatedIdentities'])

    def test_resource_not_found_exception(self):
        with self.assertRaises(ResourceNotFoundException):
            # Note the region is us-east-0 which is an invalid region name.
            self.cognito_identity.describe_identity_pool(
                identity_pool_id='us-east-0:c09e640-b014-4822-86b9-ec77c40d8d6f'
            )
