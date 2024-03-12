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
from mock import Mock

from boto.dynamodb.layer2 import Layer2
from boto.dynamodb.table import Table, Schema


DESCRIBE_TABLE = {
    "Table": {
        "CreationDateTime": 1.353526122785E9, "ItemCount": 1,
        "KeySchema": {
            "HashKeyElement": {"AttributeName": "foo", "AttributeType": "N"}},
        "ProvisionedThroughput": {
            "NumberOfDecreasesToday": 0,
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5},
        "TableName": "footest",
        "TableSizeBytes": 21,
        "TableStatus": "ACTIVE"}
}


class TestTableConstruction(unittest.TestCase):
    def setUp(self):
        self.layer2 = Layer2('access_key', 'secret_key')
        self.api = Mock()
        self.layer2.layer1 = self.api

    def test_get_table(self):
        self.api.describe_table.return_value = DESCRIBE_TABLE
        table = self.layer2.get_table('footest')
        self.assertEqual(table.name, 'footest')
        self.assertEqual(table.create_time, 1353526122.785)
        self.assertEqual(table.status, 'ACTIVE')
        self.assertEqual(table.item_count, 1)
        self.assertEqual(table.size_bytes, 21)
        self.assertEqual(table.read_units, 5)
        self.assertEqual(table.write_units, 5)
        self.assertEqual(table.schema, Schema.create(hash_key=('foo', 'N')))

    def test_create_table_without_api_call(self):
        table = self.layer2.table_from_schema(
            name='footest',
            schema=Schema.create(hash_key=('foo', 'N')))
        self.assertEqual(table.name, 'footest')
        self.assertEqual(table.schema, Schema.create(hash_key=('foo', 'N')))
        # describe_table is never called.
        self.assertEqual(self.api.describe_table.call_count, 0)

    def test_create_schema_with_hash_and_range(self):
        schema = self.layer2.create_schema('foo', int, 'bar', str)
        self.assertEqual(schema.hash_key_name, 'foo')
        self.assertEqual(schema.hash_key_type, 'N')
        self.assertEqual(schema.range_key_name, 'bar')
        self.assertEqual(schema.range_key_type, 'S')

    def test_create_schema_with_hash(self):
        schema = self.layer2.create_schema('foo', str)
        self.assertEqual(schema.hash_key_name, 'foo')
        self.assertEqual(schema.hash_key_type, 'S')
        self.assertIsNone(schema.range_key_name)
        self.assertIsNone(schema.range_key_type)


class TestSchemaEquality(unittest.TestCase):
    def test_schema_equal(self):
        s1 = Schema.create(hash_key=('foo', 'N'))
        s2 = Schema.create(hash_key=('foo', 'N'))
        self.assertEqual(s1, s2)

    def test_schema_not_equal(self):
        s1 = Schema.create(hash_key=('foo', 'N'))
        s2 = Schema.create(hash_key=('bar', 'N'))
        s3 = Schema.create(hash_key=('foo', 'S'))
        self.assertNotEqual(s1, s2)
        self.assertNotEqual(s1, s3)

    def test_equal_with_hash_and_range(self):
        s1 = Schema.create(hash_key=('foo', 'N'), range_key=('bar', 'S'))
        s2 = Schema.create(hash_key=('foo', 'N'), range_key=('bar', 'S'))
        self.assertEqual(s1, s2)

    def test_schema_with_hash_and_range_not_equal(self):
        s1 = Schema.create(hash_key=('foo', 'N'), range_key=('bar', 'S'))
        s2 = Schema.create(hash_key=('foo', 'N'), range_key=('bar', 'N'))
        s3 = Schema.create(hash_key=('foo', 'S'), range_key=('baz', 'N'))
        s4 = Schema.create(hash_key=('bar', 'N'), range_key=('baz', 'N'))
        self.assertNotEqual(s1, s2)
        self.assertNotEqual(s1, s3)
        self.assertNotEqual(s1, s4)
        self.assertNotEqual(s2, s4)
        self.assertNotEqual(s3, s4)


if __name__ == '__main__':
    unittest.main()
