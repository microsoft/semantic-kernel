from tests.compat import mock, unittest
from boto.dynamodb2 import exceptions
from boto.dynamodb2.fields import (HashKey, RangeKey,
                                   AllIndex, KeysOnlyIndex, IncludeIndex,
                                   GlobalAllIndex, GlobalKeysOnlyIndex,
                                   GlobalIncludeIndex)
from boto.dynamodb2.items import Item
from boto.dynamodb2.layer1 import DynamoDBConnection
from boto.dynamodb2.results import ResultSet, BatchGetResultSet
from boto.dynamodb2.table import Table
from boto.dynamodb2.types import (STRING, NUMBER, BINARY,
                                  FILTER_OPERATORS, QUERY_OPERATORS)
from boto.exception import JSONResponseError
from boto.compat import six, long_type


FakeDynamoDBConnection = mock.create_autospec(DynamoDBConnection)


class SchemaFieldsTestCase(unittest.TestCase):
    def test_hash_key(self):
        hash_key = HashKey('hello')
        self.assertEqual(hash_key.name, 'hello')
        self.assertEqual(hash_key.data_type, STRING)
        self.assertEqual(hash_key.attr_type, 'HASH')

        self.assertEqual(hash_key.definition(), {
            'AttributeName': 'hello',
            'AttributeType': 'S'
        })
        self.assertEqual(hash_key.schema(), {
            'AttributeName': 'hello',
            'KeyType': 'HASH'
        })

    def test_range_key(self):
        range_key = RangeKey('hello')
        self.assertEqual(range_key.name, 'hello')
        self.assertEqual(range_key.data_type, STRING)
        self.assertEqual(range_key.attr_type, 'RANGE')

        self.assertEqual(range_key.definition(), {
            'AttributeName': 'hello',
            'AttributeType': 'S'
        })
        self.assertEqual(range_key.schema(), {
            'AttributeName': 'hello',
            'KeyType': 'RANGE'
        })

    def test_alternate_type(self):
        alt_key = HashKey('alt', data_type=NUMBER)
        self.assertEqual(alt_key.name, 'alt')
        self.assertEqual(alt_key.data_type, NUMBER)
        self.assertEqual(alt_key.attr_type, 'HASH')

        self.assertEqual(alt_key.definition(), {
            'AttributeName': 'alt',
            'AttributeType': 'N'
        })
        self.assertEqual(alt_key.schema(), {
            'AttributeName': 'alt',
            'KeyType': 'HASH'
        })


class IndexFieldTestCase(unittest.TestCase):
    def test_all_index(self):
        all_index = AllIndex('AllKeys', parts=[
            HashKey('username'),
            RangeKey('date_joined')
        ])
        self.assertEqual(all_index.name, 'AllKeys')
        self.assertEqual([part.attr_type for part in all_index.parts], [
            'HASH',
            'RANGE'
        ])
        self.assertEqual(all_index.projection_type, 'ALL')

        self.assertEqual(all_index.definition(), [
            {'AttributeName': 'username', 'AttributeType': 'S'},
            {'AttributeName': 'date_joined', 'AttributeType': 'S'}
        ])
        self.assertEqual(all_index.schema(), {
            'IndexName': 'AllKeys',
            'KeySchema': [
                {
                    'AttributeName': 'username',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'date_joined',
                    'KeyType': 'RANGE'
                }
            ],
            'Projection': {
                'ProjectionType': 'ALL'
            }
        })

    def test_keys_only_index(self):
        keys_only = KeysOnlyIndex('KeysOnly', parts=[
            HashKey('username'),
            RangeKey('date_joined')
        ])
        self.assertEqual(keys_only.name, 'KeysOnly')
        self.assertEqual([part.attr_type for part in keys_only.parts], [
            'HASH',
            'RANGE'
        ])
        self.assertEqual(keys_only.projection_type, 'KEYS_ONLY')

        self.assertEqual(keys_only.definition(), [
            {'AttributeName': 'username', 'AttributeType': 'S'},
            {'AttributeName': 'date_joined', 'AttributeType': 'S'}
        ])
        self.assertEqual(keys_only.schema(), {
            'IndexName': 'KeysOnly',
            'KeySchema': [
                {
                    'AttributeName': 'username',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'date_joined',
                    'KeyType': 'RANGE'
                }
            ],
            'Projection': {
                'ProjectionType': 'KEYS_ONLY'
            }
        })

    def test_include_index(self):
        include_index = IncludeIndex('IncludeKeys', parts=[
            HashKey('username'),
            RangeKey('date_joined')
        ], includes=[
            'gender',
            'friend_count'
        ])
        self.assertEqual(include_index.name, 'IncludeKeys')
        self.assertEqual([part.attr_type for part in include_index.parts], [
            'HASH',
            'RANGE'
        ])
        self.assertEqual(include_index.projection_type, 'INCLUDE')

        self.assertEqual(include_index.definition(), [
            {'AttributeName': 'username', 'AttributeType': 'S'},
            {'AttributeName': 'date_joined', 'AttributeType': 'S'}
        ])
        self.assertEqual(include_index.schema(), {
            'IndexName': 'IncludeKeys',
            'KeySchema': [
                {
                    'AttributeName': 'username',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'date_joined',
                    'KeyType': 'RANGE'
                }
            ],
            'Projection': {
                'ProjectionType': 'INCLUDE',
                'NonKeyAttributes': [
                    'gender',
                    'friend_count',
                ]
            }
        })

    def test_global_all_index(self):
        all_index = GlobalAllIndex('AllKeys', parts=[
            HashKey('username'),
            RangeKey('date_joined')
        ],
        throughput={
            'read': 6,
            'write': 2,
        })
        self.assertEqual(all_index.name, 'AllKeys')
        self.assertEqual([part.attr_type for part in all_index.parts], [
            'HASH',
            'RANGE'
        ])
        self.assertEqual(all_index.projection_type, 'ALL')

        self.assertEqual(all_index.definition(), [
            {'AttributeName': 'username', 'AttributeType': 'S'},
            {'AttributeName': 'date_joined', 'AttributeType': 'S'}
        ])
        self.assertEqual(all_index.schema(), {
            'IndexName': 'AllKeys',
            'KeySchema': [
                {
                    'AttributeName': 'username',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'date_joined',
                    'KeyType': 'RANGE'
                }
            ],
            'Projection': {
                'ProjectionType': 'ALL'
            },
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 6,
                'WriteCapacityUnits': 2
            }
        })

    def test_global_keys_only_index(self):
        keys_only = GlobalKeysOnlyIndex('KeysOnly', parts=[
            HashKey('username'),
            RangeKey('date_joined')
        ],
        throughput={
            'read': 3,
            'write': 4,
        })
        self.assertEqual(keys_only.name, 'KeysOnly')
        self.assertEqual([part.attr_type for part in keys_only.parts], [
            'HASH',
            'RANGE'
        ])
        self.assertEqual(keys_only.projection_type, 'KEYS_ONLY')

        self.assertEqual(keys_only.definition(), [
            {'AttributeName': 'username', 'AttributeType': 'S'},
            {'AttributeName': 'date_joined', 'AttributeType': 'S'}
        ])
        self.assertEqual(keys_only.schema(), {
            'IndexName': 'KeysOnly',
            'KeySchema': [
                {
                    'AttributeName': 'username',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'date_joined',
                    'KeyType': 'RANGE'
                }
            ],
            'Projection': {
                'ProjectionType': 'KEYS_ONLY'
            },
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 3,
                'WriteCapacityUnits': 4
            }
        })

    def test_global_include_index(self):
        # Lean on the default throughput
        include_index = GlobalIncludeIndex('IncludeKeys', parts=[
            HashKey('username'),
            RangeKey('date_joined')
        ], includes=[
            'gender',
            'friend_count'
        ])
        self.assertEqual(include_index.name, 'IncludeKeys')
        self.assertEqual([part.attr_type for part in include_index.parts], [
            'HASH',
            'RANGE'
        ])
        self.assertEqual(include_index.projection_type, 'INCLUDE')

        self.assertEqual(include_index.definition(), [
            {'AttributeName': 'username', 'AttributeType': 'S'},
            {'AttributeName': 'date_joined', 'AttributeType': 'S'}
        ])
        self.assertEqual(include_index.schema(), {
            'IndexName': 'IncludeKeys',
            'KeySchema': [
                {
                    'AttributeName': 'username',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'date_joined',
                    'KeyType': 'RANGE'
                }
            ],
            'Projection': {
                'ProjectionType': 'INCLUDE',
                'NonKeyAttributes': [
                    'gender',
                    'friend_count',
                ]
            },
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        })

    def test_global_include_index_throughput(self):
        include_index = GlobalIncludeIndex('IncludeKeys', parts=[
            HashKey('username'),
            RangeKey('date_joined')
        ], includes=[
            'gender',
            'friend_count'
        ], throughput={
            'read': 10,
            'write': 8
        })

        self.assertEqual(include_index.schema(), {
            'IndexName': 'IncludeKeys',
            'KeySchema': [
                {
                    'AttributeName': 'username',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'date_joined',
                    'KeyType': 'RANGE'
                }
            ],
            'Projection': {
                'ProjectionType': 'INCLUDE',
                'NonKeyAttributes': [
                    'gender',
                    'friend_count',
                ]
            },
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 8
            }
        })


