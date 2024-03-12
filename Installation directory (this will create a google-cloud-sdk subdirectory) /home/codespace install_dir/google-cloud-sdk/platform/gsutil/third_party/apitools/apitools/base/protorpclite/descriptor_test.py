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

"""Tests for apitools.base.protorpclite.descriptor."""
import platform
import types
import unittest

import six

from apitools.base.protorpclite import descriptor
from apitools.base.protorpclite import message_types
from apitools.base.protorpclite import messages
from apitools.base.protorpclite import test_util


RUSSIA = u'\u0420\u043e\u0441\u0441\u0438\u044f'


class ModuleInterfaceTest(test_util.ModuleInterfaceTest,
                          test_util.TestCase):

    MODULE = descriptor


class DescribeEnumValueTest(test_util.TestCase):

    def testDescribe(self):
        class MyEnum(messages.Enum):
            MY_NAME = 10

        expected = descriptor.EnumValueDescriptor()
        expected.name = 'MY_NAME'
        expected.number = 10

        described = descriptor.describe_enum_value(MyEnum.MY_NAME)
        described.check_initialized()
        self.assertEquals(expected, described)


class DescribeEnumTest(test_util.TestCase):

    def testEmptyEnum(self):
        class EmptyEnum(messages.Enum):
            pass

        expected = descriptor.EnumDescriptor()
        expected.name = 'EmptyEnum'

        described = descriptor.describe_enum(EmptyEnum)
        described.check_initialized()
        self.assertEquals(expected, described)

    def testNestedEnum(self):
        class MyScope(messages.Message):

            class NestedEnum(messages.Enum):
                pass

        expected = descriptor.EnumDescriptor()
        expected.name = 'NestedEnum'

        described = descriptor.describe_enum(MyScope.NestedEnum)
        described.check_initialized()
        self.assertEquals(expected, described)

    @unittest.skipIf('PyPy' in platform.python_implementation(),
                     'todo: reenable this')
    def testEnumWithItems(self):
        class EnumWithItems(messages.Enum):
            A = 3
            B = 1
            C = 2

        expected = descriptor.EnumDescriptor()
        expected.name = 'EnumWithItems'

        a = descriptor.EnumValueDescriptor()
        a.name = 'A'
        a.number = 3

        b = descriptor.EnumValueDescriptor()
        b.name = 'B'
        b.number = 1

        c = descriptor.EnumValueDescriptor()
        c.name = 'C'
        c.number = 2

        expected.values = [b, c, a]

        described = descriptor.describe_enum(EnumWithItems)
        described.check_initialized()
        self.assertEquals(expected, described)


class DescribeFieldTest(test_util.TestCase):

    def testLabel(self):
        for repeated, required, expected_label in (
                (True, False, descriptor.FieldDescriptor.Label.REPEATED),
                (False, True, descriptor.FieldDescriptor.Label.REQUIRED),
                (False, False, descriptor.FieldDescriptor.Label.OPTIONAL)):
            field = messages.IntegerField(
                10, required=required, repeated=repeated)
            field.name = 'a_field'

            expected = descriptor.FieldDescriptor()
            expected.name = 'a_field'
            expected.number = 10
            expected.label = expected_label
            expected.variant = descriptor.FieldDescriptor.Variant.INT64

            described = descriptor.describe_field(field)
            described.check_initialized()
            self.assertEquals(expected, described)

    def testDefault(self):
        test_cases = (
            (messages.IntegerField, 200, '200'),
            (messages.FloatField, 1.5, '1.5'),
            (messages.FloatField, 1e6, '1000000.0'),
            (messages.BooleanField, True, 'true'),
            (messages.BooleanField, False, 'false'),
            (messages.BytesField,
             b''.join([six.int2byte(x) for x in (31, 32, 33)]),
             b'\\x1f !'),
            (messages.StringField, RUSSIA, RUSSIA),
        )
        for field_class, default, expected_default in test_cases:
            field = field_class(10, default=default)
            field.name = u'a_field'

            expected = descriptor.FieldDescriptor()
            expected.name = u'a_field'
            expected.number = 10
            expected.label = descriptor.FieldDescriptor.Label.OPTIONAL
            expected.variant = field_class.DEFAULT_VARIANT
            expected.default_value = expected_default

            described = descriptor.describe_field(field)
            described.check_initialized()
            self.assertEquals(expected, described)

    def testDefault_EnumField(self):
        class MyEnum(messages.Enum):

            VAL = 1

        module_name = test_util.get_module_name(MyEnum)
        field = messages.EnumField(MyEnum, 10, default=MyEnum.VAL)
        field.name = 'a_field'

        expected = descriptor.FieldDescriptor()
        expected.name = 'a_field'
        expected.number = 10
        expected.label = descriptor.FieldDescriptor.Label.OPTIONAL
        expected.variant = messages.EnumField.DEFAULT_VARIANT
        expected.type_name = '%s.MyEnum' % module_name
        expected.default_value = '1'

        described = descriptor.describe_field(field)
        self.assertEquals(expected, described)

    def testMessageField(self):
        field = messages.MessageField(descriptor.FieldDescriptor, 10)
        field.name = 'a_field'

        expected = descriptor.FieldDescriptor()
        expected.name = 'a_field'
        expected.number = 10
        expected.label = descriptor.FieldDescriptor.Label.OPTIONAL
        expected.variant = messages.MessageField.DEFAULT_VARIANT
        expected.type_name = (
            'apitools.base.protorpclite.descriptor.FieldDescriptor')

        described = descriptor.describe_field(field)
        described.check_initialized()
        self.assertEquals(expected, described)

    def testDateTimeField(self):
        field = message_types.DateTimeField(20)
        field.name = 'a_timestamp'

        expected = descriptor.FieldDescriptor()
        expected.name = 'a_timestamp'
        expected.number = 20
        expected.label = descriptor.FieldDescriptor.Label.OPTIONAL
        expected.variant = messages.MessageField.DEFAULT_VARIANT
        expected.type_name = (
            'apitools.base.protorpclite.message_types.DateTimeMessage')

        described = descriptor.describe_field(field)
        described.check_initialized()
        self.assertEquals(expected, described)


