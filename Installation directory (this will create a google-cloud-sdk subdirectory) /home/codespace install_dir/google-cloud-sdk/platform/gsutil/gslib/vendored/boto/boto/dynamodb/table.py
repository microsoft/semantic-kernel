# Copyright (c) 2012 Mitch Garnaat http://garnaat.org/
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

from boto.dynamodb.batch import BatchList
from boto.dynamodb.schema import Schema
from boto.dynamodb.item import Item
from boto.dynamodb import exceptions as dynamodb_exceptions
import time


class TableBatchGenerator(object):
    """
    A low-level generator used to page through results from
    batch_get_item operations.

    :ivar consumed_units: An integer that holds the number of
        ConsumedCapacityUnits accumulated thus far for this
        generator.
    """

    def __init__(self, table, keys, attributes_to_get=None,
                 consistent_read=False):
        self.table = table
        self.keys = keys
        self.consumed_units = 0
        self.attributes_to_get = attributes_to_get
        self.consistent_read = consistent_read

    def _queue_unprocessed(self, res):
        if u'UnprocessedKeys' not in res:
            return
        if self.table.name not in res[u'UnprocessedKeys']:
            return

        keys = res[u'UnprocessedKeys'][self.table.name][u'Keys']

        for key in keys:
            h = key[u'HashKeyElement']
            r = key[u'RangeKeyElement'] if u'RangeKeyElement' in key else None
            self.keys.append((h, r))

    def __iter__(self):
        while self.keys:
            # Build the next batch
            batch = BatchList(self.table.layer2)
            batch.add_batch(self.table, self.keys[:100],
                            self.attributes_to_get)
            res = batch.submit()

            # parse the results
            if self.table.name not in res[u'Responses']:
                continue
            self.consumed_units += res[u'Responses'][self.table.name][u'ConsumedCapacityUnits']
            for elem in res[u'Responses'][self.table.name][u'Items']:
                yield elem

            # re-queue un processed keys
            self.keys = self.keys[100:]
            self._queue_unprocessed(res)


