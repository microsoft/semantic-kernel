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

from boto.cognito.sync.exceptions import ResourceNotFoundException
from tests.integration.cognito import CognitoTest


class TestCognitoSync(CognitoTest):
    """
    Even more so for Cognito Sync, Cognito identites are required.  However,
    AWS account IDs are required to aqcuire a Cognito identity so only
    Cognito pool identity related operations are tested.
    """
    def test_cognito_sync(self):
        response = self.cognito_sync.describe_identity_pool_usage(
            identity_pool_id=self.identity_pool_id
        )
        identity_pool_usage = response['IdentityPoolUsage']
        self.assertEqual(identity_pool_usage['SyncSessionsCount'], None)
        self.assertEqual(identity_pool_usage['DataStorage'], 0)

    def test_resource_not_found_exception(self):
        with self.assertRaises(ResourceNotFoundException):
            # Note the region is us-east-0 which is an invalid region name.
            self.cognito_sync.describe_identity_pool_usage(
                identity_pool_id='us-east-0:c09e640-b014-4822-86b9-ec77c40d8d6f'
            )