class ItemTestCase(unittest.TestCase):
    if six.PY2:
        assertCountEqual = unittest.TestCase.assertItemsEqual

    def setUp(self):
        super(ItemTestCase, self).setUp()
        self.table = Table('whatever', connection=FakeDynamoDBConnection())
        self.johndoe = self.create_item({
            'username': 'johndoe',
            'first_name': 'John',
            'date_joined': 12345,
        })

    def create_item(self, data):
        return Item(self.table, data=data)

    def test_initialization(self):
        empty_item = Item(self.table)
        self.assertEqual(empty_item.table, self.table)
        self.assertEqual(empty_item._data, {})

        full_item = Item(self.table, data={
            'username': 'johndoe',
            'date_joined': 12345,
        })
        self.assertEqual(full_item.table, self.table)
        self.assertEqual(full_item._data, {
            'username': 'johndoe',
            'date_joined': 12345,
        })

    # The next couple methods make use of ``sorted(...)`` so we get consistent
    # ordering everywhere & no erroneous failures.

    def test_keys(self):
        self.assertCountEqual(self.johndoe.keys(), [
            'date_joined',
            'first_name',
            'username',
        ])

    def test_values(self):
        self.assertCountEqual(self.johndoe.values(),
                              [12345, 'John', 'johndoe'])

    def test_contains(self):
        self.assertIn('username', self.johndoe)
        self.assertIn('first_name', self.johndoe)
        self.assertIn('date_joined', self.johndoe)
        self.assertNotIn('whatever', self.johndoe)

    def test_iter(self):
        self.assertCountEqual(self.johndoe,
                              ['johndoe', 'John', 12345])

    def test_get(self):
        self.assertEqual(self.johndoe.get('username'), 'johndoe')
        self.assertEqual(self.johndoe.get('first_name'), 'John')
        self.assertEqual(self.johndoe.get('date_joined'), 12345)

        # Test a missing key. No default yields ``None``.
        self.assertEqual(self.johndoe.get('last_name'), None)
        # This time with a default.
        self.assertEqual(self.johndoe.get('last_name', True), True)

    def test_items(self):
        self.assertCountEqual(
            self.johndoe.items(),
            [
                ('date_joined', 12345),
                ('first_name', 'John'),
                ('username', 'johndoe'),
            ])

    def test_attribute_access(self):
        self.assertEqual(self.johndoe['username'], 'johndoe')
        self.assertEqual(self.johndoe['first_name'], 'John')
        self.assertEqual(self.johndoe['date_joined'], 12345)

        # Test a missing key.
        self.assertEqual(self.johndoe['last_name'], None)

        # Set a key.
        self.johndoe['last_name'] = 'Doe'
        # Test accessing the new key.
        self.assertEqual(self.johndoe['last_name'], 'Doe')

        # Delete a key.
        del self.johndoe['last_name']
        # Test the now-missing-again key.
        self.assertEqual(self.johndoe['last_name'], None)

    def test_needs_save(self):
        self.johndoe.mark_clean()
        self.assertFalse(self.johndoe.needs_save())
        self.johndoe['last_name'] = 'Doe'
        self.assertTrue(self.johndoe.needs_save())

    def test_needs_save_set_changed(self):
        # First, ensure we're clean.
        self.johndoe.mark_clean()
        self.assertFalse(self.johndoe.needs_save())
        # Add a friends collection.
        self.johndoe['friends'] = set(['jane', 'alice'])
        self.assertTrue(self.johndoe.needs_save())
        # Now mark it clean, then change the collection.
        # This does NOT call ``__setitem__``, so the item used to be
        # incorrectly appearing to be clean, when it had in fact been changed.
        self.johndoe.mark_clean()
        self.assertFalse(self.johndoe.needs_save())
        self.johndoe['friends'].add('bob')
        self.assertTrue(self.johndoe.needs_save())

    def test_mark_clean(self):
        self.johndoe['last_name'] = 'Doe'
        self.assertTrue(self.johndoe.needs_save())
        self.johndoe.mark_clean()
        self.assertFalse(self.johndoe.needs_save())

    def test_load(self):
        empty_item = Item(self.table)
        empty_item.load({
            'Item': {
                'username': {'S': 'johndoe'},
                'first_name': {'S': 'John'},
                'last_name': {'S': 'Doe'},
                'date_joined': {'N': '1366056668'},
                'friend_count': {'N': '3'},
                'friends': {'SS': ['alice', 'bob', 'jane']},
            }
        })
        self.assertEqual(empty_item['username'], 'johndoe')
        self.assertEqual(empty_item['date_joined'], 1366056668)
        self.assertEqual(sorted(empty_item['friends']), sorted([
            'alice',
            'bob',
            'jane'
        ]))

    def test_get_keys(self):
        # Setup the data.
        self.table.schema = [
            HashKey('username'),
            RangeKey('date_joined'),
        ]
        self.assertEqual(self.johndoe.get_keys(), {
            'username': 'johndoe',
            'date_joined': 12345,
        })

    def test_get_raw_keys(self):
        # Setup the data.
        self.table.schema = [
            HashKey('username'),
            RangeKey('date_joined'),
        ]
        self.assertEqual(self.johndoe.get_raw_keys(), {
            'username': {'S': 'johndoe'},
            'date_joined': {'N': '12345'},
        })

    def test_build_expects(self):
        # Pristine.
        self.assertEqual(self.johndoe.build_expects(), {
            'first_name': {
                'Exists': False,
            },
            'username': {
                'Exists': False,
            },
            'date_joined': {
                'Exists': False,
            },
        })

        # Without modifications.
        self.johndoe.mark_clean()
        self.assertEqual(self.johndoe.build_expects(), {
            'first_name': {
                'Exists': True,
                'Value': {
                    'S': 'John',
                },
            },
            'username': {
                'Exists': True,
                'Value': {
                    'S': 'johndoe',
                },
            },
            'date_joined': {
                'Exists': True,
                'Value': {
                    'N': '12345',
                },
            },
        })

        # Change some data.
        self.johndoe['first_name'] = 'Johann'
        # Add some data.
        self.johndoe['last_name'] = 'Doe'
        # Delete some data.
        del self.johndoe['date_joined']

        # All fields (default).
        self.assertEqual(self.johndoe.build_expects(), {
            'first_name': {
                'Exists': True,
                'Value': {
                    'S': 'John',
                },
            },
            'last_name': {
                'Exists': False,
            },
            'username': {
                'Exists': True,
                'Value': {
                    'S': 'johndoe',
                },
            },
            'date_joined': {
                'Exists': True,
                'Value': {
                    'N': '12345',
                },
            },
        })

        # Only a subset of the fields.
        self.assertEqual(self.johndoe.build_expects(fields=[
            'first_name',
            'last_name',
            'date_joined',
        ]), {
            'first_name': {
                'Exists': True,
                'Value': {
                    'S': 'John',
                },
            },
            'last_name': {
                'Exists': False,
            },
            'date_joined': {
                'Exists': True,
                'Value': {
                    'N': '12345',
                },
            },
        })

    def test_prepare_full(self):
        self.assertEqual(self.johndoe.prepare_full(), {
            'username': {'S': 'johndoe'},
            'first_name': {'S': 'John'},
            'date_joined': {'N': '12345'}
        })

        self.johndoe['friends'] = set(['jane', 'alice'])
        data = self.johndoe.prepare_full()
        self.assertEqual(data['username'], {'S': 'johndoe'})
        self.assertEqual(data['first_name'], {'S': 'John'})
        self.assertEqual(data['date_joined'], {'N': '12345'})
        self.assertCountEqual(data['friends']['SS'],
                              ['jane', 'alice'])

    def test_prepare_full_empty_set(self):
        self.johndoe['friends'] = set()
        self.assertEqual(self.johndoe.prepare_full(), {
            'username': {'S': 'johndoe'},
            'first_name': {'S': 'John'},
            'date_joined': {'N': '12345'}
        })

    def test_prepare_partial(self):
        self.johndoe.mark_clean()
        # Change some data.
        self.johndoe['first_name'] = 'Johann'
        # Add some data.
        self.johndoe['last_name'] = 'Doe'
        # Delete some data.
        del self.johndoe['date_joined']

        final_data, fields = self.johndoe.prepare_partial()
        self.assertEqual(final_data, {
            'date_joined': {
                'Action': 'DELETE',
            },
            'first_name': {
                'Action': 'PUT',
                'Value': {'S': 'Johann'},
            },
            'last_name': {
                'Action': 'PUT',
                'Value': {'S': 'Doe'},
            },
        })
        self.assertEqual(fields, set([
            'first_name',
            'last_name',
            'date_joined'
        ]))

    def test_prepare_partial_empty_set(self):
        self.johndoe.mark_clean()
        # Change some data.
        self.johndoe['first_name'] = 'Johann'
        # Add some data.
        self.johndoe['last_name'] = 'Doe'
        # Delete some data.
        del self.johndoe['date_joined']
        # Put an empty set on the ``Item``.
        self.johndoe['friends'] = set()

        final_data, fields = self.johndoe.prepare_partial()
        self.assertEqual(final_data, {
            'date_joined': {
                'Action': 'DELETE',
            },
            'first_name': {
                'Action': 'PUT',
                'Value': {'S': 'Johann'},
            },
            'last_name': {
                'Action': 'PUT',
                'Value': {'S': 'Doe'},
            },
        })
        self.assertEqual(fields, set([
            'first_name',
            'last_name',
            'date_joined'
        ]))

    def test_save_no_changes(self):
        # Unchanged, no save.
        with mock.patch.object(self.table, '_put_item', return_value=True) \
                as mock_put_item:
            # Pretend we loaded it via ``get_item``...
            self.johndoe.mark_clean()
            self.assertFalse(self.johndoe.save())

        self.assertFalse(mock_put_item.called)

    def test_save_with_changes(self):
        # With changed data.
        with mock.patch.object(self.table, '_put_item', return_value=True) \
                as mock_put_item:
            self.johndoe.mark_clean()
            self.johndoe['first_name'] = 'J'
            self.johndoe['new_attr'] = 'never_seen_before'
            self.assertTrue(self.johndoe.save())
            self.assertFalse(self.johndoe.needs_save())

        self.assertTrue(mock_put_item.called)
        mock_put_item.assert_called_once_with({
            'username': {'S': 'johndoe'},
            'first_name': {'S': 'J'},
            'new_attr': {'S': 'never_seen_before'},
            'date_joined': {'N': '12345'}
        }, expects={
            'username': {
                'Value': {
                    'S': 'johndoe',
                },
                'Exists': True,
            },
            'first_name': {
                'Value': {
                    'S': 'John',
                },
                'Exists': True,
            },
            'new_attr': {
                'Exists': False,
            },
            'date_joined': {
                'Value': {
                    'N': '12345',
                },
                'Exists': True,
            },
        })

    def test_save_with_changes_overwrite(self):
        # With changed data.
        with mock.patch.object(self.table, '_put_item', return_value=True) \
                as mock_put_item:
            self.johndoe['first_name'] = 'J'
            self.johndoe['new_attr'] = 'never_seen_before'
            # OVERWRITE ALL THE THINGS
            self.assertTrue(self.johndoe.save(overwrite=True))
            self.assertFalse(self.johndoe.needs_save())

        self.assertTrue(mock_put_item.called)
        mock_put_item.assert_called_once_with({
            'username': {'S': 'johndoe'},
            'first_name': {'S': 'J'},
            'new_attr': {'S': 'never_seen_before'},
            'date_joined': {'N': '12345'}
        }, expects=None)

    def test_partial_no_changes(self):
        # Unchanged, no save.
        with mock.patch.object(self.table, '_update_item', return_value=True) \
                as mock_update_item:
            # Pretend we loaded it via ``get_item``...
            self.johndoe.mark_clean()
            self.assertFalse(self.johndoe.partial_save())

        self.assertFalse(mock_update_item.called)

    def test_partial_with_changes(self):
        # Setup the data.
        self.table.schema = [
            HashKey('username'),
        ]

        # With changed data.
        with mock.patch.object(self.table, '_update_item', return_value=True) \
                as mock_update_item:
            # Pretend we loaded it via ``get_item``...
            self.johndoe.mark_clean()
            # Now... MODIFY!!!
            self.johndoe['first_name'] = 'J'
            self.johndoe['last_name'] = 'Doe'
            del self.johndoe['date_joined']
            self.assertTrue(self.johndoe.partial_save())
            self.assertFalse(self.johndoe.needs_save())

        self.assertTrue(mock_update_item.called)
        mock_update_item.assert_called_once_with({
            'username': 'johndoe',
        }, {
            'first_name': {
                'Action': 'PUT',
                'Value': {'S': 'J'},
            },
            'last_name': {
                'Action': 'PUT',
                'Value': {'S': 'Doe'},
            },
            'date_joined': {
                'Action': 'DELETE',
            }
        }, expects={
            'first_name': {
                'Value': {
                    'S': 'John',
                },
                'Exists': True
            },
            'last_name': {
                'Exists': False
            },
            'date_joined': {
                'Value': {
                    'N': '12345',
                },
                'Exists': True
            },
        })

    def test_delete(self):
        # Setup the data.
        self.table.schema = [
            HashKey('username'),
            RangeKey('date_joined'),
        ]

        with mock.patch.object(self.table, 'delete_item', return_value=True) \
                as mock_delete_item:
            self.johndoe.delete()

        self.assertTrue(mock_delete_item.called)
        mock_delete_item.assert_called_once_with(
            username='johndoe',
            date_joined=12345
        )

    def test_nonzero(self):
        self.assertTrue(self.johndoe)
        self.assertFalse(self.create_item({}))


