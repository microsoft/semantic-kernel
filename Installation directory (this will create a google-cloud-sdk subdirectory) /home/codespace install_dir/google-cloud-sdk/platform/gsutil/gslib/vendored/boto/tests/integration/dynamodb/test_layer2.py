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
Tests for Layer2 of Amazon DynamoDB
"""
import time
import uuid
from decimal import Decimal

from tests.unit import unittest
from boto.dynamodb.exceptions import DynamoDBKeyNotFoundError
from boto.dynamodb.exceptions import DynamoDBConditionalCheckFailedError
from boto.dynamodb.layer2 import Layer2
from boto.dynamodb.types import get_dynamodb_type, Binary
from boto.dynamodb.condition import BEGINS_WITH, CONTAINS, GT
from boto.compat import six, long_type


class DynamoDBLayer2Test(unittest.TestCase):
    dynamodb = True

    def setUp(self):
        self.dynamodb = Layer2()
        self.hash_key_name = 'forum_name'
        self.hash_key_proto_value = ''
        self.range_key_name = 'subject'
        self.range_key_proto_value = ''
        self.table_name = 'sample_data_%s' % int(time.time())

    def create_sample_table(self):
        schema = self.dynamodb.create_schema(
            self.hash_key_name, self.hash_key_proto_value,
            self.range_key_name,
            self.range_key_proto_value)
        table = self.create_table(self.table_name, schema, 5, 5)
        table.refresh(wait_for_active=True)
        return table

    def create_table(self, table_name, schema, read_units, write_units):
        result = self.dynamodb.create_table(table_name, schema, read_units, write_units)
        self.addCleanup(self.dynamodb.delete_table, result)
        return result

    def test_layer2_basic(self):
        print('--- running Amazon DynamoDB Layer2 tests ---')
        c = self.dynamodb

        # First create a schema for the table
        schema = c.create_schema(self.hash_key_name, self.hash_key_proto_value,
                                 self.range_key_name,
                                 self.range_key_proto_value)

        # Create another schema without a range key
        schema2 = c.create_schema('post_id', '')

        # Now create a table
        index = int(time.time())
        table_name = 'test-%d' % index
        read_units = 5
        write_units = 5
        table = self.create_table(table_name, schema, read_units, write_units)
        assert table.name == table_name
        assert table.schema.hash_key_name == self.hash_key_name
        assert table.schema.hash_key_type == get_dynamodb_type(self.hash_key_proto_value)
        assert table.schema.range_key_name == self.range_key_name
        assert table.schema.range_key_type == get_dynamodb_type(self.range_key_proto_value)
        assert table.read_units == read_units
        assert table.write_units == write_units
        assert table.item_count == 0
        assert table.size_bytes == 0

        # Create the second table
        table2_name = 'test-%d' % (index + 1)
        table2 = self.create_table(table2_name, schema2, read_units, write_units)

        # Wait for table to become active
        table.refresh(wait_for_active=True)
        table2.refresh(wait_for_active=True)

        # List tables and make sure new one is there
        table_names = c.list_tables()
        assert table_name in table_names
        assert table2_name in table_names

        # Update the tables ProvisionedThroughput
        new_read_units = 10
        new_write_units = 5
        table.update_throughput(new_read_units, new_write_units)

        # Wait for table to be updated
        table.refresh(wait_for_active=True)
        assert table.read_units == new_read_units
        assert table.write_units == new_write_units

        # Put an item
        item1_key = 'Amazon DynamoDB'
        item1_range = 'DynamoDB Thread 1'
        item1_attrs = {
            'Message': 'DynamoDB thread 1 message text',
            'LastPostedBy': 'User A',
            'Views': 0,
            'Replies': 0,
            'Answered': 0,
            'Public': True,
            'Tags': set(['index', 'primarykey', 'table']),
            'LastPostDateTime': '12/9/2011 11:36:03 PM'}

        # Test a few corner cases with new_item

        # Try supplying a hash_key as an arg and as an item in attrs
        item1_attrs[self.hash_key_name] = 'foo'
        foobar_item = table.new_item(item1_key, item1_range, item1_attrs)
        assert foobar_item.hash_key == item1_key

        # Try supplying a range_key as an arg and as an item in attrs
        item1_attrs[self.range_key_name] = 'bar'
        foobar_item = table.new_item(item1_key, item1_range, item1_attrs)
        assert foobar_item.range_key == item1_range

        # Try supplying hash and range key in attrs dict
        foobar_item = table.new_item(attrs=item1_attrs)
        assert foobar_item.hash_key == 'foo'
        assert foobar_item.range_key == 'bar'

        del item1_attrs[self.hash_key_name]
        del item1_attrs[self.range_key_name]

        item1 = table.new_item(item1_key, item1_range, item1_attrs)
        # make sure the put() succeeds
        try:
            item1.put()
        except c.layer1.ResponseError as e:
            raise Exception("Item put failed: %s" % e)

        # Try to get an item that does not exist.
        self.assertRaises(DynamoDBKeyNotFoundError,
                          table.get_item, 'bogus_key', item1_range)

        # Now do a consistent read and check results
        item1_copy = table.get_item(item1_key, item1_range,
                                    consistent_read=True)
        assert item1_copy.hash_key == item1.hash_key
        assert item1_copy.range_key == item1.range_key
        for attr_name in item1_attrs:
            val = item1_copy[attr_name]
            if isinstance(val, (int, long_type, float, six.string_types)):
                assert val == item1[attr_name]

        # Try retrieving only select attributes
        attributes = ['Message', 'Views']
        item1_small = table.get_item(item1_key, item1_range,
                                     attributes_to_get=attributes,
                                     consistent_read=True)
        for attr_name in item1_small:
            # The item will include the attributes we asked for as
            # well as the hashkey and rangekey, so filter those out.
            if attr_name not in (item1_small.hash_key_name,
                                 item1_small.range_key_name):
                assert attr_name in attributes

        self.assertTrue(table.has_item(item1_key, range_key=item1_range,
                                       consistent_read=True))

        # Try to delete the item with the wrong Expected value
        expected = {'Views': 1}
        self.assertRaises(DynamoDBConditionalCheckFailedError,
                          item1.delete, expected_value=expected)

        # Try to delete a value while expecting a non-existant attribute
        expected = {'FooBar': True}
        try:
            item1.delete(expected_value=expected)
        except c.layer1.ResponseError:
            pass

        # Now update the existing object
        item1.add_attribute('Replies', 2)

        removed_attr = 'Public'
        item1.delete_attribute(removed_attr)

        removed_tag = item1_attrs['Tags'].copy().pop()
        item1.delete_attribute('Tags', set([removed_tag]))

        replies_by_set = set(['Adam', 'Arnie'])
        item1.put_attribute('RepliesBy', replies_by_set)
        retvals = item1.save(return_values='ALL_OLD')
        # Need more tests here for variations on return_values
        assert 'Attributes' in retvals

        # Check for correct updates
        item1_updated = table.get_item(item1_key, item1_range,
                                       consistent_read=True)
        assert item1_updated['Replies'] == item1_attrs['Replies'] + 2
        self.assertFalse(removed_attr in item1_updated)
        self.assertTrue(removed_tag not in item1_updated['Tags'])
        self.assertTrue('RepliesBy' in item1_updated)
        self.assertTrue(item1_updated['RepliesBy'] == replies_by_set)

        # Put a few more items into the table
        item2_key = 'Amazon DynamoDB'
        item2_range = 'DynamoDB Thread 2'
        item2_attrs = {
            'Message': 'DynamoDB thread 2 message text',
            'LastPostedBy': 'User A',
            'Views': 0,
            'Replies': 0,
            'Answered': 0,
            'Tags': set(["index", "primarykey", "table"]),
            'LastPost2DateTime': '12/9/2011 11:36:03 PM'}
        item2 = table.new_item(item2_key, item2_range, item2_attrs)
        item2.put()

        item3_key = 'Amazon S3'
        item3_range = 'S3 Thread 1'
        item3_attrs = {
            'Message': 'S3 Thread 1 message text',
            'LastPostedBy': 'User A',
            'Views': 0,
            'Replies': 0,
            'Answered': 0,
            'Tags': set(['largeobject', 'multipart upload']),
            'LastPostDateTime': '12/9/2011 11:36:03 PM'
        }
        item3 = table.new_item(item3_key, item3_range, item3_attrs)
        item3.put()

        # Put an item into the second table
        table2_item1_key = uuid.uuid4().hex
        table2_item1_attrs = {
            'DateTimePosted': '25/1/2011 12:34:56 PM',
            'Text': 'I think boto rocks and so does DynamoDB'
        }
        table2_item1 = table2.new_item(table2_item1_key,
                                       attrs=table2_item1_attrs)
        table2_item1.put()

        # Try a few queries
        items = table.query('Amazon DynamoDB', range_key_condition=BEGINS_WITH('DynamoDB'))
        n = 0
        for item in items:
            n += 1
        assert n == 2
        assert items.consumed_units > 0

        items = table.query('Amazon DynamoDB', range_key_condition=BEGINS_WITH('DynamoDB'),
                            request_limit=1, max_results=1)
        n = 0
        for item in items:
            n += 1
        assert n == 1
        assert items.consumed_units > 0

        # Try a few scans
        items = table.scan()
        n = 0
        for item in items:
            n += 1
        assert n == 3
        assert items.consumed_units > 0

        items = table.scan(scan_filter={'Replies': GT(0)})
        n = 0
        for item in items:
            n += 1
        assert n == 1
        assert items.consumed_units > 0

        # Test some integer and float attributes
        integer_value = 42
        float_value = 345.678
        item3['IntAttr'] = integer_value
        item3['FloatAttr'] = float_value

        # Test booleans
        item3['TrueBoolean'] = True
        item3['FalseBoolean'] = False

        # Test some set values
        integer_set = set([1, 2, 3, 4, 5])
        float_set = set([1.1, 2.2, 3.3, 4.4, 5.5])
        mixed_set = set([1, 2, 3.3, 4, 5.555])
        str_set = set(['foo', 'bar', 'fie', 'baz'])
        item3['IntSetAttr'] = integer_set
        item3['FloatSetAttr'] = float_set
        item3['MixedSetAttr'] = mixed_set
        item3['StrSetAttr'] = str_set
        item3.put()

        # Now do a consistent read
        item4 = table.get_item(item3_key, item3_range, consistent_read=True)
        assert item4['IntAttr'] == integer_value
        assert item4['FloatAttr'] == float_value
        assert bool(item4['TrueBoolean']) is True
        assert bool(item4['FalseBoolean']) is False
        # The values will not necessarily be in the same order as when
        # we wrote them to the DB.
        for i in item4['IntSetAttr']:
            assert i in integer_set
        for i in item4['FloatSetAttr']:
            assert i in float_set
        for i in item4['MixedSetAttr']:
            assert i in mixed_set
        for i in item4['StrSetAttr']:
            assert i in str_set

        # Try a batch get
        batch_list = c.new_batch_list()
        batch_list.add_batch(table, [(item2_key, item2_range),
                                     (item3_key, item3_range)])
        response = batch_list.submit()
        assert len(response['Responses'][table.name]['Items']) == 2

        # Try an empty batch get
        batch_list = c.new_batch_list()
        batch_list.add_batch(table, [])
        response = batch_list.submit()
        assert response == {}

        # Try a few batch write operations
        item4_key = 'Amazon S3'
        item4_range = 'S3 Thread 2'
        item4_attrs = {
            'Message': 'S3 Thread 2 message text',
            'LastPostedBy': 'User A',
            'Views': 0,
            'Replies': 0,
            'Answered': 0,
            'Tags': set(['largeobject', 'multipart upload']),
            'LastPostDateTime': '12/9/2011 11:36:03 PM'
        }
        item5_key = 'Amazon S3'
        item5_range = 'S3 Thread 3'
        item5_attrs = {
            'Message': 'S3 Thread 3 message text',
            'LastPostedBy': 'User A',
            'Views': 0,
            'Replies': 0,
            'Answered': 0,
            'Tags': set(['largeobject', 'multipart upload']),
            'LastPostDateTime': '12/9/2011 11:36:03 PM'
        }
        item4 = table.new_item(item4_key, item4_range, item4_attrs)
        item5 = table.new_item(item5_key, item5_range, item5_attrs)
        batch_list = c.new_batch_write_list()
        batch_list.add_batch(table, puts=[item4, item5])
        response = batch_list.submit()
        # should really check for unprocessed items

        # Do some generator gymnastics
        results = table.scan(scan_filter={'Tags': CONTAINS('table')})
        assert results.scanned_count == 5
        results = table.scan(request_limit=2, max_results=5)
        assert results.count == 2
        for item in results:
            if results.count == 2:
                assert results.remaining == 4
                results.remaining -= 2
                results.next_response()
            else:
                assert results.count == 4
                assert results.remaining in (0, 1)
        assert results.count == 4
        results = table.scan(request_limit=6, max_results=4)
        assert len(list(results)) == 4
        assert results.count == 4

        batch_list = c.new_batch_write_list()
        batch_list.add_batch(table, deletes=[(item4_key, item4_range),
                                             (item5_key, item5_range)])
        response = batch_list.submit()

        # Try queries
        results = table.query('Amazon DynamoDB', range_key_condition=BEGINS_WITH('DynamoDB'))
        n = 0
        for item in results:
            n += 1
        assert n == 2

        # Try to delete the item with the right Expected value
        expected = {'Views': 0}
        item1.delete(expected_value=expected)

        self.assertFalse(table.has_item(item1_key, range_key=item1_range,
                                        consistent_read=True))
        # Now delete the remaining items
        ret_vals = item2.delete(return_values='ALL_OLD')
        # some additional checks here would be useful
        assert ret_vals['Attributes'][self.hash_key_name] == item2_key
        assert ret_vals['Attributes'][self.range_key_name] == item2_range

        item3.delete()
        table2_item1.delete()
        print('--- tests completed ---')

    def test_binary_attrs(self):
        c = self.dynamodb
        schema = c.create_schema(self.hash_key_name, self.hash_key_proto_value,
                                 self.range_key_name,
                                 self.range_key_proto_value)
        index = int(time.time())
        table_name = 'test-%d' % index
        read_units = 5
        write_units = 5
        table = self.create_table(table_name, schema, read_units, write_units)
        table.refresh(wait_for_active=True)
        item1_key = 'Amazon S3'
        item1_range = 'S3 Thread 1'
        item1_attrs = {
            'Message': 'S3 Thread 1 message text',
            'LastPostedBy': 'User A',
            'Views': 0,
            'Replies': 0,
            'Answered': 0,
            'BinaryData': Binary(b'\x01\x02\x03\x04'),
            'BinarySequence': set([Binary(b'\x01\x02'), Binary(b'\x03\x04')]),
            'Tags': set(['largeobject', 'multipart upload']),
            'LastPostDateTime': '12/9/2011 11:36:03 PM'
        }
        item1 = table.new_item(item1_key, item1_range, item1_attrs)
        item1.put()

        retrieved = table.get_item(item1_key, item1_range, consistent_read=True)
        self.assertEqual(retrieved['Message'], 'S3 Thread 1 message text')
        self.assertEqual(retrieved['Views'], 0)
        self.assertEqual(retrieved['Tags'],
                         set(['largeobject', 'multipart upload']))
        self.assertEqual(retrieved['BinaryData'], Binary(b'\x01\x02\x03\x04'))
        # Also comparable directly to bytes:
        self.assertEqual(retrieved['BinaryData'], b'\x01\x02\x03\x04')
        self.assertEqual(retrieved['BinarySequence'],
                         set([Binary(b'\x01\x02'), Binary(b'\x03\x04')]))

    def test_put_decimal_attrs(self):
        self.dynamodb.use_decimals()
        table = self.create_sample_table()
        item = table.new_item('foo', 'bar')
        item['decimalvalue'] = Decimal('1.12345678912345')
        item.put()
        retrieved = table.get_item('foo', 'bar')
        self.assertEqual(retrieved['decimalvalue'], Decimal('1.12345678912345'))

    @unittest.skipIf(six.PY3, "skipping lossy_float_conversion test for Python 3.x")
    def test_lossy_float_conversion(self):
        table = self.create_sample_table()
        item = table.new_item('foo', 'bar')
        item['floatvalue'] = 1.12345678912345
        item.put()
        retrieved = table.get_item('foo', 'bar')['floatvalue']
        # Notice how this is not equal to the original value.
        self.assertNotEqual(1.12345678912345, retrieved)
        # Instead, it's truncated:
        self.assertEqual(1.12345678912, retrieved)

    def test_large_integers(self):
        # It's not just floating point numbers, large integers
        # can trigger rouding issues.
        self.dynamodb.use_decimals()
        table = self.create_sample_table()
        item = table.new_item('foo', 'bar')
        item['decimalvalue'] = Decimal('129271300103398600')
        item.put()
        retrieved = table.get_item('foo', 'bar')
        self.assertEqual(retrieved['decimalvalue'], Decimal('129271300103398600'))
        # Also comparable directly to an int.
        self.assertEqual(retrieved['decimalvalue'], 129271300103398600)

    def test_put_single_letter_attr(self):
        # When an attr is added that is a single letter, if it overlaps with
        # the built-in "types", the decoding used to fall down. Assert that
        # it's now working correctly.
        table = self.create_sample_table()
        item = table.new_item('foo', 'foo1')
        item.put_attribute('b', 4)
        stored = item.save(return_values='UPDATED_NEW')
        self.assertEqual(stored['Attributes'], {'b': 4})
