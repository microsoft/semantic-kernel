#!/usr/bin/env python
#
# Copyright 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Tests for apitools.base.protorpclite.protojson."""
import datetime
import json
import unittest

from apitools.base.protorpclite import message_types
from apitools.base.protorpclite import messages
from apitools.base.protorpclite import protojson
from apitools.base.protorpclite import test_util


class CustomField(messages.MessageField):
    """Custom MessageField class."""

    type = int
    message_type = message_types.VoidMessage

    def __init__(self, number, **kwargs):
        super(CustomField, self).__init__(self.message_type, number, **kwargs)

    def value_to_message(self, value):
        return self.message_type()  # pylint:disable=not-callable


class MyMessage(messages.Message):
    """Test message containing various types."""

    class Color(messages.Enum):

        RED = 1
        GREEN = 2
        BLUE = 3

    class Nested(messages.Message):

        nested_value = messages.StringField(1)

    class NestedDatetime(messages.Message):

        nested_dt_value = message_types.DateTimeField(1)

    a_string = messages.StringField(2)
    an_integer = messages.IntegerField(3)
    a_float = messages.FloatField(4)
    a_boolean = messages.BooleanField(5)
    an_enum = messages.EnumField(Color, 6)
    a_nested = messages.MessageField(Nested, 7)
    a_repeated = messages.IntegerField(8, repeated=True)
    a_repeated_float = messages.FloatField(9, repeated=True)
    a_datetime = message_types.DateTimeField(10)
    a_repeated_datetime = message_types.DateTimeField(11, repeated=True)
    a_custom = CustomField(12)
    a_repeated_custom = CustomField(13, repeated=True)
    a_nested_datetime = messages.MessageField(NestedDatetime, 14)


class ModuleInterfaceTest(test_util.ModuleInterfaceTest,
                          test_util.TestCase):

    MODULE = protojson