class ItemFromItemTestCase(ItemTestCase):
    def setUp(self):
        super(ItemFromItemTestCase, self).setUp()
        self.johndoe = self.create_item(self.johndoe)


def fake_results(name, greeting='hello', exclusive_start_key=None, limit=None):
    if exclusive_start_key is None:
        exclusive_start_key = -1

    if limit == 0:
        raise Exception("Web Service Returns '400 Bad Request'")

    end_cap = 13
    results = []
    start_key = exclusive_start_key + 1

    for i in range(start_key, start_key + 5):
        if i < end_cap:
            results.append("%s %s #%s" % (greeting, name, i))

    # Don't return more than limit results
    if limit < len(results):
        results = results[:limit]

    retval = {
        'results': results,
    }

    if exclusive_start_key + 5 < end_cap:
        retval['last_key'] = exclusive_start_key + 5

    return retval


class ResultSetTestCase(unittest.TestCase):
    def setUp(self):
        super(ResultSetTestCase, self).setUp()
        self.results = ResultSet()
        self.result_function = mock.MagicMock(side_effect=fake_results)
        self.results.to_call(self.result_function, 'john', greeting='Hello', limit=20)

    def test_first_key(self):
        self.assertEqual(self.results.first_key, 'exclusive_start_key')

    def test_max_page_size_fetch_more(self):
        self.results = ResultSet(max_page_size=10)
        self.results.to_call(self.result_function, 'john', greeting='Hello')
        self.results.fetch_more()
        self.result_function.assert_called_with('john', greeting='Hello', limit=10)
        self.result_function.reset_mock()

    def test_max_page_size_and_smaller_limit_fetch_more(self):
        self.results = ResultSet(max_page_size=10)
        self.results.to_call(self.result_function, 'john', greeting='Hello', limit=5)
        self.results.fetch_more()
        self.result_function.assert_called_with('john', greeting='Hello', limit=5)
        self.result_function.reset_mock()

    def test_max_page_size_and_bigger_limit_fetch_more(self):
        self.results = ResultSet(max_page_size=10)
        self.results.to_call(self.result_function, 'john', greeting='Hello', limit=15)
        self.results.fetch_more()
        self.result_function.assert_called_with('john', greeting='Hello', limit=10)
        self.result_function.reset_mock()

    def test_fetch_more(self):
        # First "page".
        self.results.fetch_more()
        self.assertEqual(self.results._results, [
            'Hello john #0',
            'Hello john #1',
            'Hello john #2',
            'Hello john #3',
            'Hello john #4',
        ])

        self.result_function.assert_called_with('john', greeting='Hello', limit=20)
        self.result_function.reset_mock()

        # Fake in a last key.
        self.results._last_key_seen = 4
        # Second "page".
        self.results.fetch_more()
        self.assertEqual(self.results._results, [
            'Hello john #5',
            'Hello john #6',
            'Hello john #7',
            'Hello john #8',
            'Hello john #9',
        ])

        self.result_function.assert_called_with('john', greeting='Hello', limit=20, exclusive_start_key=4)
        self.result_function.reset_mock()

        # Fake in a last key.
        self.results._last_key_seen = 9
        # Last "page".
        self.results.fetch_more()
        self.assertEqual(self.results._results, [
            'Hello john #10',
            'Hello john #11',
            'Hello john #12',
        ])

        # Fake in a key outside the range.
        self.results._last_key_seen = 15
        # Empty "page". Nothing new gets added
        self.results.fetch_more()
        self.assertEqual(self.results._results, [])

        # Make sure we won't check for results in the future.
        self.assertFalse(self.results._results_left)

    def test_iteration(self):
        # First page.
        self.assertEqual(next(self.results), 'Hello john #0')
        self.assertEqual(next(self.results), 'Hello john #1')
        self.assertEqual(next(self.results), 'Hello john #2')
        self.assertEqual(next(self.results), 'Hello john #3')
        self.assertEqual(next(self.results), 'Hello john #4')
        self.assertEqual(self.results._limit, 15)
        # Second page.
        self.assertEqual(next(self.results), 'Hello john #5')
        self.assertEqual(next(self.results), 'Hello john #6')
        self.assertEqual(next(self.results), 'Hello john #7')
        self.assertEqual(next(self.results), 'Hello john #8')
        self.assertEqual(next(self.results), 'Hello john #9')
        self.assertEqual(self.results._limit, 10)
        # Third page.
        self.assertEqual(next(self.results), 'Hello john #10')
        self.assertEqual(next(self.results), 'Hello john #11')
        self.assertEqual(next(self.results), 'Hello john #12')
        self.assertRaises(StopIteration, self.results.next)
        self.assertEqual(self.results._limit, 7)

    def test_limit_smaller_than_first_page(self):
        results = ResultSet()
        results.to_call(fake_results, 'john', greeting='Hello', limit=2)
        self.assertEqual(next(results), 'Hello john #0')
        self.assertEqual(next(results), 'Hello john #1')
        self.assertRaises(StopIteration, results.next)

    def test_limit_equals_page(self):
        results = ResultSet()
        results.to_call(fake_results, 'john', greeting='Hello', limit=5)
        # First page
        self.assertEqual(next(results), 'Hello john #0')
        self.assertEqual(next(results), 'Hello john #1')
        self.assertEqual(next(results), 'Hello john #2')
        self.assertEqual(next(results), 'Hello john #3')
        self.assertEqual(next(results), 'Hello john #4')
        self.assertRaises(StopIteration, results.next)

    def test_limit_greater_than_page(self):
        results = ResultSet()
        results.to_call(fake_results, 'john', greeting='Hello', limit=6)
        # First page
        self.assertEqual(next(results), 'Hello john #0')
        self.assertEqual(next(results), 'Hello john #1')
        self.assertEqual(next(results), 'Hello john #2')
        self.assertEqual(next(results), 'Hello john #3')
        self.assertEqual(next(results), 'Hello john #4')
        # Second page
        self.assertEqual(next(results), 'Hello john #5')
        self.assertRaises(StopIteration, results.next)

    def test_iteration_noresults(self):
        def none(limit=10):
            return {
                'results': [],
            }

        results = ResultSet()
        results.to_call(none, limit=20)
        self.assertRaises(StopIteration, results.next)

    def test_iteration_sporadic_pages(self):
        # Some pages have no/incomplete results but have a ``LastEvaluatedKey``
        # (for instance, scans with filters), so we need to accommodate that.
        def sporadic():
            # A dict, because Python closures have read-only access to the
            # reference itself.
            count = {'value': -1}

            def _wrapper(limit=10, exclusive_start_key=None):
                count['value'] = count['value'] + 1

                if count['value'] == 0:
                    # Full page.
                    return {
                        'results': [
                            'Result #0',
                            'Result #1',
                            'Result #2',
                            'Result #3',
                        ],
                        'last_key': 'page-1'
                    }
                elif count['value'] == 1:
                    # Empty page but continue.
                    return {
                        'results': [],
                        'last_key': 'page-2'
                    }
                elif count['value'] == 2:
                    # Final page.
                    return {
                        'results': [
                            'Result #4',
                            'Result #5',
                            'Result #6',
                        ],
                    }

            return _wrapper

        results = ResultSet()
        results.to_call(sporadic(), limit=20)
        # First page
        self.assertEqual(next(results), 'Result #0')
        self.assertEqual(next(results), 'Result #1')
        self.assertEqual(next(results), 'Result #2')
        self.assertEqual(next(results), 'Result #3')
        # Second page (misses!)
        # Moves on to the third page
        self.assertEqual(next(results), 'Result #4')
        self.assertEqual(next(results), 'Result #5')
        self.assertEqual(next(results), 'Result #6')
        self.assertRaises(StopIteration, results.next)

    def test_list(self):
        self.assertEqual(list(self.results), [
            'Hello john #0',
            'Hello john #1',
            'Hello john #2',
            'Hello john #3',
            'Hello john #4',
            'Hello john #5',
            'Hello john #6',
            'Hello john #7',
            'Hello john #8',
            'Hello john #9',
            'Hello john #10',
            'Hello john #11',
            'Hello john #12'
        ])


def fake_batch_results(keys):
    results = []
    simulate_unprocessed = True

    if len(keys) and keys[0] == 'johndoe':
        simulate_unprocessed = False

    for key in keys:
        if simulate_unprocessed and key == 'johndoe':
            continue

        results.append("hello %s" % key)

    retval = {
        'results': results,
        'last_key': None,
    }

    if simulate_unprocessed:
        retval['unprocessed_keys'] = ['johndoe']

    return retval


