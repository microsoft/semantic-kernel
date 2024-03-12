#
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

import datetime
import json
import math
import unittest

from apitools.base.protorpclite import messages
from apitools.base.py import encoding
from apitools.base.py import exceptions
from apitools.base.py import extra_types


class ExtraTypesTest(unittest.TestCase):

    def assertRoundTrip(self, value):
        if isinstance(value, extra_types._JSON_PROTO_TYPES):
            self.assertEqual(
                value,
                extra_types._PythonValueToJsonProto(
                    extra_types._JsonProtoToPythonValue(value)))
        else:
            self.assertEqual(
                value,
                extra_types._JsonProtoToPythonValue(
                    extra_types._PythonValueToJsonProto(value)))

    def assertTranslations(self, py_value, json_proto):
        self.assertEqual(
            py_value, extra_types._JsonProtoToPythonValue(json_proto))
        self.assertEqual(
            json_proto, extra_types._PythonValueToJsonProto(py_value))

    def testInvalidProtos(self):
        with self.assertRaises(exceptions.InvalidDataError):
            extra_types._ValidateJsonValue(extra_types.JsonValue())
        with self.assertRaises(exceptions.InvalidDataError):
            extra_types._ValidateJsonValue(
                extra_types.JsonValue(is_null=True, string_value='a'))
        with self.assertRaises(exceptions.InvalidDataError):
            extra_types._ValidateJsonValue(
                extra_types.JsonValue(integer_value=3, string_value='a'))

    def testNullEncoding(self):
        self.assertTranslations(None, extra_types.JsonValue(is_null=True))

    def testJsonNumberEncoding(self):
        seventeen = extra_types.JsonValue(integer_value=17)
        self.assertRoundTrip(17)
        self.assertRoundTrip(seventeen)
        self.assertTranslations(17, seventeen)

        json_pi = extra_types.JsonValue(double_value=math.pi)
        self.assertRoundTrip(math.pi)
        self.assertRoundTrip(json_pi)
        self.assertTranslations(math.pi, json_pi)

    def testArrayEncoding(self):
        array = [3, 'four', False]
        json_array = extra_types.JsonArray(entries=[
            extra_types.JsonValue(integer_value=3),
            extra_types.JsonValue(string_value='four'),
            extra_types.JsonValue(boolean_value=False),
        ])
        self.assertRoundTrip(array)
        self.assertRoundTrip(json_array)
        self.assertTranslations(array, json_array)

    def testArrayAsValue(self):
        array_json = '[3, "four", false]'
        array = [3, 'four', False]
        value = encoding.JsonToMessage(extra_types.JsonValue, array_json)
        self.assertTrue(isinstance(value, extra_types.JsonValue))
        self.assertEqual(array, encoding.MessageToPyValue(value))

    def testObjectAsValue(self):
        obj_json = '{"works": true}'
        obj = {'works': True}
        value = encoding.JsonToMessage(extra_types.JsonValue, obj_json)
        self.assertTrue(isinstance(value, extra_types.JsonValue))
        self.assertEqual(obj, encoding.MessageToPyValue(value))

    def testDictEncoding(self):
        d = {'a': 6, 'b': 'eleventeen'}
        json_d = extra_types.JsonObject(properties=[
            extra_types.JsonObject.Property(
                key='a', value=extra_types.JsonValue(integer_value=6)),
            extra_types.JsonObject.Property(
                key='b',
                value=extra_types.JsonValue(string_value='eleventeen')),
        ])
        self.assertRoundTrip(d)
        # We don't know json_d will round-trip, because of randomness in
        # python dictionary iteration ordering. We also need to force
        # comparison as lists, since hashing protos isn't helpful.
        translated_properties = extra_types._PythonValueToJsonProto(
            d).properties
        for p in json_d.properties:
            self.assertIn(p, translated_properties)
        for p in translated_properties:
            self.assertIn(p, json_d.properties)

    def testJsonObjectPropertyTranslation(self):
        value = extra_types.JsonValue(string_value='abc')
        obj = extra_types.JsonObject(properties=[
            extra_types.JsonObject.Property(key='attr_name', value=value)])
        json_value = '"abc"'
        json_obj = '{"attr_name": "abc"}'

        self.assertRoundTrip(value)
        self.assertRoundTrip(obj)
        self.assertRoundTrip(json_value)
        self.assertRoundTrip(json_obj)

        self.assertEqual(json_value, encoding.MessageToJson(value))
        self.assertEqual(json_obj, encoding.MessageToJson(obj))

    def testJsonValueAsFieldTranslation(self):
        class HasJsonValueMsg(messages.Message):
            some_value = messages.MessageField(extra_types.JsonValue, 1)

        msg_json = '{"some_value": [1, 2, 3]}'
        msg = HasJsonValueMsg(
            some_value=encoding.PyValueToMessage(
                extra_types.JsonValue, [1, 2, 3]))
        self.assertEqual(msg,
                         encoding.JsonToMessage(HasJsonValueMsg, msg_json))
        self.assertEqual(msg_json, encoding.MessageToJson(msg))

    def testDateField(self):

        class DateMsg(messages.Message):
            start_date = extra_types.DateField(1)
            all_dates = extra_types.DateField(2, repeated=True)

        msg = DateMsg(
            start_date=datetime.date(1752, 9, 9), all_dates=[
                datetime.date(1979, 5, 6),
                datetime.date(1980, 10, 24),
                datetime.date(1981, 1, 19),
            ])
        msg_dict = {
            'start_date': '1752-09-09',
            'all_dates': ['1979-05-06', '1980-10-24', '1981-01-19'],
        }
        self.assertEqual(msg_dict, json.loads(encoding.MessageToJson(msg)))
        self.assertEqual(
            msg, encoding.JsonToMessage(DateMsg, json.dumps(msg_dict)))

    def testInt64(self):
        # Testing roundtrip of type 'long'

        class DogeMsg(messages.Message):
            such_string = messages.StringField(1)
            wow = messages.IntegerField(2, variant=messages.Variant.INT64)
            very_unsigned = messages.IntegerField(
                3, variant=messages.Variant.UINT64)
            much_repeated = messages.IntegerField(
                4, variant=messages.Variant.INT64, repeated=True)

        def MtoJ(msg):
            return encoding.MessageToJson(msg)

        def JtoM(class_type, json_str):
            return encoding.JsonToMessage(class_type, json_str)

        def DoRoundtrip(class_type, json_msg=None, message=None, times=4):
            if json_msg:
                json_msg = MtoJ(JtoM(class_type, json_msg))
            if message:
                message = JtoM(class_type, MtoJ(message))
            if times == 0:
                result = json_msg if json_msg else message
                return result
            return DoRoundtrip(class_type=class_type, json_msg=json_msg,
                               message=message, times=times - 1)

        # Single
        json_msg = ('{"such_string": "poot", "wow": "-1234", '
                    '"very_unsigned": "999", "much_repeated": ["123", "456"]}')
        out_json = MtoJ(JtoM(DogeMsg, json_msg))
        self.assertEqual(json.loads(out_json)['wow'], '-1234')

        # Repeated test case
        msg = DogeMsg(such_string='wow', wow=-1234,
                      very_unsigned=800, much_repeated=[123, 456])
        self.assertEqual(msg, DoRoundtrip(DogeMsg, message=msg))
