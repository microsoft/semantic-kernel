# -*- coding: utf-8 -*-
# Copyright 2015 Google Inc.
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

import base64
import datetime
import json
import sys
import unittest

from apitools.base.protorpclite import message_types
from apitools.base.protorpclite import messages
from apitools.base.protorpclite import util
from apitools.base.py import encoding
from apitools.base.py import exceptions
from apitools.base.py import extra_types


class SimpleMessage(messages.Message):
    field = messages.StringField(1)
    repfield = messages.StringField(2, repeated=True)


class BytesMessage(messages.Message):
    field = messages.BytesField(1)
    repfield = messages.BytesField(2, repeated=True)


class TimeMessage(messages.Message):
    timefield = message_types.DateTimeField(3)


@encoding.MapUnrecognizedFields('additionalProperties')
class AdditionalPropertiesMessage(messages.Message):

    class AdditionalProperty(messages.Message):
        key = messages.StringField(1)
        value = messages.StringField(2)

    additionalProperties = messages.MessageField(
        'AdditionalProperty', 1, repeated=True)


@encoding.MapUnrecognizedFields('additionalProperties')
class AdditionalIntPropertiesMessage(messages.Message):

    class AdditionalProperty(messages.Message):
        key = messages.StringField(1)
        value = messages.IntegerField(2)

    additionalProperties = messages.MessageField(
        'AdditionalProperty', 1, repeated=True)


@encoding.MapUnrecognizedFields('additionalProperties')
class UnrecognizedEnumMessage(messages.Message):

    class ThisEnum(messages.Enum):
        VALUE_ONE = 1
        VALUE_TWO = 2

    class AdditionalProperty(messages.Message):
        key = messages.StringField(1)
        value = messages.EnumField('UnrecognizedEnumMessage.ThisEnum', 2)

    additionalProperties = messages.MessageField(
        AdditionalProperty, 1, repeated=True)


class CompoundPropertyType(messages.Message):
    index = messages.IntegerField(1)
    name = messages.StringField(2)


class MessageWithEnum(messages.Message):

    class ThisEnum(messages.Enum):
        VALUE_ONE = 1
        VALUE_TWO = 2

    field_one = messages.EnumField(ThisEnum, 1)
    field_two = messages.EnumField(ThisEnum, 2, default=ThisEnum.VALUE_TWO)
    ignored_field = messages.EnumField(ThisEnum, 3)


@encoding.MapUnrecognizedFields('additionalProperties')
class AdditionalMessagePropertiesMessage(messages.Message):

    class AdditionalProperty(messages.Message):
        key = messages.StringField(1)
        value = messages.MessageField(CompoundPropertyType, 2)

    additionalProperties = messages.MessageField(
        'AdditionalProperty', 1, repeated=True)


@encoding.MapUnrecognizedFields('additionalProperties')
class MapToMessageWithEnum(messages.Message):

    class AdditionalProperty(messages.Message):
        key = messages.StringField(1)
        value = messages.MessageField(MessageWithEnum, 2)

    additionalProperties = messages.MessageField(
        'AdditionalProperty', 1, repeated=True)


@encoding.MapUnrecognizedFields('additionalProperties')
class NestedAdditionalPropertiesWithEnumMessage(messages.Message):

    class AdditionalProperty(messages.Message):
        key = messages.StringField(1)
        value = messages.MessageField(
            MapToMessageWithEnum, 2)

    additionalProperties = messages.MessageField(
        'AdditionalProperty', 1, repeated=True)


@encoding.MapUnrecognizedFields('additionalProperties')
class AdditionalPropertiesWithEnumMessage(messages.Message):

    class AdditionalProperty(messages.Message):
        key = messages.StringField(1)
        value = messages.MessageField(MessageWithEnum, 2)

    additionalProperties = messages.MessageField(
        'AdditionalProperty', 1, repeated=True)


