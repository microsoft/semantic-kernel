# Copyright (c) 2011 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2011 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
from boto.dynamodb.layer1 import Layer1
from boto.dynamodb.table import Table
from boto.dynamodb.schema import Schema
from boto.dynamodb.item import Item
from boto.dynamodb.batch import BatchList, BatchWriteList
from boto.dynamodb.types import get_dynamodb_type, Dynamizer, \
        LossyFloatDynamizer, NonBooleanDynamizer


class TableGenerator(object):
    """
    This is an object that wraps up the table_generator function.
    The only real reason to have this is that we want to be able
    to accumulate and return the ConsumedCapacityUnits element that
    is part of each response.

    :ivar last_evaluated_key: A sequence representing the key(s)
        of the item last evaluated, or None if no additional
        results are available.

    :ivar remaining: The remaining quantity of results requested.

    :ivar table: The table to which the call was made.
    """

    def __init__(self, table, callable, remaining, item_class, kwargs):
        self.table = table
        self.callable = callable
        self.remaining = -1 if remaining is None else remaining
        self.item_class = item_class
        self.kwargs = kwargs
        self._consumed_units = 0.0
        self.last_evaluated_key = None
        self._count = 0
        self._scanned_count = 0
        self._response = None

    @property
    def count(self):
        """
        The total number of items retrieved thus far.  This value changes with
        iteration and even when issuing a call with count=True, it is necessary
        to complete the iteration to assert an accurate count value.
        """
        self.response
        return self._count

    @property
    def scanned_count(self):
        """
        As above, but representing the total number of items scanned by
        DynamoDB, without regard to any filters.
        """
        self.response
        return self._scanned_count

    @property
    def consumed_units(self):
        """
        Returns a float representing the ConsumedCapacityUnits accumulated.
        """
        self.response
        return self._consumed_units

    @property
    def response(self):
        """
        The current response to the call from DynamoDB.
        """
        return self.next_response() if self._response is None else self._response

    def next_response(self):
        """
        Issue a call and return the result.  You can invoke this method
        while iterating over the TableGenerator in order to skip to the
        next "page" of results.
        """
        # preserve any existing limit in case the user alters self.remaining
        limit = self.kwargs.get('limit')
        if (self.remaining > 0 and (limit is None or limit > self.remaining)):
            self.kwargs['limit'] = self.remaining
        self._response = self.callable(**self.kwargs)
        self.kwargs['limit'] = limit
        self._consumed_units += self._response.get('ConsumedCapacityUnits', 0.0)
        self._count += self._response.get('Count', 0)
        self._scanned_count += self._response.get('ScannedCount', 0)
        # at the expense of a possibly gratuitous dynamize, ensure that
        # early generator termination won't result in bad LEK values
        if 'LastEvaluatedKey' in self._response:
            lek = self._response['LastEvaluatedKey']
            esk = self.table.layer2.dynamize_last_evaluated_key(lek)
            self.kwargs['exclusive_start_key'] = esk
            lektuple = (lek['HashKeyElement'],)
            if 'RangeKeyElement' in lek:
                lektuple += (lek['RangeKeyElement'],)
            self.last_evaluated_key = lektuple
        else:
            self.last_evaluated_key = None
        return self._response

    def __iter__(self):
        while self.remaining != 0:
            response = self.response
            for item in response.get('Items', []):
                self.remaining -= 1
                yield self.item_class(self.table, attrs=item)
                if self.remaining == 0:
                    break
                if response is not self._response:
                    break
            else:
                if self.last_evaluated_key is not None:
                    self.next_response()
                    continue
                break
            if response is not self._response:
                continue
            break


