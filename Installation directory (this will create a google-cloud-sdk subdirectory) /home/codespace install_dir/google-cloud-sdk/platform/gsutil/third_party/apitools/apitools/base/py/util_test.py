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

"""Tests for util.py."""
import unittest

from apitools.base.protorpclite import messages
from apitools.base.py import encoding
from apitools.base.py import exceptions
from apitools.base.py import util


class MockedMethodConfig(object):

    def __init__(self, relative_path, path_params):
        self.relative_path = relative_path
        self.path_params = path_params


class MessageWithRemappings(messages.Message):

    class AnEnum(messages.Enum):
        value_one = 1
        value_two = 2

    str_field = messages.StringField(1)
    enum_field = messages.EnumField('AnEnum', 2)
    enum_field_remapping = messages.EnumField('AnEnum', 3)


encoding.AddCustomJsonFieldMapping(
    MessageWithRemappings, 'str_field', 'path_field')
encoding.AddCustomJsonFieldMapping(
    MessageWithRemappings, 'enum_field_remapping', 'enum_field_remapped')
encoding.AddCustomJsonEnumMapping(
    MessageWithRemappings.AnEnum, 'value_one', 'ONE')


class UtilTest(unittest.TestCase):

    def testExpand(self):
        method_config_xy = MockedMethodConfig(relative_path='{x}/y/{z}',
                                              path_params=['x', 'z'])
        self.assertEquals(
            util.ExpandRelativePath(method_config_xy, {'x': '1', 'z': '2'}),
            '1/y/2')
        self.assertEquals(
            util.ExpandRelativePath(
                method_config_xy,
                {'x': '1', 'z': '2'},
                relative_path='{x}/y/{z}/q'),
            '1/y/2/q')

    def testReservedExpansion(self):
        method_config_reserved = MockedMethodConfig(relative_path='{+x}/baz',
                                                    path_params=['x'])
        self.assertEquals('foo/:bar:/baz', util.ExpandRelativePath(
            method_config_reserved, {'x': 'foo/:bar:'}))
        method_config_no_reserved = MockedMethodConfig(relative_path='{x}/baz',
                                                       path_params=['x'])
        self.assertEquals('foo%2F%3Abar%3A/baz', util.ExpandRelativePath(
            method_config_no_reserved, {'x': 'foo/:bar:'}))

    def testCalculateWaitForRetry(self):
        try0 = util.CalculateWaitForRetry(0)
        self.assertTrue(try0 >= 1.0)
        self.assertTrue(try0 <= 1.5)
        try1 = util.CalculateWaitForRetry(1)
        self.assertTrue(try1 >= 1.0)
        self.assertTrue(try1 <= 3.0)
        try2 = util.CalculateWaitForRetry(2)
        self.assertTrue(try2 >= 2.0)
        self.assertTrue(try2 <= 6.0)
        try3 = util.CalculateWaitForRetry(3)
        self.assertTrue(try3 >= 4.0)
        self.assertTrue(try3 <= 12.0)
        try4 = util.CalculateWaitForRetry(4)
        self.assertTrue(try4 >= 8.0)
        self.assertTrue(try4 <= 24.0)

        self.assertAlmostEqual(10, util.CalculateWaitForRetry(5, max_wait=10))

    def testTypecheck(self):

        class Class1(object):
            pass

        class Class2(object):
            pass

        class Class3(object):
            pass

        instance_of_class1 = Class1()

        self.assertEquals(
            instance_of_class1, util.Typecheck(instance_of_class1, Class1))

        self.assertEquals(
            instance_of_class1,
            util.Typecheck(instance_of_class1, ((Class1, Class2), Class3)))

        self.assertEquals(
            instance_of_class1,
            util.Typecheck(instance_of_class1, (Class1, (Class2, Class3))))

        self.assertEquals(
            instance_of_class1,
            util.Typecheck(instance_of_class1, Class1, 'message'))

        self.assertEquals(
            instance_of_class1,
            util.Typecheck(
                instance_of_class1, ((Class1, Class2), Class3), 'message'))

        self.assertEquals(
            instance_of_class1,
            util.Typecheck(
                instance_of_class1, (Class1, (Class2, Class3)), 'message'))

        with self.assertRaises(exceptions.TypecheckError):
            util.Typecheck(instance_of_class1, Class2)

        with self.assertRaises(exceptions.TypecheckError):
            util.Typecheck(instance_of_class1, (Class2, Class3))

        with self.assertRaises(exceptions.TypecheckError):
            util.Typecheck(instance_of_class1, Class2, 'message')

        with self.assertRaises(exceptions.TypecheckError):
            util.Typecheck(instance_of_class1, (Class2, Class3), 'message')

    def testAcceptableMimeType(self):
        valid_pairs = (
            ('*', 'text/plain'),
            ('*/*', 'text/plain'),
            ('text/*', 'text/plain'),
            ('*/plain', 'text/plain'),
            ('text/plain', 'text/plain'),
        )

        for accept, mime_type in valid_pairs:
            self.assertTrue(util.AcceptableMimeType([accept], mime_type))

        invalid_pairs = (
            ('text/*', 'application/json'),
            ('text/plain', 'application/json'),
        )

        for accept, mime_type in invalid_pairs:
            self.assertFalse(util.AcceptableMimeType([accept], mime_type))

        self.assertTrue(util.AcceptableMimeType(['application/json', '*/*'],
                                                'text/plain'))
        self.assertFalse(util.AcceptableMimeType(['application/json', 'img/*'],
                                                 'text/plain'))

    def testMalformedMimeType(self):
        self.assertRaises(
            exceptions.InvalidUserInputError,
            util.AcceptableMimeType, ['*/*'], 'abcd')

    def testUnsupportedMimeType(self):
        self.assertRaises(
            exceptions.GeneratedClientError,
            util.AcceptableMimeType, ['text/html;q=0.9'], 'text/html')

    def testMapRequestParams(self):
        params = {
            'str_field': 'foo',
            'enum_field': MessageWithRemappings.AnEnum.value_one,
            'enum_field_remapping': MessageWithRemappings.AnEnum.value_one,
        }
        remapped_params = {
            'path_field': 'foo',
            'enum_field': 'ONE',
            'enum_field_remapped': 'ONE',
        }
        self.assertEqual(remapped_params,
                         util.MapRequestParams(params, MessageWithRemappings))

        params['enum_field'] = MessageWithRemappings.AnEnum.value_two
        remapped_params['enum_field'] = 'value_two'
        self.assertEqual(remapped_params,
                         util.MapRequestParams(params, MessageWithRemappings))

    def testMapParamNames(self):
        params = ['path_field', 'enum_field']
        remapped_params = ['str_field', 'enum_field']
        self.assertEqual(remapped_params,
                         util.MapParamNames(params, MessageWithRemappings))