class NestedMapMessage(messages.Message):

    msg_field = messages.MessageField(AdditionalPropertiesWithEnumMessage, 1)


class RepeatedNestedMapMessage(messages.Message):

    map_field = messages.MessageField(NestedMapMessage, 1, repeated=True)


class NestedWithEnumMessage(messages.Message):

    class ThisEnum(messages.Enum):
        VALUE_ONE = 1
        VALUE_TWO = 2

    msg_field = messages.MessageField(MessageWithEnum, 1)
    enum_field = messages.EnumField(ThisEnum, 2)


class RepeatedNestedMessage(messages.Message):

    msg_field = messages.MessageField(SimpleMessage, 1, repeated=True)


@encoding.MapUnrecognizedFields('additionalProperties')
class MapToBytesValue(messages.Message):
    class AdditionalProperty(messages.Message):
        key = messages.StringField(1)
        value = messages.BytesField(2)

    additionalProperties = messages.MessageField('AdditionalProperty', 1,
                                                 repeated=True)


@encoding.MapUnrecognizedFields('additionalProperties')
class MapToDateTimeValue(messages.Message):
    class AdditionalProperty(messages.Message):
        key = messages.StringField(1)
        value = message_types.DateTimeField(2)

    additionalProperties = messages.MessageField('AdditionalProperty', 1,
                                                 repeated=True)


class HasNestedMessage(messages.Message):
    nested = messages.MessageField(AdditionalPropertiesMessage, 1)
    nested_list = messages.StringField(2, repeated=True)


class ExtraNestedMessage(messages.Message):
    nested = messages.MessageField(HasNestedMessage, 1)


class MessageWithRemappings(messages.Message):

    class SomeEnum(messages.Enum):
        enum_value = 1
        second_value = 2

    enum_field = messages.EnumField(SomeEnum, 1)
    double_encoding = messages.EnumField(SomeEnum, 2)
    another_field = messages.StringField(3)
    repeated_enum = messages.EnumField(SomeEnum, 4, repeated=True)
    repeated_field = messages.StringField(5, repeated=True)


class MessageWithPackageAndRemappings(messages.Message):

    class SomeEnum(messages.Enum):
        enum_value = 1
        second_value = 2

    enum_field = messages.EnumField(SomeEnum, 1)
    another_field = messages.StringField(2)


@encoding.MapUnrecognizedFields('additionalProperties')
class RepeatedJsonValueMessage(messages.Message):

    class AdditionalProperty(messages.Message):
        key = messages.StringField(1)
        value = messages.MessageField(extra_types.JsonValue, 2, repeated=True)

    additionalProperties = messages.MessageField('AdditionalProperty', 1,
                                                 repeated=True)


encoding.AddCustomJsonEnumMapping(MessageWithRemappings.SomeEnum,
                                  'enum_value', 'wire_name')
encoding.AddCustomJsonFieldMapping(MessageWithRemappings,
                                   'double_encoding', 'doubleEncoding')
encoding.AddCustomJsonFieldMapping(MessageWithRemappings,
                                   'another_field', 'anotherField')
encoding.AddCustomJsonFieldMapping(MessageWithRemappings,
                                   'repeated_field', 'repeatedField')