class DescribeMessageTest(test_util.TestCase):

    def testEmptyDefinition(self):
        class MyMessage(messages.Message):
            pass

        expected = descriptor.MessageDescriptor()
        expected.name = 'MyMessage'

        described = descriptor.describe_message(MyMessage)
        described.check_initialized()
        self.assertEquals(expected, described)

    def testDefinitionWithFields(self):
        class MessageWithFields(messages.Message):
            field1 = messages.IntegerField(10)
            field2 = messages.StringField(30)
            field3 = messages.IntegerField(20)

        expected = descriptor.MessageDescriptor()
        expected.name = 'MessageWithFields'

        expected.fields = [
            descriptor.describe_field(
                MessageWithFields.field_by_name('field1')),
            descriptor.describe_field(
                MessageWithFields.field_by_name('field3')),
            descriptor.describe_field(
                MessageWithFields.field_by_name('field2')),
        ]

        described = descriptor.describe_message(MessageWithFields)
        described.check_initialized()
        self.assertEquals(expected, described)

    def testNestedEnum(self):
        class MessageWithEnum(messages.Message):

            class Mood(messages.Enum):
                GOOD = 1
                BAD = 2
                UGLY = 3

            class Music(messages.Enum):
                CLASSIC = 1
                JAZZ = 2
                BLUES = 3

        expected = descriptor.MessageDescriptor()
        expected.name = 'MessageWithEnum'

        expected.enum_types = [descriptor.describe_enum(MessageWithEnum.Mood),
                               descriptor.describe_enum(MessageWithEnum.Music)]

        described = descriptor.describe_message(MessageWithEnum)
        described.check_initialized()
        self.assertEquals(expected, described)

    def testNestedMessage(self):
        class MessageWithMessage(messages.Message):

            class Nesty(messages.Message):
                pass

        expected = descriptor.MessageDescriptor()
        expected.name = 'MessageWithMessage'

        expected.message_types = [
            descriptor.describe_message(MessageWithMessage.Nesty)]

        described = descriptor.describe_message(MessageWithMessage)
        described.check_initialized()
        self.assertEquals(expected, described)


class DescribeFileTest(test_util.TestCase):
    """Test describing modules."""

    def LoadModule(self, module_name, source):
        result = {
            '__name__': module_name,
            'messages': messages,
        }
        exec(source, result)

        module = types.ModuleType(module_name)
        for name, value in result.items():
            setattr(module, name, value)

        return module

    def testEmptyModule(self):
        """Test describing an empty file."""
        module = types.ModuleType('my.package.name')

        expected = descriptor.FileDescriptor()
        expected.package = 'my.package.name'

        described = descriptor.describe_file(module)
        described.check_initialized()
        self.assertEquals(expected, described)

    def testNoPackageName(self):
        """Test describing a module with no module name."""
        module = types.ModuleType('')

        expected = descriptor.FileDescriptor()

        described = descriptor.describe_file(module)
        described.check_initialized()
        self.assertEquals(expected, described)

    def testPackageName(self):
        """Test using the 'package' module attribute."""
        module = types.ModuleType('my.module.name')
        module.package = 'my.package.name'

        expected = descriptor.FileDescriptor()
        expected.package = 'my.package.name'

        described = descriptor.describe_file(module)
        described.check_initialized()
        self.assertEquals(expected, described)

    def testMain(self):
        """Test using the 'package' module attribute."""
        module = types.ModuleType('__main__')
        module.__file__ = '/blim/blam/bloom/my_package.py'

        expected = descriptor.FileDescriptor()
        expected.package = 'my_package'

        described = descriptor.describe_file(module)
        described.check_initialized()
        self.assertEquals(expected, described)

    def testMessages(self):
        """Test that messages are described."""
        module = self.LoadModule('my.package',
                                 'class Message1(messages.Message): pass\n'
                                 'class Message2(messages.Message): pass\n')

        message1 = descriptor.MessageDescriptor()
        message1.name = 'Message1'

        message2 = descriptor.MessageDescriptor()
        message2.name = 'Message2'

        expected = descriptor.FileDescriptor()
        expected.package = 'my.package'
        expected.message_types = [message1, message2]

        described = descriptor.describe_file(module)
        described.check_initialized()
        self.assertEquals(expected, described)

    def testEnums(self):
        """Test that enums are described."""
        module = self.LoadModule('my.package',
                                 'class Enum1(messages.Enum): pass\n'
                                 'class Enum2(messages.Enum): pass\n')

        enum1 = descriptor.EnumDescriptor()
        enum1.name = 'Enum1'

        enum2 = descriptor.EnumDescriptor()
        enum2.name = 'Enum2'

        expected = descriptor.FileDescriptor()
        expected.package = 'my.package'
        expected.enum_types = [enum1, enum2]

        described = descriptor.describe_file(module)
        described.check_initialized()
        self.assertEquals(expected, described)