class Layer2(object):

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, port=None, proxy=None, proxy_port=None,
                 debug=0, security_token=None, region=None,
                 validate_certs=True, dynamizer=LossyFloatDynamizer,
                 profile_name=None):
        self.layer1 = Layer1(aws_access_key_id, aws_secret_access_key,
                             is_secure, port, proxy, proxy_port,
                             debug, security_token, region,
                             validate_certs=validate_certs,
                             profile_name=profile_name)
        self.dynamizer = dynamizer()

    def use_decimals(self, use_boolean=False):
        """
        Use the ``decimal.Decimal`` type for encoding/decoding numeric types.

        By default, ints/floats are used to represent numeric types
        ('N', 'NS') received from DynamoDB.  Using the ``Decimal``
        type is recommended to prevent loss of precision.

        """
        # Eventually this should be made the default dynamizer.
        self.dynamizer = Dynamizer() if use_boolean else NonBooleanDynamizer()

    def dynamize_attribute_updates(self, pending_updates):
        """
        Convert a set of pending item updates into the structure
        required by Layer1.
        """
        d = {}
        for attr_name in pending_updates:
            action, value = pending_updates[attr_name]
            if value is None:
                # DELETE without an attribute value
                d[attr_name] = {"Action": action}
            else:
                d[attr_name] = {"Action": action,
                                "Value": self.dynamizer.encode(value)}
        return d

    def dynamize_item(self, item):
        d = {}
        for attr_name in item:
            d[attr_name] = self.dynamizer.encode(item[attr_name])
        return d

    def dynamize_range_key_condition(self, range_key_condition):
        """
        Convert a layer2 range_key_condition parameter into the
        structure required by Layer1.
        """
        return range_key_condition.to_dict()

    def dynamize_scan_filter(self, scan_filter):
        """
        Convert a layer2 scan_filter parameter into the
        structure required by Layer1.
        """
        d = None
        if scan_filter:
            d = {}
            for attr_name in scan_filter:
                condition = scan_filter[attr_name]
                d[attr_name] = condition.to_dict()
        return d

    def dynamize_expected_value(self, expected_value):
        """
        Convert an expected_value parameter into the data structure
        required for Layer1.
        """
        d = None
        if expected_value:
            d = {}
            for attr_name in expected_value:
                attr_value = expected_value[attr_name]
                if attr_value is True:
                    attr_value = {'Exists': True}
                elif attr_value is False:
                    attr_value = {'Exists': False}
                else:
                    val = self.dynamizer.encode(expected_value[attr_name])
                    attr_value = {'Value': val}
                d[attr_name] = attr_value
        return d

    def dynamize_last_evaluated_key(self, last_evaluated_key):
        """
        Convert a last_evaluated_key parameter into the data structure
        required for Layer1.
        """
        d = None
        if last_evaluated_key:
            hash_key = last_evaluated_key['HashKeyElement']
            d = {'HashKeyElement': self.dynamizer.encode(hash_key)}
            if 'RangeKeyElement' in last_evaluated_key:
                range_key = last_evaluated_key['RangeKeyElement']
                d['RangeKeyElement'] = self.dynamizer.encode(range_key)
        return d

    def build_key_from_values(self, schema, hash_key, range_key=None):
        """
        Build a Key structure to be used for accessing items
        in Amazon DynamoDB.  This method takes the supplied hash_key
        and optional range_key and validates them against the
        schema.  If there is a mismatch, a TypeError is raised.
        Otherwise, a Python dict version of a Amazon DynamoDB Key
        data structure is returned.

        :type hash_key: int|float|str|unicode|Binary
        :param hash_key: The hash key of the item you are looking for.
            The type of the hash key should match the type defined in
            the schema.

        :type range_key: int|float|str|unicode|Binary
        :param range_key: The range key of the item your are looking for.
            This should be supplied only if the schema requires a
            range key.  The type of the range key should match the
            type defined in the schema.
        """
        dynamodb_key = {}
        dynamodb_value = self.dynamizer.encode(hash_key)
        if list(dynamodb_value.keys())[0] != schema.hash_key_type:
            msg = 'Hashkey must be of type: %s' % schema.hash_key_type
            raise TypeError(msg)
        dynamodb_key['HashKeyElement'] = dynamodb_value
        if range_key is not None:
            dynamodb_value = self.dynamizer.encode(range_key)
            if list(dynamodb_value.keys())[0] != schema.range_key_type:
                msg = 'RangeKey must be of type: %s' % schema.range_key_type
                raise TypeError(msg)
            dynamodb_key['RangeKeyElement'] = dynamodb_value
        return dynamodb_key

    def new_batch_list(self):
        """
        Return a new, empty :class:`boto.dynamodb.batch.BatchList`
        object.
        """
        return BatchList(self)

    def new_batch_write_list(self):
        """
        Return a new, empty :class:`boto.dynamodb.batch.BatchWriteList`
        object.
        """
        return BatchWriteList(self)

    def list_tables(self, limit=None):
        """
        Return a list of the names of all tables associated with the
        current account and region.

        :type limit: int
        :param limit: The maximum number of tables to return.
        """
        tables = []
        start_table = None
        while not limit or len(tables) < limit:
            this_round_limit = None
            if limit:
                this_round_limit = limit - len(tables)
                this_round_limit = min(this_round_limit, 100)
            result = self.layer1.list_tables(limit=this_round_limit, start_table=start_table)
            tables.extend(result.get('TableNames', []))
            start_table = result.get('LastEvaluatedTableName', None)
            if not start_table:
                break
        return tables

    def describe_table(self, name):
        """
        Retrieve information about an existing table.

        :type name: str
        :param name: The name of the desired table.

        """
        return self.layer1.describe_table(name)

    def table_from_schema(self, name, schema):
        """
        Create a Table object from a schema.

        This method will create a Table object without
        making any API calls.  If you know the name and schema
        of the table, you can use this method instead of
        ``get_table``.

        Example usage::

            table = layer2.table_from_schema(
                'tablename',
                Schema.create(hash_key=('foo', 'N')))

        :type name: str
        :param name: The name of the table.

        :type schema: :class:`boto.dynamodb.schema.Schema`
        :param schema: The schema associated with the table.

        :rtype: :class:`boto.dynamodb.table.Table`
        :return: A Table object representing the table.

        """
        return Table.create_from_schema(self, name, schema)

    def get_table(self, name):
        """
        Retrieve the Table object for an existing table.

        :type name: str
        :param name: The name of the desired table.

        :rtype: :class:`boto.dynamodb.table.Table`
        :return: A Table object representing the table.
        """
        response = self.layer1.describe_table(name)
        return Table(self, response)

    lookup = get_table

    def create_table(self, name, schema, read_units, write_units):
        """
        Create a new Amazon DynamoDB table.

        :type name: str
        :param name: The name of the desired table.

        :type schema: :class:`boto.dynamodb.schema.Schema`
        :param schema: The Schema object that defines the schema used
            by this table.

        :type read_units: int
        :param read_units: The value for ReadCapacityUnits.

        :type write_units: int
        :param write_units: The value for WriteCapacityUnits.

        :rtype: :class:`boto.dynamodb.table.Table`
        :return: A Table object representing the new Amazon DynamoDB table.
        """
        response = self.layer1.create_table(name, schema.dict,
                                            {'ReadCapacityUnits': read_units,
                                             'WriteCapacityUnits': write_units})
        return Table(self,  response)

    def update_throughput(self, table, read_units, write_units):
        """
        Update the ProvisionedThroughput for the Amazon DynamoDB Table.

        :type table: :class:`boto.dynamodb.table.Table`
        :param table: The Table object whose throughput is being updated.

        :type read_units: int
        :param read_units: The new value for ReadCapacityUnits.

        :type write_units: int
        :param write_units: The new value for WriteCapacityUnits.
        """
        response = self.layer1.update_table(table.name,
                                            {'ReadCapacityUnits': read_units,
                                             'WriteCapacityUnits': write_units})
        table.update_from_response(response)

    def delete_table(self, table):
        """
        Delete this table and all items in it.  After calling this
        the Table objects status attribute will be set to 'DELETING'.

        :type table: :class:`boto.dynamodb.table.Table`
        :param table: The Table object that is being deleted.
        """
        response = self.layer1.delete_table(table.name)
        table.update_from_response(response)

    def create_schema(self, hash_key_name, hash_key_proto_value,
                      range_key_name=None, range_key_proto_value=None):
        """
        Create a Schema object used when creating a Table.

        :type hash_key_name: str
        :param hash_key_name: The name of the HashKey for the schema.

        :type hash_key_proto_value: int|long|float|str|unicode|Binary
        :param hash_key_proto_value: A sample or prototype of the type
            of value you want to use for the HashKey.  Alternatively,
            you can also just pass in the Python type (e.g. int, float, etc.).

        :type range_key_name: str
        :param range_key_name: The name of the RangeKey for the schema.
            This parameter is optional.

        :type range_key_proto_value: int|long|float|str|unicode|Binary
        :param range_key_proto_value: A sample or prototype of the type
            of value you want to use for the RangeKey.  Alternatively,
            you can also pass in the Python type (e.g. int, float, etc.)
            This parameter is optional.
        """
        hash_key = (hash_key_name, get_dynamodb_type(hash_key_proto_value))
        if range_key_name and range_key_proto_value is not None:
            range_key = (range_key_name,
                         get_dynamodb_type(range_key_proto_value))
        else:
            range_key = None
        return Schema.create(hash_key, range_key)

    def get_item(self, table, hash_key, range_key=None,
                 attributes_to_get=None, consistent_read=False,
                 item_class=Item):
        """
        Retrieve an existing item from the table.

        :type table: :class:`boto.dynamodb.table.Table`
        :param table: The Table object from which the item is retrieved.

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
        key = self.build_key_from_values(table.schema, hash_key, range_key)
        response = self.layer1.get_item(table.name, key,
                                        attributes_to_get, consistent_read,
                                        object_hook=self.dynamizer.decode)
        item = item_class(table, hash_key, range_key, response['Item'])
        if 'ConsumedCapacityUnits' in response:
            item.consumed_units = response['ConsumedCapacityUnits']
        return item

    def batch_get_item(self, batch_list):
        """
        Return a set of attributes for a multiple items in
        multiple tables using their primary keys.

        :type batch_list: :class:`boto.dynamodb.batch.BatchList`
        :param batch_list: A BatchList object which consists of a
            list of :class:`boto.dynamoddb.batch.Batch` objects.
            Each Batch object contains the information about one
            batch of objects that you wish to retrieve in this
            request.
        """
        request_items = batch_list.to_dict()
        return self.layer1.batch_get_item(request_items,
                                          object_hook=self.dynamizer.decode)

    def batch_write_item(self, batch_list):
        """
        Performs multiple Puts and Deletes in one batch.

        :type batch_list: :class:`boto.dynamodb.batch.BatchWriteList`
        :param batch_list: A BatchWriteList object which consists of a
            list of :class:`boto.dynamoddb.batch.BatchWrite` objects.
            Each Batch object contains the information about one
            batch of objects that you wish to put or delete.
        """
        request_items = batch_list.to_dict()
        return self.layer1.batch_write_item(request_items,
                                            object_hook=self.dynamizer.decode)

    def put_item(self, item, expected_value=None, return_values=None):
        """
        Store a new item or completely replace an existing item
        in Amazon DynamoDB.

        :type item: :class:`boto.dynamodb.item.Item`
        :param item: The Item to write to Amazon DynamoDB.

        :type expected_value: dict
        :param expected_value: A dictionary of name/value pairs that you expect.
            This dictionary should have name/value pairs where the name
            is the name of the attribute and the value is either the value
            you are expecting or False if you expect the attribute not to
            exist.

        :type return_values: str
        :param return_values: Controls the return of attribute
            name-value pairs before then were changed.  Possible
            values are: None or 'ALL_OLD'. If 'ALL_OLD' is
            specified and the item is overwritten, the content
            of the old item is returned.
        """
        expected_value = self.dynamize_expected_value(expected_value)
        response = self.layer1.put_item(item.table.name,
                                        self.dynamize_item(item),
                                        expected_value, return_values,
                                        object_hook=self.dynamizer.decode)
        if 'ConsumedCapacityUnits' in response:
            item.consumed_units = response['ConsumedCapacityUnits']
        return response

    def update_item(self, item, expected_value=None, return_values=None):
        """
        Commit pending item updates to Amazon DynamoDB.

        :type item: :class:`boto.dynamodb.item.Item`
        :param item: The Item to update in Amazon DynamoDB.  It is expected
            that you would have called the add_attribute, put_attribute
            and/or delete_attribute methods on this Item prior to calling
            this method.  Those queued changes are what will be updated.

        :type expected_value: dict
        :param expected_value: A dictionary of name/value pairs that you
            expect.  This dictionary should have name/value pairs where the
            name is the name of the attribute and the value is either the
            value you are expecting or False if you expect the attribute
            not to exist.

        :type return_values: str
        :param return_values: Controls the return of attribute name/value pairs
            before they were updated. Possible values are: None, 'ALL_OLD',
            'UPDATED_OLD', 'ALL_NEW' or 'UPDATED_NEW'. If 'ALL_OLD' is
            specified and the item is overwritten, the content of the old item
            is returned. If 'ALL_NEW' is specified, then all the attributes of
            the new version of the item are returned. If 'UPDATED_NEW' is
            specified, the new versions of only the updated attributes are
            returned.

        """
        expected_value = self.dynamize_expected_value(expected_value)
        key = self.build_key_from_values(item.table.schema,
                                         item.hash_key, item.range_key)
        attr_updates = self.dynamize_attribute_updates(item._updates)

        response = self.layer1.update_item(item.table.name, key,
                                           attr_updates,
                                           expected_value, return_values,
                                           object_hook=self.dynamizer.decode)
        item._updates.clear()
        if 'ConsumedCapacityUnits' in response:
            item.consumed_units = response['ConsumedCapacityUnits']
        return response

    def delete_item(self, item, expected_value=None, return_values=None):
        """
        Delete the item from Amazon DynamoDB.

        :type item: :class:`boto.dynamodb.item.Item`
        :param item: The Item to delete from Amazon DynamoDB.

        :type expected_value: dict
        :param expected_value: A dictionary of name/value pairs that you expect.
            This dictionary should have name/value pairs where the name
            is the name of the attribute and the value is either the value
            you are expecting or False if you expect the attribute not to
            exist.

        :type return_values: str
        :param return_values: Controls the return of attribute
            name-value pairs before then were changed.  Possible
            values are: None or 'ALL_OLD'. If 'ALL_OLD' is
            specified and the item is overwritten, the content
            of the old item is returned.
        """
        expected_value = self.dynamize_expected_value(expected_value)
        key = self.build_key_from_values(item.table.schema,
                                         item.hash_key, item.range_key)
        return self.layer1.delete_item(item.table.name, key,
                                       expected=expected_value,
                                       return_values=return_values,
                                       object_hook=self.dynamizer.decode)

    def query(self, table, hash_key, range_key_condition=None,
              attributes_to_get=None, request_limit=None,
              max_results=None, consistent_read=False,
              scan_index_forward=True, exclusive_start_key=None,
              item_class=Item, count=False):
        """
        Perform a query on the table.

        :type table: :class:`boto.dynamodb.table.Table`
        :param table: The Table object that is being queried.

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

        :type count: bool
        :param count: If True, Amazon DynamoDB returns a total
            number of items for the Query operation, even if the
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

        :rtype: :class:`boto.dynamodb.layer2.TableGenerator`
        """
        if range_key_condition:
            rkc = self.dynamize_range_key_condition(range_key_condition)
        else:
            rkc = None
        if exclusive_start_key:
            esk = self.build_key_from_values(table.schema,
                                             *exclusive_start_key)
        else:
            esk = None
        kwargs = {'table_name': table.name,
                  'hash_key_value': self.dynamizer.encode(hash_key),
                  'range_key_conditions': rkc,
                  'attributes_to_get': attributes_to_get,
                  'limit': request_limit,
                  'count': count,
                  'consistent_read': consistent_read,
                  'scan_index_forward': scan_index_forward,
                  'exclusive_start_key': esk,
                  'object_hook': self.dynamizer.decode}
        return TableGenerator(table, self.layer1.query,
                              max_results, item_class, kwargs)

    def scan(self, table, scan_filter=None,
             attributes_to_get=None, request_limit=None, max_results=None,
             exclusive_start_key=None, item_class=Item, count=False):
        """
        Perform a scan of DynamoDB.

        :type table: :class:`boto.dynamodb.table.Table`
        :param table: The Table object that is being scanned.

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

        :rtype: :class:`boto.dynamodb.layer2.TableGenerator`
        """
        if exclusive_start_key:
            esk = self.build_key_from_values(table.schema,
                                             *exclusive_start_key)
        else:
            esk = None
        kwargs = {'table_name': table.name,
                  'scan_filter': self.dynamize_scan_filter(scan_filter),
                  'attributes_to_get': attributes_to_get,
                  'limit': request_limit,
                  'count': count,
                  'exclusive_start_key': esk,
                  'object_hook': self.dynamizer.decode}
        return TableGenerator(table, self.layer1.scan,
                              max_results, item_class, kwargs)
