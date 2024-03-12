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
import time

from tests.unit import unittest
from boto.dynamodb2 import exceptions
from boto.dynamodb2.layer1 import DynamoDBConnection


class DynamoDBv2Layer1Test(unittest.TestCase):
    dynamodb = True

    def setUp(self):
        self.dynamodb = DynamoDBConnection()
        self.table_name = 'test-%d' % int(time.time())
        self.hash_key_name = 'username'
        self.hash_key_type = 'S'
        self.range_key_name = 'date_joined'
        self.range_key_type = 'N'
        self.read_units = 5
        self.write_units = 5
        self.attributes = [
            {
                'AttributeName': self.hash_key_name,
                'AttributeType': self.hash_key_type,
            },
            {
                'AttributeName': self.range_key_name,
                'AttributeType': self.range_key_type,
            }
        ]
        self.schema = [
            {
                'AttributeName': self.hash_key_name,
                'KeyType': 'HASH',
            },
            {
                'AttributeName': self.range_key_name,
                'KeyType': 'RANGE',
            },
        ]
        self.provisioned_throughput = {
            'ReadCapacityUnits': self.read_units,
            'WriteCapacityUnits': self.write_units,
        }
        self.lsi = [
            {
                'IndexName': 'MostRecentIndex',
                'KeySchema': [
                    {
                        'AttributeName': self.hash_key_name,
                        'KeyType': 'HASH',
                    },
                    {
                        'AttributeName': self.range_key_name,
                        'KeyType': 'RANGE',
                    },
                ],
                'Projection': {
                    'ProjectionType': 'KEYS_ONLY',
                }
            }
        ]

    def create_table(self, table_name, attributes, schema,
                     provisioned_throughput, lsi=None, wait=True):
        # Note: This is a slightly different ordering that makes less sense.
        result = self.dynamodb.create_table(
            attributes,
            table_name,
            schema,
            provisioned_throughput,
            local_secondary_indexes=lsi
        )
        self.addCleanup(self.dynamodb.delete_table, table_name)
        if wait:
            while True:
                description = self.dynamodb.describe_table(table_name)
                if description['Table']['TableStatus'].lower() == 'active':
                    return result
                else:
                    time.sleep(5)
        else:
            return result

    def test_integrated(self):
        result = self.create_table(
            self.table_name,
            self.attributes,
            self.schema,
            self.provisioned_throughput,
            self.lsi
        )
        self.assertEqual(
            result['TableDescription']['TableName'],
            self.table_name
        )

        description = self.dynamodb.describe_table(self.table_name)
        self.assertEqual(description['Table']['ItemCount'], 0)

        # Create some records.
        record_1_data = {
            'username': {'S': 'johndoe'},
            'first_name': {'S': 'John'},
            'last_name': {'S': 'Doe'},
            'date_joined': {'N': '1366056668'},
            'friend_count': {'N': '3'},
            'friends': {'SS': ['alice', 'bob', 'jane']},
        }
        r1_result = self.dynamodb.put_item(self.table_name, record_1_data)

        # Get the data.
        record_1 = self.dynamodb.get_item(self.table_name, key={
            'username': {'S': 'johndoe'},
            'date_joined': {'N': '1366056668'},
        }, consistent_read=True)
        self.assertEqual(record_1['Item']['username']['S'], 'johndoe')
        self.assertEqual(record_1['Item']['first_name']['S'], 'John')
        self.assertEqual(record_1['Item']['friends']['SS'], [
            'alice', 'bob', 'jane'
        ])

        # Now in a batch.
        self.dynamodb.batch_write_item({
            self.table_name: [
                {
                    'PutRequest': {
                        'Item': {
                            'username': {'S': 'jane'},
                            'first_name': {'S': 'Jane'},
                            'last_name': {'S': 'Doe'},
                            'date_joined': {'N': '1366056789'},
                            'friend_count': {'N': '1'},
                            'friends': {'SS': ['johndoe']},
                        },
                    },
                },
            ]
        })

        # Now a query.
        lsi_results = self.dynamodb.query(
            self.table_name,
            index_name='MostRecentIndex',
            key_conditions={
                'username': {
                    'AttributeValueList': [
                        {'S': 'johndoe'},
                    ],
                    'ComparisonOperator': 'EQ',
                },
            },
            consistent_read=True
        )
        self.assertEqual(lsi_results['Count'], 1)

        results = self.dynamodb.query(self.table_name, key_conditions={
            'username': {
                'AttributeValueList': [
                    {'S': 'jane'},
                ],
                'ComparisonOperator': 'EQ',
            },
            'date_joined': {
                'AttributeValueList': [
                    {'N': '1366050000'}
                ],
                'ComparisonOperator': 'GT',
            }
        }, consistent_read=True)
        self.assertEqual(results['Count'], 1)

        # Now a scan.
        results = self.dynamodb.scan(self.table_name)
        self.assertEqual(results['Count'], 2)
        s_items = sorted([res['username']['S'] for res in results['Items']])
        self.assertEqual(s_items, ['jane', 'johndoe'])

        self.dynamodb.delete_item(self.table_name, key={
            'username': {'S': 'johndoe'},
            'date_joined': {'N': '1366056668'},
        })

        results = self.dynamodb.scan(self.table_name)
        self.assertEqual(results['Count'], 1)

        # Parallel scan (minus client-side threading).
        self.dynamodb.batch_write_item({
            self.table_name: [
                {
                    'PutRequest': {
                        'Item': {
                            'username': {'S': 'johndoe'},
                            'first_name': {'S': 'Johann'},
                            'last_name': {'S': 'Does'},
                            'date_joined': {'N': '1366058000'},
                            'friend_count': {'N': '1'},
                            'friends': {'SS': ['jane']},
                        },
                    },
                    'PutRequest': {
                        'Item': {
                            'username': {'S': 'alice'},
                            'first_name': {'S': 'Alice'},
                            'last_name': {'S': 'Expert'},
                            'date_joined': {'N': '1366056800'},
                            'friend_count': {'N': '2'},
                            'friends': {'SS': ['johndoe', 'jane']},
                        },
                    },
                },
            ]
        })
        time.sleep(20)
        results = self.dynamodb.scan(self.table_name, segment=0, total_segments=2)
        self.assertTrue(results['Count'] in [1, 2])
        results = self.dynamodb.scan(self.table_name, segment=1, total_segments=2)
        self.assertTrue(results['Count'] in [1, 2])

    def test_without_range_key(self):
        result = self.create_table(
            self.table_name,
            [
                {
                    'AttributeName': self.hash_key_name,
                    'AttributeType': self.hash_key_type,
                },
            ],
            [
                {
                    'AttributeName': self.hash_key_name,
                    'KeyType': 'HASH',
                },
            ],
            self.provisioned_throughput
        )
        self.assertEqual(
            result['TableDescription']['TableName'],
            self.table_name
        )

        description = self.dynamodb.describe_table(self.table_name)
        self.assertEqual(description['Table']['ItemCount'], 0)

        # Create some records.
        record_1_data = {
            'username': {'S': 'johndoe'},
            'first_name': {'S': 'John'},
            'last_name': {'S': 'Doe'},
            'date_joined': {'N': '1366056668'},
            'friend_count': {'N': '3'},
            'friends': {'SS': ['alice', 'bob', 'jane']},
        }
        r1_result = self.dynamodb.put_item(self.table_name, record_1_data)

        # Now try a range-less get.
        johndoe = self.dynamodb.get_item(self.table_name, key={
            'username': {'S': 'johndoe'},
        }, consistent_read=True)
        self.assertEqual(johndoe['Item']['username']['S'], 'johndoe')
        self.assertEqual(johndoe['Item']['first_name']['S'], 'John')
        self.assertEqual(johndoe['Item']['friends']['SS'], [
            'alice', 'bob', 'jane'
        ])

    def test_throughput_exceeded_regression(self):
        tiny_tablename = 'TinyThroughput'
        tiny = self.create_table(
            tiny_tablename,
            self.attributes,
            self.schema,
            {
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1,
            }
        )

        self.dynamodb.put_item(tiny_tablename, {
            'username': {'S': 'johndoe'},
            'first_name': {'S': 'John'},
            'last_name': {'S': 'Doe'},
            'date_joined': {'N': '1366056668'},
        })
        self.dynamodb.put_item(tiny_tablename, {
            'username': {'S': 'jane'},
            'first_name': {'S': 'Jane'},
            'last_name': {'S': 'Doe'},
            'date_joined': {'N': '1366056669'},
        })
        self.dynamodb.put_item(tiny_tablename, {
            'username': {'S': 'alice'},
            'first_name': {'S': 'Alice'},
            'last_name': {'S': 'Expert'},
            'date_joined': {'N': '1366057000'},
        })
        time.sleep(20)

        for i in range(100):
            # This would cause an exception due to a non-existant instance variable.
            self.dynamodb.scan(tiny_tablename)

    def test_recursive(self):
        result = self.create_table(
            self.table_name,
            self.attributes,
            self.schema,
            self.provisioned_throughput,
            self.lsi
        )
        self.assertEqual(
            result['TableDescription']['TableName'],
            self.table_name
        )

        description = self.dynamodb.describe_table(self.table_name)
        self.assertEqual(description['Table']['ItemCount'], 0)

        # Create some records with one being a recursive shape.
        record_1_data = {
            'username': {'S': 'johndoe'},
            'first_name': {'S': 'John'},
            'last_name': {'S': 'Doe'},
            'date_joined': {'N': '1366056668'},
            'friend_count': {'N': '3'},
            'friend_data': {'M': {'username': {'S': 'alice'},
                                  'friend_count': {'N': '4'}}}
        }
        r1_result = self.dynamodb.put_item(self.table_name, record_1_data)

        # Get the data.
        record_1 = self.dynamodb.get_item(self.table_name, key={
            'username': {'S': 'johndoe'},
            'date_joined': {'N': '1366056668'},
        }, consistent_read=True)
        self.assertEqual(record_1['Item']['username']['S'], 'johndoe')
        self.assertEqual(record_1['Item']['first_name']['S'], 'John')
        recursive_data = record_1['Item']['friend_data']['M']
        self.assertEqual(recursive_data['username']['S'], 'alice')
        self.assertEqual(recursive_data['friend_count']['N'], '4')
