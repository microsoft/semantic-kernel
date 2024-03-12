from boto.dynamodb2.types import STRING


class BaseSchemaField(object):
    """
    An abstract class for defining schema fields.

    Contains most of the core functionality for the field. Subclasses must
    define an ``attr_type`` to pass to DynamoDB.
    """
    attr_type = None

    def __init__(self, name, data_type=STRING):
        """
        Creates a Python schema field, to represent the data to pass to
        DynamoDB.

        Requires a ``name`` parameter, which should be a string name of the
        field.

        Optionally accepts a ``data_type`` parameter, which should be a
        constant from ``boto.dynamodb2.types``. (Default: ``STRING``)
        """
        self.name = name
        self.data_type = data_type

    def definition(self):
        """
        Returns the attribute definition structure DynamoDB expects.

        Example::

            >>> field.definition()
            {
                'AttributeName': 'username',
                'AttributeType': 'S',
            }

        """
        return {
            'AttributeName': self.name,
            'AttributeType': self.data_type,
        }

    def schema(self):
        """
        Returns the schema structure DynamoDB expects.

        Example::

            >>> field.schema()
            {
                'AttributeName': 'username',
                'KeyType': 'HASH',
            }

        """
        return {
            'AttributeName': self.name,
            'KeyType': self.attr_type,
        }


class HashKey(BaseSchemaField):
    """
    An field representing a hash key.

    Example::

        >>> from boto.dynamodb2.types import NUMBER
        >>> HashKey('username')
        >>> HashKey('date_joined', data_type=NUMBER)

    """
    attr_type = 'HASH'


class RangeKey(BaseSchemaField):
    """
    An field representing a range key.

    Example::

        >>> from boto.dynamodb2.types import NUMBER
        >>> HashKey('username')
        >>> HashKey('date_joined', data_type=NUMBER)

    """
    attr_type = 'RANGE'


class BaseIndexField(object):
    """
    An abstract class for defining schema indexes.

    Contains most of the core functionality for the index. Subclasses must
    define a ``projection_type`` to pass to DynamoDB.
    """
    def __init__(self, name, parts):
        self.name = name
        self.parts = parts

    def definition(self):
        """
        Returns the attribute definition structure DynamoDB expects.

        Example::

            >>> index.definition()
            {
                'AttributeName': 'username',
                'AttributeType': 'S',
            }

        """
        definition = []

        for part in self.parts:
            definition.append({
                'AttributeName': part.name,
                'AttributeType': part.data_type,
            })

        return definition

    def schema(self):
        """
        Returns the schema structure DynamoDB expects.

        Example::

            >>> index.schema()
            {
                'IndexName': 'LastNameIndex',
                'KeySchema': [
                    {
                        'AttributeName': 'username',
                        'KeyType': 'HASH',
                    },
                ],
                'Projection': {
                    'ProjectionType': 'KEYS_ONLY',
                }
            }

        """
        key_schema = []

        for part in self.parts:
            key_schema.append(part.schema())

        return {
            'IndexName': self.name,
            'KeySchema': key_schema,
            'Projection': {
                'ProjectionType': self.projection_type,
            }
        }


class AllIndex(BaseIndexField):
    """
    An index signifying all fields should be in the index.

    Example::

        >>> AllIndex('MostRecentlyJoined', parts=[
        ...     HashKey('username'),
        ...     RangeKey('date_joined')
        ... ])

    """
    projection_type = 'ALL'


class KeysOnlyIndex(BaseIndexField):
    """
    An index signifying only key fields should be in the index.

    Example::

        >>> KeysOnlyIndex('MostRecentlyJoined', parts=[
        ...     HashKey('username'),
        ...     RangeKey('date_joined')
        ... ])

    """
    projection_type = 'KEYS_ONLY'


class IncludeIndex(BaseIndexField):
    """
    An index signifying only certain fields should be in the index.

    Example::

        >>> IncludeIndex('GenderIndex', parts=[
        ...     HashKey('username'),
        ...     RangeKey('date_joined')
        ... ], includes=['gender'])

    """
    projection_type = 'INCLUDE'

    def __init__(self, *args, **kwargs):
        self.includes_fields = kwargs.pop('includes', [])
        super(IncludeIndex, self).__init__(*args, **kwargs)

    def schema(self):
        schema_data = super(IncludeIndex, self).schema()
        schema_data['Projection']['NonKeyAttributes'] = self.includes_fields
        return schema_data


class GlobalBaseIndexField(BaseIndexField):
    """
    An abstract class for defining global indexes.

    Contains most of the core functionality for the index. Subclasses must
    define a ``projection_type`` to pass to DynamoDB.
    """
    throughput = {
        'read': 5,
        'write': 5,
    }

    def __init__(self, *args, **kwargs):
        throughput = kwargs.pop('throughput', None)

        if throughput is not None:
            self.throughput = throughput

        super(GlobalBaseIndexField, self).__init__(*args, **kwargs)

    def schema(self):
        """
        Returns the schema structure DynamoDB expects.

        Example::

            >>> index.schema()
            {
                'IndexName': 'LastNameIndex',
                'KeySchema': [
                    {
                        'AttributeName': 'username',
                        'KeyType': 'HASH',
                    },
                ],
                'Projection': {
                    'ProjectionType': 'KEYS_ONLY',
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            }

        """
        schema_data = super(GlobalBaseIndexField, self).schema()
        schema_data['ProvisionedThroughput'] = {
            'ReadCapacityUnits': int(self.throughput['read']),
            'WriteCapacityUnits': int(self.throughput['write']),
        }
        return schema_data


class GlobalAllIndex(GlobalBaseIndexField):
    """
    An index signifying all fields should be in the index.

    Example::

        >>> GlobalAllIndex('MostRecentlyJoined', parts=[
        ...     HashKey('username'),
        ...     RangeKey('date_joined')
        ... ],
        ... throughput={
        ...     'read': 2,
        ...     'write': 1,
        ... })

    """
    projection_type = 'ALL'


class GlobalKeysOnlyIndex(GlobalBaseIndexField):
    """
    An index signifying only key fields should be in the index.

    Example::

        >>> GlobalKeysOnlyIndex('MostRecentlyJoined', parts=[
        ...     HashKey('username'),
        ...     RangeKey('date_joined')
        ... ],
        ... throughput={
        ...     'read': 2,
        ...     'write': 1,
        ... })

    """
    projection_type = 'KEYS_ONLY'


class GlobalIncludeIndex(GlobalBaseIndexField, IncludeIndex):
    """
    An index signifying only certain fields should be in the index.

    Example::

        >>> GlobalIncludeIndex('GenderIndex', parts=[
        ...     HashKey('username'),
        ...     RangeKey('date_joined')
        ... ],
        ... includes=['gender'],
        ... throughput={
        ...     'read': 2,
        ...     'write': 1,
        ... })

    """
    projection_type = 'INCLUDE'

    def __init__(self, *args, **kwargs):
        throughput = kwargs.pop('throughput', None)
        IncludeIndex.__init__(self, *args, **kwargs)
        if throughput:
            kwargs['throughput'] = throughput
        GlobalBaseIndexField.__init__(self, *args, **kwargs)

    def schema(self):
        # Pick up the includes.
        schema_data = IncludeIndex.schema(self)
        # Also the throughput.
        schema_data.update(GlobalBaseIndexField.schema(self))
        return schema_data
