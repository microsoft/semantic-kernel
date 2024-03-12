import boto
from boto.dynamodb2 import exceptions
from boto.dynamodb2.fields import (HashKey, RangeKey,
                                   AllIndex, KeysOnlyIndex, IncludeIndex,
                                   GlobalAllIndex, GlobalKeysOnlyIndex,
                                   GlobalIncludeIndex)
from boto.dynamodb2.items import Item
from boto.dynamodb2.layer1 import DynamoDBConnection
from boto.dynamodb2.results import ResultSet, BatchGetResultSet
from boto.dynamodb2.types import (NonBooleanDynamizer, Dynamizer, FILTER_OPERATORS,
                                  QUERY_OPERATORS, STRING)
from boto.exception import JSONResponseError


class Table(object):
    """
    Interacts & models the behavior of a DynamoDB table.

    The ``Table`` object represents a set (or rough categorization) of
    records within DynamoDB. The important part is that all records within the
    table, while largely-schema-free, share the same schema & are essentially
    namespaced for use in your application. For example, you might have a
    ``users`` table or a ``forums`` table.
    """
    max_batch_get = 100

    _PROJECTION_TYPE_TO_INDEX = dict(
        global_indexes=dict(
            ALL=GlobalAllIndex,
            KEYS_ONLY=GlobalKeysOnlyIndex,
            INCLUDE=GlobalIncludeIndex,
        ), local_indexes=dict(
            ALL=AllIndex,
            KEYS_ONLY=KeysOnlyIndex,
            INCLUDE=IncludeIndex,
        )
    )

    def __init__(self, table_name, schema=None, throughput=None, indexes=None,
                 global_indexes=None, connection=None):
        """
        Sets up a new in-memory ``Table``.

        This is useful if the table already exists within DynamoDB & you simply
        want to use it for additional interactions. The only required parameter
        is the ``table_name``. However, under the hood, the object will call
        ``describe_table`` to determine the schema/indexes/throughput. You
        can avoid this extra call by passing in ``schema`` & ``indexes``.

        **IMPORTANT** - If you're creating a new ``Table`` for the first time,
        you should use the ``Table.create`` method instead, as it will
        persist the table structure to DynamoDB.

        Requires a ``table_name`` parameter, which should be a simple string
        of the name of the table.

        Optionally accepts a ``schema`` parameter, which should be a list of
        ``BaseSchemaField`` subclasses representing the desired schema.

        Optionally accepts a ``throughput`` parameter, which should be a
        dictionary. If provided, it should specify a ``read`` & ``write`` key,
        both of which should have an integer value associated with them.

        Optionally accepts a ``indexes`` parameter, which should be a list of
        ``BaseIndexField`` subclasses representing the desired indexes.

        Optionally accepts a ``global_indexes`` parameter, which should be a
        list of ``GlobalBaseIndexField`` subclasses representing the desired
        indexes.

        Optionally accepts a ``connection`` parameter, which should be a
        ``DynamoDBConnection`` instance (or subclass). This is primarily useful
        for specifying alternate connection parameters.

        Example::

            # The simple, it-already-exists case.
            >>> conn = Table('users')

            # The full, minimum-extra-calls case.
            >>> from boto import dynamodb2
            >>> users = Table('users', schema=[
            ...     HashKey('username'),
            ...     RangeKey('date_joined', data_type=NUMBER)
            ... ], throughput={
            ...     'read':20,
            ...     'write': 10,
            ... }, indexes=[
            ...     KeysOnlyIndex('MostRecentlyJoined', parts=[
            ...         HashKey('username')
            ...         RangeKey('date_joined')
            ...     ]),
            ... ], global_indexes=[
            ...     GlobalAllIndex('UsersByZipcode', parts=[
            ...         HashKey('zipcode'),
            ...         RangeKey('username'),
            ...     ],
            ...     throughput={
            ...       'read':10,
            ...       'write':10,
            ...     }),
            ... ], connection=dynamodb2.connect_to_region('us-west-2',
            ...     aws_access_key_id='key',
            ...     aws_secret_access_key='key',
            ... ))

        """
        self.table_name = table_name
        self.connection = connection
        self.throughput = {
            'read': 5,
            'write': 5,
        }
        self.schema = schema
        self.indexes = indexes
        self.global_indexes = global_indexes

        if self.connection is None:
            self.connection = DynamoDBConnection()

        if throughput is not None:
            self.throughput = throughput

        self._dynamizer = NonBooleanDynamizer()

    def use_boolean(self):
        self._dynamizer = Dynamizer()

    @classmethod
    def create(cls, table_name, schema, throughput=None, indexes=None,
               global_indexes=None, connection=None):
        """
        Creates a new table in DynamoDB & returns an in-memory ``Table`` object.

        This will setup a brand new table within DynamoDB. The ``table_name``
        must be unique for your AWS account. The ``schema`` is also required
        to define the key structure of the table.

        **IMPORTANT** - You should consider the usage pattern of your table
        up-front, as the schema can **NOT** be modified once the table is
        created, requiring the creation of a new table & migrating the data
        should you wish to revise it.

        **IMPORTANT** - If the table already exists in DynamoDB, additional
        calls to this method will result in an error. If you just need
        a ``Table`` object to interact with the existing table, you should
        just initialize a new ``Table`` object, which requires only the
        ``table_name``.

        Requires a ``table_name`` parameter, which should be a simple string
        of the name of the table.

        Requires a ``schema`` parameter, which should be a list of
        ``BaseSchemaField`` subclasses representing the desired schema.

        Optionally accepts a ``throughput`` parameter, which should be a
        dictionary. If provided, it should specify a ``read`` & ``write`` key,
        both of which should have an integer value associated with them.

        Optionally accepts a ``indexes`` parameter, which should be a list of
        ``BaseIndexField`` subclasses representing the desired indexes.

        Optionally accepts a ``global_indexes`` parameter, which should be a
        list of ``GlobalBaseIndexField`` subclasses representing the desired
        indexes.

        Optionally accepts a ``connection`` parameter, which should be a
        ``DynamoDBConnection`` instance (or subclass). This is primarily useful
        for specifying alternate connection parameters.

        Example::

            >>> users = Table.create('users', schema=[
            ...     HashKey('username'),
            ...     RangeKey('date_joined', data_type=NUMBER)
            ... ], throughput={
            ...     'read':20,
            ...     'write': 10,
            ... }, indexes=[
            ...     KeysOnlyIndex('MostRecentlyJoined', parts=[
            ...         HashKey('username'),
            ...         RangeKey('date_joined'),
            ... ]), global_indexes=[
            ...     GlobalAllIndex('UsersByZipcode', parts=[
            ...         HashKey('zipcode'),
            ...         RangeKey('username'),
            ...     ],
            ...     throughput={
            ...       'read':10,
            ...       'write':10,
            ...     }),
            ... ])

        """
        table = cls(table_name=table_name, connection=connection)
        table.schema = schema

        if throughput is not None:
            table.throughput = throughput

        if indexes is not None:
            table.indexes = indexes

        if global_indexes is not None:
            table.global_indexes = global_indexes

        # Prep the schema.
        raw_schema = []
        attr_defs = []
        seen_attrs = set()

        for field in table.schema:
            raw_schema.append(field.schema())
            # Build the attributes off what we know.
            seen_attrs.add(field.name)
            attr_defs.append(field.definition())

        raw_throughput = {
            'ReadCapacityUnits': int(table.throughput['read']),
            'WriteCapacityUnits': int(table.throughput['write']),
        }
        kwargs = {}

        kwarg_map = {
            'indexes': 'local_secondary_indexes',
            'global_indexes': 'global_secondary_indexes',
        }
        for index_attr in ('indexes', 'global_indexes'):
            table_indexes = getattr(table, index_attr)
            if table_indexes:
                raw_indexes = []
                for index_field in table_indexes:
                    raw_indexes.append(index_field.schema())
                    # Make sure all attributes specified in the indexes are
                    # added to the definition
                    for field in index_field.parts:
                        if field.name not in seen_attrs:
                            seen_attrs.add(field.name)
                            attr_defs.append(field.definition())

                kwargs[kwarg_map[index_attr]] = raw_indexes

        table.connection.create_table(
            table_name=table.table_name,
            attribute_definitions=attr_defs,
            key_schema=raw_schema,
            provisioned_throughput=raw_throughput,
            **kwargs
        )
        return table

    def _introspect_schema(self, raw_schema, raw_attributes=None):
        """
        Given a raw schema structure back from a DynamoDB response, parse
        out & build the high-level Python objects that represent them.
        """
        schema = []
        sane_attributes = {}

        if raw_attributes:
            for field in raw_attributes:
                sane_attributes[field['AttributeName']] = field['AttributeType']

        for field in raw_schema:
            data_type = sane_attributes.get(field['AttributeName'], STRING)

            if field['KeyType'] == 'HASH':
                schema.append(
                    HashKey(field['AttributeName'], data_type=data_type)
                )
            elif field['KeyType'] == 'RANGE':
                schema.append(
                    RangeKey(field['AttributeName'], data_type=data_type)
                )
            else:
                raise exceptions.UnknownSchemaFieldError(
                    "%s was seen, but is unknown. Please report this at "
                    "https://github.com/boto/boto/issues." % field['KeyType']
                )

        return schema

    def _introspect_all_indexes(self, raw_indexes, map_indexes_projection):
        """
        Given a raw index/global index structure back from a DynamoDB response,
        parse out & build the high-level Python objects that represent them.
        """
        indexes = []

        for field in raw_indexes:
            index_klass = map_indexes_projection.get('ALL')
            kwargs = {
                'parts': []
            }

            if field['Projection']['ProjectionType'] == 'ALL':
                index_klass = map_indexes_projection.get('ALL')
            elif field['Projection']['ProjectionType'] == 'KEYS_ONLY':
                index_klass = map_indexes_projection.get('KEYS_ONLY')
            elif field['Projection']['ProjectionType'] == 'INCLUDE':
                index_klass = map_indexes_projection.get('INCLUDE')
                kwargs['includes'] = field['Projection']['NonKeyAttributes']
            else:
                raise exceptions.UnknownIndexFieldError(
                    "%s was seen, but is unknown. Please report this at "
                    "https://github.com/boto/boto/issues." % \
                    field['Projection']['ProjectionType']
                )

            name = field['IndexName']
            kwargs['parts'] = self._introspect_schema(field['KeySchema'], None)
            indexes.append(index_klass(name, **kwargs))

        return indexes

    def _introspect_indexes(self, raw_indexes):
        """
        Given a raw index structure back from a DynamoDB response, parse
        out & build the high-level Python objects that represent them.
        """
        return self._introspect_all_indexes(
            raw_indexes, self._PROJECTION_TYPE_TO_INDEX.get('local_indexes'))

    def _introspect_global_indexes(self, raw_global_indexes):
        """
        Given a raw global index structure back from a DynamoDB response, parse
        out & build the high-level Python objects that represent them.
        """
        return self._introspect_all_indexes(
            raw_global_indexes,
            self._PROJECTION_TYPE_TO_INDEX.get('global_indexes'))

    def describe(self):
        """
        Describes the current structure of the table in DynamoDB.

        This information will be used to update the ``schema``, ``indexes``,
        ``global_indexes`` and ``throughput`` information on the ``Table``. Some
        calls, such as those involving creating keys or querying, will require
        this information to be populated.

        It also returns the full raw data structure from DynamoDB, in the
        event you'd like to parse out additional information (such as the
        ``ItemCount`` or usage information).

        Example::

            >>> users.describe()
            {
                # Lots of keys here...
            }
            >>> len(users.schema)
            2

        """
        result = self.connection.describe_table(self.table_name)

        # Blindly update throughput, since what's on DynamoDB's end is likely
        # more correct.
        raw_throughput = result['Table']['ProvisionedThroughput']
        self.throughput['read'] = int(raw_throughput['ReadCapacityUnits'])
        self.throughput['write'] = int(raw_throughput['WriteCapacityUnits'])

        if not self.schema:
            # Since we have the data, build the schema.
            raw_schema = result['Table'].get('KeySchema', [])
            raw_attributes = result['Table'].get('AttributeDefinitions', [])
            self.schema = self._introspect_schema(raw_schema, raw_attributes)

        if not self.indexes:
            # Build the index information as well.
            raw_indexes = result['Table'].get('LocalSecondaryIndexes', [])
            self.indexes = self._introspect_indexes(raw_indexes)

        # Build the global index information as well.
        raw_global_indexes = result['Table'].get('GlobalSecondaryIndexes', [])
        self.global_indexes = self._introspect_global_indexes(raw_global_indexes)

        # This is leaky.
        return result

    def update(self, throughput=None, global_indexes=None):
        """
        Updates table attributes and global indexes in DynamoDB.

        Optionally accepts a ``throughput`` parameter, which should be a
        dictionary. If provided, it should specify a ``read`` & ``write`` key,
        both of which should have an integer value associated with them.

        Optionally accepts a ``global_indexes`` parameter, which should be a
        dictionary. If provided, it should specify the index name, which is also
        a dict containing a ``read`` & ``write`` key, both of which
        should have an integer value associated with them. If you are writing
        new code, please use ``Table.update_global_secondary_index``.

        Returns ``True`` on success.

        Example::

            # For a read-heavier application...
            >>> users.update(throughput={
            ...     'read': 20,
            ...     'write': 10,
            ... })
            True

            # To also update the global index(es) throughput.
            >>> users.update(throughput={
            ...     'read': 20,
            ...     'write': 10,
            ... },
            ... global_secondary_indexes={
            ...     'TheIndexNameHere': {
            ...         'read': 15,
            ...         'write': 5,
            ...     }
            ... })
            True
        """

        data = None

        if throughput:
            self.throughput = throughput
            data = {
                'ReadCapacityUnits': int(self.throughput['read']),
                'WriteCapacityUnits': int(self.throughput['write']),
            }

        gsi_data = None

        if global_indexes:
            gsi_data = []

            for gsi_name, gsi_throughput in global_indexes.items():
                gsi_data.append({
                    "Update": {
                        "IndexName": gsi_name,
                        "ProvisionedThroughput": {
                            "ReadCapacityUnits": int(gsi_throughput['read']),
                            "WriteCapacityUnits": int(gsi_throughput['write']),
                        },
                    },
                })

        if throughput or global_indexes:
            self.connection.update_table(
                self.table_name,
                provisioned_throughput=data,
                global_secondary_index_updates=gsi_data,
            )

            return True
        else:
            msg = 'You need to provide either the throughput or the ' \
                  'global_indexes to update method'
            boto.log.error(msg)

            return False

    def create_global_secondary_index(self, global_index):
        """
        Creates a global index in DynamoDB after the table has been created.

        Requires a ``global_indexes`` parameter, which should be a
        ``GlobalBaseIndexField`` subclass representing the desired index.

        To update ``global_indexes`` information on the ``Table``, you'll need
        to call ``Table.describe``.

        Returns ``True`` on success.

        Example::

            # To create a global index
            >>> users.create_global_secondary_index(
            ...     global_index=GlobalAllIndex(
            ...         'TheIndexNameHere', parts=[
            ...             HashKey('requiredHashkey', data_type=STRING),
            ...             RangeKey('optionalRangeKey', data_type=STRING)
            ...         ],
            ...         throughput={
            ...             'read': 2,
            ...             'write': 1,
            ...         })
            ... )
            True

        """

        if global_index:
            gsi_data = []
            gsi_data_attr_def = []

            gsi_data.append({
                "Create": global_index.schema()
            })

            for attr_def in global_index.parts:
                gsi_data_attr_def.append(attr_def.definition())

            self.connection.update_table(
                self.table_name,
                global_secondary_index_updates=gsi_data,
                attribute_definitions=gsi_data_attr_def
            )

            return True
        else:
            msg = 'You need to provide the global_index to ' \
                  'create_global_secondary_index method'
            boto.log.error(msg)

            return False

    def delete_global_secondary_index(self, global_index_name):
        """
        Deletes a global index in DynamoDB after the table has been created.

        Requires a ``global_index_name`` parameter, which should be a simple
        string of the name of the global secondary index.

        To update ``global_indexes`` information on the ``Table``, you'll need
        to call ``Table.describe``.

        Returns ``True`` on success.

        Example::

            # To delete a global index
            >>> users.delete_global_secondary_index('TheIndexNameHere')
            True

        """

        if global_index_name:
            gsi_data = [
                {
                    "Delete": {
                        "IndexName": global_index_name
                    }
                }
            ]

            self.connection.update_table(
                self.table_name,
                global_secondary_index_updates=gsi_data,
            )

            return True
        else:
            msg = 'You need to provide the global index name to ' \
                  'delete_global_secondary_index method'
            boto.log.error(msg)

            return False

    def update_global_secondary_index(self, global_indexes):
        """
        Updates a global index(es) in DynamoDB after the table has been created.

        Requires a ``global_indexes`` parameter, which should be a
        dictionary. If provided, it should specify the index name, which is also
        a dict containing a ``read`` & ``write`` key, both of which
        should have an integer value associated with them.

        To update ``global_indexes`` information on the ``Table``, you'll need
        to call ``Table.describe``.

        Returns ``True`` on success.

        Example::

            # To update a global index
            >>> users.update_global_secondary_index(global_indexes={
            ...     'TheIndexNameHere': {
            ...         'read': 15,
            ...         'write': 5,
            ...     }
            ... })
            True

        """

        if global_indexes:
            gsi_data = []

            for gsi_name, gsi_throughput in global_indexes.items():
                gsi_data.append({
                    "Update": {
                        "IndexName": gsi_name,
                        "ProvisionedThroughput": {
                            "ReadCapacityUnits": int(gsi_throughput['read']),
                            "WriteCapacityUnits": int(gsi_throughput['write']),
                        },
                    },
                })

            self.connection.update_table(
                self.table_name,
                global_secondary_index_updates=gsi_data,
            )
            return True
        else:
            msg = 'You need to provide the global indexes to ' \
                  'update_global_secondary_index method'
            boto.log.error(msg)

            return False

    def delete(self):
        """
        Deletes a table in DynamoDB.

        **IMPORTANT** - Be careful when using this method, there is no undo.

        Returns ``True`` on success.

        Example::

            >>> users.delete()
            True

        """
        self.connection.delete_table(self.table_name)
        return True

    def _encode_keys(self, keys):
        """
        Given a flat Python dictionary of keys/values, converts it into the
        nested dictionary DynamoDB expects.

        Converts::

            {
                'username': 'john',
                'tags': [1, 2, 5],
            }

        ...to...::

            {
                'username': {'S': 'john'},
                'tags': {'NS': ['1', '2', '5']},
            }

        """
        raw_key = {}

        for key, value in keys.items():
            raw_key[key] = self._dynamizer.encode(value)

        return raw_key

    def get_item(self, consistent=False, attributes=None, **kwargs):
        """
        Fetches an item (record) from a table in DynamoDB.

        To specify the key of the item you'd like to get, you can specify the
        key attributes as kwargs.

        Optionally accepts a ``consistent`` parameter, which should be a
        boolean. If you provide ``True``, it will perform
        a consistent (but more expensive) read from DynamoDB.
        (Default: ``False``)

        Optionally accepts an ``attributes`` parameter, which should be a
        list of fieldname to fetch. (Default: ``None``, which means all fields
        should be fetched)

        Returns an ``Item`` instance containing all the data for that record.

        Raises an ``ItemNotFound`` exception if the item is not found.

        Example::

            # A simple hash key.
            >>> john = users.get_item(username='johndoe')
            >>> john['first_name']
            'John'

            # A complex hash+range key.
            >>> john = users.get_item(username='johndoe', last_name='Doe')
            >>> john['first_name']
            'John'

            # A consistent read (assuming the data might have just changed).
            >>> john = users.get_item(username='johndoe', consistent=True)
            >>> john['first_name']
            'Johann'

            # With a key that is an invalid variable name in Python.
            # Also, assumes a different schema than previous examples.
            >>> john = users.get_item(**{
            ...     'date-joined': 127549192,
            ... })
            >>> john['first_name']
            'John'

        """
        raw_key = self._encode_keys(kwargs)
        item_data = self.connection.get_item(
            self.table_name,
            raw_key,
            attributes_to_get=attributes,
            consistent_read=consistent
        )
        if 'Item' not in item_data:
            raise exceptions.ItemNotFound("Item %s couldn't be found." % kwargs)
        item = Item(self)
        item.load(item_data)
        return item

    def has_item(self, **kwargs):
        """
        Return whether an item (record) exists within a table in DynamoDB.

        To specify the key of the item you'd like to get, you can specify the
        key attributes as kwargs.

        Optionally accepts a ``consistent`` parameter, which should be a
        boolean. If you provide ``True``, it will perform
        a consistent (but more expensive) read from DynamoDB.
        (Default: ``False``)

        Optionally accepts an ``attributes`` parameter, which should be a
        list of fieldnames to fetch. (Default: ``None``, which means all fields
        should be fetched)

        Returns ``True`` if an ``Item`` is present, ``False`` if not.

        Example::

            # Simple, just hash-key schema.
            >>> users.has_item(username='johndoe')
            True

            # Complex schema, item not present.
            >>> users.has_item(
            ...     username='johndoe',
            ...     date_joined='2014-01-07'
            ... )
            False

        """
        try:
            self.get_item(**kwargs)
        except (JSONResponseError, exceptions.ItemNotFound):
            return False

        return True

    def lookup(self, *args, **kwargs):
        """
        Look up an entry in DynamoDB. This is mostly backwards compatible
        with boto.dynamodb. Unlike get_item, it takes hash_key and range_key first,
        although you may still specify keyword arguments instead.

        Also unlike the get_item command, if the returned item has no keys
        (i.e., it does not exist in DynamoDB), a None result is returned, instead
        of an empty key object.

        Example::
            >>> user = users.lookup(username)
            >>> user = users.lookup(username, consistent=True)
            >>> app = apps.lookup('my_customer_id', 'my_app_id')

        """
        if not self.schema:
            self.describe()
        for x, arg in enumerate(args):
            kwargs[self.schema[x].name] = arg
        ret = self.get_item(**kwargs)
        if not ret.keys():
            return None
        return ret

    def new_item(self, *args):
        """
        Returns a new, blank item

        This is mostly for consistency with boto.dynamodb
        """
        if not self.schema:
            self.describe()
        data = {}
        for x, arg in enumerate(args):
            data[self.schema[x].name] = arg
        return Item(self, data=data)

    def put_item(self, data, overwrite=False):
        """
        Saves an entire item to DynamoDB.

        By default, if any part of the ``Item``'s original data doesn't match
        what's currently in DynamoDB, this request will fail. This prevents
        other processes from updating the data in between when you read the
        item & when your request to update the item's data is processed, which
        would typically result in some data loss.

        Requires a ``data`` parameter, which should be a dictionary of the data
        you'd like to store in DynamoDB.

        Optionally accepts an ``overwrite`` parameter, which should be a
        boolean. If you provide ``True``, this will tell DynamoDB to blindly
        overwrite whatever data is present, if any.

        Returns ``True`` on success.

        Example::

            >>> users.put_item(data={
            ...     'username': 'jane',
            ...     'first_name': 'Jane',
            ...     'last_name': 'Doe',
            ...     'date_joined': 126478915,
            ... })
            True

        """
        item = Item(self, data=data)
        return item.save(overwrite=overwrite)

    def _put_item(self, item_data, expects=None):
        """
        The internal variant of ``put_item`` (full data). This is used by the
        ``Item`` objects, since that operation is represented at the
        table-level by the API, but conceptually maps better to telling an
        individual ``Item`` to save itself.
        """
        kwargs = {}

        if expects is not None:
            kwargs['expected'] = expects

        self.connection.put_item(self.table_name, item_data, **kwargs)
        return True

    def _update_item(self, key, item_data, expects=None):
        """
        The internal variant of ``put_item`` (partial data). This is used by the
        ``Item`` objects, since that operation is represented at the
        table-level by the API, but conceptually maps better to telling an
        individual ``Item`` to save itself.
        """
        raw_key = self._encode_keys(key)
        kwargs = {}

        if expects is not None:
            kwargs['expected'] = expects

        self.connection.update_item(self.table_name, raw_key, item_data, **kwargs)
        return True

    def delete_item(self, expected=None, conditional_operator=None, **kwargs):
        """
        Deletes a single item. You can perform a conditional delete operation
        that deletes the item if it exists, or if it has an expected attribute
        value.

        Conditional deletes are useful for only deleting items if specific
        conditions are met. If those conditions are met, DynamoDB performs
        the delete. Otherwise, the item is not deleted.

        To specify the expected attribute values of the item, you can pass a
        dictionary of conditions to ``expected``. Each condition should follow
        the pattern ``<attributename>__<comparison_operator>=<value_to_expect>``.

        **IMPORTANT** - Be careful when using this method, there is no undo.

        To specify the key of the item you'd like to get, you can specify the
        key attributes as kwargs.

        Optionally accepts an ``expected`` parameter which is a dictionary of
        expected attribute value conditions.

        Optionally accepts a ``conditional_operator`` which applies to the
        expected attribute value conditions:

        + `AND` - If all of the conditions evaluate to true (default)
        + `OR` - True if at least one condition evaluates to true

        Returns ``True`` on success, ``False`` on failed conditional delete.

        Example::

            # A simple hash key.
            >>> users.delete_item(username='johndoe')
            True

            # A complex hash+range key.
            >>> users.delete_item(username='jane', last_name='Doe')
            True

            # With a key that is an invalid variable name in Python.
            # Also, assumes a different schema than previous examples.
            >>> users.delete_item(**{
            ...     'date-joined': 127549192,
            ... })
            True

            # Conditional delete
            >>> users.delete_item(username='johndoe',
            ...                   expected={'balance__eq': 0})
            True
        """
        expected = self._build_filters(expected, using=FILTER_OPERATORS)
        raw_key = self._encode_keys(kwargs)

        try:
            self.connection.delete_item(self.table_name, raw_key,
                                        expected=expected,
                                        conditional_operator=conditional_operator)
        except exceptions.ConditionalCheckFailedException:
            return False

        return True

    def get_key_fields(self):
        """
        Returns the fields necessary to make a key for a table.

        If the ``Table`` does not already have a populated ``schema``,
        this will request it via a ``Table.describe`` call.

        Returns a list of fieldnames (strings).

        Example::

            # A simple hash key.
            >>> users.get_key_fields()
            ['username']

            # A complex hash+range key.
            >>> users.get_key_fields()
            ['username', 'last_name']

        """
        if not self.schema:
            # We don't know the structure of the table. Get a description to
            # populate the schema.
            self.describe()

        return [field.name for field in self.schema]

    def batch_write(self):
        """
        Allows the batching of writes to DynamoDB.

        Since each write/delete call to DynamoDB has a cost associated with it,
        when loading lots of data, it makes sense to batch them, creating as
        few calls as possible.

        This returns a context manager that will transparently handle creating
        these batches. The object you get back lightly-resembles a ``Table``
        object, sharing just the ``put_item`` & ``delete_item`` methods
        (which are all that DynamoDB can batch in terms of writing data).

        DynamoDB's maximum batch size is 25 items per request. If you attempt
        to put/delete more than that, the context manager will batch as many
        as it can up to that number, then flush them to DynamoDB & continue
        batching as more calls come in.

        Example::

            # Assuming a table with one record...
            >>> with users.batch_write() as batch:
            ...     batch.put_item(data={
            ...         'username': 'johndoe',
            ...         'first_name': 'John',
            ...         'last_name': 'Doe',
            ...         'owner': 1,
            ...     })
            ...     # Nothing across the wire yet.
            ...     batch.delete_item(username='bob')
            ...     # Still no requests sent.
            ...     batch.put_item(data={
            ...         'username': 'jane',
            ...         'first_name': 'Jane',
            ...         'last_name': 'Doe',
            ...         'date_joined': 127436192,
            ...     })
            ...     # Nothing yet, but once we leave the context, the
            ...     # put/deletes will be sent.

        """
        # PHENOMENAL COSMIC DOCS!!! itty-bitty code.
        return BatchTable(self)

    def _build_filters(self, filter_kwargs, using=QUERY_OPERATORS):
        """
        An internal method for taking query/scan-style ``**kwargs`` & turning
        them into the raw structure DynamoDB expects for filtering.
        """
        if filter_kwargs is None:
            return

        filters = {}

        for field_and_op, value in filter_kwargs.items():
            field_bits = field_and_op.split('__')
            fieldname = '__'.join(field_bits[:-1])

            try:
                op = using[field_bits[-1]]
            except KeyError:
                raise exceptions.UnknownFilterTypeError(
                    "Operator '%s' from '%s' is not recognized." % (
                        field_bits[-1],
                        field_and_op
                    )
                )

            lookup = {
                'AttributeValueList': [],
                'ComparisonOperator': op,
            }

            # Special-case the ``NULL/NOT_NULL`` case.
            if field_bits[-1] == 'null':
                del lookup['AttributeValueList']

                if value is False:
                    lookup['ComparisonOperator'] = 'NOT_NULL'
                else:
                    lookup['ComparisonOperator'] = 'NULL'
            # Special-case the ``BETWEEN`` case.
            elif field_bits[-1] == 'between':
                if len(value) == 2 and isinstance(value, (list, tuple)):
                    lookup['AttributeValueList'].append(
                        self._dynamizer.encode(value[0])
                    )
                    lookup['AttributeValueList'].append(
                        self._dynamizer.encode(value[1])
                    )
            # Special-case the ``IN`` case
            elif field_bits[-1] == 'in':
                for val in value:
                    lookup['AttributeValueList'].append(self._dynamizer.encode(val))
            else:
                # Fix up the value for encoding, because it was built to only work
                # with ``set``s.
                if isinstance(value, (list, tuple)):
                    value = set(value)
                lookup['AttributeValueList'].append(
                    self._dynamizer.encode(value)
                )

            # Finally, insert it into the filters.
            filters[fieldname] = lookup

        return filters

    def query(self, limit=None, index=None, reverse=False, consistent=False,
              attributes=None, max_page_size=None, **filter_kwargs):
        """
        **WARNING:** This method is provided **strictly** for
        backward-compatibility. It returns results in an incorrect order.

        If you are writing new code, please use ``Table.query_2``.
        """
        reverse = not reverse
        return self.query_2(limit=limit, index=index, reverse=reverse,
                            consistent=consistent, attributes=attributes,
                            max_page_size=max_page_size, **filter_kwargs)

    def query_2(self, limit=None, index=None, reverse=False,
                consistent=False, attributes=None, max_page_size=None,
                query_filter=None, conditional_operator=None,
                **filter_kwargs):
        """
        Queries for a set of matching items in a DynamoDB table.

        Queries can be performed against a hash key, a hash+range key or
        against any data stored in your local secondary indexes. Query filters
        can be used to filter on arbitrary fields.

        **Note** - You can not query against arbitrary fields within the data
        stored in DynamoDB unless you specify ``query_filter`` values.

        To specify the filters of the items you'd like to get, you can specify
        the filters as kwargs. Each filter kwarg should follow the pattern
        ``<fieldname>__<filter_operation>=<value_to_look_for>``. Query filters
        are specified in the same way.

        Optionally accepts a ``limit`` parameter, which should be an integer
        count of the total number of items to return. (Default: ``None`` -
        all results)

        Optionally accepts an ``index`` parameter, which should be a string of
        name of the local secondary index you want to query against.
        (Default: ``None``)

        Optionally accepts a ``reverse`` parameter, which will present the
        results in reverse order. (Default: ``False`` - normal order)

        Optionally accepts a ``consistent`` parameter, which should be a
        boolean. If you provide ``True``, it will force a consistent read of
        the data (more expensive). (Default: ``False`` - use eventually
        consistent reads)

        Optionally accepts a ``attributes`` parameter, which should be a
        tuple. If you provide any attributes only these will be fetched
        from DynamoDB. This uses the ``AttributesToGet`` and set's
        ``Select`` to ``SPECIFIC_ATTRIBUTES`` API.

        Optionally accepts a ``max_page_size`` parameter, which should be an
        integer count of the maximum number of items to retrieve
        **per-request**. This is useful in making faster requests & prevent
        the scan from drowning out other queries. (Default: ``None`` -
        fetch as many as DynamoDB will return)

        Optionally accepts a ``query_filter`` which is a dictionary of filter
        conditions against any arbitrary field in the returned data.

        Optionally accepts a ``conditional_operator`` which applies to the
        query filter conditions:

        + `AND` - True if all filter conditions evaluate to true (default)
        + `OR` - True if at least one filter condition evaluates to true

        Returns a ``ResultSet`` containing ``Item``s, which transparently handles the pagination of
        results you get back.

        Example::

            # Look for last names equal to "Doe".
            >>> results = users.query(last_name__eq='Doe')
            >>> for res in results:
            ...     print res['first_name']
            'John'
            'Jane'

            # Look for last names beginning with "D", in reverse order, limit 3.
            >>> results = users.query(
            ...     last_name__beginswith='D',
            ...     reverse=True,
            ...     limit=3
            ... )
            >>> for res in results:
            ...     print res['first_name']
            'Alice'
            'Jane'
            'John'

            # Use an LSI & a consistent read.
            >>> results = users.query(
            ...     date_joined__gte=1236451000,
            ...     owner__eq=1,
            ...     index='DateJoinedIndex',
            ...     consistent=True
            ... )
            >>> for res in results:
            ...     print res['first_name']
            'Alice'
            'Bob'
            'John'
            'Fred'

            # Filter by non-indexed field(s)
            >>> results = users.query(
            ...     last_name__eq='Doe',
            ...     reverse=True,
            ...     query_filter={
            ...         'first_name__beginswith': 'A'
            ...     }
            ... )
            >>> for res in results:
            ...     print res['first_name'] + ' ' + res['last_name']
            'Alice Doe'

        """
        if self.schema:
            if len(self.schema) == 1:
                if len(filter_kwargs) <= 1:
                    if not self.global_indexes or not len(self.global_indexes):
                        # If the schema only has one field, there's <= 1 filter
                        # param & no Global Secondary Indexes, this is user
                        # error. Bail early.
                        raise exceptions.QueryError(
                            "You must specify more than one key to filter on."
                        )

        if attributes is not None:
            select = 'SPECIFIC_ATTRIBUTES'
        else:
            select = None

        results = ResultSet(
            max_page_size=max_page_size
        )
        kwargs = filter_kwargs.copy()
        kwargs.update({
            'limit': limit,
            'index': index,
            'reverse': reverse,
            'consistent': consistent,
            'select': select,
            'attributes_to_get': attributes,
            'query_filter': query_filter,
            'conditional_operator': conditional_operator,
        })
        results.to_call(self._query, **kwargs)
        return results

    def query_count(self, index=None, consistent=False, conditional_operator=None,
                    query_filter=None, scan_index_forward=True, limit=None,
                    exclusive_start_key=None, **filter_kwargs):
        """
        Queries the exact count of matching items in a DynamoDB table.

        Queries can be performed against a hash key, a hash+range key or
        against any data stored in your local secondary indexes. Query filters
        can be used to filter on arbitrary fields.

        To specify the filters of the items you'd like to get, you can specify
        the filters as kwargs. Each filter kwarg should follow the pattern
        ``<fieldname>__<filter_operation>=<value_to_look_for>``. Query filters
        are specified in the same way.

        Optionally accepts an ``index`` parameter, which should be a string of
        name of the local secondary index you want to query against.
        (Default: ``None``)

        Optionally accepts a ``consistent`` parameter, which should be a
        boolean. If you provide ``True``, it will force a consistent read of
        the data (more expensive). (Default: ``False`` - use eventually
        consistent reads)

        Optionally accepts a ``query_filter`` which is a dictionary of filter
        conditions against any arbitrary field in the returned data.

        Optionally accepts a ``conditional_operator`` which applies to the
        query filter conditions:

        + `AND` - True if all filter conditions evaluate to true (default)
        + `OR` - True if at least one filter condition evaluates to true

        Optionally accept a ``exclusive_start_key`` which is used to get
        the remaining items when a query cannot return the complete count.

        Returns an integer which represents the exact amount of matched
        items.

        :type scan_index_forward: boolean
        :param scan_index_forward: Specifies ascending (true) or descending
            (false) traversal of the index. DynamoDB returns results reflecting
            the requested order determined by the range key. If the data type
            is Number, the results are returned in numeric order. For String,
            the results are returned in order of ASCII character code values.
            For Binary, DynamoDB treats each byte of the binary data as
            unsigned when it compares binary values.

        If ScanIndexForward is not specified, the results are returned in
            ascending order.

        :type limit: integer
        :param limit: The maximum number of items to evaluate (not necessarily
            the number of matching items).

        Example::

            # Look for last names equal to "Doe".
            >>> users.query_count(last_name__eq='Doe')
            5

            # Use an LSI & a consistent read.
            >>> users.query_count(
            ...     date_joined__gte=1236451000,
            ...     owner__eq=1,
            ...     index='DateJoinedIndex',
            ...     consistent=True
            ... )
            2

        """
        key_conditions = self._build_filters(
            filter_kwargs,
            using=QUERY_OPERATORS
        )

        built_query_filter = self._build_filters(
            query_filter,
            using=FILTER_OPERATORS
        )

        count_buffer = 0
        last_evaluated_key = exclusive_start_key

        while True:
            raw_results = self.connection.query(
                self.table_name,
                index_name=index,
                consistent_read=consistent,
                select='COUNT',
                key_conditions=key_conditions,
                query_filter=built_query_filter,
                conditional_operator=conditional_operator,
                limit=limit,
                scan_index_forward=scan_index_forward,
                exclusive_start_key=last_evaluated_key
            )

            count_buffer += int(raw_results.get('Count', 0))
            last_evaluated_key = raw_results.get('LastEvaluatedKey')
            if not last_evaluated_key or count_buffer < 1:
                break

        return count_buffer

    def _query(self, limit=None, index=None, reverse=False, consistent=False,
               exclusive_start_key=None, select=None, attributes_to_get=None,
               query_filter=None, conditional_operator=None, **filter_kwargs):
        """
        The internal method that performs the actual queries. Used extensively
        by ``ResultSet`` to perform each (paginated) request.
        """
        kwargs = {
            'limit': limit,
            'index_name': index,
            'consistent_read': consistent,
            'select': select,
            'attributes_to_get': attributes_to_get,
            'conditional_operator': conditional_operator,
        }

        if reverse:
            kwargs['scan_index_forward'] = False

        if exclusive_start_key:
            kwargs['exclusive_start_key'] = {}

            for key, value in exclusive_start_key.items():
                kwargs['exclusive_start_key'][key] = \
                    self._dynamizer.encode(value)

        # Convert the filters into something we can actually use.
        kwargs['key_conditions'] = self._build_filters(
            filter_kwargs,
            using=QUERY_OPERATORS
        )

        kwargs['query_filter'] = self._build_filters(
            query_filter,
            using=FILTER_OPERATORS
        )

        raw_results = self.connection.query(
            self.table_name,
            **kwargs
        )
        results = []
        last_key = None

        for raw_item in raw_results.get('Items', []):
            item = Item(self)
            item.load({
                'Item': raw_item,
            })
            results.append(item)

        if raw_results.get('LastEvaluatedKey', None):
            last_key = {}

            for key, value in raw_results['LastEvaluatedKey'].items():
                last_key[key] = self._dynamizer.decode(value)

        return {
            'results': results,
            'last_key': last_key,
        }

    def scan(self, limit=None, segment=None, total_segments=None,
             max_page_size=None, attributes=None, conditional_operator=None,
             **filter_kwargs):
        """
        Scans across all items within a DynamoDB table.

        Scans can be performed against a hash key or a hash+range key. You can
        additionally filter the results after the table has been read but
        before the response is returned by using query filters.

        To specify the filters of the items you'd like to get, you can specify
        the filters as kwargs. Each filter kwarg should follow the pattern
        ``<fieldname>__<filter_operation>=<value_to_look_for>``.

        Optionally accepts a ``limit`` parameter, which should be an integer
        count of the total number of items to return. (Default: ``None`` -
        all results)

        Optionally accepts a ``segment`` parameter, which should be an integer
        of the segment to retrieve on. Please see the documentation about
        Parallel Scans (Default: ``None`` - no segments)

        Optionally accepts a ``total_segments`` parameter, which should be an
        integer count of number of segments to divide the table into.
        Please see the documentation about Parallel Scans (Default: ``None`` -
        no segments)

        Optionally accepts a ``max_page_size`` parameter, which should be an
        integer count of the maximum number of items to retrieve
        **per-request**. This is useful in making faster requests & prevent
        the scan from drowning out other queries. (Default: ``None`` -
        fetch as many as DynamoDB will return)

        Optionally accepts an ``attributes`` parameter, which should be a
        tuple. If you provide any attributes only these will be fetched
        from DynamoDB. This uses the ``AttributesToGet`` and set's
        ``Select`` to ``SPECIFIC_ATTRIBUTES`` API.

        Returns a ``ResultSet``, which transparently handles the pagination of
        results you get back.

        Example::

            # All results.
            >>> everything = users.scan()

            # Look for last names beginning with "D".
            >>> results = users.scan(last_name__beginswith='D')
            >>> for res in results:
            ...     print res['first_name']
            'Alice'
            'John'
            'Jane'

            # Use an ``IN`` filter & limit.
            >>> results = users.scan(
            ...     age__in=[25, 26, 27, 28, 29],
            ...     limit=1
            ... )
            >>> for res in results:
            ...     print res['first_name']
            'Alice'

        """
        results = ResultSet(
            max_page_size=max_page_size
        )
        kwargs = filter_kwargs.copy()
        kwargs.update({
            'limit': limit,
            'segment': segment,
            'total_segments': total_segments,
            'attributes': attributes,
            'conditional_operator': conditional_operator,
        })
        results.to_call(self._scan, **kwargs)
        return results

    def _scan(self, limit=None, exclusive_start_key=None, segment=None,
              total_segments=None, attributes=None, conditional_operator=None,
              **filter_kwargs):
        """
        The internal method that performs the actual scan. Used extensively
        by ``ResultSet`` to perform each (paginated) request.
        """
        kwargs = {
            'limit': limit,
            'segment': segment,
            'total_segments': total_segments,
            'attributes_to_get': attributes,
            'conditional_operator': conditional_operator,
        }

        if exclusive_start_key:
            kwargs['exclusive_start_key'] = {}

            for key, value in exclusive_start_key.items():
                kwargs['exclusive_start_key'][key] = \
                    self._dynamizer.encode(value)

        # Convert the filters into something we can actually use.
        kwargs['scan_filter'] = self._build_filters(
            filter_kwargs,
            using=FILTER_OPERATORS
        )

        raw_results = self.connection.scan(
            self.table_name,
            **kwargs
        )
        results = []
        last_key = None

        for raw_item in raw_results.get('Items', []):
            item = Item(self)
            item.load({
                'Item': raw_item,
            })
            results.append(item)

        if raw_results.get('LastEvaluatedKey', None):
            last_key = {}

            for key, value in raw_results['LastEvaluatedKey'].items():
                last_key[key] = self._dynamizer.decode(value)

        return {
            'results': results,
            'last_key': last_key,
        }

    def batch_get(self, keys, consistent=False, attributes=None):
        """
        Fetches many specific items in batch from a table.

        Requires a ``keys`` parameter, which should be a list of dictionaries.
        Each dictionary should consist of the keys values to specify.

        Optionally accepts a ``consistent`` parameter, which should be a
        boolean. If you provide ``True``, a strongly consistent read will be
        used. (Default: False)

        Optionally accepts an ``attributes`` parameter, which should be a
        tuple. If you provide any attributes only these will be fetched
        from DynamoDB.

        Returns a ``ResultSet``, which transparently handles the pagination of
        results you get back.

        Example::

            >>> results = users.batch_get(keys=[
            ...     {
            ...         'username': 'johndoe',
            ...     },
            ...     {
            ...         'username': 'jane',
            ...     },
            ...     {
            ...         'username': 'fred',
            ...     },
            ... ])
            >>> for res in results:
            ...     print res['first_name']
            'John'
            'Jane'
            'Fred'

        """
        # We pass the keys to the constructor instead, so it can maintain it's
        # own internal state as to what keys have been processed.
        results = BatchGetResultSet(keys=keys, max_batch_get=self.max_batch_get)
        results.to_call(self._batch_get, consistent=consistent, attributes=attributes)
        return results

    def _batch_get(self, keys, consistent=False, attributes=None):
        """
        The internal method that performs the actual batch get. Used extensively
        by ``BatchGetResultSet`` to perform each (paginated) request.
        """
        items = {
            self.table_name: {
                'Keys': [],
            },
        }

        if consistent:
            items[self.table_name]['ConsistentRead'] = True

        if attributes is not None:
            items[self.table_name]['AttributesToGet'] = attributes

        for key_data in keys:
            raw_key = {}

            for key, value in key_data.items():
                raw_key[key] = self._dynamizer.encode(value)

            items[self.table_name]['Keys'].append(raw_key)

        raw_results = self.connection.batch_get_item(request_items=items)
        results = []
        unprocessed_keys = []

        for raw_item in raw_results['Responses'].get(self.table_name, []):
            item = Item(self)
            item.load({
                'Item': raw_item,
            })
            results.append(item)

        raw_unprocessed = raw_results.get('UnprocessedKeys', {}).get(self.table_name, {})

        for raw_key in raw_unprocessed.get('Keys', []):
            py_key = {}

            for key, value in raw_key.items():
                py_key[key] = self._dynamizer.decode(value)

            unprocessed_keys.append(py_key)

        return {
            'results': results,
            # NEVER return a ``last_key``. Just in-case any part of
            # ``ResultSet`` peeks through, since much of the
            # original underlying implementation is based on this key.
            'last_key': None,
            'unprocessed_keys': unprocessed_keys,
        }

    def count(self):
        """
        Returns a (very) eventually consistent count of the number of items
        in a table.

        Lag time is about 6 hours, so don't expect a high degree of accuracy.

        Example::

            >>> users.count()
            6

        """
        info = self.describe()
        return info['Table'].get('ItemCount', 0)


