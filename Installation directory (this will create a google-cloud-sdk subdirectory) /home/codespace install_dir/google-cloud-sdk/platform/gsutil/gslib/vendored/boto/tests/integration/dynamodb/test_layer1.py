# Copyright (c) 2012 Mitch Garnaat http://garnaat.org/
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
Tests for Layer1 of DynamoDB
"""
import time
import base64

from tests.unit import unittest
from boto.dynamodb.exceptions import DynamoDBKeyNotFoundError
from boto.dynamodb.exceptions import DynamoDBConditionalCheckFailedError
from boto.dynamodb.exceptions import DynamoDBValidationError
from boto.dynamodb.layer1 import Layer1


class DynamoDBLayer1Test(unittest.TestCase):
    dynamodb = True

    def setUp(self):
        self.dynamodb = Layer1()
        self.table_name = 'test-%d' % int(time.time())
        self.hash_key_name = 'forum_name'
        self.hash_key_type = 'S'
        self.range_key_name = 'subject'
        self.range_key_type = 'S'
        self.read_units = 5
        self.write_units = 5
        self.schema = {'HashKeyElement': {'AttributeName': self.hash_key_name,
                                          'AttributeType': self.hash_key_type},
                       'RangeKeyElement': {'AttributeName': self.range_key_name,
                                           'AttributeType': self.range_key_type}}
        self.provisioned_throughput = {'ReadCapacityUnits': self.read_units,
                                       'WriteCapacityUnits': self.write_units}

    def tearDown(self):
        pass

    def create_table(self, table_name, schema, provisioned_throughput):
        result = self.dynamodb.create_table(table_name, schema, provisioned_throughput)
        self.addCleanup(self.dynamodb.delete_table, table_name)
        return result

    def test_layer1_basic(self):
        print('--- running DynamoDB Layer1 tests ---')

        c = self.dynamodb

        # First create a table
        table_name = self.table_name
        hash_key_name = self.hash_key_name
        hash_key_type = self.hash_key_type
        range_key_name = self.range_key_name
        range_key_type = self.range_key_type
        read_units = self.read_units
        write_units = self.write_units
        schema = self.schema
        provisioned_throughput = self.provisioned_throughput

        result = self.create_table(table_name, schema, provisioned_throughput)
        assert result['TableDescription']['TableName'] == table_name
        result_schema = result['TableDescription']['KeySchema']
        assert result_schema['HashKeyElement']['AttributeName'] == hash_key_name
        assert result_schema['HashKeyElement']['AttributeType'] == hash_key_type
        assert result_schema['RangeKeyElement']['AttributeName'] == range_key_name
        assert result_schema['RangeKeyElement']['AttributeType'] == range_key_type
        result_thruput = result['TableDescription']['ProvisionedThroughput']
        assert result_thruput['ReadCapacityUnits'] == read_units
        assert result_thruput['WriteCapacityUnits'] == write_units

        # Wait for table to become active
        result = c.describe_table(table_name)
        while result['Table']['TableStatus'] != 'ACTIVE':
            time.sleep(5)
            result = c.describe_table(table_name)

        # List tables and make sure new one is there
        result = c.list_tables()
        assert table_name in result['TableNames']

        # Update the tables ProvisionedThroughput
        new_read_units = 10
        new_write_units = 5
        new_provisioned_throughput = {'ReadCapacityUnits': new_read_units,
                                      'WriteCapacityUnits': new_write_units}
        result = c.update_table(table_name, new_provisioned_throughput)

        # Wait for table to be updated
        result = c.describe_table(table_name)
        while result['Table']['TableStatus'] == 'UPDATING':
            time.sleep(5)
            result = c.describe_table(table_name)

        result_thruput = result['Table']['ProvisionedThroughput']
        assert result_thruput['ReadCapacityUnits'] == new_read_units
        assert result_thruput['WriteCapacityUnits'] == new_write_units

        # Put an item
        item1_key = 'Amazon DynamoDB'
        item1_range = 'DynamoDB Thread 1'
        item1_data = {
            hash_key_name: {hash_key_type: item1_key},
            range_key_name: {range_key_type: item1_range},
            'Message': {'S': 'DynamoDB thread 1 message text'},
            'LastPostedBy': {'S': 'User A'},
            'Views': {'N': '0'},
            'Replies': {'N': '0'},
            'Answered': {'N': '0'},
            'Tags': {'SS': ["index", "primarykey", "table"]},
            'LastPostDateTime': {'S': '12/9/2011 11:36:03 PM'}
        }
        result = c.put_item(table_name, item1_data)

        # Now do a consistent read and check results
        key1 = {'HashKeyElement': {hash_key_type: item1_key},
                'RangeKeyElement': {range_key_type: item1_range}}
        result = c.get_item(table_name, key=key1, consistent_read=True)
        for name in item1_data:
            assert name in result['Item']

        # Try to get an item that does not exist.
        invalid_key = {'HashKeyElement': {hash_key_type: 'bogus_key'},
                       'RangeKeyElement': {range_key_type: item1_range}}
        self.assertRaises(DynamoDBKeyNotFoundError,
                          c.get_item, table_name, key=invalid_key)

        # Try retrieving only select attributes
        attributes = ['Message', 'Views']
        result = c.get_item(table_name, key=key1, consistent_read=True,
                            attributes_to_get=attributes)
        for name in result['Item']:
            assert name in attributes

        # Try to delete the item with the wrong Expected value
        expected = {'Views': {'Value': {'N': '1'}}}
        self.assertRaises(DynamoDBConditionalCheckFailedError,
                          c.delete_item, table_name, key=key1,
                          expected=expected)

        # Now update the existing object
        attribute_updates = {'Views': {'Value': {'N': '5'},
                                       'Action': 'PUT'},
                             'Tags': {'Value': {'SS': ['foobar']},
                                      'Action': 'ADD'}}
        result = c.update_item(table_name, key=key1,
                               attribute_updates=attribute_updates)

        # Try and update an item, in a fashion which makes it too large.
        # The new message text is the item size limit minus 32 bytes and
        # the current object is larger than 32 bytes.
        item_size_overflow_text = 'Text to be padded'.zfill(64 * 1024 - 32)
        attribute_updates = {'Message': {'Value': {'S': item_size_overflow_text},
                                         'Action': 'PUT'}}
        self.assertRaises(DynamoDBValidationError,
                          c.update_item, table_name, key=key1,
                          attribute_updates=attribute_updates)


        # Put a few more items into the table
        item2_key = 'Amazon DynamoDB'
        item2_range = 'DynamoDB Thread 2'
        item2_data = {
            hash_key_name: {hash_key_type: item2_key},
            range_key_name: {range_key_type: item2_range},
            'Message': {'S': 'DynamoDB thread 2 message text'},
            'LastPostedBy': {'S': 'User A'},
            'Views': {'N': '0'},
            'Replies': {'N': '0'},
            'Answered': {'N': '0'},
            'Tags': {'SS': ["index", "primarykey", "table"]},
            'LastPostDateTime': {'S': '12/9/2011 11:36:03 PM'}
        }
        result = c.put_item(table_name, item2_data)
        key2 = {'HashKeyElement': {hash_key_type: item2_key},
                'RangeKeyElement': {range_key_type: item2_range}}

        item3_key = 'Amazon S3'
        item3_range = 'S3 Thread 1'
        item3_data = {
            hash_key_name: {hash_key_type: item3_key},
            range_key_name: {range_key_type: item3_range},
            'Message': {'S': 'S3 Thread 1 message text'},
            'LastPostedBy': {'S': 'User A'},
            'Views': {'N': '0'},
            'Replies': {'N': '0'},
            'Answered': {'N': '0'},
            'Tags': {'SS': ['largeobject', 'multipart upload']},
            'LastPostDateTime': {'S': '12/9/2011 11:36:03 PM'}
        }
        result = c.put_item(table_name, item3_data)
        key3 = {'HashKeyElement': {hash_key_type: item3_key},
                'RangeKeyElement': {range_key_type: item3_range}}

        # Try a few queries
        result = c.query(table_name, {'S': 'Amazon DynamoDB'},
                         {'AttributeValueList': [{'S': 'DynamoDB'}],
                          'ComparisonOperator': 'BEGINS_WITH'})
        assert 'Count' in result
        assert result['Count'] == 2

        # Try a few scans
        result = c.scan(table_name,
                        {'Tags': {'AttributeValueList': [{'S': 'table'}],
                                  'ComparisonOperator': 'CONTAINS'}})
        assert 'Count' in result
        assert result['Count'] == 2

        # Now delete the items
        result = c.delete_item(table_name, key=key1)
        result = c.delete_item(table_name, key=key2)
        result = c.delete_item(table_name, key=key3)

        print('--- tests completed ---')

    def test_binary_attributes(self):
        c = self.dynamodb
        result = self.create_table(self.table_name, self.schema,
                                   self.provisioned_throughput)
        # Wait for table to become active
        result = c.describe_table(self.table_name)
        while result['Table']['TableStatus'] != 'ACTIVE':
            time.sleep(5)
            result = c.describe_table(self.table_name)

        # Put an item
        item1_key = 'Amazon DynamoDB'
        item1_range = 'DynamoDB Thread 1'
        item1_data = {
            self.hash_key_name: {self.hash_key_type: item1_key},
            self.range_key_name: {self.range_key_type: item1_range},
            'Message': {'S': 'DynamoDB thread 1 message text'},
            'LastPostedBy': {'S': 'User A'},
            'Views': {'N': '0'},
            'Replies': {'N': '0'},
            'BinaryData': {'B': base64.b64encode(b'\x01\x02\x03\x04').decode('utf-8')},
            'Answered': {'N': '0'},
            'Tags': {'SS': ["index", "primarykey", "table"]},
            'LastPostDateTime': {'S': '12/9/2011 11:36:03 PM'}
        }
        result = c.put_item(self.table_name, item1_data)

        # Now do a consistent read and check results
        key1 = {'HashKeyElement': {self.hash_key_type: item1_key},
                'RangeKeyElement': {self.range_key_type: item1_range}}
        result = c.get_item(self.table_name, key=key1, consistent_read=True)
        self.assertEqual(result['Item']['BinaryData'],
                         {'B': base64.b64encode(b'\x01\x02\x03\x04').decode('utf-8')})