class BatchGetResultSetTestCase(unittest.TestCase):
    def setUp(self):
        super(BatchGetResultSetTestCase, self).setUp()
        self.results = BatchGetResultSet(keys=[
            'alice',
            'bob',
            'jane',
            'johndoe',
        ])
        self.results.to_call(fake_batch_results)

    def test_fetch_more(self):
        # First "page".
        self.results.fetch_more()
        self.assertEqual(self.results._results, [
            'hello alice',
            'hello bob',
            'hello jane',
        ])
        self.assertEqual(self.results._keys_left, ['johndoe'])

        # Second "page".
        self.results.fetch_more()
        self.assertEqual(self.results._results, [
            'hello johndoe',
        ])

        # Empty "page". Nothing new gets added
        self.results.fetch_more()
        self.assertEqual(self.results._results, [])

        # Make sure we won't check for results in the future.
        self.assertFalse(self.results._results_left)

    def test_fetch_more_empty(self):
        self.results.to_call(lambda keys: {'results': [], 'last_key': None})

        self.results.fetch_more()
        self.assertEqual(self.results._results, [])
        self.assertRaises(StopIteration, self.results.next)

    def test_iteration(self):
        # First page.
        self.assertEqual(next(self.results), 'hello alice')
        self.assertEqual(next(self.results), 'hello bob')
        self.assertEqual(next(self.results), 'hello jane')
        self.assertEqual(next(self.results), 'hello johndoe')
        self.assertRaises(StopIteration, self.results.next)