class Table(object):
    """
    An Amazon DynamoDB table.

    :ivar name: The name of the table.
    :ivar create_time: The date and time that the table was created.
    :ivar status: The current status of the table.  One of:
        'ACTIVE', 'UPDATING', 'DELETING'.
    :ivar schema: A :class:`boto.dynamodb.schema.Schema` object representing
        the schema defined for the table.
    :ivar item_count: The number of items in the table.  This value is
        set only when the Table object is created or refreshed and
        may not reflect the actual count.
    :ivar size_bytes: Total size of the specified table, in bytes.
        Amazon DynamoDB updates this value approximately every six hours.
        Recent changes might not be reflected in this value.
    :ivar read_units: The ReadCapacityUnits of the tables
        Provisioned Throughput.
    :ivar write_units: The WriteCapacityUnits of the tables
        Provisioned Throughput.
    :ivar schema: The Schema object associated with the table.
    """

    def __init__(self, layer2, response):
        """

        :type layer2: :class:`boto.dynamodb.layer2.Layer2`
        :param layer2: A `Layer2` api object.

        :type response: dict
        :param response: The output of
            `boto.dynamodb.layer1.Layer1.describe_table`.

        """
        self.layer2 = layer2
        self._dict = {}
        self.update_from_response(response)

    @classmethod
    def create_from_schema(cls, layer2, name, schema):
        """Create a Table object.

        If you know the name and schema of your table, you can
        create a ``Table`` object without having to make any
        API calls (normally an API call is made to retrieve
        the schema of a table).

        Example usage::

            table = Table.create_from_schema(
                boto.connect_dynamodb(),
                'tablename',
                Schema.create(hash_key=('keyname', 'N')))

        :type layer2: :class:`boto.dynamodb.layer2.Layer2`
        :param layer2: A ``Layer2`` api object.

        :type name: str
        :param name: The name of the table.

        :type schema: :class:`boto.dynamodb.schema.Schema`
        :param schema: The schema associated with the table.

        :rtype: :class:`boto.dynamodb.table.Table`
        :return: A Table object representing the table.

        """
        table = cls(layer2, {'Table': {'TableName': name}})
        table._schema = schema
        return table

    def __repr__(self):
        return 'Table(%s)' % self.name

    @property
    def name(self):
        return self._dict['TableName']

    @property
    def create_time(self):
        return self._dict.get('CreationDateTime', None)

    @property
    def status(self):
        return self._dict.get('TableStatus', None)

    @property
    def item_count(self):
        return self._dict.get('ItemCount', 0)

    @property
    def size_bytes(self):
        return self._dict.get('TableSizeBytes', 0)

    @property
    def schema(self):
        return self._schema

    @property
    def read_units(self):
        try:
            return self._dict['ProvisionedThroughput']['ReadCapacityUnits']
        except KeyError:
            return None

    @property
    def write_units(self):
        try:
            return self._dict['ProvisionedThroughput']['WriteCapacityUnits']
        except KeyError:
            return None

    def update_from_response(self, response):
        """
        Update the state of the Table object based on the response
        data received from Amazon DynamoDB.
        """
        # 'Table' is from a describe_table call.
        if 'Table' in response:
            self._dict.update(response['Table'])
        # 'TableDescription' is from a create_table call.
        elif 'TableDescription' in response:
            self._dict.update(response['TableDescription'])
        if 'KeySchema' in self._dict:
            self._schema = Schema(self._dict['KeySchema'])

    def refresh(self, wait_for_active=False, retry_seconds=5):
        """
        Refresh all of the fields of the Table object by calling
        the underlying DescribeTable request.

        :type wait_for_active: bool
        :param wait_for_active: If True, this command will not return
            until the table status, as returned from Amazon DynamoDB, is
            'ACTIVE'.

        :type retry_seconds: int
        :param retry_seconds: If wait_for_active is True, this
            parameter controls the number of seconds of delay between
            calls to update_table in Amazon DynamoDB.  Default is 5 seconds.
        """
        done = False
        while not done:
            response = self.layer2.describe_table(self.name)
            self.update_from_response(response)
            if wait_for_active:
                if self.status == 'ACTIVE':
                    done = True
                else:
                    time.sleep(retry_seconds)
            else:
                done = True

    def update_throughput(self, read_units, write_units):
        """
        Update the ProvisionedThroughput for the Amazon DynamoDB Table.

        :type read_units: int
        :param read_units: The new value for ReadCapacityUnits.

        :type write_units: int
        :param write_units: The new value for WriteCapacityUnits.
        """
        self.layer2.update_throughput(self, read_units, write_units)

    def delete(self):
        """
        Delete this table and all items in it.  After calling this
        the Table objects status attribute will be set to 'DELETING'.
        """
        self.layer2.delete_table(self)

    def get_item(self, hash_key, range_key=None,
                 attributes_to_get=None, consistent_read=False,
                 item_class=Item):
        """
        Retrieve an existing item from the table.

        :type hash_key: int|long|float|str|unicode|Binary
        :param hash_key: The HashKey of the requested item.  The
            type of the value must match the type defined in the
            schema for the table.

        :type range_key: int|long|float|str|unicode|Binary
        :param range_key: The optional RangeKey of the requested item.
            The type of the value must match the type defined in the
            schema for the table.

        :type attributes_to_get: list
        :param attributes_to_get: A list of attribute names.
            If supplied, only the specified attribute names will
            be returned.  Otherwise, all attributes will be returned.

        :type consistent_read: bool
        :param consistent_read: If True, a consistent read
            request is issued.  Otherwise, an eventually consistent
            request is issued.

        :type item_class: Class
        :param item_class: Allows you to override the class used
            to generate the items. This should be a subclass of
            :class:`boto.dynamodb.item.Item`
        """
        return self.layer2.get_item(self, hash_key, range_key,
                                    attributes_to_get, consistent_read,
                                    item_class)
    lookup = get_item

    def has_item(self, hash_key, range_key=None, consistent_read=False):
        """
        Checks the table to see if the Item with the specified ``hash_key``
        exists. This may save a tiny bit of time/bandwidth over a
        straight :py:meth:`get_item` if you have no intention to touch
        the data that is returned, since this method specifically tells
        Amazon not to return anything but the Item's key.

        :type hash_key: int|long|float|str|unicode|Binary
        :param hash_key: The HashKey of the requested item.  The
            type of the value must match the type defined in the
            schema for the table.

        :type range_key: int|long|float|str|unicode|Binary
        :param range_key: The optional RangeKey of the requested item.
            The type of the value must match the type defined in the
            schema for the table.

        :type consistent_read: bool
        :param consistent_read: If True, a consistent read
            request is issued.  Otherwise, an eventually consistent
            request is issued.

        :rtype: bool
        :returns: ``True`` if the Item exists, ``False`` if not.
        """
        try:
            # Attempt to get the key. If it can't be found, it'll raise
            # an exception.
            self.get_item(hash_key, range_key=range_key,
                          # This minimizes the size of the response body.
                          attributes_to_get=[hash_key],
                          consistent_read=consistent_read)
        except dynamodb_exceptions.DynamoDBKeyNotFoundError:
            # Key doesn't exist.
            return False
        return True

    def new_item(self, hash_key=None, range_key=None, attrs=None,
                 item_class=Item):
        """
        Return an new, unsaved Item which can later be PUT to
        Amazon DynamoDB.

        This method has explicit (but optional) parameters for
        the hash_key and range_key values of the item.  You can use
        these explicit parameters when calling the method, such as::

            >>> my_item = my_table.new_item(hash_key='a', range_key=1,
                                        attrs={'key1': 'val1', 'key2': 'val2'})
            >>> my_item
            {u'bar': 1, u'foo': 'a', 'key1': 'val1', 'key2': 'val2'}

        Or, if you prefer, you can simply put the hash_key and range_key
        in the attrs dictionary itself, like this::

            >>> attrs = {'foo': 'a', 'bar': 1, 'key1': 'val1', 'key2': 'val2'}
            >>> my_item = my_table.new_item(attrs=attrs)
            >>> my_item
            {u'bar': 1, u'foo': 'a', 'key1': 'val1', 'key2': 'val2'}

        The effect is the same.

        .. note:
           The explicit parameters take priority over the values in
           the attrs dict.  So, if you have a hash_key or range_key
           in the attrs dict and you also supply either or both using
           the explicit parameters, the values in the attrs will be
           ignored.

        :type hash_key: int|long|float|str|unicode|Binary
        :param hash_key: The HashKey of the new item.  The
            type of the value must match the type defined in the
            schema for the table.

        :type range_key: int|long|float|str|unicode|Binary
        :param range_key: The optional RangeKey of the new item.
            The type of the value must match the type defined in the
            schema for the table.

        :type attrs: dict
        :param attrs: A dictionary of key value pairs used to
            populate the new item.

        :type item_class: Class
        :param item_class: Allows you to override the class used
            to generate the items. This should be a subclass of
            :class:`boto.dynamodb.item.Item`
        """
        return item_class(self, hash_key, range_key, attrs)

    def query(self, hash_key, *args, **kw):
        """
        Perform a query on the table.

        :type hash_key: int|long|float|str|unicode|Binary
        :param hash_key: The HashKey of the requested item.  The
            type of the value must match the type defined in the
            schema for the table.

        :type range_key_condition: :class:`boto.dynamodb.condition.Condition`
        :param range_key_condition: A Condition object.
            Condition object can be one of the following types:

            EQ|LE|LT|GE|GT|BEGINS_WITH|BETWEEN

            The only condition which expects or will accept two
            values is 'BETWEEN', otherwise a single value should
            be passed to the Condition constructor.

        :type attributes_to_get: list
        :param attributes_to_get: A list of attribute names.
            If supplied, only the specified attribute names will
            be returned.  Otherwise, all attributes will be returned.

        :type request_limit: int
        :param request_limit: The maximum number of items to retrieve
            from Amazon DynamoDB on each request.  You may want to set
            a specific request_limit based on the provisioned throughput
            of your table.  The default behavior is to retrieve as many
            results as possible per request.

        :type max_results: int
        :param max_results: The maximum number of results that will
            be retrieved from Amazon DynamoDB in total.  For example,
            if you only wanted to see the first 100 results from the
            query, regardless of how many were actually available, you
            could set max_results to 100 and the generator returned
            from the query method will only yeild 100 results max.

        :type consistent_read: bool
        :param consistent_read: If True, a consistent read
            request is issued.  Otherwise, an eventually consistent
            request is issued.

        :type scan_index_forward: bool
        :param scan_index_forward: Specified forward or backward
            traversal of the index.  Default is forward (True).

        :type exclusive_start_key: list or tuple
        :param exclusive_start_key: Primary key of the item from
            which to continue an earlier query.  This would be
            provided as the LastEvaluatedKey in that query.

        :type count: bool
        :param count: If True, Amazon DynamoDB returns a total
            number of items for the Query operation, even if the
            operation has no matching items for the assigned filter.
            If count is True, the actual items are not returned and
            the count is accessible as the ``count`` attribute of
            the returned object.


        :type item_class: Class
        :param item_class: Allows you to override the class used
            to generate the items. This should be a subclass of
            :class:`boto.dynamodb.item.Item`
        """
        return self.layer2.query(self, hash_key, *args, **kw)

    def scan(self, *args, **kw):
        """
        Scan through this table, this is a very long
        and expensive operation, and should be avoided if
        at all possible.

        :type scan_filter: A dict
        :param scan_filter: A dictionary where the key is the
            attribute name and the value is a
            :class:`boto.dynamodb.condition.Condition` object.
            Valid Condition objects include:

             * EQ - equal (1)
             * NE - not equal (1)
             * LE - less than or equal (1)
             * LT - less than (1)
             * GE - greater than or equal (1)
             * GT - greater than (1)
             * NOT_NULL - attribute exists (0, use None)
             * NULL - attribute does not exist (0, use None)
             * CONTAINS - substring or value in list (1)
             * NOT_CONTAINS - absence of substring or value in list (1)
             * BEGINS_WITH - substring prefix (1)
             * IN - exact match in list (N)
             * BETWEEN - >= first value, <= second value (2)

        :type attributes_to_get: list
        :param attributes_to_get: A list of attribute names.
            If supplied, only the specified attribute names will
            be returned.  Otherwise, all attributes will be returned.

        :type request_limit: int
        :param request_limit: The maximum number of items to retrieve
            from Amazon DynamoDB on each request.  You may want to set
            a specific request_limit based on the provisioned throughput
            of your table.  The default behavior is to retrieve as many
            results as possible per request.

        :type max_results: int
        :param max_results: The maximum number of results that will
            be retrieved from Amazon DynamoDB in total.  For example,
            if you only wanted to see the first 100 results from the
            query, regardless of how many were actually available, you
            could set max_results to 100 and the generator returned
            from the query method will only yeild 100 results max.

        :type count: bool
        :param count: If True, Amazon DynamoDB returns a total
            number of items for the Scan operation, even if the
            operation has no matching items for the assigned filter.
            If count is True, the actual items are not returned and
            the count is accessible as the ``count`` attribute of
            the returned object.

        :type exclusive_start_key: list or tuple
        :param exclusive_start_key: Primary key of the item from
            which to continue an earlier query.  This would be
            provided as the LastEvaluatedKey in that query.

        :type item_class: Class
        :param item_class: Allows you to override the class used
            to generate the items. This should be a subclass of
            :class:`boto.dynamodb.item.Item`

        :return: A TableGenerator (generator) object which will iterate
            over all results
        :rtype: :class:`boto.dynamodb.layer2.TableGenerator`
        """
        return self.layer2.scan(self, *args, **kw)

    def batch_get_item(self, keys, attributes_to_get=None):
        """
        Return a set of attributes for a multiple items from a single table
        using their primary keys. This abstraction removes the 100 Items per
        batch limitations as well as the "UnprocessedKeys" logic.

        :type keys: list
        :param keys: A list of scalar or tuple values.  Each element in the
            list represents one Item to retrieve.  If the schema for the
            table has both a HashKey and a RangeKey, each element in the
            list should be a tuple consisting of (hash_key, range_key).  If
            the schema for the table contains only a HashKey, each element
            in the list should be a scalar value of the appropriate type
            for the table schema. NOTE: The maximum number of items that
            can be retrieved for a single operation is 100. Also, the
            number of items retrieved is constrained by a 1 MB size limit.

        :type attributes_to_get: list
        :param attributes_to_get: A list of attribute names.
            If supplied, only the specified attribute names will
            be returned.  Otherwise, all attributes will be returned.

        :return: A TableBatchGenerator (generator) object which will
            iterate over all results
        :rtype: :class:`boto.dynamodb.table.TableBatchGenerator`
        """
        return TableBatchGenerator(self, keys, attributes_to_get)
