# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.
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
Tests for Layer1 of DynamoDB v2
"""
from tests.unit import unittest
from boto.dynamodb2.layer1 import DynamoDBConnection
from boto.regioninfo import RegionInfo


class DynamoDBv2Layer1UnitTest(unittest.TestCase):
    dynamodb = True

    def test_init_region(self):
        dynamodb = DynamoDBConnection(
            aws_access_key_id='aws_access_key_id',
            aws_secret_access_key='aws_secret_access_key')
        self.assertEqual(dynamodb.region.name, 'us-east-1')
        dynamodb = DynamoDBConnection(
            region=RegionInfo(name='us-west-2',
                              endpoint='dynamodb.us-west-2.amazonaws.com'),
            aws_access_key_id='aws_access_key_id',
            aws_secret_access_key='aws_secret_access_key',
        )
        self.assertEqual(dynamodb.region.name, 'us-west-2')

    def test_init_host_override(self):
        dynamodb = DynamoDBConnection(
            aws_access_key_id='aws_access_key_id',
            aws_secret_access_key='aws_secret_access_key',
            host='localhost', port=8000)
        self.assertEqual(dynamodb.host, 'localhost')
        self.assertEqual(dynamodb.port, 8000)
