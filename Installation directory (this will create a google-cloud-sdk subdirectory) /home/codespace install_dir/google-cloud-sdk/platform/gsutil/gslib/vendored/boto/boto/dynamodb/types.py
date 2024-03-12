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
"""
Some utility functions to deal with mapping Amazon DynamoDB types to
Python types and vice-versa.
"""
import base64
from decimal import (Decimal, DecimalException, Context,
                     Clamped, Overflow, Inexact, Underflow, Rounded)
from collections.abc import Mapping
from boto.dynamodb.exceptions import DynamoDBNumberError
from boto.compat import filter, map, six, long_type


DYNAMODB_CONTEXT = Context(
    Emin=-128, Emax=126, rounding=None, prec=38,
    traps=[Clamped, Overflow, Inexact, Rounded, Underflow])


# python2.6 cannot convert floats directly to
# Decimals.  This is taken from:
# http://docs.python.org/release/2.6.7/library/decimal.html#decimal-faq
def float_to_decimal(f):
    n, d = f.as_integer_ratio()
    numerator, denominator = Decimal(n), Decimal(d)
    ctx = DYNAMODB_CONTEXT
    result = ctx.divide(numerator, denominator)
    while ctx.flags[Inexact]:
        ctx.flags[Inexact] = False
        ctx.prec *= 2
        result = ctx.divide(numerator, denominator)
    return result


def is_num(n, boolean_as_int=True):
    if boolean_as_int:
        types = (int, long_type, float, Decimal, bool)
    else:
        types = (int, long_type, float, Decimal)

    return isinstance(n, types) or n in types


if six.PY2:
    def is_str(n):
        return (isinstance(n, basestring) or
                isinstance(n, type) and issubclass(n, basestring))

    def is_binary(n):
        return isinstance(n, Binary)

else:  # PY3
    def is_str(n):
        return (isinstance(n, str) or
                isinstance(n, type) and issubclass(n, str))

    def is_binary(n):
        return isinstance(n, bytes)  # Binary is subclass of bytes.


def serialize_num(val):
    """Cast a number to a string and perform
       validation to ensure no loss of precision.
    """
    if isinstance(val, bool):
        return str(int(val))
    return str(val)


def convert_num(s):
    if '.' in s:
        n = float(s)
    else:
        n = int(s)
    return n


def convert_binary(n):
    return Binary(base64.b64decode(n))


def get_dynamodb_type(val, use_boolean=True):
    """
    Take a scalar Python value and return a string representing
    the corresponding Amazon DynamoDB type.  If the value passed in is
    not a supported type, raise a TypeError.
    """
    dynamodb_type = None
    if val is None:
        dynamodb_type = 'NULL'
    elif is_num(val):
        if isinstance(val, bool) and use_boolean:
            dynamodb_type = 'BOOL'
        else:
            dynamodb_type = 'N'
    elif is_str(val):
        dynamodb_type = 'S'
    elif isinstance(val, (set, frozenset)):
        if False not in map(is_num, val):
            dynamodb_type = 'NS'
        elif False not in map(is_str, val):
            dynamodb_type = 'SS'
        elif False not in map(is_binary, val):
            dynamodb_type = 'BS'
    elif is_binary(val):
        dynamodb_type = 'B'
    elif isinstance(val, Mapping):
        dynamodb_type = 'M'
    elif isinstance(val, list):
        dynamodb_type = 'L'
    if dynamodb_type is None:
        msg = 'Unsupported type "%s" for value "%s"' % (type(val), val)
        raise TypeError(msg)
    return dynamodb_type


def dynamize_value(val):
    """
    Take a scalar Python value and return a dict consisting
    of the Amazon DynamoDB type specification and the value that
    needs to be sent to Amazon DynamoDB.  If the type of the value
    is not supported, raise a TypeError
    """
    dynamodb_type = get_dynamodb_type(val)
    if dynamodb_type == 'N':
        val = {dynamodb_type: serialize_num(val)}
    elif dynamodb_type == 'S':
        val = {dynamodb_type: val}
    elif dynamodb_type == 'NS':
        val = {dynamodb_type: list(map(serialize_num, val))}
    elif dynamodb_type == 'SS':
        val = {dynamodb_type: [n for n in val]}
    elif dynamodb_type == 'B':
        if isinstance(val, bytes):
            val = Binary(val)
        val = {dynamodb_type: val.encode()}
    elif dynamodb_type == 'BS':
        val = {dynamodb_type: [n.encode() for n in val]}
    return val


if six.PY2:
    class Binary(object):
        def __init__(self, value):
            if not isinstance(value, (bytes, six.text_type)):
                raise TypeError('Value must be a string of binary data!')
            if not isinstance(value, bytes):
                value = value.encode("utf-8")

            self.value = value

        def encode(self):
            return base64.b64encode(self.value).decode('utf-8')

        def __eq__(self, other):
            if isinstance(other, Binary):
                return self.value == other.value
            else:
                return self.value == other

        def __ne__(self, other):
            return not self.__eq__(other)

        def __repr__(self):
            return 'Binary(%r)' % self.value

        def __str__(self):
            return self.value

        def __hash__(self):
            return hash(self.value)
else:
    class Binary(bytes):
        def encode(self):
            return base64.b64encode(self).decode('utf-8')

        @property
        def value(self):
            # This matches the public API of the Python 2 version,
            # but just returns itself since it is already a bytes
            # instance.
            return bytes(self)

        def __repr__(self):
            return 'Binary(%r)' % self.value


