# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.
# All Rights Reserved
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
from boto.directconnect.layer1 import DirectConnectConnection
from tests.unit import AWSMockServiceTestCase


class TestDescribeTrails(AWSMockServiceTestCase):
    connection_class = DirectConnectConnection

    def default_body(self):
        return b'''
{
    "connections": [
        {
            "bandwidth": "string",
            "connectionId": "string",
            "connectionName": "string",
            "connectionState": "string",
            "location": "string",
            "ownerAccount": "string",
            "partnerName": "string",
            "region": "string",
            "vlan": 1
        }
    ]
}'''

    def test_describe(self):
        self.set_http_response(status_code=200)
        api_response = self.service_connection.describe_connections()

        self.assertEqual(1, len(api_response['connections']))
        self.assertEqual('string', api_response['connections'][0]['region'])

        self.assert_request_parameters({})

        target = self.actual_request.headers['X-Amz-Target']
        self.assertTrue('DescribeConnections' in target)
