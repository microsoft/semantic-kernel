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

import time

import boto
from tests.compat import unittest
from boto.kinesis.exceptions import ResourceNotFoundException


class TimeoutError(Exception):
    pass


class TestKinesis(unittest.TestCase):
    def setUp(self):
        self.kinesis = boto.connect_kinesis()

    def test_kinesis(self):
        kinesis = self.kinesis

        # Create a new stream
        kinesis.create_stream('test', 1)
        self.addCleanup(self.kinesis.delete_stream, 'test')

        # Wait for the stream to be ready
        tries = 0
        while tries < 10:
            tries += 1
            time.sleep(15)
            response = kinesis.describe_stream('test')

            if response['StreamDescription']['StreamStatus'] == 'ACTIVE':
                shard_id = response['StreamDescription']['Shards'][0]['ShardId']
                break
        else:
            raise TimeoutError('Stream is still not active, aborting...')

        # Make a tag.
        kinesis.add_tags_to_stream(stream_name='test', tags={'foo': 'bar'})

        # Check that the correct tag is there.
        response = kinesis.list_tags_for_stream(stream_name='test')
        self.assertEqual(len(response['Tags']), 1)
        self.assertEqual(response['Tags'][0],
                         {'Key':'foo', 'Value': 'bar'})

        # Remove the tag and ensure it is removed.
        kinesis.remove_tags_from_stream(stream_name='test', tag_keys=['foo'])
        response = kinesis.list_tags_for_stream(stream_name='test')
        self.assertEqual(len(response['Tags']), 0)

        # Get ready to process some data from the stream
        response = kinesis.get_shard_iterator('test', shard_id, 'TRIM_HORIZON')
        shard_iterator = response['ShardIterator']

        # Write some data to the stream
        data = 'Some data ...'
        record = {
            'Data': data,
            'PartitionKey': data,
        }
        response = kinesis.put_record('test', data, data)
        response = kinesis.put_records([record, record.copy()], 'test')

        # Wait for the data to show up
        tries = 0
        num_collected = 0
        num_expected_records = 3
        collected_records = []
        while tries < 100:
            tries += 1
            time.sleep(1)

            response = kinesis.get_records(shard_iterator)
            shard_iterator = response['NextShardIterator']
            for record in response['Records']:
                if 'Data' in record:
                    collected_records.append(record['Data'])
                    num_collected += 1
            if num_collected >= num_expected_records:
                self.assertEqual(num_expected_records, num_collected)
                break
        else:
            raise TimeoutError('No records found, aborting...')

        # Read the data, which should be the same as what we wrote
        for record in collected_records:
            self.assertEqual(data, record)

    def test_describe_non_existent_stream(self):
        with self.assertRaises(ResourceNotFoundException) as cm:
            self.kinesis.describe_stream('this-stream-shouldnt-exist')

        # Assert things about the data we passed along.
        self.assertEqual(cm.exception.error_code, None)
        self.assertTrue('not found' in cm.exception.message)