def item_object_hook(dct):
    """
    A custom object hook for use when decoding JSON item bodys.
    This hook will transform Amazon DynamoDB JSON responses to something
    that maps directly to native Python types.
    """
    if len(dct.keys()) > 1:
        return dct
    if 'S' in dct:
        return dct['S']
    if 'N' in dct:
        return convert_num(dct['N'])
    if 'SS' in dct:
        return set(dct['SS'])
    if 'NS' in dct:
        return set(map(convert_num, dct['NS']))
    if 'B' in dct:
        return convert_binary(dct['B'])
    if 'BS' in dct:
        return set(map(convert_binary, dct['BS']))
    return dct


class Dynamizer(object):
    """Control serialization/deserialization of types.

    This class controls the encoding of python types to the
    format that is expected by the DynamoDB API, as well as
    taking DynamoDB types and constructing the appropriate
    python types.

    If you want to customize this process, you can subclass
    this class and override the encoding/decoding of
    specific types.  For example::

        'foo'      (Python type)
            |
            v
        encode('foo')
            |
            v
        _encode_s('foo')
            |
            v
        {'S': 'foo'}  (Encoding sent to/received from DynamoDB)
            |
            V
        decode({'S': 'foo'})
            |
            v
        _decode_s({'S': 'foo'})
            |
            v
        'foo'     (Python type)

    """
    def _get_dynamodb_type(self, attr):
        return get_dynamodb_type(attr)

    def encode(self, attr):
        """
        Encodes a python type to the format expected
        by DynamoDB.

        """
        dynamodb_type = self._get_dynamodb_type(attr)
        try:
            encoder = getattr(self, '_encode_%s' % dynamodb_type.lower())
        except AttributeError:
            raise ValueError("Unable to encode dynamodb type: %s" %
                             dynamodb_type)
        return {dynamodb_type: encoder(attr)}

    def _encode_n(self, attr):
        try:
            if isinstance(attr, float) and not hasattr(Decimal, 'from_float'):
                # python2.6 does not support creating Decimals directly
                # from floats so we have to do this ourself.
                n = str(float_to_decimal(attr))
            else:
                n = str(DYNAMODB_CONTEXT.create_decimal(attr))
            if list(filter(lambda x: x in n, ('Infinity', 'NaN'))):
                raise TypeError('Infinity and NaN not supported')
            return n
        except (TypeError, DecimalException) as e:
            msg = '{0} numeric for `{1}`\n{2}'.format(
                e.__class__.__name__, attr, str(e) or '')
        raise DynamoDBNumberError(msg)

    def _encode_s(self, attr):
        if isinstance(attr, bytes):
            attr = attr.decode('utf-8')
        elif not isinstance(attr, six.text_type):
            attr = str(attr)
        return attr

    def _encode_ns(self, attr):
        return list(map(self._encode_n, attr))

    def _encode_ss(self, attr):
        return [self._encode_s(n) for n in attr]

    def _encode_b(self, attr):
        if isinstance(attr, bytes):
            attr = Binary(attr)
        return attr.encode()

    def _encode_bs(self, attr):
        return [self._encode_b(n) for n in attr]

    def _encode_null(self, attr):
        return True

    def _encode_bool(self, attr):
        return attr

    def _encode_m(self, attr):
        return dict([(k, self.encode(v)) for k, v in attr.items()])

    def _encode_l(self, attr):
        return [self.encode(i) for i in attr]

    def decode(self, attr):
        """
        Takes the format returned by DynamoDB and constructs
        the appropriate python type.

        """
        if len(attr) > 1 or not attr or is_str(attr):
            return attr
        dynamodb_type = list(attr.keys())[0]
        if dynamodb_type.lower() == dynamodb_type:
            # It's not an actual type, just a single character attr that
            # overlaps with the DDB types. Return it.
            return attr
        try:
            decoder = getattr(self, '_decode_%s' % dynamodb_type.lower())
        except AttributeError:
            return attr
        return decoder(attr[dynamodb_type])

    def _decode_n(self, attr):
        return DYNAMODB_CONTEXT.create_decimal(attr)

    def _decode_s(self, attr):
        return attr

    def _decode_ns(self, attr):
        return set(map(self._decode_n, attr))

    def _decode_ss(self, attr):
        return set(map(self._decode_s, attr))

    def _decode_b(self, attr):
        return convert_binary(attr)

    def _decode_bs(self, attr):
        return set(map(self._decode_b, attr))

    def _decode_null(self, attr):
        return None

    def _decode_bool(self, attr):
        return attr

    def _decode_m(self, attr):
        return dict([(k, self.decode(v)) for k, v in attr.items()])

    def _decode_l(self, attr):
        return [self.decode(i) for i in attr]


class NonBooleanDynamizer(Dynamizer):
    """Casting boolean type to numeric types.

    This class is provided for backward compatibility.
    """
    def _get_dynamodb_type(self, attr):
        return get_dynamodb_type(attr, use_boolean=False)


class LossyFloatDynamizer(NonBooleanDynamizer):
    """Use float/int instead of Decimal for numeric types.

    This class is provided for backwards compatibility.  Instead of
    using Decimals for the 'N', 'NS' types it uses ints/floats.

    This class is deprecated and its usage is not encouraged,
    as doing so may result in loss of precision.  Use the
    `Dynamizer` class instead.

    """
    def _encode_n(self, attr):
        return serialize_num(attr)

    def _encode_ns(self, attr):
        return [str(i) for i in attr]

    def _decode_n(self, attr):
        return convert_num(attr)

    def _decode_ns(self, attr):
        return set(map(self._decode_n, attr))
