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


class Schema(object):
    """
    Represents a DynamoDB schema.

    :ivar hash_key_name: The name of the hash key of the schema.
    :ivar hash_key_type: The DynamoDB type specification for the
        hash key of the schema.
    :ivar range_key_name: The name of the range key of the schema
        or None if no range key is defined.
    :ivar range_key_type: The DynamoDB type specification for the
        range key of the schema or None if no range key is defined.
    :ivar dict: The underlying Python dictionary that needs to be
        passed to Layer1 methods.
    """

    def __init__(self, schema_dict):
        self._dict = schema_dict

    def __repr__(self):
        if self.range_key_name:
            s = 'Schema(%s:%s)' % (self.hash_key_name, self.range_key_name)
        else:
            s = 'Schema(%s)' % self.hash_key_name
        return s

    @classmethod
    def create(cls, hash_key, range_key=None):
        """Convenience method to create a schema object.

        Example usage::

            schema = Schema.create(hash_key=('foo', 'N'))
            schema2 = Schema.create(hash_key=('foo', 'N'),
                                    range_key=('bar', 'S'))

        :type hash_key: tuple
        :param hash_key: A tuple of (hash_key_name, hash_key_type)

        :type range_key: tuple
        :param hash_key: A tuple of (range_key_name, range_key_type)

        """
        reconstructed = {
            'HashKeyElement': {
                'AttributeName': hash_key[0],
                'AttributeType': hash_key[1],
            }
        }
        if range_key is not None:
            reconstructed['RangeKeyElement'] = {
                'AttributeName': range_key[0],
                'AttributeType': range_key[1],
            }
        instance = cls(None)
        instance._dict = reconstructed
        return instance

    @property
    def dict(self):
        return self._dict

    @property
    def hash_key_name(self):
        return self._dict['HashKeyElement']['AttributeName']

    @property
    def hash_key_type(self):
        return self._dict['HashKeyElement']['AttributeType']

    @property
    def range_key_name(self):
        name = None
        if 'RangeKeyElement' in self._dict:
            name = self._dict['RangeKeyElement']['AttributeName']
        return name

    @property
    def range_key_type(self):
        type = None
        if 'RangeKeyElement' in self._dict:
            type = self._dict['RangeKeyElement']['AttributeType']
        return type

    def __eq__(self, other):
        return (self.hash_key_name == other.hash_key_name and
                self.hash_key_type == other.hash_key_type and
                self.range_key_name == other.range_key_name and
                self.range_key_type == other.range_key_type)
