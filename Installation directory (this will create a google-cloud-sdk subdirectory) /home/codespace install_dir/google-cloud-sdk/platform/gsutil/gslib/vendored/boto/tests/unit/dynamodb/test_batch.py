#!/usr/bin/env python
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
from tests.unit import unittest

from boto.dynamodb.batch import Batch
from boto.dynamodb.table import Table
from boto.dynamodb.layer2 import Layer2
from boto.dynamodb.batch import BatchList


DESCRIBE_TABLE_1 = {
    'Table': {
        'CreationDateTime': 1349910554.478,
        'ItemCount': 1,
        'KeySchema': {'HashKeyElement': {'AttributeName': u'foo',
                                         'AttributeType': u'S'}},
        'ProvisionedThroughput': {'ReadCapacityUnits': 10,
                                  'WriteCapacityUnits': 10},
        'TableName': 'testtable',
        'TableSizeBytes': 54,
        'TableStatus': 'ACTIVE'}
}

DESCRIBE_TABLE_2 = {
    'Table': {
        'CreationDateTime': 1349910554.478,
        'ItemCount': 1,
        'KeySchema': {'HashKeyElement': {'AttributeName': u'baz',
                                         'AttributeType': u'S'},
                      'RangeKeyElement': {'AttributeName': 'myrange',
                                          'AttributeType': 'N'}},
        'ProvisionedThroughput': {'ReadCapacityUnits': 10,
                                  'WriteCapacityUnits': 10},
        'TableName': 'testtable2',
        'TableSizeBytes': 54,
        'TableStatus': 'ACTIVE'}
}


class TestBatchObjects(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.layer2 = Layer2('access_key', 'secret_key')
        self.table = Table(self.layer2, DESCRIBE_TABLE_1)
        self.table2 = Table(self.layer2, DESCRIBE_TABLE_2)

    def test_batch_to_dict(self):
        b = Batch(self.table, ['k1', 'k2'], attributes_to_get=['foo'],
                  consistent_read=True)
        self.assertDictEqual(
            b.to_dict(),
            {'AttributesToGet': ['foo'],
             'Keys': [{'HashKeyElement': {'S': 'k1'}},
                      {'HashKeyElement': {'S': 'k2'}}],
             'ConsistentRead': True}
        )

    def test_batch_consistent_read_defaults_to_false(self):
        b = Batch(self.table, ['k1'])
        self.assertDictEqual(
            b.to_dict(),
            {'Keys': [{'HashKeyElement': {'S': 'k1'}}],
             'ConsistentRead': False}
        )

    def test_batch_list_consistent_read(self):
        b = BatchList(self.layer2)
        b.add_batch(self.table, ['k1'], ['foo'], consistent_read=True)
        b.add_batch(self.table2, [('k2', 54)], ['bar'], consistent_read=False)
        self.assertDictEqual(
            b.to_dict(),
            {'testtable': {'AttributesToGet': ['foo'],
                           'Keys': [{'HashKeyElement': {'S': 'k1'}}],
                           'ConsistentRead': True},
              'testtable2': {'AttributesToGet': ['bar'],
                             'Keys': [{'HashKeyElement': {'S': 'k2'},
                                       'RangeKeyElement': {'N': '54'}}],
                             'ConsistentRead': False}})


if __name__ == '__main__':
    unittest.main()