class TableTestCase(unittest.TestCase):
    def setUp(self):
        super(TableTestCase, self).setUp()
        self.users = Table('users', connection=FakeDynamoDBConnection())
        self.default_connection = DynamoDBConnection(
            aws_access_key_id='access_key',
            aws_secret_access_key='secret_key'
        )

    def test__introspect_schema(self):
        raw_schema_1 = [
            {
                "AttributeName": "username",
                "KeyType": "HASH"
            },
            {
                "AttributeName": "date_joined",
                "KeyType": "RANGE"
            }
        ]
        raw_attributes_1 = [
            {
                'AttributeName': 'username',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'date_joined',
                'AttributeType': 'S'
            },
        ]
        schema_1 = self.users._introspect_schema(raw_schema_1, raw_attributes_1)
        self.assertEqual(len(schema_1), 2)
        self.assertTrue(isinstance(schema_1[0], HashKey))
        self.assertEqual(schema_1[0].name, 'username')
        self.assertTrue(isinstance(schema_1[1], RangeKey))
        self.assertEqual(schema_1[1].name, 'date_joined')

        raw_schema_2 = [
            {
                "AttributeName": "username",
                "KeyType": "BTREE"
            },
        ]
        raw_attributes_2 = [
            {
                'AttributeName': 'username',
                'AttributeType': 'S'
            },
        ]
        self.assertRaises(
            exceptions.UnknownSchemaFieldError,
            self.users._introspect_schema,
            raw_schema_2,
            raw_attributes_2
        )

        # Test a complex schema & ensure the types come back correctly.
        raw_schema_3 = [
            {
                "AttributeName": "user_id",
                "KeyType": "HASH"
            },
            {
                "AttributeName": "junk",
                "KeyType": "RANGE"
            }
        ]
        raw_attributes_3 = [
            {
                'AttributeName': 'user_id',
                'AttributeType': 'N'
            },
            {
                'AttributeName': 'junk',
                'AttributeType': 'B'
            },
        ]
        schema_3 = self.users._introspect_schema(raw_schema_3, raw_attributes_3)
        self.assertEqual(len(schema_3), 2)
        self.assertTrue(isinstance(schema_3[0], HashKey))
        self.assertEqual(schema_3[0].name, 'user_id')
        self.assertEqual(schema_3[0].data_type, NUMBER)
        self.assertTrue(isinstance(schema_3[1], RangeKey))
        self.assertEqual(schema_3[1].name, 'junk')
        self.assertEqual(schema_3[1].data_type, BINARY)

    def test__introspect_indexes(self):
        raw_indexes_1 = [
            {
                "IndexName": "MostRecentlyJoinedIndex",
                "KeySchema": [
                    {
                        "AttributeName": "username",
                        "KeyType": "HASH"
                    },
                    {
                        "AttributeName": "date_joined",
                        "KeyType": "RANGE"
                    }
                ],
                "Projection": {
                    "ProjectionType": "KEYS_ONLY"
                }
            },
            {
                "IndexName": "EverybodyIndex",
                "KeySchema": [
                    {
                        "AttributeName": "username",
                        "KeyType": "HASH"
                    },
                ],
                "Projection": {
                    "ProjectionType": "ALL"
                }
            },
            {
                "IndexName": "GenderIndex",
                "KeySchema": [
                    {
                        "AttributeName": "username",
                        "KeyType": "HASH"
                    },
                    {
                        "AttributeName": "date_joined",
                        "KeyType": "RANGE"
                    }
                ],
                "Projection": {
                    "ProjectionType": "INCLUDE",
                    "NonKeyAttributes": [
                        'gender',
                    ]
                }
            }
        ]
        indexes_1 = self.users._introspect_indexes(raw_indexes_1)
        self.assertEqual(len(indexes_1), 3)
        self.assertTrue(isinstance(indexes_1[0], KeysOnlyIndex))
        self.assertEqual(indexes_1[0].name, 'MostRecentlyJoinedIndex')
        self.assertEqual(len(indexes_1[0].parts), 2)
        self.assertTrue(isinstance(indexes_1[1], AllIndex))
        self.assertEqual(indexes_1[1].name, 'EverybodyIndex')
        self.assertEqual(len(indexes_1[1].parts), 1)
        self.assertTrue(isinstance(indexes_1[2], IncludeIndex))
        self.assertEqual(indexes_1[2].name, 'GenderIndex')
        self.assertEqual(len(indexes_1[2].parts), 2)
        self.assertEqual(indexes_1[2].includes_fields, ['gender'])

        raw_indexes_2 = [
            {
                "IndexName": "MostRecentlyJoinedIndex",
                "KeySchema": [
                    {
                        "AttributeName": "username",
                        "KeyType": "HASH"
                    },
                    {
                        "AttributeName": "date_joined",
                        "KeyType": "RANGE"
                    }
                ],
                "Projection": {
                    "ProjectionType": "SOMETHING_CRAZY"
                }
            },
        ]
        self.assertRaises(
            exceptions.UnknownIndexFieldError,
            self.users._introspect_indexes,
            raw_indexes_2
        )

    def test_initialization(self):
        users = Table('users', connection=self.default_connection)
        self.assertEqual(users.table_name, 'users')
        self.assertTrue(isinstance(users.connection, DynamoDBConnection))
        self.assertEqual(users.throughput['read'], 5)
        self.assertEqual(users.throughput['write'], 5)
        self.assertEqual(users.schema, None)
        self.assertEqual(users.indexes, None)

        groups = Table('groups', connection=FakeDynamoDBConnection())
        self.assertEqual(groups.table_name, 'groups')
        self.assertTrue(hasattr(groups.connection, 'assert_called_once_with'))

    def test_create_simple(self):
        conn = FakeDynamoDBConnection()

        with mock.patch.object(conn, 'create_table', return_value={}) \
                as mock_create_table:
            retval = Table.create('users', schema=[
                HashKey('username'),
                RangeKey('date_joined', data_type=NUMBER)
            ], connection=conn)
            self.assertTrue(retval)

        self.assertTrue(mock_create_table.called)
        mock_create_table.assert_called_once_with(attribute_definitions=[
            {
                'AttributeName': 'username',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'date_joined',
                'AttributeType': 'N'
            }
        ],
        table_name='users',
        key_schema=[
            {
                'KeyType': 'HASH',
                'AttributeName': 'username'
            },
            {
                'KeyType': 'RANGE',
                'AttributeName': 'date_joined'
            }
        ],
        provisioned_throughput={
            'WriteCapacityUnits': 5,
            'ReadCapacityUnits': 5
        })

    def test_create_full(self):
        conn = FakeDynamoDBConnection()

        with mock.patch.object(conn, 'create_table', return_value={}) \
                as mock_create_table:
            retval = Table.create('users', schema=[
                HashKey('username'),
                RangeKey('date_joined', data_type=NUMBER)
            ], throughput={
                'read':20,
                'write': 10,
            }, indexes=[
                KeysOnlyIndex('FriendCountIndex', parts=[
                    RangeKey('friend_count')
                ]),
            ], global_indexes=[
                GlobalKeysOnlyIndex('FullFriendCountIndex', parts=[
                    RangeKey('friend_count')
                ], throughput={
                    'read': 10,
                    'write': 8,
                }),
            ], connection=conn)
            self.assertTrue(retval)

        self.assertTrue(mock_create_table.called)
        mock_create_table.assert_called_once_with(attribute_definitions=[
            {
                'AttributeName': 'username',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'date_joined',
                'AttributeType': 'N'
            },
            {
                'AttributeName': 'friend_count',
                'AttributeType': 'S'
            }
        ],
        key_schema=[
            {
                'KeyType': 'HASH',
                'AttributeName': 'username'
            },
            {
                'KeyType': 'RANGE',
                'AttributeName': 'date_joined'
            }
        ],
        table_name='users',
        provisioned_throughput={
            'WriteCapacityUnits': 10,
            'ReadCapacityUnits': 20
        },
        global_secondary_indexes=[
            {
                'KeySchema': [
                    {
                        'KeyType': 'RANGE',
                        'AttributeName': 'friend_count'
                    }
                ],
                'IndexName': 'FullFriendCountIndex',
                'Projection': {
                    'ProjectionType': 'KEYS_ONLY'
                },
                'ProvisionedThroughput': {
                    'WriteCapacityUnits': 8,
                    'ReadCapacityUnits': 10
                }
            }
        ],
        local_secondary_indexes=[
            {
                'KeySchema': [
                    {
                        'KeyType': 'RANGE',
                        'AttributeName': 'friend_count'
                    }
                ],
                'IndexName': 'FriendCountIndex',
                'Projection': {
                    'ProjectionType': 'KEYS_ONLY'
                }
            }
        ])

    def test_describe(self):
        expected = {
            "Table": {
                "AttributeDefinitions": [
                    {
                        "AttributeName": "username",
                        "AttributeType": "S"
                    }
                ],
                "ItemCount": 5,
                "KeySchema": [
                    {
                        "AttributeName": "username",
                        "KeyType": "HASH"
                    }
                ],
                "LocalSecondaryIndexes": [
                    {
                        "IndexName": "UsernameIndex",
                        "KeySchema": [
                            {
                                "AttributeName": "username",
                                "KeyType": "HASH"
                            }
                        ],
                        "Projection": {
                            "ProjectionType": "KEYS_ONLY"
                        }
                    }
                ],
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 20,
                    "WriteCapacityUnits": 6
                },
                "TableName": "Thread",
                "TableStatus": "ACTIVE"
            }
        }

        with mock.patch.object(
                self.users.connection,
                'describe_table',
                return_value=expected) as mock_describe:
            self.assertEqual(self.users.throughput['read'], 5)
            self.assertEqual(self.users.throughput['write'], 5)
            self.assertEqual(self.users.schema, None)
            self.assertEqual(self.users.indexes, None)

            self.users.describe()

            self.assertEqual(self.users.throughput['read'], 20)
            self.assertEqual(self.users.throughput['write'], 6)
            self.assertEqual(len(self.users.schema), 1)
            self.assertEqual(isinstance(self.users.schema[0], HashKey), 1)
            self.assertEqual(len(self.users.indexes), 1)

        mock_describe.assert_called_once_with('users')

    def test_update(self):
        with mock.patch.object(
                self.users.connection,
                'update_table',
                return_value={}) as mock_update:
            self.assertEqual(self.users.throughput['read'], 5)
            self.assertEqual(self.users.throughput['write'], 5)
            self.users.update(throughput={
                'read': 7,
                'write': 2,
            })
            self.assertEqual(self.users.throughput['read'], 7)
            self.assertEqual(self.users.throughput['write'], 2)

        mock_update.assert_called_once_with(
            'users',
            global_secondary_index_updates=None,
            provisioned_throughput={
                'WriteCapacityUnits': 2,
                'ReadCapacityUnits': 7
            }
        )

        with mock.patch.object(
                self.users.connection,
                'update_table',
                return_value={}) as mock_update:
            self.assertEqual(self.users.throughput['read'], 7)
            self.assertEqual(self.users.throughput['write'], 2)
            self.users.update(throughput={
                'read': 9,
                'write': 5,
            },
            global_indexes={
                'WhateverIndex': {
                    'read': 6,
                    'write': 1
                },
                'AnotherIndex': {
                    'read': 1,
                    'write': 2
                }
            })
            self.assertEqual(self.users.throughput['read'], 9)
            self.assertEqual(self.users.throughput['write'], 5)

        args, kwargs = mock_update.call_args
        self.assertEqual(args, ('users',))
        self.assertEqual(kwargs['provisioned_throughput'], {
            'WriteCapacityUnits': 5,
            'ReadCapacityUnits': 9,
            })
        update = kwargs['global_secondary_index_updates'][:]
        update.sort(key=lambda x: x['Update']['IndexName'])
        self.assertDictEqual(
            update[0],
            {
                'Update': {
                    'IndexName': 'AnotherIndex',
                    'ProvisionedThroughput': {
                        'WriteCapacityUnits': 2,
                        'ReadCapacityUnits': 1
                    }
                }
            })
        self.assertDictEqual(
            update[1],
            {
                'Update': {
                    'IndexName': 'WhateverIndex',
                    'ProvisionedThroughput': {
                        'WriteCapacityUnits': 1,
                        'ReadCapacityUnits': 6
                    }
                }
            })

    def test_create_global_secondary_index(self):
        with mock.patch.object(
                self.users.connection,
                'update_table',
                return_value={}) as mock_update:
            self.users.create_global_secondary_index(
                global_index=GlobalAllIndex(
                    'JustCreatedIndex',
                    parts=[
                        HashKey('requiredHashKey')
                    ],
                    throughput={
                        'read': 2,
                        'write': 2
                    }
                )
            )

        mock_update.assert_called_once_with(
            'users',
            global_secondary_index_updates=[
                {
                    'Create': {
                        'IndexName': 'JustCreatedIndex',
                        'KeySchema': [
                            {
                                'KeyType': 'HASH',
                                'AttributeName': 'requiredHashKey'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'WriteCapacityUnits': 2,
                            'ReadCapacityUnits': 2
                        }
                    }
                }
            ],
            attribute_definitions=[
                {
                    'AttributeName': 'requiredHashKey',
                    'AttributeType': 'S'
                }
            ]
        )

    def test_delete_global_secondary_index(self):
        with mock.patch.object(
                self.users.connection,
                'update_table',
                return_value={}) as mock_update:
            self.users.delete_global_secondary_index('RandomGSIIndex')

        mock_update.assert_called_once_with(
            'users',
            global_secondary_index_updates=[
                {
                    'Delete': {
                        'IndexName': 'RandomGSIIndex',
                    }
                }
            ]
        )

    def test_update_global_secondary_index(self):
        # Updating a single global secondary index
        with mock.patch.object(
                self.users.connection,
                'update_table',
                return_value={}) as mock_update:
            self.users.update_global_secondary_index(global_indexes={
                'A_IndexToBeUpdated': {
                    'read': 5,
                    'write': 5
                }
            })

        mock_update.assert_called_once_with(
            'users',
            global_secondary_index_updates=[
                {
                    'Update': {
                        'IndexName': 'A_IndexToBeUpdated',
                        "ProvisionedThroughput": {
                            "ReadCapacityUnits": 5,
                            "WriteCapacityUnits": 5
                        },
                    }
                }
            ]
        )

        # Updating multiple global secondary indexes
        with mock.patch.object(
                self.users.connection,
                'update_table',
                return_value={}) as mock_update:
            self.users.update_global_secondary_index(global_indexes={
                'A_IndexToBeUpdated': {
                    'read': 5,
                    'write': 5
                },
                'B_IndexToBeUpdated': {
                    'read': 9,
                    'write': 9
                }
            })

        args, kwargs = mock_update.call_args
        self.assertEqual(args, ('users',))
        update = kwargs['global_secondary_index_updates'][:]
        update.sort(key=lambda x: x['Update']['IndexName'])
        self.assertDictEqual(
            update[0],
            {
                'Update': {
                    'IndexName': 'A_IndexToBeUpdated',
                    'ProvisionedThroughput': {
                        'WriteCapacityUnits': 5,
                        'ReadCapacityUnits': 5
                    }
                }
            })
        self.assertDictEqual(
            update[1],
            {
                'Update': {
                    'IndexName': 'B_IndexToBeUpdated',
                    'ProvisionedThroughput': {
                        'WriteCapacityUnits': 9,
                        'ReadCapacityUnits': 9
                    }
                }
            })

    def test_delete(self):
        with mock.patch.object(
                self.users.connection,
                'delete_table',
                return_value={}) as mock_delete:
            self.assertTrue(self.users.delete())

        mock_delete.assert_called_once_with('users')

    def test_get_item(self):
        expected = {
            'Item': {
                'username': {'S': 'johndoe'},
                'first_name': {'S': 'John'},
                'last_name': {'S': 'Doe'},
                'date_joined': {'N': '1366056668'},
                'friend_count': {'N': '3'},
                'friends': {'SS': ['alice', 'bob', 'jane']},
            }
        }

        with mock.patch.object(
                self.users.connection,
                'get_item',
                return_value=expected) as mock_get_item:
            item = self.users.get_item(username='johndoe')
            self.assertEqual(item['username'], 'johndoe')
            self.assertEqual(item['first_name'], 'John')

        mock_get_item.assert_called_once_with('users', {
            'username': {'S': 'johndoe'}
        }, consistent_read=False, attributes_to_get=None)

        with mock.patch.object(
                self.users.connection,
                'get_item',
                return_value=expected) as mock_get_item:
            item = self.users.get_item(username='johndoe', attributes=[
                'username',
                'first_name',
            ])

        mock_get_item.assert_called_once_with('users', {
            'username': {'S': 'johndoe'}
        }, consistent_read=False, attributes_to_get=['username', 'first_name'])

    def test_has_item(self):
        expected = {
            'Item': {
                'username': {'S': 'johndoe'},
                'first_name': {'S': 'John'},
                'last_name': {'S': 'Doe'},
                'date_joined': {'N': '1366056668'},
                'friend_count': {'N': '3'},
                'friends': {'SS': ['alice', 'bob', 'jane']},
            }
        }

        with mock.patch.object(
                self.users.connection,
                'get_item',
                return_value=expected) as mock_get_item:
            found = self.users.has_item(username='johndoe')
            self.assertTrue(found)

        with mock.patch.object(
                self.users.connection,
                'get_item') as mock_get_item:
            mock_get_item.side_effect = JSONResponseError("Nope.", None, None)
            found = self.users.has_item(username='mrsmith')
            self.assertFalse(found)

    def test_lookup_hash(self):
        """Tests the "lookup" function with just a hash key"""
        expected = {
            'Item': {
                'username': {'S': 'johndoe'},
                'first_name': {'S': 'John'},
                'last_name': {'S': 'Doe'},
                'date_joined': {'N': '1366056668'},
                'friend_count': {'N': '3'},
                'friends': {'SS': ['alice', 'bob', 'jane']},
            }
        }

        # Set the Schema
        self.users.schema = [
            HashKey('username'),
            RangeKey('date_joined', data_type=NUMBER),
        ]

        with mock.patch.object(
                self.users,
                'get_item',
                return_value=expected) as mock_get_item:
            self.users.lookup('johndoe')

        mock_get_item.assert_called_once_with(
            username= 'johndoe')

    def test_lookup_hash_and_range(self):
        """Test the "lookup" function with a hash and range key"""
        expected = {
            'Item': {
                'username': {'S': 'johndoe'},
                'first_name': {'S': 'John'},
                'last_name': {'S': 'Doe'},
                'date_joined': {'N': '1366056668'},
                'friend_count': {'N': '3'},
                'friends': {'SS': ['alice', 'bob', 'jane']},
            }
        }

        # Set the Schema
        self.users.schema = [
            HashKey('username'),
            RangeKey('date_joined', data_type=NUMBER),
        ]

        with mock.patch.object(
                self.users,
                'get_item',
                return_value=expected) as mock_get_item:
            self.users.lookup('johndoe', 1366056668)

        mock_get_item.assert_called_once_with(
            username= 'johndoe',
            date_joined= 1366056668)

    def test_put_item(self):
        with mock.patch.object(
                self.users.connection,
                'put_item',
                return_value={}) as mock_put_item:
            self.users.put_item(data={
                'username': 'johndoe',
                'last_name': 'Doe',
                'date_joined': 12345,
            })

        mock_put_item.assert_called_once_with('users', {
            'username': {'S': 'johndoe'},
            'last_name': {'S': 'Doe'},
            'date_joined': {'N': '12345'}
        }, expected={
            'username': {
                'Exists': False,
            },
            'last_name': {
                'Exists': False,
            },
            'date_joined': {
                'Exists': False,
            }
        })

    def test_private_put_item(self):
        with mock.patch.object(
                self.users.connection,
                'put_item',
                return_value={}) as mock_put_item:
            self.users._put_item({'some': 'data'})

        mock_put_item.assert_called_once_with('users', {'some': 'data'})

    def test_private_update_item(self):
        with mock.patch.object(
                self.users.connection,
                'update_item',
                return_value={}) as mock_update_item:
            self.users._update_item({
                'username': 'johndoe'
            }, {
                'some': 'data',
            })

        mock_update_item.assert_called_once_with('users', {
            'username': {'S': 'johndoe'},
        }, {
            'some': 'data',
        })

    def test_delete_item(self):
        with mock.patch.object(
                self.users.connection,
                'delete_item',
                return_value={}) as mock_delete_item:
            self.assertTrue(self.users.delete_item(username='johndoe', date_joined=23456))

        mock_delete_item.assert_called_once_with('users', {
            'username': {
                'S': 'johndoe'
            },
            'date_joined': {
                'N': '23456'
            }
        }, expected=None, conditional_operator=None)

    def test_delete_item_conditionally(self):
        with mock.patch.object(
                self.users.connection,
                'delete_item',
                return_value={}) as mock_delete_item:
            self.assertTrue(self.users.delete_item(expected={'balance__eq': 0},
                                                   username='johndoe', date_joined=23456))

        mock_delete_item.assert_called_once_with('users', {
            'username': {
                'S': 'johndoe'
            },
            'date_joined': {
                'N': '23456'
            }
        },
        expected={
            'balance': {
                'ComparisonOperator': 'EQ', 'AttributeValueList': [{'N': '0'}]
                },
            },
        conditional_operator=None)

        def side_effect(*args, **kwargs):
            raise exceptions.ConditionalCheckFailedException(400, '', {})

        with mock.patch.object(
                self.users.connection,
                'delete_item',
                side_effect=side_effect) as mock_delete_item:
            self.assertFalse(self.users.delete_item(expected={'balance__eq': 0},
                                                    username='johndoe', date_joined=23456))

    def test_get_key_fields_no_schema_populated(self):
        expected = {
            "Table": {
                "AttributeDefinitions": [
                    {
                        "AttributeName": "username",
                        "AttributeType": "S"
                    },
                    {
                        "AttributeName": "date_joined",
                        "AttributeType": "N"
                    }
                ],
                "ItemCount": 5,
                "KeySchema": [
                    {
                        "AttributeName": "username",
                        "KeyType": "HASH"
                    },
                    {
                        "AttributeName": "date_joined",
                        "KeyType": "RANGE"
                    }
                ],
                "LocalSecondaryIndexes": [
                    {
                        "IndexName": "UsernameIndex",
                        "KeySchema": [
                            {
                                "AttributeName": "username",
                                "KeyType": "HASH"
                            }
                        ],
                        "Projection": {
                            "ProjectionType": "KEYS_ONLY"
                        }
                    }
                ],
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 20,
                    "WriteCapacityUnits": 6
                },
                "TableName": "Thread",
                "TableStatus": "ACTIVE"
            }
        }

        with mock.patch.object(
                self.users.connection,
                'describe_table',
                return_value=expected) as mock_describe:
            self.assertEqual(self.users.schema, None)

            key_fields = self.users.get_key_fields()
            self.assertEqual(key_fields, ['username', 'date_joined'])

            self.assertEqual(len(self.users.schema), 2)

        mock_describe.assert_called_once_with('users')

    def test_batch_write_no_writes(self):
        with mock.patch.object(
                self.users.connection,
                'batch_write_item',
                return_value={}) as mock_batch:
            with self.users.batch_write() as batch:
                pass

        self.assertFalse(mock_batch.called)

    def test_batch_write(self):
        with mock.patch.object(
                self.users.connection,
                'batch_write_item',
                return_value={}) as mock_batch:
            with self.users.batch_write() as batch:
                batch.put_item(data={
                    'username': 'jane',
                    'date_joined': 12342547
                })
                batch.delete_item(username='johndoe')
                batch.put_item(data={
                    'username': 'alice',
                    'date_joined': 12342888
                })

        mock_batch.assert_called_once_with({
            'users': [
                {
                    'PutRequest': {
                        'Item': {
                            'username': {'S': 'jane'},
                            'date_joined': {'N': '12342547'}
                        }
                    }
                },
                {
                    'PutRequest': {
                        'Item': {
                            'username': {'S': 'alice'},
                            'date_joined': {'N': '12342888'}
                        }
                    }
                },
                {
                    'DeleteRequest': {
                        'Key': {
                            'username': {'S': 'johndoe'},
                        }
                    }
                },
            ]
        })

    def test_batch_write_dont_swallow_exceptions(self):
        with mock.patch.object(
                self.users.connection,
                'batch_write_item',
                return_value={}) as mock_batch:
            try:
                with self.users.batch_write() as batch:
                    raise Exception('OH NOES')
            except Exception as e:
                self.assertEqual(str(e), 'OH NOES')

        self.assertFalse(mock_batch.called)

    def test_batch_write_flushing(self):
        with mock.patch.object(
                self.users.connection,
                'batch_write_item',
                return_value={}) as mock_batch:
            with self.users.batch_write() as batch:
                batch.put_item(data={
                    'username': 'jane',
                    'date_joined': 12342547
                })
                # This would only be enough for one batch.
                batch.delete_item(username='johndoe1')
                batch.delete_item(username='johndoe2')
                batch.delete_item(username='johndoe3')
                batch.delete_item(username='johndoe4')
                batch.delete_item(username='johndoe5')
                batch.delete_item(username='johndoe6')
                batch.delete_item(username='johndoe7')
                batch.delete_item(username='johndoe8')
                batch.delete_item(username='johndoe9')
                batch.delete_item(username='johndoe10')
                batch.delete_item(username='johndoe11')
                batch.delete_item(username='johndoe12')
                batch.delete_item(username='johndoe13')
                batch.delete_item(username='johndoe14')
                batch.delete_item(username='johndoe15')
                batch.delete_item(username='johndoe16')
                batch.delete_item(username='johndoe17')
                batch.delete_item(username='johndoe18')
                batch.delete_item(username='johndoe19')
                batch.delete_item(username='johndoe20')
                batch.delete_item(username='johndoe21')
                batch.delete_item(username='johndoe22')
                batch.delete_item(username='johndoe23')

                # We're only at 24 items. No flushing yet.
                self.assertEqual(mock_batch.call_count, 0)

                # This pushes it over the edge. A flush happens then we start
                # queuing objects again.
                batch.delete_item(username='johndoe24')
                self.assertEqual(mock_batch.call_count, 1)
                # Since we add another, there's enough for a second call to
                # flush.
                batch.delete_item(username='johndoe25')

        self.assertEqual(mock_batch.call_count, 2)

    def test_batch_write_unprocessed_items(self):
        unprocessed = {
            'UnprocessedItems': {
                'users': [
                    {
                        'PutRequest': {
                            'username': {
                                'S': 'jane',
                            },
                            'date_joined': {
                                'N': 12342547
                            }
                        },
                    },
                ],
            },
        }

        # Test enqueuing the unprocessed bits.
        with mock.patch.object(
                self.users.connection,
                'batch_write_item',
                return_value=unprocessed) as mock_batch:
            with self.users.batch_write() as batch:
                self.assertEqual(len(batch._unprocessed), 0)

                # Trash the ``resend_unprocessed`` method so that we don't
                # infinite loop forever here.
                batch.resend_unprocessed = lambda: True

                batch.put_item(data={
                    'username': 'jane',
                    'date_joined': 12342547
                })
                batch.delete_item(username='johndoe')
                batch.put_item(data={
                    'username': 'alice',
                    'date_joined': 12342888
                })

            self.assertEqual(len(batch._unprocessed), 1)

        # Now test resending those unprocessed items.
        with mock.patch.object(
                self.users.connection,
                'batch_write_item',
                return_value={}) as mock_batch:
            with self.users.batch_write() as batch:
                self.assertEqual(len(batch._unprocessed), 0)

                # Toss in faked unprocessed items, as though a previous batch
                # had failed.
                batch._unprocessed = [
                    {
                        'PutRequest': {
                            'username': {
                                'S': 'jane',
                            },
                            'date_joined': {
                                'N': 12342547
                            }
                        },
                    },
                ]

                batch.put_item(data={
                    'username': 'jane',
                    'date_joined': 12342547
                })
                batch.delete_item(username='johndoe')
                batch.put_item(data={
                    'username': 'alice',
                    'date_joined': 12342888
                })

                # Flush, to make sure everything has been processed.
                # Unprocessed items should still be hanging around.
                batch.flush()
                self.assertEqual(len(batch._unprocessed), 1)

            # Post-exit, this should be emptied.
            self.assertEqual(len(batch._unprocessed), 0)

    def test__build_filters(self):
        filters = self.users._build_filters({
            'username__eq': 'johndoe',
            'date_joined__gte': 1234567,
            'age__in': [30, 31, 32, 33],
            'last_name__between': ['danzig', 'only'],
            'first_name__null': False,
            'gender__null': True,
        }, using=FILTER_OPERATORS)
        self.assertEqual(filters, {
            'username': {
                'AttributeValueList': [
                    {
                        'S': 'johndoe',
                    },
                ],
                'ComparisonOperator': 'EQ',
            },
            'date_joined': {
                'AttributeValueList': [
                    {
                        'N': '1234567',
                    },
                ],
                'ComparisonOperator': 'GE',
            },
            'age': {
                'AttributeValueList': [
                    {'N': '30'},
                    {'N': '31'},
                    {'N': '32'},
                    {'N': '33'},
                ],
                'ComparisonOperator': 'IN',
            },
            'last_name': {
                'AttributeValueList': [{'S': 'danzig'}, {'S': 'only'}],
                'ComparisonOperator': 'BETWEEN',
            },
            'first_name': {
                'ComparisonOperator': 'NOT_NULL'
            },
            'gender': {
                'ComparisonOperator': 'NULL'
            },
        })

        self.assertRaises(exceptions.UnknownFilterTypeError,
            self.users._build_filters,
            {
                'darling__die': True,
            }
        )

        q_filters = self.users._build_filters({
            'username__eq': 'johndoe',
            'date_joined__gte': 1234567,
            'last_name__between': ['danzig', 'only'],
            'gender__beginswith': 'm',
        }, using=QUERY_OPERATORS)
        self.assertEqual(q_filters, {
            'username': {
                'AttributeValueList': [
                    {
                        'S': 'johndoe',
                    },
                ],
                'ComparisonOperator': 'EQ',
            },
            'date_joined': {
                'AttributeValueList': [
                    {
                        'N': '1234567',
                    },
                ],
                'ComparisonOperator': 'GE',
            },
            'last_name': {
                'AttributeValueList': [{'S': 'danzig'}, {'S': 'only'}],
                'ComparisonOperator': 'BETWEEN',
            },
            'gender': {
                'AttributeValueList': [{'S': 'm'}],
                'ComparisonOperator': 'BEGINS_WITH',
            },
        })

        self.assertRaises(exceptions.UnknownFilterTypeError,
            self.users._build_filters,
            {
                'darling__die': True,
            },
            using=QUERY_OPERATORS
        )
        self.assertRaises(exceptions.UnknownFilterTypeError,
            self.users._build_filters,
            {
                'first_name__null': True,
            },
            using=QUERY_OPERATORS
        )

    def test_private_query(self):
        expected = {
            "ConsumedCapacity": {
                "CapacityUnits": 0.5,
                "TableName": "users"
            },
            "Count": 4,
            "Items": [
                {
                    'username': {'S': 'johndoe'},
                    'first_name': {'S': 'John'},
                    'last_name': {'S': 'Doe'},
                    'date_joined': {'N': '1366056668'},
                    'friend_count': {'N': '3'},
                    'friends': {'SS': ['alice', 'bob', 'jane']},
                },
                {
                    'username': {'S': 'jane'},
                    'first_name': {'S': 'Jane'},
                    'last_name': {'S': 'Doe'},
                    'date_joined': {'N': '1366057777'},
                    'friend_count': {'N': '2'},
                    'friends': {'SS': ['alice', 'johndoe']},
                },
                {
                    'username': {'S': 'alice'},
                    'first_name': {'S': 'Alice'},
                    'last_name': {'S': 'Expert'},
                    'date_joined': {'N': '1366056680'},
                    'friend_count': {'N': '1'},
                    'friends': {'SS': ['jane']},
                },
                {
                    'username': {'S': 'bob'},
                    'first_name': {'S': 'Bob'},
                    'last_name': {'S': 'Smith'},
                    'date_joined': {'N': '1366056888'},
                    'friend_count': {'N': '1'},
                    'friends': {'SS': ['johndoe']},
                },
            ],
            "ScannedCount": 4
        }

        with mock.patch.object(
                self.users.connection,
                'query',
                return_value=expected) as mock_query:
            results = self.users._query(
                limit=4,
                reverse=True,
                username__between=['aaa', 'mmm']
            )
            usernames = [res['username'] for res in results['results']]
            self.assertEqual(usernames, ['johndoe', 'jane', 'alice', 'bob'])
            self.assertEqual(len(results['results']), 4)
            self.assertEqual(results['last_key'], None)

        mock_query.assert_called_once_with('users',
            consistent_read=False,
            scan_index_forward=False,
            index_name=None,
            attributes_to_get=None,
            limit=4,
            key_conditions={
                'username': {
                    'AttributeValueList': [{'S': 'aaa'}, {'S': 'mmm'}],
                    'ComparisonOperator': 'BETWEEN',
                }
            },
            select=None,
            query_filter=None,
            conditional_operator=None
        )

        # Now alter the expected.
        expected['LastEvaluatedKey'] = {
            'username': {
                'S': 'johndoe',
            },
        }

        with mock.patch.object(
                self.users.connection,
                'query',
                return_value=expected) as mock_query_2:
            results = self.users._query(
                limit=4,
                reverse=True,
                username__between=['aaa', 'mmm'],
                exclusive_start_key={
                    'username': 'adam',
                },
                consistent=True,
                query_filter=None,
                conditional_operator='AND'
            )
            usernames = [res['username'] for res in results['results']]
            self.assertEqual(usernames, ['johndoe', 'jane', 'alice', 'bob'])
            self.assertEqual(len(results['results']), 4)
            self.assertEqual(results['last_key'], {'username': 'johndoe'})

        mock_query_2.assert_called_once_with('users',
            key_conditions={
                'username': {
                    'AttributeValueList': [{'S': 'aaa'}, {'S': 'mmm'}],
                    'ComparisonOperator': 'BETWEEN',
                }
            },
            index_name=None,
            attributes_to_get=None,
            scan_index_forward=False,
            limit=4,
            exclusive_start_key={
                'username': {
                    'S': 'adam',
                },
            },
            consistent_read=True,
            select=None,
            query_filter=None,
            conditional_operator='AND'
        )

    def test_private_scan(self):
        expected = {
            "ConsumedCapacity": {
                "CapacityUnits": 0.5,
                "TableName": "users"
            },
            "Count": 4,
            "Items": [
                {
                    'username': {'S': 'alice'},
                    'first_name': {'S': 'Alice'},
                    'last_name': {'S': 'Expert'},
                    'date_joined': {'N': '1366056680'},
                    'friend_count': {'N': '1'},
                    'friends': {'SS': ['jane']},
                },
                {
                    'username': {'S': 'bob'},
                    'first_name': {'S': 'Bob'},
                    'last_name': {'S': 'Smith'},
                    'date_joined': {'N': '1366056888'},
                    'friend_count': {'N': '1'},
                    'friends': {'SS': ['johndoe']},
                },
                {
                    'username': {'S': 'jane'},
                    'first_name': {'S': 'Jane'},
                    'last_name': {'S': 'Doe'},
                    'date_joined': {'N': '1366057777'},
                    'friend_count': {'N': '2'},
                    'friends': {'SS': ['alice', 'johndoe']},
                },
            ],
            "ScannedCount": 4
        }

        with mock.patch.object(
                self.users.connection,
                'scan',
                return_value=expected) as mock_scan:
            results = self.users._scan(
                limit=2,
                friend_count__lte=2
            )
            usernames = [res['username'] for res in results['results']]
            self.assertEqual(usernames, ['alice', 'bob', 'jane'])
            self.assertEqual(len(results['results']), 3)
            self.assertEqual(results['last_key'], None)

        mock_scan.assert_called_once_with('users',
            scan_filter={
                'friend_count': {
                    'AttributeValueList': [{'N': '2'}],
                    'ComparisonOperator': 'LE',
                }
            },
            limit=2,
            segment=None,
            attributes_to_get=None,
            total_segments=None,
            conditional_operator=None
        )

        # Now alter the expected.
        expected['LastEvaluatedKey'] = {
            'username': {
                'S': 'jane',
            },
        }

        with mock.patch.object(
                self.users.connection,
                'scan',
                return_value=expected) as mock_scan_2:
            results = self.users._scan(
                limit=3,
                friend_count__lte=2,
                exclusive_start_key={
                    'username': 'adam',
                },
                segment=None,
                total_segments=None
            )
            usernames = [res['username'] for res in results['results']]
            self.assertEqual(usernames, ['alice', 'bob', 'jane'])
            self.assertEqual(len(results['results']), 3)
            self.assertEqual(results['last_key'], {'username': 'jane'})

        mock_scan_2.assert_called_once_with('users',
            scan_filter={
                'friend_count': {
                    'AttributeValueList': [{'N': '2'}],
                    'ComparisonOperator': 'LE',
                }
            },
            limit=3,
            exclusive_start_key={
                'username': {
                    'S': 'adam',
                },
            },
            segment=None,
            attributes_to_get=None,
            total_segments=None,
            conditional_operator=None
        )

    def test_query(self):
        items_1 = {
            'results': [
                Item(self.users, data={
                    'username': 'johndoe',
                    'first_name': 'John',
                    'last_name': 'Doe',
                }),
                Item(self.users, data={
                    'username': 'jane',
                    'first_name': 'Jane',
                    'last_name': 'Doe',
                }),
            ],
            'last_key': 'jane',
        }

        results = self.users.query_2(last_name__eq='Doe')
        self.assertTrue(isinstance(results, ResultSet))
        self.assertEqual(len(results._results), 0)
        self.assertEqual(results.the_callable, self.users._query)

        with mock.patch.object(
                results,
                'the_callable',
                return_value=items_1) as mock_query:
            res_1 = next(results)
            # Now it should be populated.
            self.assertEqual(len(results._results), 2)
            self.assertEqual(res_1['username'], 'johndoe')
            res_2 = next(results)
            self.assertEqual(res_2['username'], 'jane')

        self.assertEqual(mock_query.call_count, 1)

        items_2 = {
            'results': [
                Item(self.users, data={
                    'username': 'foodoe',
                    'first_name': 'Foo',
                    'last_name': 'Doe',
                }),
            ],
        }

        with mock.patch.object(
                results,
                'the_callable',
                return_value=items_2) as mock_query_2:
            res_3 = next(results)
            # New results should have been found.
            self.assertEqual(len(results._results), 1)
            self.assertEqual(res_3['username'], 'foodoe')

            self.assertRaises(StopIteration, results.next)

        self.assertEqual(mock_query_2.call_count, 1)

    def test_query_with_specific_attributes(self):
        items_1 = {
            'results': [
                Item(self.users, data={
                    'username': 'johndoe',
                }),
                Item(self.users, data={
                    'username': 'jane',
                }),
            ],
            'last_key': 'jane',
        }

        results = self.users.query_2(last_name__eq='Doe',
                                   attributes=['username'])
        self.assertTrue(isinstance(results, ResultSet))
        self.assertEqual(len(results._results), 0)
        self.assertEqual(results.the_callable, self.users._query)

        with mock.patch.object(
                results,
                'the_callable',
                return_value=items_1) as mock_query:
            res_1 = next(results)
            # Now it should be populated.
            self.assertEqual(len(results._results), 2)
            self.assertEqual(res_1['username'], 'johndoe')
            self.assertEqual(list(res_1.keys()), ['username'])
            res_2 = next(results)
            self.assertEqual(res_2['username'], 'jane')

        self.assertEqual(mock_query.call_count, 1)

    def test_scan(self):
        items_1 = {
            'results': [
                Item(self.users, data={
                    'username': 'johndoe',
                    'first_name': 'John',
                    'last_name': 'Doe',
                }),
                Item(self.users, data={
                    'username': 'jane',
                    'first_name': 'Jane',
                    'last_name': 'Doe',
                }),
            ],
            'last_key': 'jane',
        }

        results = self.users.scan(last_name__eq='Doe')
        self.assertTrue(isinstance(results, ResultSet))
        self.assertEqual(len(results._results), 0)
        self.assertEqual(results.the_callable, self.users._scan)

        with mock.patch.object(
                results,
                'the_callable',
                return_value=items_1) as mock_scan:
            res_1 = next(results)
            # Now it should be populated.
            self.assertEqual(len(results._results), 2)
            self.assertEqual(res_1['username'], 'johndoe')
            res_2 = next(results)
            self.assertEqual(res_2['username'], 'jane')

        self.assertEqual(mock_scan.call_count, 1)

        items_2 = {
            'results': [
                Item(self.users, data={
                    'username': 'zoeydoe',
                    'first_name': 'Zoey',
                    'last_name': 'Doe',
                }),
            ],
        }

        with mock.patch.object(
                results,
                'the_callable',
                return_value=items_2) as mock_scan_2:
            res_3 = next(results)
            # New results should have been found.
            self.assertEqual(len(results._results), 1)
            self.assertEqual(res_3['username'], 'zoeydoe')

            self.assertRaises(StopIteration, results.next)

        self.assertEqual(mock_scan_2.call_count, 1)

    def test_scan_with_specific_attributes(self):
        items_1 = {
            'results': [
                Item(self.users, data={
                    'username': 'johndoe',
                }),
                Item(self.users, data={
                    'username': 'jane',
                }),
            ],
            'last_key': 'jane',
        }

        results = self.users.scan(attributes=['username'])
        self.assertTrue(isinstance(results, ResultSet))
        self.assertEqual(len(results._results), 0)
        self.assertEqual(results.the_callable, self.users._scan)

        with mock.patch.object(
                results,
                'the_callable',
                return_value=items_1) as mock_query:
            res_1 = next(results)
            # Now it should be populated.
            self.assertEqual(len(results._results), 2)
            self.assertEqual(res_1['username'], 'johndoe')
            self.assertEqual(list(res_1.keys()), ['username'])
            res_2 = next(results)
            self.assertEqual(res_2['username'], 'jane')

        self.assertEqual(mock_query.call_count, 1)

    def test_count(self):
        expected = {
            "Table": {
                "AttributeDefinitions": [
                    {
                        "AttributeName": "username",
                        "AttributeType": "S"
                    }
                ],
                "ItemCount": 5,
                "KeySchema": [
                    {
                        "AttributeName": "username",
                        "KeyType": "HASH"
                    }
                ],
                "LocalSecondaryIndexes": [
                    {
                        "IndexName": "UsernameIndex",
                        "KeySchema": [
                            {
                                "AttributeName": "username",
                                "KeyType": "HASH"
                            }
                        ],
                        "Projection": {
                            "ProjectionType": "KEYS_ONLY"
                        }
                    }
                ],
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 20,
                    "WriteCapacityUnits": 6
                },
                "TableName": "Thread",
                "TableStatus": "ACTIVE"
            }
        }

        with mock.patch.object(
                self.users,
                'describe',
                return_value=expected) as mock_count:
            self.assertEqual(self.users.count(), 5)

    def test_query_count_simple(self):
        expected_0 = {
            'Count': 0.0,
        }

        expected_1 = {
            'Count': 10.0,
        }

        with mock.patch.object(
                self.users.connection,
                'query',
                return_value=expected_0) as mock_query:
            results = self.users.query_count(username__eq='notmyname')
            self.assertTrue(isinstance(results, int))
            self.assertEqual(results, 0)
        self.assertEqual(mock_query.call_count, 1)
        self.assertIn('scan_index_forward', mock_query.call_args[1])
        self.assertEqual(True, mock_query.call_args[1]['scan_index_forward'])
        self.assertIn('limit', mock_query.call_args[1])
        self.assertEqual(None, mock_query.call_args[1]['limit'])

        with mock.patch.object(
                self.users.connection,
                'query',
                return_value=expected_1) as mock_query:
            results = self.users.query_count(username__gt='somename', consistent=True, scan_index_forward=False, limit=10)
            self.assertTrue(isinstance(results, int))
            self.assertEqual(results, 10)
        self.assertEqual(mock_query.call_count, 1)
        self.assertIn('scan_index_forward', mock_query.call_args[1])
        self.assertEqual(False, mock_query.call_args[1]['scan_index_forward'])
        self.assertIn('limit', mock_query.call_args[1])
        self.assertEqual(10, mock_query.call_args[1]['limit'])

    def test_query_count_paginated(self):
        def return_side_effect(*args, **kwargs):
            if kwargs.get('exclusive_start_key'):
                return {'Count': 10, 'LastEvaluatedKey': None}
            else:
                return {
                    'Count': 20,
                    'LastEvaluatedKey': {
                        'username': {
                            'S': 'johndoe'
                        },
                        'date_joined': {
                            'N': '4118642633'
                        }
                    }
                }

        with mock.patch.object(
                self.users.connection,
                'query',
                side_effect=return_side_effect
        ) as mock_query:
            count = self.users.query_count(username__eq='johndoe')
            self.assertTrue(isinstance(count, int))
            self.assertEqual(30, count)
            self.assertEqual(mock_query.call_count, 2)

    def test_private_batch_get(self):
        expected = {
            "ConsumedCapacity": {
                "CapacityUnits": 0.5,
                "TableName": "users"
            },
            'Responses': {
                'users': [
                    {
                        'username': {'S': 'alice'},
                        'first_name': {'S': 'Alice'},
                        'last_name': {'S': 'Expert'},
                        'date_joined': {'N': '1366056680'},
                        'friend_count': {'N': '1'},
                        'friends': {'SS': ['jane']},
                    },
                    {
                        'username': {'S': 'bob'},
                        'first_name': {'S': 'Bob'},
                        'last_name': {'S': 'Smith'},
                        'date_joined': {'N': '1366056888'},
                        'friend_count': {'N': '1'},
                        'friends': {'SS': ['johndoe']},
                    },
                    {
                        'username': {'S': 'jane'},
                        'first_name': {'S': 'Jane'},
                        'last_name': {'S': 'Doe'},
                        'date_joined': {'N': '1366057777'},
                        'friend_count': {'N': '2'},
                        'friends': {'SS': ['alice', 'johndoe']},
                    },
                ],
            },
            "UnprocessedKeys": {
            },
        }

        with mock.patch.object(
                self.users.connection,
                'batch_get_item',
                return_value=expected) as mock_batch_get:
            results = self.users._batch_get(keys=[
                {'username': 'alice', 'friend_count': 1},
                {'username': 'bob', 'friend_count': 1},
                {'username': 'jane'},
            ])
            usernames = [res['username'] for res in results['results']]
            self.assertEqual(usernames, ['alice', 'bob', 'jane'])
            self.assertEqual(len(results['results']), 3)
            self.assertEqual(results['last_key'], None)
            self.assertEqual(results['unprocessed_keys'], [])

        mock_batch_get.assert_called_once_with(request_items={
            'users': {
                'Keys': [
                    {
                        'username': {'S': 'alice'},
                        'friend_count': {'N': '1'}
                    },
                    {
                        'username': {'S': 'bob'},
                        'friend_count': {'N': '1'}
                    }, {
                        'username': {'S': 'jane'},
                    }
                ]
            }
        })

        # Now alter the expected.
        del expected['Responses']['users'][2]
        expected['UnprocessedKeys'] = {
            'users': {
                'Keys': [
                    {'username': {'S': 'jane',}},
                ],
            },
        }

        with mock.patch.object(
                self.users.connection,
                'batch_get_item',
                return_value=expected) as mock_batch_get_2:
            results = self.users._batch_get(keys=[
                {'username': 'alice', 'friend_count': 1},
                {'username': 'bob', 'friend_count': 1},
                {'username': 'jane'},
            ])
            usernames = [res['username'] for res in results['results']]
            self.assertEqual(usernames, ['alice', 'bob'])
            self.assertEqual(len(results['results']), 2)
            self.assertEqual(results['last_key'], None)
            self.assertEqual(results['unprocessed_keys'], [
                {'username': 'jane'}
            ])

        mock_batch_get_2.assert_called_once_with(request_items={
            'users': {
                'Keys': [
                    {
                        'username': {'S': 'alice'},
                        'friend_count': {'N': '1'}
                    },
                    {
                        'username': {'S': 'bob'},
                        'friend_count': {'N': '1'}
                    }, {
                        'username': {'S': 'jane'},
                    }
                ]
            }
        })

    def test_private_batch_get_attributes(self):
        # test if AttributesToGet parameter is passed to DynamoDB API
        expected = {
            "ConsumedCapacity": {
                "CapacityUnits": 0.5,
                "TableName": "users"
            },
            'Responses': {
                'users': [
                    {
                        'username': {'S': 'alice'},
                        'first_name': {'S': 'Alice'},
                    },
                    {
                        'username': {'S': 'bob'},
                        'first_name': {'S': 'Bob'},
                    },
                ],
            },
            "UnprocessedKeys": {},
        }

        with mock.patch.object(
                self.users.connection,
                'batch_get_item',
                return_value=expected) as mock_batch_get_attr:
            results = self.users._batch_get(keys=[
                    {'username': 'alice'},
                    {'username': 'bob'},
                ], attributes=['username', 'first_name'])
            usernames = [res['username'] for res in results['results']]
            first_names = [res['first_name'] for res in results['results']]
            self.assertEqual(usernames, ['alice', 'bob'])
            self.assertEqual(first_names, ['Alice', 'Bob'])
            self.assertEqual(len(results['results']), 2)
            self.assertEqual(results['last_key'], None)
            self.assertEqual(results['unprocessed_keys'], [])

        mock_batch_get_attr.assert_called_once_with(request_items={
            'users': {
                'Keys': [ { 'username': {'S': 'alice'} },
                          { 'username': {'S': 'bob'} }, ],
                'AttributesToGet': ['username', 'first_name'],
            },
        })

    def test_batch_get(self):
        items_1 = {
            'results': [
                Item(self.users, data={
                    'username': 'johndoe',
                    'first_name': 'John',
                    'last_name': 'Doe',
                }),
                Item(self.users, data={
                    'username': 'jane',
                    'first_name': 'Jane',
                    'last_name': 'Doe',
                }),
            ],
            'last_key': None,
            'unprocessed_keys': [
                'zoeydoe',
            ]
        }

        results = self.users.batch_get(keys=[
            {'username': 'johndoe'},
            {'username': 'jane'},
            {'username': 'zoeydoe'},
        ])
        self.assertTrue(isinstance(results, BatchGetResultSet))
        self.assertEqual(len(results._results), 0)
        self.assertEqual(results.the_callable, self.users._batch_get)

        with mock.patch.object(
                results,
                'the_callable',
                return_value=items_1) as mock_batch_get:
            res_1 = next(results)
            # Now it should be populated.
            self.assertEqual(len(results._results), 2)
            self.assertEqual(res_1['username'], 'johndoe')
            res_2 = next(results)
            self.assertEqual(res_2['username'], 'jane')

        self.assertEqual(mock_batch_get.call_count, 1)
        self.assertEqual(results._keys_left, ['zoeydoe'])

        items_2 = {
            'results': [
                Item(self.users, data={
                    'username': 'zoeydoe',
                    'first_name': 'Zoey',
                    'last_name': 'Doe',
                }),
            ],
        }

        with mock.patch.object(
                results,
                'the_callable',
                return_value=items_2) as mock_batch_get_2:
            res_3 = next(results)
            # New results should have been found.
            self.assertEqual(len(results._results), 1)
            self.assertEqual(res_3['username'], 'zoeydoe')

            self.assertRaises(StopIteration, results.next)

        self.assertEqual(mock_batch_get_2.call_count, 1)
        self.assertEqual(results._keys_left, [])
