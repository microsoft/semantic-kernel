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

from boto.compat import json
from boto.kinesis.layer1 import KinesisConnection
from tests.unit import AWSMockServiceTestCase


class TestKinesis(AWSMockServiceTestCase):
    connection_class = KinesisConnection

    def default_body(self):
        return b'{}'

    def test_put_record_binary(self):
        self.set_http_response(status_code=200)
        self.service_connection.put_record('stream-name',
            b'\x00\x01\x02\x03\x04\x05', 'partition-key')

        body = json.loads(self.actual_request.body.decode('utf-8'))
        self.assertEqual(body['Data'], 'AAECAwQF')

        target = self.actual_request.headers['X-Amz-Target']
        self.assertTrue('PutRecord' in target)

    def test_put_record_string(self):
        self.set_http_response(status_code=200)
        self.service_connection.put_record('stream-name',
            'data', 'partition-key')

        body = json.loads(self.actual_request.body.decode('utf-8'))
        self.assertEqual(body['Data'], 'ZGF0YQ==')

        target = self.actual_request.headers['X-Amz-Target']
        self.assertTrue('PutRecord' in target)

    def test_put_records(self):
        self.set_http_response(status_code=200)
        record_binary = {
            'Data': b'\x00\x01\x02\x03\x04\x05',
            'PartitionKey': 'partition-key'
        }
        record_str = {
            'Data': 'data',
            'PartitionKey': 'partition-key'
        }
        self.service_connection.put_records(stream_name='stream-name',
            records=[record_binary, record_str])

        body = json.loads(self.actual_request.body.decode('utf-8'))
        self.assertEqual(body['Records'][0]['Data'], 'AAECAwQF')
        self.assertEqual(body['Records'][1]['Data'], 'ZGF0YQ==')

        target = self.actual_request.headers['X-Amz-Target']
        self.assertTrue('PutRecord' in target)
