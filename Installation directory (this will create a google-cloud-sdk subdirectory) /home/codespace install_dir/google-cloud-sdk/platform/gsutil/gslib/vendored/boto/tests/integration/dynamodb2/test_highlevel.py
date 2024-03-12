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
Tests for DynamoDB v2 high-level abstractions.
"""
import os
import time

from tests.unit import unittest
from boto.dynamodb2 import exceptions
from boto.dynamodb2.fields import (HashKey, RangeKey, KeysOnlyIndex,
                                   GlobalKeysOnlyIndex, GlobalIncludeIndex,
                                   GlobalAllIndex)
from boto.dynamodb2.items import Item
from boto.dynamodb2.table import Table
from boto.dynamodb2.types import NUMBER, STRING

try:
    import json
except ImportError:
    import simplejson as json


class DynamoDBv2Test(unittest.TestCase):
    dynamodb = True

    def test_integration(self):
        # Test creating a full table with all options specified.
        users = Table.create('users', schema=[
            HashKey('username'),
            RangeKey('friend_count', data_type=NUMBER)
        ], throughput={
            'read': 5,
            'write': 5,
        }, indexes=[
            KeysOnlyIndex('LastNameIndex', parts=[
                HashKey('username'),
                RangeKey('last_name')
            ]),
        ])
        self.addCleanup(users.delete)

        self.assertEqual(len(users.schema), 2)
        self.assertEqual(users.throughput['read'], 5)

        # Wait for it.
        time.sleep(60)

        # Make sure things line up if we're introspecting the table.
        users_hit_api = Table('users')
        users_hit_api.describe()
        self.assertEqual(len(users.schema), len(users_hit_api.schema))
        self.assertEqual(users.throughput, users_hit_api.throughput)
        self.assertEqual(len(users.indexes), len(users_hit_api.indexes))

        # Test putting some items individually.
        users.put_item(data={
            'username': 'johndoe',
            'first_name': 'John',
            'last_name': 'Doe',
            'friend_count': 4
        })

        users.put_item(data={
            'username': 'alice',
            'first_name': 'Alice',
            'last_name': 'Expert',
            'friend_count': 2
        })

        time.sleep(5)

        # Test batch writing.
        with users.batch_write() as batch:
            batch.put_item({
                'username': 'jane',
                'first_name': 'Jane',
                'last_name': 'Doe',
                'friend_count': 3
            })
            batch.delete_item(username='alice', friend_count=2)
            batch.put_item({
                'username': 'bob',
                'first_name': 'Bob',
                'last_name': 'Smith',
                'friend_count': 1
            })

        time.sleep(5)

        # Does it exist? It should?
        self.assertTrue(users.has_item(username='jane', friend_count=3))
        # But this shouldn't be there...
        self.assertFalse(users.has_item(
            username='mrcarmichaeljones',
            friend_count=72948
        ))

        # Test getting an item & updating it.
        # This is the "safe" variant (only write if there have been no
        # changes).
        jane = users.get_item(username='jane', friend_count=3)
        self.assertEqual(jane['first_name'], 'Jane')
        jane['last_name'] = 'Doh'
        self.assertTrue(jane.save())

        # Test strongly consistent getting of an item.
        # Additionally, test the overwrite behavior.
        client_1_jane = users.get_item(
            username='jane',
            friend_count=3,
            consistent=True
        )
        self.assertEqual(jane['first_name'], 'Jane')
        client_2_jane = users.get_item(
            username='jane',
            friend_count=3,
            consistent=True
        )
        self.assertEqual(jane['first_name'], 'Jane')

        # Write & assert the ``first_name`` is gone, then...
        del client_1_jane['first_name']
        self.assertTrue(client_1_jane.save())
        check_name = users.get_item(
            username='jane',
            friend_count=3,
            consistent=True
        )
        self.assertEqual(check_name['first_name'], None)

        # ...overwrite the data with what's in memory.
        client_2_jane['first_name'] = 'Joan'
        # Now a write that fails due to default expectations...
        self.assertRaises(exceptions.JSONResponseError, client_2_jane.save)
        # ... so we force an overwrite.
        self.assertTrue(client_2_jane.save(overwrite=True))
        check_name_again = users.get_item(
            username='jane',
            friend_count=3,
            consistent=True
        )
        self.assertEqual(check_name_again['first_name'], 'Joan')

        # Reset it.
        jane['username'] = 'jane'
        jane['first_name'] = 'Jane'
        jane['last_name'] = 'Doe'
        jane['friend_count'] = 3
        self.assertTrue(jane.save(overwrite=True))

        # Test the partial update behavior.
        client_3_jane = users.get_item(
            username='jane',
            friend_count=3,
            consistent=True
        )
        client_4_jane = users.get_item(
            username='jane',
            friend_count=3,
            consistent=True
        )
        client_3_jane['favorite_band'] = 'Feed Me'
        # No ``overwrite`` needed due to new data.
        self.assertTrue(client_3_jane.save())
        # Expectations are only checked on the ``first_name``, so what wouldn't
        # have succeeded by default does succeed here.
        client_4_jane['first_name'] = 'Jacqueline'
        self.assertTrue(client_4_jane.partial_save())
        partial_jane = users.get_item(
            username='jane',
            friend_count=3,
            consistent=True
        )
        self.assertEqual(partial_jane['favorite_band'], 'Feed Me')
        self.assertEqual(partial_jane['first_name'], 'Jacqueline')

        # Reset it.
        jane['username'] = 'jane'
        jane['first_name'] = 'Jane'
        jane['last_name'] = 'Doe'
        jane['friend_count'] = 3
        self.assertTrue(jane.save(overwrite=True))

        # Ensure that partial saves of a brand-new object work.
        sadie = Item(users, data={
            'username': 'sadie',
            'first_name': 'Sadie',
            'favorite_band': 'Zedd',
            'friend_count': 7
        })
        self.assertTrue(sadie.partial_save())
        serverside_sadie = users.get_item(
            username='sadie',
            friend_count=7,
            consistent=True
        )
        self.assertEqual(serverside_sadie['first_name'], 'Sadie')

        # Test the eventually consistent query.
        results = users.query_2(
            username__eq='johndoe',
            last_name__eq='Doe',
            index='LastNameIndex',
            attributes=('username',),
            reverse=True
        )

        for res in results:
            self.assertTrue(res['username'] in ['johndoe',])
            self.assertEqual(list(res.keys()), ['username'])

        # Ensure that queries with attributes don't return the hash key.
        results = users.query_2(
            username__eq='johndoe',
            friend_count__eq=4,
            attributes=('first_name',)
        )

        for res in results:
            self.assertEqual(res['first_name'], 'John')
            self.assertEqual(list(res.keys()), ['first_name'])

        # Test the strongly consistent query.
        c_results = users.query_2(
            username__eq='johndoe',
            last_name__eq='Doe',
            index='LastNameIndex',
            reverse=True,
            consistent=True
        )

        for res in c_results:
            self.assertEqual(res['username'], 'johndoe')

        # Test a query with query filters
        results = users.query_2(
            username__eq='johndoe',
            query_filter={
                'first_name__beginswith': 'J'
            },
            attributes=('first_name',)
        )

        for res in results:
            self.assertTrue(res['first_name'] in ['John'])

        # Test scans without filters.
        all_users = users.scan(limit=7)
        self.assertEqual(next(all_users)['username'], 'bob')
        self.assertEqual(next(all_users)['username'], 'jane')
        self.assertEqual(next(all_users)['username'], 'johndoe')

        # Test scans with a filter.
        filtered_users = users.scan(limit=2, username__beginswith='j')
        self.assertEqual(next(filtered_users)['username'], 'jane')
        self.assertEqual(next(filtered_users)['username'], 'johndoe')

        # Test deleting a single item.
        johndoe = users.get_item(username='johndoe', friend_count=4)
        johndoe.delete()

        # Set batch get limit to ensure keys with no results are
        # handled correctly.
        users.max_batch_get = 2

        # Test the eventually consistent batch get.
        results = users.batch_get(keys=[
            {'username': 'noone', 'friend_count': 4},
            {'username': 'nothere', 'friend_count': 10},
            {'username': 'bob', 'friend_count': 1},
            {'username': 'jane', 'friend_count': 3}
        ])
        batch_users = []

        for res in results:
            batch_users.append(res)
            self.assertIn(res['first_name'], ['Bob', 'Jane'])

        self.assertEqual(len(batch_users), 2)

        # Test the strongly consistent batch get.
        c_results = users.batch_get(keys=[
            {'username': 'bob', 'friend_count': 1},
            {'username': 'jane', 'friend_count': 3}
        ], consistent=True)
        c_batch_users = []

        for res in c_results:
            c_batch_users.append(res)
            self.assertTrue(res['first_name'] in ['Bob', 'Jane'])

        self.assertEqual(len(c_batch_users), 2)

        # Test count, but in a weak fashion. Because lag time.
        self.assertTrue(users.count() > -1)

        # Test query count
        count = users.query_count(
            username__eq='bob',
        )

        self.assertEqual(count, 1)

        # Test without LSIs (describe calls shouldn't fail).
        admins = Table.create('admins', schema=[
            HashKey('username')
        ])
        self.addCleanup(admins.delete)
        time.sleep(60)
        admins.describe()
        self.assertEqual(admins.throughput['read'], 5)
        self.assertEqual(admins.indexes, [])

        # A single query term should fail on a table with *ONLY* a HashKey.
        self.assertRaises(
            exceptions.QueryError,
            admins.query,
            username__eq='johndoe'
        )
        # But it shouldn't break on more complex tables.
        res = users.query_2(username__eq='johndoe')

        # Test putting with/without sets.
        mau5_created = users.put_item(data={
            'username': 'mau5',
            'first_name': 'dead',
            'last_name': 'mau5',
            'friend_count': 2,
            'friends': set(['skrill', 'penny']),
        })
        self.assertTrue(mau5_created)

        penny_created = users.put_item(data={
            'username': 'penny',
            'first_name': 'Penny',
            'friend_count': 0,
            'friends': set([]),
        })
        self.assertTrue(penny_created)

        # Test attributes.
        mau5 = users.get_item(
            username='mau5',
            friend_count=2,
            attributes=['username', 'first_name']
        )
        self.assertEqual(mau5['username'], 'mau5')
        self.assertEqual(mau5['first_name'], 'dead')
        self.assertTrue('last_name' not in mau5)

    def test_unprocessed_batch_writes(self):
        # Create a very limited table w/ low throughput.
        users = Table.create('slow_users', schema=[
            HashKey('user_id'),
        ], throughput={
            'read': 1,
            'write': 1,
        })
        self.addCleanup(users.delete)

        # Wait for it.
        time.sleep(60)

        with users.batch_write() as batch:
            for i in range(500):
                batch.put_item(data={
                    'user_id': str(i),
                    'name': 'Droid #{0}'.format(i),
                })

            # Before ``__exit__`` runs, we should have a bunch of unprocessed
            # items.
            self.assertTrue(len(batch._unprocessed) > 0)

        # Post-__exit__, they should all be gone.
        self.assertEqual(len(batch._unprocessed), 0)

    def test_gsi(self):
        users = Table.create('gsi_users', schema=[
            HashKey('user_id'),
        ], throughput={
            'read': 5,
            'write': 3,
        },
        global_indexes=[
            GlobalKeysOnlyIndex('StuffIndex', parts=[
                HashKey('user_id')
            ], throughput={
                'read': 2,
                'write': 1,
            }),
        ])
        self.addCleanup(users.delete)

        # Wait for it.
        time.sleep(60)

        users.update(
            throughput={
                'read': 3,
                'write': 4
            },
            global_indexes={
                'StuffIndex': {
                    'read': 1,
                    'write': 2
                }
            }
        )

        # Wait again for the changes to finish propagating.
        time.sleep(150)

    def test_gsi_with_just_hash_key(self):
        # GSI allows for querying off of different keys. This is behavior we
        # previously disallowed (due to standard & LSI queries).
        # See https://forums.aws.amazon.com/thread.jspa?threadID=146212&tstart=0
        users = Table.create('gsi_query_users', schema=[
            HashKey('user_id')
        ], throughput={
            'read': 5,
            'write': 3,
        },
        global_indexes=[
            GlobalIncludeIndex('UsernameIndex', parts=[
                HashKey('username'),
            ], includes=['user_id', 'username'], throughput={
                'read': 3,
                'write': 1,
            })
        ])
        self.addCleanup(users.delete)

        # Wait for it.
        time.sleep(60)

        users.put_item(data={
            'user_id': '7',
            'username': 'johndoe',
            'first_name': 'John',
            'last_name': 'Doe',
        })
        users.put_item(data={
            'user_id': '24',
            'username': 'alice',
            'first_name': 'Alice',
            'last_name': 'Expert',
        })
        users.put_item(data={
            'user_id': '35',
            'username': 'jane',
            'first_name': 'Jane',
            'last_name': 'Doe',
        })

        # Try the main key. Should be fine.
        rs = users.query_2(
            user_id__eq='24'
        )
        results = sorted([user['username'] for user in rs])
        self.assertEqual(results, ['alice'])

        # Now try the GSI. Also should work.
        rs = users.query_2(
            username__eq='johndoe',
            index='UsernameIndex'
        )
        results = sorted([user['username'] for user in rs])
        self.assertEqual(results, ['johndoe'])

    def test_query_with_limits(self):
        # Per the DDB team, it's recommended to do many smaller gets with a
        # reduced page size.
        # Clamp down the page size while ensuring that the correct number of
        # results are still returned.
        posts = Table.create('posts', schema=[
            HashKey('thread'),
            RangeKey('posted_on')
        ], throughput={
            'read': 5,
            'write': 5,
        })
        self.addCleanup(posts.delete)

        # Wait for it.
        time.sleep(60)

        # Add some data.
        test_data_path = os.path.join(
            os.path.dirname(__file__),
            'forum_test_data.json'
        )
        with open(test_data_path, 'r') as test_data:
            data = json.load(test_data)

            with posts.batch_write() as batch:
                for post in data:
                    batch.put_item(post)

        time.sleep(5)

        # Test the reduced page size.
        results = posts.query_2(
            thread__eq='Favorite chiptune band?',
            posted_on__gte='2013-12-24T00:00:00',
            max_page_size=2
        )

        all_posts = list(results)
        self.assertEqual(
            [post['posted_by'] for post in all_posts],
            ['joe', 'jane', 'joe', 'joe', 'jane', 'joe']
        )
        self.assertTrue(results._fetches >= 3)

    def test_query_with_reverse(self):
        posts = Table.create('more-posts', schema=[
            HashKey('thread'),
            RangeKey('posted_on')
        ], throughput={
            'read': 5,
            'write': 5,
        })
        self.addCleanup(posts.delete)

        # Wait for it.
        time.sleep(60)

        # Add some data.
        test_data_path = os.path.join(
            os.path.dirname(__file__),
            'forum_test_data.json'
        )
        with open(test_data_path, 'r') as test_data:
            data = json.load(test_data)

            with posts.batch_write() as batch:
                for post in data:
                    batch.put_item(post)

        time.sleep(5)

        # Test the default order (ascending).
        results = posts.query_2(
            thread__eq='Favorite chiptune band?',
            posted_on__gte='2013-12-24T00:00:00'
        )
        self.assertEqual(
            [post['posted_on'] for post in results],
            [
                '2013-12-24T12:30:54',
                '2013-12-24T12:35:40',
                '2013-12-24T13:45:30',
                '2013-12-24T14:15:14',
                '2013-12-24T14:25:33',
                '2013-12-24T15:22:22',
            ]
        )

        # Test the explicit ascending order.
        results = posts.query_2(
            thread__eq='Favorite chiptune band?',
            posted_on__gte='2013-12-24T00:00:00',
            reverse=False
        )
        self.assertEqual(
            [post['posted_on'] for post in results],
            [
                '2013-12-24T12:30:54',
                '2013-12-24T12:35:40',
                '2013-12-24T13:45:30',
                '2013-12-24T14:15:14',
                '2013-12-24T14:25:33',
                '2013-12-24T15:22:22',
            ]
        )

        # Test the explicit descending order.
        results = posts.query_2(
            thread__eq='Favorite chiptune band?',
            posted_on__gte='2013-12-24T00:00:00',
            reverse=True
        )
        self.assertEqual(
            [post['posted_on'] for post in results],
            [
                '2013-12-24T15:22:22',
                '2013-12-24T14:25:33',
                '2013-12-24T14:15:14',
                '2013-12-24T13:45:30',
                '2013-12-24T12:35:40',
                '2013-12-24T12:30:54',
            ]
        )

        # Test the old, broken style.
        results = posts.query(
            thread__eq='Favorite chiptune band?',
            posted_on__gte='2013-12-24T00:00:00'
        )
        self.assertEqual(
            [post['posted_on'] for post in results],
            [
                '2013-12-24T15:22:22',
                '2013-12-24T14:25:33',
                '2013-12-24T14:15:14',
                '2013-12-24T13:45:30',
                '2013-12-24T12:35:40',
                '2013-12-24T12:30:54',
            ]
        )
        results = posts.query(
            thread__eq='Favorite chiptune band?',
            posted_on__gte='2013-12-24T00:00:00',
            reverse=True
        )
        self.assertEqual(
            [post['posted_on'] for post in results],
            [
                '2013-12-24T12:30:54',
                '2013-12-24T12:35:40',
                '2013-12-24T13:45:30',
                '2013-12-24T14:15:14',
                '2013-12-24T14:25:33',
                '2013-12-24T15:22:22',
            ]
        )

    def test_query_after_describe_with_gsi(self):
        # Create a table to using gsi to reproduce the error mentioned on issue
        # https://github.com/boto/boto/issues/2828
        users = Table.create('more_gsi_query_users', schema=[
            HashKey('user_id')
        ], throughput={
            'read': 5,
            'write': 5
        }, global_indexes=[
            GlobalAllIndex('EmailGSIIndex', parts=[
                HashKey('email')
            ], throughput={
                'read': 1,
                'write': 1
            })
        ])

        # Add this function to be called after tearDown()
        self.addCleanup(users.delete)

        # Wait for it.
        time.sleep(60)

        # populate a couple of items in it
        users.put_item(data={
            'user_id': '7',
            'username': 'johndoe',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'johndoe@johndoe.com',
        })
        users.put_item(data={
            'user_id': '24',
            'username': 'alice',
            'first_name': 'Alice',
            'last_name': 'Expert',
            'email': 'alice@alice.com',
        })
        users.put_item(data={
            'user_id': '35',
            'username': 'jane',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@jane.com',
        })

        # Try the GSI. it should work.
        rs = users.query_2(
            email__eq='johndoe@johndoe.com',
            index='EmailGSIIndex'
        )

        for rs_item in rs:
            self.assertEqual(rs_item['username'], ['johndoe'])

        # The issue arises when we're introspecting the table and try to
        # query_2 after call describe method
        users_hit_api = Table('more_gsi_query_users')
        users_hit_api.describe()

        # Try the GSI. This is what os going wrong on #2828 issue. It should
        # work fine now.
        rs = users_hit_api.query_2(
            email__eq='johndoe@johndoe.com',
            index='EmailGSIIndex'
        )

        for rs_item in rs:
            self.assertEqual(rs_item['username'], ['johndoe'])

    def test_update_table_online_indexing_support(self):
        # Create a table using gsi to test the DynamoDB online indexing support
        # https://github.com/boto/boto/pull/2925
        users = Table.create('online_indexing_support_users', schema=[
            HashKey('user_id')
        ], throughput={
            'read': 5,
            'write': 5
        }, global_indexes=[
            GlobalAllIndex('EmailGSIIndex', parts=[
                HashKey('email')
            ], throughput={
                'read': 2,
                'write': 2
            })
        ])

        # Add this function to be called after tearDown()
        self.addCleanup(users.delete)

        # Wait for it.
        time.sleep(60)

        # Fetch fresh table desc from DynamoDB
        users.describe()

        # Assert if everything is fine so far
        self.assertEqual(len(users.global_indexes), 1)
        self.assertEqual(users.global_indexes[0].throughput['read'], 2)
        self.assertEqual(users.global_indexes[0].throughput['write'], 2)

        # Update a GSI throughput. it should work.
        users.update_global_secondary_index(global_indexes={
            'EmailGSIIndex': {
                'read': 2,
                'write': 1,
            }
        })

        # Wait for it.
        time.sleep(60)

        # Fetch fresh table desc from DynamoDB
        users.describe()

        # Assert if everything is fine so far
        self.assertEqual(len(users.global_indexes), 1)
        self.assertEqual(users.global_indexes[0].throughput['read'], 2)
        self.assertEqual(users.global_indexes[0].throughput['write'], 1)

        # Update a GSI throughput using the old fashion way for compatibility
        # purposes. it should work.
        users.update(global_indexes={
            'EmailGSIIndex': {
                'read': 3,
                'write': 2,
            }
        })

        # Wait for it.
        time.sleep(60)

        # Fetch fresh table desc from DynamoDB
        users.describe()

        # Assert if everything is fine so far
        self.assertEqual(len(users.global_indexes), 1)
        self.assertEqual(users.global_indexes[0].throughput['read'], 3)
        self.assertEqual(users.global_indexes[0].throughput['write'], 2)

        # Delete a GSI. it should work.
        users.delete_global_secondary_index('EmailGSIIndex')

        # Wait for it.
        time.sleep(60)

        # Fetch fresh table desc from DynamoDB
        users.describe()

        # Assert if everything is fine so far
        self.assertEqual(len(users.global_indexes), 0)

        # Create a GSI. it should work.
        users.create_global_secondary_index(
            global_index=GlobalAllIndex(
                'AddressGSIIndex', parts=[
                    HashKey('address', data_type=STRING)
                ], throughput={
                    'read': 1,
                    'write': 1,
                })
        )
        # Wait for it. This operation usually takes much longer than the others
        time.sleep(60*10)

        # Fetch fresh table desc from DynamoDB
        users.describe()

        # Assert if everything is fine so far
        self.assertEqual(len(users.global_indexes), 1)
        self.assertEqual(users.global_indexes[0].throughput['read'], 1)
        self.assertEqual(users.global_indexes[0].throughput['write'], 1)