# TODO(rafek): Convert this test to the compliance test in test_util.
class ProtojsonTest(test_util.TestCase,
                    test_util.ProtoConformanceTestBase):
    """Test JSON encoding and decoding."""

    PROTOLIB = protojson

    def CompareEncoded(self, expected_encoded, actual_encoded):
        """JSON encoding will be laundered to remove string differences."""
        self.assertEquals(json.loads(expected_encoded),
                          json.loads(actual_encoded))

    encoded_empty_message = '{}'

    encoded_partial = """{
    "double_value": 1.23,
    "int64_value": -100000000000,
    "int32_value": 1020,
    "string_value": "a string",
    "enum_value": "VAL2"
    }
    """

    # pylint:disable=anomalous-unicode-escape-in-string
    encoded_full = """{
    "double_value": 1.23,
    "float_value": -2.5,
    "int64_value": -100000000000,
    "uint64_value": 102020202020,
    "int32_value": 1020,
    "bool_value": true,
    "string_value": "a string\u044f",
    "bytes_value": "YSBieXRlc//+",
    "enum_value": "VAL2"
    }
    """

    encoded_repeated = """{
    "double_value": [1.23, 2.3],
    "float_value": [-2.5, 0.5],
    "int64_value": [-100000000000, 20],
    "uint64_value": [102020202020, 10],
    "int32_value": [1020, 718],
    "bool_value": [true, false],
    "string_value": ["a string\u044f", "another string"],
    "bytes_value": ["YSBieXRlc//+", "YW5vdGhlciBieXRlcw=="],
    "enum_value": ["VAL2", "VAL1"]
    }
    """

    encoded_nested = """{
    "nested": {
      "a_value": "a string"
    }
    }
    """

    encoded_repeated_nested = """{
    "repeated_nested": [{"a_value": "a string"},
                        {"a_value": "another string"}]
    }
    """

    unexpected_tag_message = '{"unknown": "value"}'

    encoded_default_assigned = '{"a_value": "a default"}'

    encoded_nested_empty = '{"nested": {}}'

    encoded_repeated_nested_empty = '{"repeated_nested": [{}, {}]}'

    encoded_extend_message = '{"int64_value": [400, 50, 6000]}'

    encoded_string_types = '{"string_value": "Latin"}'

    encoded_invalid_enum = '{"enum_value": "undefined"}'

    def testConvertIntegerToFloat(self):
        """Test that integers passed in to float fields are converted.

        This is necessary because JSON outputs integers for numbers
        with 0 decimals.

        """
        message = protojson.decode_message(MyMessage, '{"a_float": 10}')

        self.assertTrue(isinstance(message.a_float, float))
        self.assertEquals(10.0, message.a_float)

    def testConvertStringToNumbers(self):
        """Test that strings passed to integer fields are converted."""
        message = protojson.decode_message(MyMessage,
                                           """{"an_integer": "10",
                                           "a_float": "3.5",
                                           "a_repeated": ["1", "2"],
                                           "a_repeated_float": ["1.5", "2", 10]
                                           }""")

        self.assertEquals(MyMessage(an_integer=10,
                                    a_float=3.5,
                                    a_repeated=[1, 2],
                                    a_repeated_float=[1.5, 2.0, 10.0]),
                          message)

    def testWrongTypeAssignment(self):
        """Test when wrong type is assigned to a field."""
        self.assertRaises(messages.ValidationError,
                          protojson.decode_message,
                          MyMessage, '{"a_string": 10}')
        self.assertRaises(messages.ValidationError,
                          protojson.decode_message,
                          MyMessage, '{"an_integer": 10.2}')
        self.assertRaises(messages.ValidationError,
                          protojson.decode_message,
                          MyMessage, '{"an_integer": "10.2"}')

    def testNumericEnumeration(self):
        """Test that numbers work for enum values."""
        message = protojson.decode_message(MyMessage, '{"an_enum": 2}')

        expected_message = MyMessage()
        expected_message.an_enum = MyMessage.Color.GREEN

        self.assertEquals(expected_message, message)

    def testNumericEnumerationNegativeTest(self):
        """Test with an invalid number for the enum value."""
        # The message should successfully decode.
        message = protojson.decode_message(MyMessage,
                                           '{"an_enum": 89}')

        expected_message = MyMessage()

        self.assertEquals(expected_message, message)
        # The roundtrip should result in equivalent encoded
        # message.
        self.assertEquals('{"an_enum": 89}', protojson.encode_message(message))

    def testAlphaEnumeration(self):
        """Test that alpha enum values work."""
        message = protojson.decode_message(MyMessage, '{"an_enum": "RED"}')

        expected_message = MyMessage()
        expected_message.an_enum = MyMessage.Color.RED

        self.assertEquals(expected_message, message)

    def testAlphaEnumerationNegativeTest(self):
        """The alpha enum value is invalid."""
        # The message should successfully decode.
        message = protojson.decode_message(MyMessage,
                                           '{"an_enum": "IAMINVALID"}')

        expected_message = MyMessage()

        self.assertEquals(expected_message, message)
        # The roundtrip should result in equivalent encoded message.
        self.assertEquals('{"an_enum": "IAMINVALID"}',
                          protojson.encode_message(message))

    def testEnumerationNegativeTestWithEmptyString(self):
        """The enum value is an empty string."""
        # The message should successfully decode.
        message = protojson.decode_message(MyMessage, '{"an_enum": ""}')

        expected_message = MyMessage()

        self.assertEquals(expected_message, message)
        # The roundtrip should result in equivalent encoded message.
        self.assertEquals('{"an_enum": ""}', protojson.encode_message(message))

    def testNullValues(self):
        """Test that null values overwrite existing values."""
        self.assertEquals(MyMessage(),
                          protojson.decode_message(MyMessage,
                                                   ('{"an_integer": null,'
                                                    ' "a_nested": null,'
                                                    ' "an_enum": null'
                                                    '}')))

    def testEmptyList(self):
        """Test that empty lists are ignored."""
        self.assertEquals(MyMessage(),
                          protojson.decode_message(MyMessage,
                                                   '{"a_repeated": []}'))

    def testNotJSON(self):
        """Test error when string is not valid JSON."""
        self.assertRaises(
            ValueError,
            protojson.decode_message, MyMessage,
            '{this is not json}')

    def testDoNotEncodeStrangeObjects(self):
        """Test trying to encode a strange object.

        The main purpose of this test is to complete coverage. It
        ensures that the default behavior of the JSON encoder is
        preserved when someone tries to serialized an unexpected type.

        """
        class BogusObject(object):

            def check_initialized(self):
                pass

        self.assertRaises(TypeError,
                          protojson.encode_message,
                          BogusObject())

    def testMergeEmptyString(self):
        """Test merging the empty or space only string."""
        message = protojson.decode_message(test_util.OptionalMessage, '')
        self.assertEquals(test_util.OptionalMessage(), message)

        message = protojson.decode_message(test_util.OptionalMessage, ' ')
        self.assertEquals(test_util.OptionalMessage(), message)

    def testProtojsonUnrecognizedFieldName(self):
        """Test that unrecognized fields are saved and can be accessed."""
        decoded = protojson.decode_message(
            MyMessage,
            ('{"an_integer": 1, "unknown_val": 2}'))
        self.assertEquals(decoded.an_integer, 1)
        self.assertEquals(1, len(decoded.all_unrecognized_fields()))
        self.assertEquals('unknown_val', decoded.all_unrecognized_fields()[0])
        self.assertEquals((2, messages.Variant.INT64),
                          decoded.get_unrecognized_field_info('unknown_val'))

    def testProtojsonUnrecognizedFieldNumber(self):
        """Test that unrecognized fields are saved and can be accessed."""
        decoded = protojson.decode_message(
            MyMessage,
            '{"an_integer": 1, "1001": "unknown", "-123": "negative", '
            '"456_mixed": 2}')
        self.assertEquals(decoded.an_integer, 1)
        self.assertEquals(3, len(decoded.all_unrecognized_fields()))
        self.assertFalse(1001 in decoded.all_unrecognized_fields())
        self.assertTrue('1001' in decoded.all_unrecognized_fields())
        self.assertEquals(('unknown', messages.Variant.STRING),
                          decoded.get_unrecognized_field_info('1001'))
        self.assertTrue('-123' in decoded.all_unrecognized_fields())
        self.assertEquals(('negative', messages.Variant.STRING),
                          decoded.get_unrecognized_field_info('-123'))
        self.assertTrue('456_mixed' in decoded.all_unrecognized_fields())
        self.assertEquals((2, messages.Variant.INT64),
                          decoded.get_unrecognized_field_info('456_mixed'))

    def testProtojsonUnrecognizedNull(self):
        """Test that unrecognized fields that are None are skipped."""
        decoded = protojson.decode_message(
            MyMessage,
            '{"an_integer": 1, "unrecognized_null": null}')
        self.assertEquals(decoded.an_integer, 1)
        self.assertEquals(decoded.all_unrecognized_fields(), [])

    def testUnrecognizedFieldVariants(self):
        """Test that unrecognized fields are mapped to the right variants."""
        for encoded, expected_variant in (
                ('{"an_integer": 1, "unknown_val": 2}',
                 messages.Variant.INT64),
                ('{"an_integer": 1, "unknown_val": 2.0}',
                 messages.Variant.DOUBLE),
                ('{"an_integer": 1, "unknown_val": "string value"}',
                 messages.Variant.STRING),
                ('{"an_integer": 1, "unknown_val": [1, 2, 3]}',
                 messages.Variant.INT64),
                ('{"an_integer": 1, "unknown_val": [1, 2.0, 3]}',
                 messages.Variant.DOUBLE),
                ('{"an_integer": 1, "unknown_val": [1, "foo", 3]}',
                 messages.Variant.STRING),
                ('{"an_integer": 1, "unknown_val": true}',
                 messages.Variant.BOOL)):
            decoded = protojson.decode_message(MyMessage, encoded)
            self.assertEquals(decoded.an_integer, 1)
            self.assertEquals(1, len(decoded.all_unrecognized_fields()))
            self.assertEquals(
                'unknown_val', decoded.all_unrecognized_fields()[0])
            _, decoded_variant = decoded.get_unrecognized_field_info(
                'unknown_val')
            self.assertEquals(expected_variant, decoded_variant)

    def testDecodeDateTime(self):
        for datetime_string, datetime_vals in (
                ('2012-09-30T15:31:50.262', (2012, 9, 30, 15, 31, 50, 262000)),
                ('2012-09-30T15:31:50', (2012, 9, 30, 15, 31, 50, 0))):
            message = protojson.decode_message(
                MyMessage, '{"a_datetime": "%s"}' % datetime_string)
            expected_message = MyMessage(
                a_datetime=datetime.datetime(*datetime_vals))

            self.assertEquals(expected_message, message)

    def testDecodeInvalidDateTime(self):
        self.assertRaises(messages.DecodeError, protojson.decode_message,
                          MyMessage, '{"a_datetime": "invalid"}')

    def testDecodeInvalidMessage(self):
        encoded = """{
        "a_nested_datetime": {
          "nested_dt_value": "invalid"
          }
        }
        """
        self.assertRaises(messages.DecodeError, protojson.decode_message,
                          MyMessage, encoded)

    def testEncodeDateTime(self):
        for datetime_string, datetime_vals in (
                ('2012-09-30T15:31:50.262000',
                 (2012, 9, 30, 15, 31, 50, 262000)),
                ('2012-09-30T15:31:50.262123',
                 (2012, 9, 30, 15, 31, 50, 262123)),
                ('2012-09-30T15:31:50',
                 (2012, 9, 30, 15, 31, 50, 0))):
            decoded_message = protojson.encode_message(
                MyMessage(a_datetime=datetime.datetime(*datetime_vals)))
            expected_decoding = '{"a_datetime": "%s"}' % datetime_string
            self.CompareEncoded(expected_decoding, decoded_message)

    def testDecodeRepeatedDateTime(self):
        message = protojson.decode_message(
            MyMessage,
            '{"a_repeated_datetime": ["2012-09-30T15:31:50.262", '
            '"2010-01-21T09:52:00", "2000-01-01T01:00:59.999999"]}')
        expected_message = MyMessage(
            a_repeated_datetime=[
                datetime.datetime(2012, 9, 30, 15, 31, 50, 262000),
                datetime.datetime(2010, 1, 21, 9, 52),
                datetime.datetime(2000, 1, 1, 1, 0, 59, 999999)])

        self.assertEquals(expected_message, message)

    def testDecodeCustom(self):
        message = protojson.decode_message(MyMessage, '{"a_custom": 1}')
        self.assertEquals(MyMessage(a_custom=1), message)

    def testDecodeInvalidCustom(self):
        self.assertRaises(messages.ValidationError, protojson.decode_message,
                          MyMessage, '{"a_custom": "invalid"}')

    def testEncodeCustom(self):
        decoded_message = protojson.encode_message(MyMessage(a_custom=1))
        self.CompareEncoded('{"a_custom": 1}', decoded_message)

    def testDecodeRepeatedCustom(self):
        message = protojson.decode_message(
            MyMessage, '{"a_repeated_custom": [1, 2, 3]}')
        self.assertEquals(MyMessage(a_repeated_custom=[1, 2, 3]), message)

    def testDecodeRepeatedEmpty(self):
        message = protojson.decode_message(
            MyMessage, '{"a_repeated": []}')
        self.assertEquals(MyMessage(a_repeated=[]), message)

    def testDecodeNone(self):
        message = protojson.decode_message(
            MyMessage, '{"an_integer": []}')
        self.assertEquals(MyMessage(an_integer=None), message)

    def testDecodeBadBase64BytesField(self):
        """Test decoding improperly encoded base64 bytes value."""
        self.assertRaisesWithRegexpMatch(
            messages.DecodeError,
            'Base64 decoding error: Incorrect padding',
            protojson.decode_message,
            test_util.OptionalMessage,
            '{"bytes_value": "abcdefghijklmnopq"}')


class CustomProtoJson(protojson.ProtoJson):

    def encode_field(self, field, value):
        return '{encoded}' + value

    def decode_field(self, field, value):
        return '{decoded}' + value


class CustomProtoJsonTest(test_util.TestCase):
    """Tests for serialization overriding functionality."""

    def setUp(self):
        self.protojson = CustomProtoJson()

    def testEncode(self):
        self.assertEqual(
            '{"a_string": "{encoded}xyz"}',
            self.protojson.encode_message(MyMessage(a_string='xyz')))

    def testDecode(self):
        self.assertEqual(
            MyMessage(a_string='{decoded}xyz'),
            self.protojson.decode_message(MyMessage, '{"a_string": "xyz"}'))

    def testDecodeEmptyMessage(self):
        self.assertEqual(
            MyMessage(a_string='{decoded}'),
            self.protojson.decode_message(MyMessage, '{"a_string": ""}'))

    def testDefault(self):
        self.assertTrue(protojson.ProtoJson.get_default(),
                        protojson.ProtoJson.get_default())

        instance = CustomProtoJson()
        protojson.ProtoJson.set_default(instance)
        self.assertTrue(instance is protojson.ProtoJson.get_default())


if __name__ == '__main__':
    unittest.main()