class DescribeFileSetTest(test_util.TestCase):
    """Test describing multiple modules."""

    def testNoModules(self):
        """Test what happens when no modules provided."""
        described = descriptor.describe_file_set([])
        described.check_initialized()
        # The described FileSet.files will be None.
        self.assertEquals(descriptor.FileSet(), described)

    def testWithModules(self):
        """Test what happens when no modules provided."""
        modules = [types.ModuleType('package1'), types.ModuleType('package1')]

        file1 = descriptor.FileDescriptor()
        file1.package = 'package1'
        file2 = descriptor.FileDescriptor()
        file2.package = 'package2'

        expected = descriptor.FileSet()
        expected.files = [file1, file1]

        described = descriptor.describe_file_set(modules)
        described.check_initialized()
        self.assertEquals(expected, described)


class DescribeTest(test_util.TestCase):

    def testModule(self):
        self.assertEquals(descriptor.describe_file(test_util),
                          descriptor.describe(test_util))

    def testField(self):
        self.assertEquals(
            descriptor.describe_field(test_util.NestedMessage.a_value),
            descriptor.describe(test_util.NestedMessage.a_value))

    def testEnumValue(self):
        self.assertEquals(
            descriptor.describe_enum_value(
                test_util.OptionalMessage.SimpleEnum.VAL1),
            descriptor.describe(test_util.OptionalMessage.SimpleEnum.VAL1))

    def testMessage(self):
        self.assertEquals(descriptor.describe_message(test_util.NestedMessage),
                          descriptor.describe(test_util.NestedMessage))

    def testEnum(self):
        self.assertEquals(
            descriptor.describe_enum(test_util.OptionalMessage.SimpleEnum),
            descriptor.describe(test_util.OptionalMessage.SimpleEnum))

    def testUndescribable(self):
        class NonService(object):

            def fn(self):
                pass

        for value in (NonService,
                      NonService.fn,
                      1,
                      'string',
                      1.2,
                      None):
            self.assertEquals(None, descriptor.describe(value))


class ModuleFinderTest(test_util.TestCase):

    def testFindMessage(self):
        self.assertEquals(
            descriptor.describe_message(descriptor.FileSet),
            descriptor.import_descriptor_loader(
                'apitools.base.protorpclite.descriptor.FileSet'))

    def testFindField(self):
        self.assertEquals(
            descriptor.describe_field(descriptor.FileSet.files),
            descriptor.import_descriptor_loader(
                'apitools.base.protorpclite.descriptor.FileSet.files'))

    def testFindEnumValue(self):
        self.assertEquals(
            descriptor.describe_enum_value(
                test_util.OptionalMessage.SimpleEnum.VAL1),
            descriptor.import_descriptor_loader(
                'apitools.base.protorpclite.test_util.'
                'OptionalMessage.SimpleEnum.VAL1'))


class DescriptorLibraryTest(test_util.TestCase):

    def setUp(self):
        self.packageless = descriptor.MessageDescriptor()
        self.packageless.name = 'Packageless'
        self.library = descriptor.DescriptorLibrary(
            descriptors={
                'not.real.Packageless': self.packageless,
                'Packageless': self.packageless,
            })

    def testLookupPackage(self):
        self.assertEquals('csv', self.library.lookup_package('csv'))
        self.assertEquals(
            'apitools.base.protorpclite',
            self.library.lookup_package('apitools.base.protorpclite'))

    def testLookupNonPackages(self):
        lib = 'apitools.base.protorpclite.descriptor.DescriptorLibrary'
        for name in ('', 'a', lib):
            self.assertRaisesWithRegexpMatch(
                messages.DefinitionNotFoundError,
                'Could not find definition for %s' % name,
                self.library.lookup_package, name)

    def testNoPackage(self):
        self.assertRaisesWithRegexpMatch(
            messages.DefinitionNotFoundError,
            'Could not find definition for not.real',
            self.library.lookup_package, 'not.real.Packageless')

        self.assertEquals(None, self.library.lookup_package('Packageless'))


if __name__ == '__main__':
    unittest.main()
