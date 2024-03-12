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
import time
from tests.unit import unittest

from boto.dynamodb.layer2 import Layer2
from boto.dynamodb.table import Table
from boto.dynamodb.schema import Schema


class TestDynamoDBTable(unittest.TestCase):
    dynamodb = True

    def setUp(self):
        self.dynamodb = Layer2()
        self.schema = Schema.create(('foo', 'N'), ('bar', 'S'))
        self.table_name = 'testtable%s' % int(time.time())

    def create_table(self, table_name, schema, read_units, write_units):
        result = self.dynamodb.create_table(table_name, schema, read_units, write_units)
        self.addCleanup(self.dynamodb.delete_table, result)
        return result

    def assertAllEqual(self, *items):
        first = items[0]
        for item in items[1:]:
            self.assertEqual(first, item)

    def test_table_retrieval_parity(self):
        created_table = self.dynamodb.create_table(
            self.table_name, self.schema, 1, 1)
        created_table.refresh(wait_for_active=True)

        retrieved_table = self.dynamodb.get_table(self.table_name)

        constructed_table = self.dynamodb.table_from_schema(self.table_name,
                                                            self.schema)

        # All three tables should have the same name
        # and schema attributes.
        self.assertAllEqual(created_table.name,
                            retrieved_table.name,
                            constructed_table.name)

        self.assertAllEqual(created_table.schema,
                            retrieved_table.schema,
                            constructed_table.schema)

        # However for create_time, status, read/write units,
        # only the created/retrieved table will have equal
        # values.
        self.assertEqual(created_table.create_time,
                         retrieved_table.create_time)
        self.assertEqual(created_table.status,
                         retrieved_table.status)
        self.assertEqual(created_table.read_units,
                         retrieved_table.read_units)
        self.assertEqual(created_table.write_units,
                         retrieved_table.write_units)

        # The constructed table will have values of None.
        self.assertIsNone(constructed_table.create_time)
        self.assertIsNone(constructed_table.status)
        self.assertIsNone(constructed_table.read_units)
        self.assertIsNone(constructed_table.write_units)