class EncodingTest(unittest.TestCase):

    def testCopyProtoMessage(self):
        msg = SimpleMessage(field='abc')
        new_msg = encoding.CopyProtoMessage(msg)
        self.assertEqual(msg.field, new_msg.field)
        msg.field = 'def'
        self.assertNotEqual(msg.field, new_msg.field)

    def testCopyProtoMessageInvalidEnum(self):
        json_msg = '{"field_one": "BAD_VALUE"}'
        orig_msg = encoding.JsonToMessage(MessageWithEnum, json_msg)
        new_msg = encoding.CopyProtoMessage(orig_msg)
        for msg in (orig_msg, new_msg):
            self.assertEqual(msg.all_unrecognized_fields(), ['field_one'])
            self.assertEqual(
                msg.get_unrecognized_field_info('field_one',
                                                value_default=None),
                ('BAD_VALUE', messages.Variant.ENUM))

    def testCopyProtoMessageAdditionalProperties(self):
        msg = AdditionalPropertiesMessage(additionalProperties=[
            AdditionalPropertiesMessage.AdditionalProperty(
                key='key', value='value')])
        new_msg = encoding.CopyProtoMessage(msg)
        self.assertEqual(len(new_msg.additionalProperties), 1)
        self.assertEqual(new_msg.additionalProperties[0].key, 'key')
        self.assertEqual(new_msg.additionalProperties[0].value, 'value')

    def testCopyProtoMessageMappingInvalidEnum(self):
        json_msg = '{"key_one": {"field_one": "BAD_VALUE"}}'
        orig_msg = encoding.JsonToMessage(MapToMessageWithEnum, json_msg)
        new_msg = encoding.CopyProtoMessage(orig_msg)
        for msg in (orig_msg, new_msg):
            self.assertEqual(
                msg.additionalProperties[0].value.all_unrecognized_fields(),
                ['field_one'])
            self.assertEqual(
                msg.additionalProperties[0].value.get_unrecognized_field_info(
                    'field_one', value_default=None),
                ('BAD_VALUE', messages.Variant.ENUM))

    def testBytesEncoding(self):
        b64_str = 'AAc+'
        b64_msg = '{"field": "%s"}' % b64_str
        urlsafe_b64_str = 'AAc-'
        urlsafe_b64_msg = '{"field": "%s"}' % urlsafe_b64_str
        data = base64.b64decode(b64_str)
        msg = BytesMessage(field=data)
        self.assertEqual(
            msg, encoding.JsonToMessage(BytesMessage, urlsafe_b64_msg))
        self.assertEqual(msg, encoding.JsonToMessage(BytesMessage, b64_msg))
        self.assertEqual(urlsafe_b64_msg, encoding.MessageToJson(msg))

        enc_rep_msg = '{"repfield": ["%(b)s", "%(b)s"]}' % {
            'b': urlsafe_b64_str}
        rep_msg = BytesMessage(repfield=[data, data])
        self.assertEqual(
            rep_msg, encoding.JsonToMessage(BytesMessage, enc_rep_msg))
        self.assertEqual(enc_rep_msg, encoding.MessageToJson(rep_msg))

    def testBase64RoundtripForMapFields(self):
        raw_data = b'\xFF\x0F\x80'
        encoded_data = '/w+A'  # Has url-unsafe base64 characters
        safe_encoded_data = base64.urlsafe_b64encode(raw_data).decode("utf-8")
        self.assertEqual(raw_data, base64.b64decode(encoded_data))

        # Use unsafe encoding, make sure we can load it.
        json_data = '{"1st": "%s"}' % encoded_data
        msg = encoding.JsonToMessage(MapToBytesValue, json_data)
        self.assertEqual(raw_data, msg.additionalProperties[0].value)

        # Now back to json and again to message
        from_msg_json_data = encoding.MessageToJson(msg)
        # Make sure now it is safe url encoded
        self.assertEqual(safe_encoded_data,
                         json.loads(from_msg_json_data)['1st'])
        # Make sure we can also load url safe encoded bytes.
        redone_msg = encoding.JsonToMessage(MapToBytesValue,
                                            from_msg_json_data)
        # Still matches
        self.assertEqual(raw_data, redone_msg.additionalProperties[0].value)

    def testBytesEncodingInAMap(self):
        # Leading bit is 1 should not be interpreted as unicode.
        data1 = b'\xF0\x11\x0F'
        data2 = b'\xFF\xFF\xFF'

        msg = MapToBytesValue(
            additionalProperties=[
                MapToBytesValue.AdditionalProperty(key='1st', value=data1),
                MapToBytesValue.AdditionalProperty(key='2nd', value=data2)
            ])

        self.assertEqual(
            '{"1st": "%s", "2nd": "%s"}' % (
                base64.b64encode(data1, b'-_').decode("utf-8"),
                base64.b64encode(data2, b'-_').decode("utf-8")),
            encoding.MessageToJson(msg))

    def testDateTimeEncodingInAMap(self):
        msg = MapToDateTimeValue(
            additionalProperties=[
                MapToDateTimeValue.AdditionalProperty(
                    key='1st',
                    value=datetime.datetime(
                        2014, 7, 2, 23, 33, 25, 541000,
                        tzinfo=util.TimeZoneOffset(datetime.timedelta(0)))),
                MapToDateTimeValue.AdditionalProperty(
                    key='2nd',
                    value=datetime.datetime(
                        2015, 7, 2, 23, 33, 25, 541000,
                        tzinfo=util.TimeZoneOffset(datetime.timedelta(0))))
            ])

        self.assertEqual(
            '{"1st": "2014-07-02T23:33:25.541000+00:00",'
            ' "2nd": "2015-07-02T23:33:25.541000+00:00"}',
            encoding.MessageToJson(msg))

    def testInvalidEnumEncodingInAMap(self):
        json_msg = '{"key_one": {"field_one": "BAD_VALUE"}}'
        msg = encoding.JsonToMessage(MapToMessageWithEnum, json_msg)
        new_msg = encoding.MessageToJson(msg)
        self.assertEqual('{"key_one": {"field_one": "BAD_VALUE"}}', new_msg)

    def testIncludeFields(self):
        msg = SimpleMessage()
        self.assertEqual('{}', encoding.MessageToJson(msg))
        self.assertEqual(
            '{"field": null}',
            encoding.MessageToJson(msg, include_fields=['field']))
        self.assertEqual(
            '{"repfield": []}',
            encoding.MessageToJson(msg, include_fields=['repfield']))

    def testNestedIncludeFields(self):
        msg = HasNestedMessage(
            nested=AdditionalPropertiesMessage(
                additionalProperties=[]))
        self.assertEqual(
            '{"nested": null}',
            encoding.MessageToJson(msg, include_fields=['nested']))
        self.assertEqual(
            '{"nested": {"additionalProperties": []}}',
            encoding.MessageToJson(
                msg, include_fields=['nested.additionalProperties']))
        msg = ExtraNestedMessage(nested=msg)
        self.assertEqual(
            '{"nested": {"nested": null}}',
            encoding.MessageToJson(msg, include_fields=['nested.nested']))
        # When clearing 'nested.nested_list', its sibling ('nested.nested')
        # should remain unaffected.
        self.assertIn(
            encoding.MessageToJson(msg, include_fields=['nested.nested_list']),
            ['{"nested": {"nested": {}, "nested_list": []}}',
             '{"nested": {"nested_list": [], "nested": {}}}'])
        self.assertEqual(
            '{"nested": {"nested": {"additionalProperties": []}}}',
            encoding.MessageToJson(
                msg, include_fields=['nested.nested.additionalProperties']))

    def testAdditionalPropertyMapping(self):
        msg = AdditionalPropertiesMessage()
        msg.additionalProperties = [
            AdditionalPropertiesMessage.AdditionalProperty(
                key='key_one', value='value_one'),
            AdditionalPropertiesMessage.AdditionalProperty(
                key=u'key_twð', value='value_two'),
        ]

        encoded_msg = encoding.MessageToJson(msg)
        self.assertEqual(
            {'key_one': 'value_one', u'key_twð': 'value_two'},
            json.loads(encoded_msg))

        new_msg = encoding.JsonToMessage(type(msg), encoded_msg)
        self.assertEqual(
            set(('key_one', u'key_twð')),
            set([x.key for x in new_msg.additionalProperties]))
        self.assertIsNot(msg, new_msg)

        new_msg.additionalProperties.pop()
        self.assertEqual(1, len(new_msg.additionalProperties))
        self.assertEqual(2, len(msg.additionalProperties))

    def testNumericPropertyName(self):
        json_msg = '{"nested": {"123": "def"}}'
        msg = encoding.JsonToMessage(HasNestedMessage, json_msg)
        self.assertEqual(1, len(msg.nested.additionalProperties))

    def testNumericPropertyValue(self):
        json_msg = '{"key_one": "123"}'
        msg = encoding.JsonToMessage(AdditionalIntPropertiesMessage, json_msg)
        self.assertEqual(
            AdditionalIntPropertiesMessage(
                additionalProperties=[
                    AdditionalIntPropertiesMessage.AdditionalProperty(
                        key='key_one', value=123)]),
            msg)

    def testAdditionalMessageProperties(self):
        json_msg = '{"input": {"index": 0, "name": "output"}}'
        result = encoding.JsonToMessage(
            AdditionalMessagePropertiesMessage, json_msg)
        self.assertEqual(1, len(result.additionalProperties))
        self.assertEqual(0, result.additionalProperties[0].value.index)

    def testUnrecognizedEnum(self):
        json_msg = '{"input": "VALUE_ONE"}'
        result = encoding.JsonToMessage(
            UnrecognizedEnumMessage, json_msg)
        self.assertEqual(1, len(result.additionalProperties))
        self.assertEqual(UnrecognizedEnumMessage.ThisEnum.VALUE_ONE,
                         result.additionalProperties[0].value)

    def testNestedFieldMapping(self):
        nested_msg = AdditionalPropertiesMessage()
        nested_msg.additionalProperties = [
            AdditionalPropertiesMessage.AdditionalProperty(
                key='key_one', value='value_one'),
            AdditionalPropertiesMessage.AdditionalProperty(
                key='key_two', value='value_two'),
        ]
        msg = HasNestedMessage(nested=nested_msg)

        encoded_msg = encoding.MessageToJson(msg)
        self.assertEqual(
            {'nested': {'key_one': 'value_one', 'key_two': 'value_two'}},
            json.loads(encoded_msg))

        new_msg = encoding.JsonToMessage(type(msg), encoded_msg)
        self.assertEqual(
            set(('key_one', 'key_two')),
            set([x.key for x in new_msg.nested.additionalProperties]))

        new_msg.nested.additionalProperties.pop()
        self.assertEqual(1, len(new_msg.nested.additionalProperties))
        self.assertEqual(2, len(msg.nested.additionalProperties))

    def testValidEnums(self):
        message_json = '{"field_one": "VALUE_ONE"}'
        message = encoding.JsonToMessage(MessageWithEnum, message_json)
        self.assertEqual(MessageWithEnum.ThisEnum.VALUE_ONE, message.field_one)
        self.assertEqual(MessageWithEnum.ThisEnum.VALUE_TWO, message.field_two)
        self.assertEqual(json.loads(message_json),
                         json.loads(encoding.MessageToJson(message)))

    def testIgnoredEnums(self):
        json_with_typo = '{"field_one": "VALUE_OEN"}'
        message = encoding.JsonToMessage(MessageWithEnum, json_with_typo)
        self.assertEqual(None, message.field_one)
        self.assertEqual(('VALUE_OEN', messages.Variant.ENUM),
                         message.get_unrecognized_field_info('field_one'))
        self.assertEqual(json.loads(json_with_typo),
                         json.loads(encoding.MessageToJson(message)))

        empty_json = ''
        message = encoding.JsonToMessage(MessageWithEnum, empty_json)
        self.assertEqual(None, message.field_one)

    def testIgnoredEnumsWithDefaults(self):
        json_with_typo = '{"field_two": "VALUE_OEN"}'
        message = encoding.JsonToMessage(MessageWithEnum, json_with_typo)
        self.assertEqual(MessageWithEnum.ThisEnum.VALUE_TWO, message.field_two)
        self.assertEqual(json.loads(json_with_typo),
                         json.loads(encoding.MessageToJson(message)))

    def testUnknownNestedRoundtrip(self):
        json_message = '{"field": "abc", "submessage": {"a": 1, "b": "foo"}}'
        message = encoding.JsonToMessage(SimpleMessage, json_message)
        self.assertEqual(json.loads(json_message),
                         json.loads(encoding.MessageToJson(message)))

    def testUnknownEnumNestedRoundtrip(self):
        json_with_typo = ('{"outer_key": {"key_one": {"field_one": '
                          '"VALUE_OEN", "field_two": "VALUE_OEN"}}}')
        msg = encoding.JsonToMessage(NestedAdditionalPropertiesWithEnumMessage,
                                     json_with_typo)
        self.assertEqual(json.loads(json_with_typo),
                         json.loads(encoding.MessageToJson(msg)))

    def testJsonDatetime(self):
        msg = TimeMessage(timefield=datetime.datetime(
            2014, 7, 2, 23, 33, 25, 541000,
            tzinfo=util.TimeZoneOffset(datetime.timedelta(0))))
        self.assertEqual(
            '{"timefield": "2014-07-02T23:33:25.541000+00:00"}',
            encoding.MessageToJson(msg))

    def testEnumRemapping(self):
        msg = MessageWithRemappings(
            enum_field=MessageWithRemappings.SomeEnum.enum_value)
        json_message = encoding.MessageToJson(msg)
        self.assertEqual('{"enum_field": "wire_name"}', json_message)
        self.assertEqual(
            msg, encoding.JsonToMessage(MessageWithRemappings, json_message))

    def testRepeatedEnumRemapping(self):
        msg = MessageWithRemappings(
            repeated_enum=[
                MessageWithRemappings.SomeEnum.enum_value,
                MessageWithRemappings.SomeEnum.second_value,
            ])
        json_message = encoding.MessageToJson(msg)
        self.assertEqual('{"repeated_enum": ["wire_name", "second_value"]}',
                         json_message)
        self.assertEqual(
            msg, encoding.JsonToMessage(MessageWithRemappings, json_message))

    def testFieldRemapping(self):
        msg = MessageWithRemappings(another_field='abc')
        json_message = encoding.MessageToJson(msg)
        self.assertEqual('{"anotherField": "abc"}', json_message)
        self.assertEqual(
            msg, encoding.JsonToMessage(MessageWithRemappings, json_message))

    def testFieldRemappingWithPackage(self):
        this_module = sys.modules[__name__]
        package_name = 'my_package'
        try:
            setattr(this_module, 'package', package_name)

            encoding.AddCustomJsonFieldMapping(
                MessageWithPackageAndRemappings,
                'another_field', 'wire_field_name', package=package_name)

            msg = MessageWithPackageAndRemappings(another_field='my value')
            json_message = encoding.MessageToJson(msg)
            self.assertEqual('{"wire_field_name": "my value"}', json_message)
            self.assertEqual(
                msg,
                encoding.JsonToMessage(MessageWithPackageAndRemappings,
                                       json_message))
        finally:
            delattr(this_module, 'package')

    def testEnumRemappingWithPackage(self):
        this_module = sys.modules[__name__]
        package_name = 'my_package'
        try:
            setattr(this_module, 'package', package_name)

            encoding.AddCustomJsonEnumMapping(
                MessageWithPackageAndRemappings.SomeEnum,
                'enum_value', 'other_wire_name', package=package_name)

            msg = MessageWithPackageAndRemappings(
                enum_field=MessageWithPackageAndRemappings.SomeEnum.enum_value)
            json_message = encoding.MessageToJson(msg)
            self.assertEqual('{"enum_field": "other_wire_name"}', json_message)
            self.assertEqual(
                msg,
                encoding.JsonToMessage(MessageWithPackageAndRemappings,
                                       json_message))

        finally:
            delattr(this_module, 'package')

    def testRepeatedFieldRemapping(self):
        msg = MessageWithRemappings(repeated_field=['abc', 'def'])
        json_message = encoding.MessageToJson(msg)
        self.assertEqual('{"repeatedField": ["abc", "def"]}', json_message)
        self.assertEqual(
            msg, encoding.JsonToMessage(MessageWithRemappings, json_message))

    def testMultipleRemapping(self):
        msg = MessageWithRemappings(
            double_encoding=MessageWithRemappings.SomeEnum.enum_value)
        json_message = encoding.MessageToJson(msg)
        self.assertEqual('{"doubleEncoding": "wire_name"}', json_message)
        self.assertEqual(
            msg, encoding.JsonToMessage(MessageWithRemappings, json_message))

    def testRepeatedRemapping(self):
        # Should allow remapping if the mapping remains the same.
        encoding.AddCustomJsonEnumMapping(MessageWithRemappings.SomeEnum,
                                          'enum_value', 'wire_name')
        encoding.AddCustomJsonFieldMapping(MessageWithRemappings,
                                           'double_encoding', 'doubleEncoding')
        encoding.AddCustomJsonFieldMapping(MessageWithRemappings,
                                           'another_field', 'anotherField')
        encoding.AddCustomJsonFieldMapping(MessageWithRemappings,
                                           'repeated_field', 'repeatedField')

        # Should raise errors if the remapping changes the mapping.
        self.assertRaises(
            exceptions.InvalidDataError,
            encoding.AddCustomJsonFieldMapping,
            MessageWithRemappings, 'double_encoding', 'something_else')
        self.assertRaises(
            exceptions.InvalidDataError,
            encoding.AddCustomJsonFieldMapping,
            MessageWithRemappings, 'enum_field', 'anotherField')
        self.assertRaises(
            exceptions.InvalidDataError,
            encoding.AddCustomJsonEnumMapping,
            MessageWithRemappings.SomeEnum, 'enum_value', 'another_name')
        self.assertRaises(
            exceptions.InvalidDataError,
            encoding.AddCustomJsonEnumMapping,
            MessageWithRemappings.SomeEnum, 'second_value', 'wire_name')

    def testMessageToRepr(self):
        # Using the same string returned by MessageToRepr, with the
        # module names fixed.
        # pylint: disable=bad-whitespace
        msg = SimpleMessage(field='field', repfield=['field', 'field', ],)
        # pylint: enable=bad-whitespace
        self.assertEqual(
            encoding.MessageToRepr(msg),
            r"%s.SimpleMessage(field='field',repfield=['field','field',],)" % (
                __name__,))
        self.assertEqual(
            encoding.MessageToRepr(msg, no_modules=True),
            r"SimpleMessage(field='field',repfield=['field','field',],)")

    def testMessageToReprWithTime(self):
        msg = TimeMessage(timefield=datetime.datetime(
            2014, 7, 2, 23, 33, 25, 541000,
            tzinfo=util.TimeZoneOffset(datetime.timedelta(0))))
        self.assertEqual(
            encoding.MessageToRepr(msg, multiline=True),
            ('%s.TimeMessage(\n    '
             'timefield=datetime.datetime(2014, 7, 2, 23, 33, 25, 541000, '
             'tzinfo=apitools.base.protorpclite.util.TimeZoneOffset('
             'datetime.timedelta(0))),\n)') % __name__)
        self.assertEqual(
            encoding.MessageToRepr(msg, multiline=True, no_modules=True),
            'TimeMessage(\n    '
            'timefield=datetime.datetime(2014, 7, 2, 23, 33, 25, 541000, '
            'tzinfo=TimeZoneOffset(datetime.timedelta(0))),\n)')

    def testRepeatedJsonValuesAsRepeatedProperty(self):
        encoded_msg = '{"a": [{"one": 1}]}'
        msg = encoding.JsonToMessage(RepeatedJsonValueMessage, encoded_msg)
        self.assertEqual(encoded_msg, encoding.MessageToJson(msg))

    def testDictToAdditionalPropertyMessage(self):
        dict_ = {'key': 'value'}

        encoded_msg = encoding.DictToAdditionalPropertyMessage(
            dict_, AdditionalPropertiesMessage)
        expected_msg = AdditionalPropertiesMessage()
        expected_msg.additionalProperties = [
            AdditionalPropertiesMessage.AdditionalProperty(
                key='key', value='value')
        ]
        self.assertEqual(encoded_msg, expected_msg)

    def testDictToAdditionalPropertyMessageSorted(self):
        tuples = [('key{0:02}'.format(i), 'value') for i in range(100)]
        dict_ = dict(tuples)

        encoded_msg = encoding.DictToAdditionalPropertyMessage(
            dict_, AdditionalPropertiesMessage, sort_items=True)
        expected_msg = AdditionalPropertiesMessage()
        expected_msg.additionalProperties = [
            AdditionalPropertiesMessage.AdditionalProperty(
                key=key, value=value)
            for key, value in tuples
        ]
        self.assertEqual(encoded_msg, expected_msg)

    def testDictToAdditionalPropertyMessageNumeric(self):
        dict_ = {'key': 1}

        encoded_msg = encoding.DictToAdditionalPropertyMessage(
            dict_, AdditionalIntPropertiesMessage)
        expected_msg = AdditionalIntPropertiesMessage()
        expected_msg.additionalProperties = [
            AdditionalIntPropertiesMessage.AdditionalProperty(
                key='key', value=1)
        ]
        self.assertEqual(encoded_msg, expected_msg)

    def testUnrecognizedFieldIter(self):
        m = encoding.DictToMessage({
            'nested': {
                'nested': {'a': 'b'},
                'nested_list': ['foo'],
                'extra_field': 'foo',
            }
        }, ExtraNestedMessage)
        results = list(encoding.UnrecognizedFieldIter(m))
        self.assertEqual(1, len(results))
        edges, fields = results[0]
        expected_edge = encoding.ProtoEdge(
            encoding.EdgeType.SCALAR, 'nested', None)
        self.assertEqual((expected_edge,), edges)
        self.assertEqual(['extra_field'], fields)

    def testUnrecognizedFieldIterRepeated(self):
        m = encoding.DictToMessage({
            'msg_field': [
                {'field': 'foo'},
                {'not_a_field': 'bar'}
            ]
        }, RepeatedNestedMessage)
        results = list(encoding.UnrecognizedFieldIter(m))
        self.assertEqual(1, len(results))
        edges, fields = results[0]
        expected_edge = encoding.ProtoEdge(
            encoding.EdgeType.REPEATED, 'msg_field', 1)
        self.assertEqual((expected_edge,), edges)
        self.assertEqual(['not_a_field'], fields)

    def testUnrecognizedFieldIterNestedMap(self):
        m = encoding.DictToMessage({
            'map_field': [{
                'msg_field': {
                    'foo': {'field_one': 1},
                    'bar': {'not_a_field': 1},
                }
            }]
        }, RepeatedNestedMapMessage)
        results = list(encoding.UnrecognizedFieldIter(m))
        self.assertEqual(1, len(results))
        edges, fields = results[0]
        expected_edges = (
            encoding.ProtoEdge(encoding.EdgeType.REPEATED, 'map_field', 0),
            encoding.ProtoEdge(encoding.EdgeType.MAP, 'msg_field', 'bar'),
        )
        self.assertEqual(expected_edges, edges)
        self.assertEqual(['not_a_field'], fields)

    def testUnrecognizedFieldIterAbortAfterFirstError(self):
        m = encoding.DictToMessage({
            'msg_field': {'field_one': 3},
            'enum_field': 3,
        }, NestedWithEnumMessage)
        self.assertEqual(1, len(list(encoding.UnrecognizedFieldIter(m))))