class BatchTable(object):
    """
    Used by ``Table`` as the context manager for batch writes.

    You likely don't want to try to use this object directly.
    """
    def __init__(self, table):
        self.table = table
        self._to_put = []
        self._to_delete = []
        self._unprocessed = []

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self._to_put or self._to_delete:
            # Flush anything that's left.
            self.flush()

        if self._unprocessed:
            # Finally, handle anything that wasn't processed.
            self.resend_unprocessed()

    def put_item(self, data, overwrite=False):
        self._to_put.append(data)

        if self.should_flush():
            self.flush()

    def delete_item(self, **kwargs):
        self._to_delete.append(kwargs)

        if self.should_flush():
            self.flush()

    def should_flush(self):
        if len(self._to_put) + len(self._to_delete) == 25:
            return True

        return False

    def flush(self):
        batch_data = {
            self.table.table_name: [
                # We'll insert data here shortly.
            ],
        }

        for put in self._to_put:
            item = Item(self.table, data=put)
            batch_data[self.table.table_name].append({
                'PutRequest': {
                    'Item': item.prepare_full(),
                }
            })

        for delete in self._to_delete:
            batch_data[self.table.table_name].append({
                'DeleteRequest': {
                    'Key': self.table._encode_keys(delete),
                }
            })

        resp = self.table.connection.batch_write_item(batch_data)
        self.handle_unprocessed(resp)

        self._to_put = []
        self._to_delete = []
        return True

    def handle_unprocessed(self, resp):
        if len(resp.get('UnprocessedItems', [])):
            table_name = self.table.table_name
            unprocessed = resp['UnprocessedItems'].get(table_name, [])

            # Some items have not been processed. Stow them for now &
            # re-attempt processing on ``__exit__``.
            msg = "%s items were unprocessed. Storing for later."
            boto.log.info(msg % len(unprocessed))
            self._unprocessed.extend(unprocessed)

    def resend_unprocessed(self):
        # If there are unprocessed records (for instance, the user was over
        # their throughput limitations), iterate over them & send until they're
        # all there.
        boto.log.info(
            "Re-sending %s unprocessed items." % len(self._unprocessed)
        )

        while len(self._unprocessed):
            # Again, do 25 at a time.
            to_resend = self._unprocessed[:25]
            # Remove them from the list.
            self._unprocessed = self._unprocessed[25:]
            batch_data = {
                self.table.table_name: to_resend
            }
            boto.log.info("Sending %s items" % len(to_resend))
            resp = self.table.connection.batch_write_item(batch_data)
            self.handle_unprocessed(resp)
            boto.log.info(
                "%s unprocessed items left" % len(self._unprocessed)
            )
