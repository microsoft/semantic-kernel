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

"""Tests for apitools.base.protorpclite.messages."""
import pickle
import re
import sys
import types
import unittest

import six

from apitools.base.protorpclite import descriptor
from apitools.base.protorpclite import message_types
from apitools.base.protorpclite import messages
from apitools.base.protorpclite import test_util

# This package plays lots of games with modifying global variables inside
# test cases. Hence:
# pylint:disable=function-redefined
# pylint:disable=global-variable-not-assigned
# pylint:disable=global-variable-undefined
# pylint:disable=redefined-outer-name
# pylint:disable=undefined-variable
# pylint:disable=unused-variable
# pylint:disable=too-many-lines

try:
    long        # Python 2
except NameError:
    long = int  # Python 3


class ModuleInterfaceTest(test_util.ModuleInterfaceTest,
                          test_util.TestCase):

    MODULE = messages


class ValidationErrorTest(test_util.TestCase):

    def testStr_NoFieldName(self):
        """Test string version of ValidationError when no name provided."""
        self.assertEquals('Validation error',
                          str(messages.ValidationError('Validation error')))

    def testStr_FieldName(self):
        """Test string version of ValidationError when no name provided."""
        validation_error = messages.ValidationError('Validation error')
        validation_error.field_name = 'a_field'
        self.assertEquals('Validation error', str(validation_error))


class EnumTest(test_util.TestCase):

    def setUp(self):
        """Set up tests."""
        # Redefine Color class in case so that changes to it (an
        # error) in one test does not affect other tests.
        global Color  # pylint:disable=global-variable-not-assigned

        # pylint:disable=unused-variable
        class Color(messages.Enum):
            RED = 20
            ORANGE = 2
            YELLOW = 40
            GREEN = 4
            BLUE = 50
            INDIGO = 5
            VIOLET = 80

    def testNames(self):
        """Test that names iterates over enum names."""
        self.assertEquals(
            set(['BLUE', 'GREEN', 'INDIGO', 'ORANGE', 'RED',
                 'VIOLET', 'YELLOW']),
            set(Color.names()))

    def testNumbers(self):
        """Tests that numbers iterates of enum numbers."""
        self.assertEquals(set([2, 4, 5, 20, 40, 50, 80]), set(Color.numbers()))

    def testIterate(self):
        """Test that __iter__ iterates over all enum values."""
        self.assertEquals(set(Color),
                          set([Color.RED,
                               Color.ORANGE,
                               Color.YELLOW,
                               Color.GREEN,
                               Color.BLUE,
                               Color.INDIGO,
                               Color.VIOLET]))

    def testNaturalOrder(self):
        """Test that natural order enumeration is in numeric order."""
        self.assertEquals([Color.ORANGE,
                           Color.GREEN,
                           Color.INDIGO,
                           Color.RED,
                           Color.YELLOW,
                           Color.BLUE,
                           Color.VIOLET],
                          sorted(Color))

    def testByName(self):
        """Test look-up by name."""
        self.assertEquals(Color.RED, Color.lookup_by_name('RED'))
        self.assertRaises(KeyError, Color.lookup_by_name, 20)
        self.assertRaises(KeyError, Color.lookup_by_name, Color.RED)

    def testByNumber(self):
        """Test look-up by number."""
        self.assertRaises(KeyError, Color.lookup_by_number, 'RED')
        self.assertEquals(Color.RED, Color.lookup_by_number(20))
        self.assertRaises(KeyError, Color.lookup_by_number, Color.RED)

    def testConstructor(self):
        """Test that constructor look-up by name or number."""
        self.assertEquals(Color.RED, Color('RED'))
        self.assertEquals(Color.RED, Color(u'RED'))
        self.assertEquals(Color.RED, Color(20))
        if six.PY2:
            self.assertEquals(Color.RED, Color(long(20)))
        self.assertEquals(Color.RED, Color(Color.RED))
        self.assertRaises(TypeError, Color, 'Not exists')
        self.assertRaises(TypeError, Color, 'Red')
        self.assertRaises(TypeError, Color, 100)
        self.assertRaises(TypeError, Color, 10.0)

    def testLen(self):
        """Test that len function works to count enums."""
        self.assertEquals(7, len(Color))

    def testNoSubclasses(self):
        """Test that it is not possible to sub-class enum classes."""
        def declare_subclass():
            class MoreColor(Color):
                pass
        self.assertRaises(messages.EnumDefinitionError,
                          declare_subclass)

    def testClassNotMutable(self):
        """Test that enum classes themselves are not mutable."""
        self.assertRaises(AttributeError,
                          setattr,
                          Color,
                          'something_new',
                          10)

    def testInstancesMutable(self):
        """Test that enum instances are not mutable."""
        self.assertRaises(TypeError,
                          setattr,
                          Color.RED,
                          'something_new',
                          10)

    def testDefEnum(self):
        """Test def_enum works by building enum class from dict."""
        WeekDay = messages.Enum.def_enum({'Monday': 1,
                                          'Tuesday': 2,
                                          'Wednesday': 3,
                                          'Thursday': 4,
                                          'Friday': 6,
                                          'Saturday': 7,
                                          'Sunday': 8},
                                         'WeekDay')
        self.assertEquals('Wednesday', WeekDay(3).name)
        self.assertEquals(6, WeekDay('Friday').number)
        self.assertEquals(WeekDay.Sunday, WeekDay('Sunday'))

    def testNonInt(self):
        """Test that non-integer values rejection by enum def."""
        self.assertRaises(messages.EnumDefinitionError,
                          messages.Enum.def_enum,
                          {'Bad': '1'},
                          'BadEnum')

    def testNegativeInt(self):
        """Test that negative numbers rejection by enum def."""
        self.assertRaises(messages.EnumDefinitionError,
                          messages.Enum.def_enum,
                          {'Bad': -1},
                          'BadEnum')

    def testLowerBound(self):
        """Test that zero is accepted by enum def."""
        class NotImportant(messages.Enum):
            """Testing for value zero"""
            VALUE = 0

        self.assertEquals(0, int(NotImportant.VALUE))

    def testTooLargeInt(self):
        """Test that numbers too large are rejected."""
        self.assertRaises(messages.EnumDefinitionError,
                          messages.Enum.def_enum,
                          {'Bad': (2 ** 29)},
                          'BadEnum')

    def testRepeatedInt(self):
        """Test duplicated numbers are forbidden."""
        self.assertRaises(messages.EnumDefinitionError,
                          messages.Enum.def_enum,
                          {'Ok': 1, 'Repeated': 1},
                          'BadEnum')

    def testStr(self):
        """Test converting to string."""
        self.assertEquals('RED', str(Color.RED))
        self.assertEquals('ORANGE', str(Color.ORANGE))

    def testInt(self):
        """Test converting to int."""
        self.assertEquals(20, int(Color.RED))
        self.assertEquals(2, int(Color.ORANGE))

    def testRepr(self):
        """Test enum representation."""
        self.assertEquals('Color(RED, 20)', repr(Color.RED))
        self.assertEquals('Color(YELLOW, 40)', repr(Color.YELLOW))

    def testDocstring(self):
        """Test that docstring is supported ok."""
        class NotImportant(messages.Enum):
            """I have a docstring."""

            VALUE1 = 1

        self.assertEquals('I have a docstring.', NotImportant.__doc__)

    def testDeleteEnumValue(self):
        """Test that enum values cannot be deleted."""
        self.assertRaises(TypeError, delattr, Color, 'RED')

    def testEnumName(self):
        """Test enum name."""
        module_name = test_util.get_module_name(EnumTest)
        self.assertEquals('%s.Color' % module_name, Color.definition_name())
        self.assertEquals(module_name, Color.outer_definition_name())
        self.assertEquals(module_name, Color.definition_package())

    def testDefinitionName_OverrideModule(self):
        """Test enum module is overriden by module package name."""
        global package
        try:
            package = 'my.package'
            self.assertEquals('my.package.Color', Color.definition_name())
            self.assertEquals('my.package', Color.outer_definition_name())
            self.assertEquals('my.package', Color.definition_package())
        finally:
            del package

    def testDefinitionName_NoModule(self):
        """Test what happens when there is no module for enum."""
        class Enum1(messages.Enum):
            pass

        original_modules = sys.modules
        sys.modules = dict(sys.modules)
        try:
            del sys.modules[__name__]
            self.assertEquals('Enum1', Enum1.definition_name())
            self.assertEquals(None, Enum1.outer_definition_name())
            self.assertEquals(None, Enum1.definition_package())
            self.assertEquals(six.text_type, type(Enum1.definition_name()))
        finally:
            sys.modules = original_modules

    def testDefinitionName_Nested(self):
        """Test nested Enum names."""
        class MyMessage(messages.Message):

            class NestedEnum(messages.Enum):

                pass

            class NestedMessage(messages.Message):

                class NestedEnum(messages.Enum):

                    pass

        module_name = test_util.get_module_name(EnumTest)
        self.assertEquals('%s.MyMessage.NestedEnum' % module_name,
                          MyMessage.NestedEnum.definition_name())
        self.assertEquals('%s.MyMessage' % module_name,
                          MyMessage.NestedEnum.outer_definition_name())
        self.assertEquals(module_name,
                          MyMessage.NestedEnum.definition_package())

        self.assertEquals(
            '%s.MyMessage.NestedMessage.NestedEnum' % module_name,
            MyMessage.NestedMessage.NestedEnum.definition_name())
        self.assertEquals(
            '%s.MyMessage.NestedMessage' % module_name,
            MyMessage.NestedMessage.NestedEnum.outer_definition_name())
        self.assertEquals(
            module_name,
            MyMessage.NestedMessage.NestedEnum.definition_package())

    def testMessageDefinition(self):
        """Test that enumeration knows its enclosing message definition."""
        class OuterEnum(messages.Enum):
            pass

        self.assertEquals(None, OuterEnum.message_definition())

        class OuterMessage(messages.Message):

            class InnerEnum(messages.Enum):
                pass

        self.assertEquals(
            OuterMessage, OuterMessage.InnerEnum.message_definition())

    def testComparison(self):
        """Test comparing various enums to different types."""
        class Enum1(messages.Enum):
            VAL1 = 1
            VAL2 = 2

        class Enum2(messages.Enum):
            VAL1 = 1

        self.assertEquals(Enum1.VAL1, Enum1.VAL1)
        self.assertNotEquals(Enum1.VAL1, Enum1.VAL2)
        self.assertNotEquals(Enum1.VAL1, Enum2.VAL1)
        self.assertNotEquals(Enum1.VAL1, 'VAL1')
        self.assertNotEquals(Enum1.VAL1, 1)
        self.assertNotEquals(Enum1.VAL1, 2)
        self.assertNotEquals(Enum1.VAL1, None)
        self.assertNotEquals(Enum1.VAL1, Enum2.VAL1)

        self.assertTrue(Enum1.VAL1 < Enum1.VAL2)
        self.assertTrue(Enum1.VAL2 > Enum1.VAL1)

        self.assertNotEquals(1, Enum2.VAL1)

    def testPickle(self):
        """Testing pickling and unpickling of Enum instances."""
        colors = list(Color)
        unpickled = pickle.loads(pickle.dumps(colors))
        self.assertEquals(colors, unpickled)
        # Unpickling shouldn't create new enum instances.
        for i, color in enumerate(colors):
            self.assertTrue(color is unpickled[i])


class FieldListTest(test_util.TestCase):

    def setUp(self):
        self.integer_field = messages.IntegerField(1, repeated=True)

    def testConstructor(self):
        self.assertEquals([1, 2, 3],
                          messages.FieldList(self.integer_field, [1, 2, 3]))
        self.assertEquals([1, 2, 3],
                          messages.FieldList(self.integer_field, (1, 2, 3)))
        self.assertEquals([], messages.FieldList(self.integer_field, []))

    def testNone(self):
        self.assertRaises(TypeError, messages.FieldList,
                          self.integer_field, None)

    def testDoNotAutoConvertString(self):
        string_field = messages.StringField(1, repeated=True)
        self.assertRaises(messages.ValidationError,
                          messages.FieldList, string_field, 'abc')

    def testConstructorCopies(self):
        a_list = [1, 3, 6]
        field_list = messages.FieldList(self.integer_field, a_list)
        self.assertFalse(a_list is field_list)
        self.assertFalse(field_list is
                         messages.FieldList(self.integer_field, field_list))

    def testNonRepeatedField(self):
        self.assertRaisesWithRegexpMatch(
            messages.FieldDefinitionError,
            'FieldList may only accept repeated fields',
            messages.FieldList,
            messages.IntegerField(1),
            [])

    def testConstructor_InvalidValues(self):
        self.assertRaisesWithRegexpMatch(
            messages.ValidationError,
            re.escape("Expected type %r "
                      "for IntegerField, found 1 (type %r)"
                      % (six.integer_types, str)),
            messages.FieldList, self.integer_field, ["1", "2", "3"])

    def testConstructor_Scalars(self):
        self.assertRaisesWithRegexpMatch(
            messages.ValidationError,
            "IntegerField is repeated. Found: 3",
            messages.FieldList, self.integer_field, 3)

        self.assertRaisesWithRegexpMatch(
            messages.ValidationError,
            ("IntegerField is repeated. Found: "
             "<(list[_]?|sequence)iterator object"),
            messages.FieldList, self.integer_field, iter([1, 2, 3]))

    def testSetSlice(self):
        field_list = messages.FieldList(self.integer_field, [1, 2, 3, 4, 5])
        field_list[1:3] = [10, 20]
        self.assertEquals([1, 10, 20, 4, 5], field_list)

    def testSetSlice_InvalidValues(self):
        field_list = messages.FieldList(self.integer_field, [1, 2, 3, 4, 5])

        def setslice():
            field_list[1:3] = ['10', '20']

        msg_re = re.escape("Expected type %r "
                           "for IntegerField, found 10 (type %r)"
                           % (six.integer_types, str))
        self.assertRaisesWithRegexpMatch(
            messages.ValidationError,
            msg_re,
            setslice)

    def testSetItem(self):
        field_list = messages.FieldList(self.integer_field, [2])
        field_list[0] = 10
        self.assertEquals([10], field_list)

    def testSetItem_InvalidValues(self):
        field_list = messages.FieldList(self.integer_field, [2])

        def setitem():
            field_list[0] = '10'
        self.assertRaisesWithRegexpMatch(
            messages.ValidationError,
            re.escape("Expected type %r "
                      "for IntegerField, found 10 (type %r)"
                      % (six.integer_types, str)),
            setitem)

    def testAppend(self):
        field_list = messages.FieldList(self.integer_field, [2])
        field_list.append(10)
        self.assertEquals([2, 10], field_list)

    def testAppend_InvalidValues(self):
        field_list = messages.FieldList(self.integer_field, [2])
        field_list.name = 'a_field'

        def append():
            field_list.append('10')
        self.assertRaisesWithRegexpMatch(
            messages.ValidationError,
            re.escape("Expected type %r "
                      "for IntegerField, found 10 (type %r)"
                      % (six.integer_types, str)),
            append)

    def testExtend(self):
        field_list = messages.FieldList(self.integer_field, [2])
        field_list.extend([10])
        self.assertEquals([2, 10], field_list)

    def testExtend_InvalidValues(self):
        field_list = messages.FieldList(self.integer_field, [2])

        def extend():
            field_list.extend(['10'])
        self.assertRaisesWithRegexpMatch(
            messages.ValidationError,
            re.escape("Expected type %r "
                      "for IntegerField, found 10 (type %r)"
                      % (six.integer_types, str)),
            extend)

    def testInsert(self):
        field_list = messages.FieldList(self.integer_field, [2, 3])
        field_list.insert(1, 10)
        self.assertEquals([2, 10, 3], field_list)

    def testInsert_InvalidValues(self):
        field_list = messages.FieldList(self.integer_field, [2, 3])

        def insert():
            field_list.insert(1, '10')
        self.assertRaisesWithRegexpMatch(
            messages.ValidationError,
            re.escape("Expected type %r "
                      "for IntegerField, found 10 (type %r)"
                      % (six.integer_types, str)),
            insert)

    def testPickle(self):
        """Testing pickling and unpickling of FieldList instances."""
        field_list = messages.FieldList(self.integer_field, [1, 2, 3, 4, 5])
        unpickled = pickle.loads(pickle.dumps(field_list))
        self.assertEquals(field_list, unpickled)
        self.assertIsInstance(unpickled.field, messages.IntegerField)
        self.assertEquals(1, unpickled.field.number)
        self.assertTrue(unpickled.field.repeated)


class FieldTest(test_util.TestCase):

    def ActionOnAllFieldClasses(self, action):
        """Test all field classes except Message and Enum.

        Message and Enum require separate tests.

        Args:
          action: Callable that takes the field class as a parameter.
        """
        classes = (messages.IntegerField,
                   messages.FloatField,
                   messages.BooleanField,
                   messages.BytesField,
                   messages.StringField)
        for field_class in classes:
            action(field_class)

    def testNumberAttribute(self):
        """Test setting the number attribute."""
        def action(field_class):
            # Check range.
            self.assertRaises(messages.InvalidNumberError,
                              field_class,
                              0)
            self.assertRaises(messages.InvalidNumberError,
                              field_class,
                              -1)
            self.assertRaises(messages.InvalidNumberError,
                              field_class,
                              messages.MAX_FIELD_NUMBER + 1)

            # Check reserved.
            self.assertRaises(messages.InvalidNumberError,
                              field_class,
                              messages.FIRST_RESERVED_FIELD_NUMBER)
            self.assertRaises(messages.InvalidNumberError,
                              field_class,
                              messages.LAST_RESERVED_FIELD_NUMBER)
            self.assertRaises(messages.InvalidNumberError,
                              field_class,
                              '1')

            # This one should work.
            field_class(number=1)
        self.ActionOnAllFieldClasses(action)

    def testRequiredAndRepeated(self):
        """Test setting the required and repeated fields."""
        def action(field_class):
            field_class(1, required=True)
            field_class(1, repeated=True)
            self.assertRaises(messages.FieldDefinitionError,
                              field_class,
                              1,
                              required=True,
                              repeated=True)
        self.ActionOnAllFieldClasses(action)

    def testInvalidVariant(self):
        """Test field with invalid variants."""
        def action(field_class):
            if field_class is not message_types.DateTimeField:
                self.assertRaises(messages.InvalidVariantError,
                                  field_class,
                                  1,
                                  variant=messages.Variant.ENUM)
        self.ActionOnAllFieldClasses(action)

    def testDefaultVariant(self):
        """Test that default variant is used when not set."""
        def action(field_class):
            field = field_class(1)
            self.assertEquals(field_class.DEFAULT_VARIANT, field.variant)

        self.ActionOnAllFieldClasses(action)

    def testAlternateVariant(self):
        """Test that default variant is used when not set."""
        field = messages.IntegerField(1, variant=messages.Variant.UINT32)
        self.assertEquals(messages.Variant.UINT32, field.variant)

    def testDefaultFields_Single(self):
        """Test default field is correct type (single)."""
        defaults = {
            messages.IntegerField: 10,
            messages.FloatField: 1.5,
            messages.BooleanField: False,
            messages.BytesField: b'abc',
            messages.StringField: u'abc',
        }

        def action(field_class):
            field_class(1, default=defaults[field_class])
        self.ActionOnAllFieldClasses(action)

        # Run defaults test again checking for str/unicode compatiblity.
        defaults[messages.StringField] = 'abc'
        self.ActionOnAllFieldClasses(action)

    def testStringField_BadUnicodeInDefault(self):
        """Test binary values in string field."""
        self.assertRaisesWithRegexpMatch(
            messages.InvalidDefaultError,
            r"Invalid default value for StringField:.*: "
            r"Field encountered non-UTF-8 string .*: "
            r"'utf.?8' codec can't decode byte 0xc3 in position 0: "
            r"invalid continuation byte",
            messages.StringField, 1, default=b'\xc3\x28')

    def testDefaultFields_InvalidSingle(self):
        """Test default field is correct type (invalid single)."""
        def action(field_class):
            self.assertRaises(messages.InvalidDefaultError,
                              field_class,
                              1,
                              default=object())
        self.ActionOnAllFieldClasses(action)

    def testDefaultFields_InvalidRepeated(self):
        """Test default field does not accept defaults."""
        self.assertRaisesWithRegexpMatch(
            messages.FieldDefinitionError,
            'Repeated fields may not have defaults',
            messages.StringField, 1, repeated=True, default=[1, 2, 3])

    def testDefaultFields_None(self):
        """Test none is always acceptable."""
        def action(field_class):
            field_class(1, default=None)
            field_class(1, required=True, default=None)
            field_class(1, repeated=True, default=None)
        self.ActionOnAllFieldClasses(action)

    def testDefaultFields_Enum(self):
        """Test the default for enum fields."""
        class Symbol(messages.Enum):

            ALPHA = 1
            BETA = 2
            GAMMA = 3

        field = messages.EnumField(Symbol, 1, default=Symbol.ALPHA)

        self.assertEquals(Symbol.ALPHA, field.default)

    def testDefaultFields_EnumStringDelayedResolution(self):
        """Test that enum fields resolve default strings."""
        field = messages.EnumField(
            'apitools.base.protorpclite.descriptor.FieldDescriptor.Label',
            1,
            default='OPTIONAL')

        self.assertEquals(
            descriptor.FieldDescriptor.Label.OPTIONAL, field.default)

    def testDefaultFields_EnumIntDelayedResolution(self):
        """Test that enum fields resolve default integers."""
        field = messages.EnumField(
            'apitools.base.protorpclite.descriptor.FieldDescriptor.Label',
            1,
            default=2)

        self.assertEquals(
            descriptor.FieldDescriptor.Label.REQUIRED, field.default)

    def testDefaultFields_EnumOkIfTypeKnown(self):
        """Test enum fields accept valid default values when type is known."""
        field = messages.EnumField(descriptor.FieldDescriptor.Label,
                                   1,
                                   default='REPEATED')

        self.assertEquals(
            descriptor.FieldDescriptor.Label.REPEATED, field.default)

    def testDefaultFields_EnumForceCheckIfTypeKnown(self):
        """Test that enum fields validate default values if type is known."""
        self.assertRaisesWithRegexpMatch(TypeError,
                                         'No such value for NOT_A_LABEL in '
                                         'Enum Label',
                                         messages.EnumField,
                                         descriptor.FieldDescriptor.Label,
                                         1,
                                         default='NOT_A_LABEL')

    def testDefaultFields_EnumInvalidDelayedResolution(self):
        """Test that enum fields raise errors upon delayed resolution error."""
        field = messages.EnumField(
            'apitools.base.protorpclite.descriptor.FieldDescriptor.Label',
            1,
            default=200)

        self.assertRaisesWithRegexpMatch(TypeError,
                                         'No such value for 200 in Enum Label',
                                         getattr,
                                         field,
                                         'default')

    def testValidate_Valid(self):
        """Test validation of valid values."""
        values = {
            messages.IntegerField: 10,
            messages.FloatField: 1.5,
            messages.BooleanField: False,
            messages.BytesField: b'abc',
            messages.StringField: u'abc',
        }

        def action(field_class):
            # Optional.
            field = field_class(1)
            field.validate(values[field_class])

            # Required.
            field = field_class(1, required=True)
            field.validate(values[field_class])

            # Repeated.
            field = field_class(1, repeated=True)
            field.validate([])
            field.validate(())
            field.validate([values[field_class]])
            field.validate((values[field_class],))

            # Right value, but not repeated.
            self.assertRaises(messages.ValidationError,
                              field.validate,
                              values[field_class])
            self.assertRaises(messages.ValidationError,
                              field.validate,
                              values[field_class])

        self.ActionOnAllFieldClasses(action)

    def testValidate_Invalid(self):
        """Test validation of valid values."""
        values = {
            messages.IntegerField: "10",
            messages.FloatField: "blah",
            messages.BooleanField: 0,
            messages.BytesField: 10.20,
            messages.StringField: 42,
        }

        def action(field_class):
            # Optional.
            field = field_class(1)
            self.assertRaises(messages.ValidationError,
                              field.validate,
                              values[field_class])

            # Required.
            field = field_class(1, required=True)
            self.assertRaises(messages.ValidationError,
                              field.validate,
                              values[field_class])

            # Repeated.
            field = field_class(1, repeated=True)
            self.assertRaises(messages.ValidationError,
                              field.validate,
                              [values[field_class]])
            self.assertRaises(messages.ValidationError,
                              field.validate,
                              (values[field_class],))
        self.ActionOnAllFieldClasses(action)

    def testValidate_None(self):
        """Test that None is valid for non-required fields."""
        def action(field_class):
            # Optional.
            field = field_class(1)
            field.validate(None)

            # Required.
            field = field_class(1, required=True)
            self.assertRaisesWithRegexpMatch(messages.ValidationError,
                                             'Required field is missing',
                                             field.validate,
                                             None)

            # Repeated.
            field = field_class(1, repeated=True)
            field.validate(None)
            self.assertRaisesWithRegexpMatch(
                messages.ValidationError,
                'Repeated values for %s may '
                'not be None' % field_class.__name__,
                field.validate,
                [None])
            self.assertRaises(messages.ValidationError,
                              field.validate,
                              (None,))
        self.ActionOnAllFieldClasses(action)

    def testValidateElement(self):
        """Test validation of valid values."""
        values = {
            messages.IntegerField: (10, -1, 0),
            messages.FloatField: (1.5, -1.5, 3),  # for json it is all a number
            messages.BooleanField: (True, False),
            messages.BytesField: (b'abc',),
            messages.StringField: (u'abc',),
        }

        def action(field_class):
            # Optional.
            field = field_class(1)
            for value in values[field_class]:
                field.validate_element(value)

            # Required.
            field = field_class(1, required=True)
            for value in values[field_class]:
                field.validate_element(value)

            # Repeated.
            field = field_class(1, repeated=True)
            self.assertRaises(messages.ValidationError,
                              field.validate_element,
                              [])
            self.assertRaises(messages.ValidationError,
                              field.validate_element,
                              ())
            for value in values[field_class]:
                field.validate_element(value)

            # Right value, but repeated.
            self.assertRaises(messages.ValidationError,
                              field.validate_element,
                              list(values[field_class]))  # testing list
            self.assertRaises(messages.ValidationError,
                              field.validate_element,
                              values[field_class])  # testing tuple

        self.ActionOnAllFieldClasses(action)

    def testValidateCastingElement(self):
        field = messages.FloatField(1)
        self.assertEquals(type(field.validate_element(12)), float)
        self.assertEquals(type(field.validate_element(12.0)), float)
        field = messages.IntegerField(1)
        self.assertEquals(type(field.validate_element(12)), int)
        self.assertRaises(messages.ValidationError,
                          field.validate_element,
                          12.0)  # should fails from float to int

    def testReadOnly(self):
        """Test that objects are all read-only."""
        def action(field_class):
            field = field_class(10)
            self.assertRaises(AttributeError,
                              setattr,
                              field,
                              'number',
                              20)
            self.assertRaises(AttributeError,
                              setattr,
                              field,
                              'anything_else',
                              'whatever')
        self.ActionOnAllFieldClasses(action)

    def testMessageField(self):
        """Test the construction of message fields."""
        self.assertRaises(messages.FieldDefinitionError,
                          messages.MessageField,
                          str,
                          10)

        self.assertRaises(messages.FieldDefinitionError,
                          messages.MessageField,
                          messages.Message,
                          10)

        class MyMessage(messages.Message):
            pass

        field = messages.MessageField(MyMessage, 10)
        self.assertEquals(MyMessage, field.type)

    def testMessageField_ForwardReference(self):
        """Test the construction of forward reference message fields."""
        global MyMessage
        global ForwardMessage
        try:
            class MyMessage(messages.Message):

                self_reference = messages.MessageField('MyMessage', 1)
                forward = messages.MessageField('ForwardMessage', 2)
                nested = messages.MessageField(
                    'ForwardMessage.NestedMessage', 3)
                inner = messages.MessageField('Inner', 4)

                class Inner(messages.Message):

                    sibling = messages.MessageField('Sibling', 1)

                class Sibling(messages.Message):

                    pass

            class ForwardMessage(messages.Message):

                class NestedMessage(messages.Message):

                    pass

            self.assertEquals(MyMessage,
                              MyMessage.field_by_name('self_reference').type)

            self.assertEquals(ForwardMessage,
                              MyMessage.field_by_name('forward').type)

            self.assertEquals(ForwardMessage.NestedMessage,
                              MyMessage.field_by_name('nested').type)

            self.assertEquals(MyMessage.Inner,
                              MyMessage.field_by_name('inner').type)

            self.assertEquals(MyMessage.Sibling,
                              MyMessage.Inner.field_by_name('sibling').type)
        finally:
            try:
                del MyMessage
                del ForwardMessage
            except:  # pylint:disable=bare-except
                pass

    def testMessageField_WrongType(self):
        """Test that forward referencing the wrong type raises an error."""
        global AnEnum
        try:
            class AnEnum(messages.Enum):
                pass

            class AnotherMessage(messages.Message):

                a_field = messages.MessageField('AnEnum', 1)

            self.assertRaises(messages.FieldDefinitionError,
                              getattr,
                              AnotherMessage.field_by_name('a_field'),
                              'type')
        finally:
            del AnEnum

    def testMessageFieldValidate(self):
        """Test validation on message field."""
        class MyMessage(messages.Message):
            pass

        class AnotherMessage(messages.Message):
            pass

        field = messages.MessageField(MyMessage, 10)
        field.validate(MyMessage())

        self.assertRaises(messages.ValidationError,
                          field.validate,
                          AnotherMessage())

    def testMessageFieldMessageType(self):
        """Test message_type property."""
        class MyMessage(messages.Message):
            pass

        class HasMessage(messages.Message):
            field = messages.MessageField(MyMessage, 1)

        self.assertEqual(HasMessage.field.type, HasMessage.field.message_type)

    def testMessageFieldValueFromMessage(self):
        class MyMessage(messages.Message):
            pass

        class HasMessage(messages.Message):
            field = messages.MessageField(MyMessage, 1)

        instance = MyMessage()

        self.assertTrue(
            instance is HasMessage.field.value_from_message(instance))

    def testMessageFieldValueFromMessageWrongType(self):
        class MyMessage(messages.Message):
            pass

        class HasMessage(messages.Message):
            field = messages.MessageField(MyMessage, 1)

        self.assertRaisesWithRegexpMatch(
            messages.DecodeError,
            'Expected type MyMessage, got int: 10',
            HasMessage.field.value_from_message, 10)

    def testMessageFieldValueToMessage(self):
        class MyMessage(messages.Message):
            pass

        class HasMessage(messages.Message):
            field = messages.MessageField(MyMessage, 1)

        instance = MyMessage()

        self.assertTrue(
            instance is HasMessage.field.value_to_message(instance))

    def testMessageFieldValueToMessageWrongType(self):
        class MyMessage(messages.Message):
            pass

        class MyOtherMessage(messages.Message):
            pass

        class HasMessage(messages.Message):
            field = messages.MessageField(MyMessage, 1)

        instance = MyOtherMessage()

        self.assertRaisesWithRegexpMatch(
            messages.EncodeError,
            'Expected type MyMessage, got MyOtherMessage: <MyOtherMessage>',
            HasMessage.field.value_to_message, instance)

    def testIntegerField_AllowLong(self):
        """Test that the integer field allows for longs."""
        if six.PY2:
            messages.IntegerField(10, default=long(10))

    def testMessageFieldValidate_Initialized(self):
        """Test validation on message field."""
        class MyMessage(messages.Message):
            field1 = messages.IntegerField(1, required=True)

        field = messages.MessageField(MyMessage, 10)

        # Will validate messages where is_initialized() is False.
        message = MyMessage()
        field.validate(message)
        message.field1 = 20
        field.validate(message)

    def testEnumField(self):
        """Test the construction of enum fields."""
        self.assertRaises(messages.FieldDefinitionError,
                          messages.EnumField,
                          str,
                          10)

        self.assertRaises(messages.FieldDefinitionError,
                          messages.EnumField,
                          messages.Enum,
                          10)

        class Color(messages.Enum):
            RED = 1
            GREEN = 2
            BLUE = 3

        field = messages.EnumField(Color, 10)
        self.assertEquals(Color, field.type)

        class Another(messages.Enum):
            VALUE = 1

        self.assertRaises(messages.InvalidDefaultError,
                          messages.EnumField,
                          Color,
                          10,
                          default=Another.VALUE)

    def testEnumField_ForwardReference(self):
        """Test the construction of forward reference enum fields."""
        global MyMessage
        global ForwardEnum
        global ForwardMessage
        try:
            class MyMessage(messages.Message):

                forward = messages.EnumField('ForwardEnum', 1)
                nested = messages.EnumField('ForwardMessage.NestedEnum', 2)
                inner = messages.EnumField('Inner', 3)

                class Inner(messages.Enum):
                    pass

            class ForwardEnum(messages.Enum):
                pass

            class ForwardMessage(messages.Message):

                class NestedEnum(messages.Enum):
                    pass

            self.assertEquals(ForwardEnum,
                              MyMessage.field_by_name('forward').type)

            self.assertEquals(ForwardMessage.NestedEnum,
                              MyMessage.field_by_name('nested').type)

            self.assertEquals(MyMessage.Inner,
                              MyMessage.field_by_name('inner').type)
        finally:
            try:
                del MyMessage
                del ForwardEnum
                del ForwardMessage
            except:  # pylint:disable=bare-except
                pass

    def testEnumField_WrongType(self):
        """Test that forward referencing the wrong type raises an error."""
        global AMessage
        try:
            class AMessage(messages.Message):
                pass

            class AnotherMessage(messages.Message):

                a_field = messages.EnumField('AMessage', 1)

            self.assertRaises(messages.FieldDefinitionError,
                              getattr,
                              AnotherMessage.field_by_name('a_field'),
                              'type')
        finally:
            del AMessage

    def testMessageDefinition(self):
        """Test that message definition is set on fields."""
        class MyMessage(messages.Message):

            my_field = messages.StringField(1)

        self.assertEquals(
            MyMessage,
            MyMessage.field_by_name('my_field').message_definition())

    def testNoneAssignment(self):
        """Test that assigning None does not change comparison."""
        class MyMessage(messages.Message):

            my_field = messages.StringField(1)

        m1 = MyMessage()
        m2 = MyMessage()
        m2.my_field = None
        self.assertEquals(m1, m2)

    def testNonUtf8Str(self):
        """Test validation fails for non-UTF-8 StringField values."""
        class Thing(messages.Message):
            string_field = messages.StringField(2)

        thing = Thing()
        self.assertRaisesWithRegexpMatch(
            messages.ValidationError,
            'Field string_field encountered non-UTF-8 string',
            setattr, thing, 'string_field', test_util.BINARY)


class MessageTest(test_util.TestCase):
    """Tests for message class."""

    def CreateMessageClass(self):
        """Creates a simple message class with 3 fields.

        Fields are defined in alphabetical order but with conflicting numeric
        order.
        """
        class ComplexMessage(messages.Message):
            a3 = messages.IntegerField(3)
            b1 = messages.StringField(1)
            c2 = messages.StringField(2)

        return ComplexMessage

    def testSameNumbers(self):
        """Test that cannot assign two fields with same numbers."""

        def action():
            class BadMessage(messages.Message):
                f1 = messages.IntegerField(1)
                f2 = messages.IntegerField(1)
        self.assertRaises(messages.DuplicateNumberError,
                          action)

    def testStrictAssignment(self):
        """Tests that cannot assign to unknown or non-reserved attributes."""
        class SimpleMessage(messages.Message):
            field = messages.IntegerField(1)

        simple_message = SimpleMessage()
        self.assertRaises(AttributeError,
                          setattr,
                          simple_message,
                          'does_not_exist',
                          10)

    def testListAssignmentDoesNotCopy(self):
        class SimpleMessage(messages.Message):
            repeated = messages.IntegerField(1, repeated=True)

        message = SimpleMessage()
        original = message.repeated
        message.repeated = []
        self.assertFalse(original is message.repeated)

    def testValidate_Optional(self):
        """Tests validation of optional fields."""
        class SimpleMessage(messages.Message):
            non_required = messages.IntegerField(1)

        simple_message = SimpleMessage()
        simple_message.check_initialized()
        simple_message.non_required = 10
        simple_message.check_initialized()

    def testValidate_Required(self):
        """Tests validation of required fields."""
        class SimpleMessage(messages.Message):
            required = messages.IntegerField(1, required=True)

        simple_message = SimpleMessage()
        self.assertRaises(messages.ValidationError,
                          simple_message.check_initialized)
        simple_message.required = 10
        simple_message.check_initialized()

    def testValidate_Repeated(self):
        """Tests validation of repeated fields."""
        class SimpleMessage(messages.Message):
            repeated = messages.IntegerField(1, repeated=True)

        simple_message = SimpleMessage()

        # Check valid values.
        for valid_value in [], [10], [10, 20], (), (10,), (10, 20):
            simple_message.repeated = valid_value
            simple_message.check_initialized()

        # Check cleared.
        simple_message.repeated = []
        simple_message.check_initialized()

        # Check invalid values.
        for invalid_value in 10, ['10', '20'], [None], (None,):
            self.assertRaises(
                messages.ValidationError,
                setattr, simple_message, 'repeated', invalid_value)

    def testIsInitialized(self):
        """Tests is_initialized."""
        class SimpleMessage(messages.Message):
            required = messages.IntegerField(1, required=True)

        simple_message = SimpleMessage()
        self.assertFalse(simple_message.is_initialized())

        simple_message.required = 10

        self.assertTrue(simple_message.is_initialized())

    def testIsInitializedNestedField(self):
        """Tests is_initialized for nested fields."""
        class SimpleMessage(messages.Message):
            required = messages.IntegerField(1, required=True)

        class NestedMessage(messages.Message):
            simple = messages.MessageField(SimpleMessage, 1)

        simple_message = SimpleMessage()
        self.assertFalse(simple_message.is_initialized())
        nested_message = NestedMessage(simple=simple_message)
        self.assertFalse(nested_message.is_initialized())

        simple_message.required = 10

        self.assertTrue(simple_message.is_initialized())
        self.assertTrue(nested_message.is_initialized())

    def testInitializeNestedFieldFromDict(self):
        """Tests initializing nested fields from dict."""
        class SimpleMessage(messages.Message):
            required = messages.IntegerField(1, required=True)

        class NestedMessage(messages.Message):
            simple = messages.MessageField(SimpleMessage, 1)

        class RepeatedMessage(messages.Message):
            simple = messages.MessageField(SimpleMessage, 1, repeated=True)

        nested_message1 = NestedMessage(simple={'required': 10})
        self.assertTrue(nested_message1.is_initialized())
        self.assertTrue(nested_message1.simple.is_initialized())

        nested_message2 = NestedMessage()
        nested_message2.simple = {'required': 10}
        self.assertTrue(nested_message2.is_initialized())
        self.assertTrue(nested_message2.simple.is_initialized())

        repeated_values = [{}, {'required': 10}, SimpleMessage(required=20)]

        repeated_message1 = RepeatedMessage(simple=repeated_values)
        self.assertEquals(3, len(repeated_message1.simple))
        self.assertFalse(repeated_message1.is_initialized())

        repeated_message1.simple[0].required = 0
        self.assertTrue(repeated_message1.is_initialized())

        repeated_message2 = RepeatedMessage()
        repeated_message2.simple = repeated_values
        self.assertEquals(3, len(repeated_message2.simple))
        self.assertFalse(repeated_message2.is_initialized())

        repeated_message2.simple[0].required = 0
        self.assertTrue(repeated_message2.is_initialized())

    def testNestedMethodsNotAllowed(self):
        """Test that method definitions on Message classes are not allowed."""
        def action():
            class WithMethods(messages.Message):

                def not_allowed(self):
                    pass

        self.assertRaises(messages.MessageDefinitionError,
                          action)

    def testNestedAttributesNotAllowed(self):
        """Test attribute assignment on Message classes is not allowed."""
        def int_attribute():
            class WithMethods(messages.Message):
                not_allowed = 1

        def string_attribute():
            class WithMethods(messages.Message):
                not_allowed = 'not allowed'

        def enum_attribute():
            class WithMethods(messages.Message):
                not_allowed = Color.RED

        for action in (int_attribute, string_attribute, enum_attribute):
            self.assertRaises(messages.MessageDefinitionError,
                              action)

    def testNameIsSetOnFields(self):
        """Make sure name is set on fields after Message class init."""
        class HasNamedFields(messages.Message):
            field = messages.StringField(1)

        self.assertEquals('field', HasNamedFields.field_by_number(1).name)

    def testSubclassingMessageDisallowed(self):
        """Not permitted to create sub-classes of message classes."""
        class SuperClass(messages.Message):
            pass

        def action():
            class SubClass(SuperClass):
                pass

        self.assertRaises(messages.MessageDefinitionError,
                          action)

    def testAllFields(self):
        """Test all_fields method."""
        ComplexMessage = self.CreateMessageClass()
        fields = list(ComplexMessage.all_fields())

        # Order does not matter, so sort now.
        fields = sorted(fields, key=lambda f: f.name)

        self.assertEquals(3, len(fields))
        self.assertEquals('a3', fields[0].name)
        self.assertEquals('b1', fields[1].name)
        self.assertEquals('c2', fields[2].name)

    def testFieldByName(self):
        """Test getting field by name."""
        ComplexMessage = self.CreateMessageClass()

        self.assertEquals(3, ComplexMessage.field_by_name('a3').number)
        self.assertEquals(1, ComplexMessage.field_by_name('b1').number)
        self.assertEquals(2, ComplexMessage.field_by_name('c2').number)

        self.assertRaises(KeyError,
                          ComplexMessage.field_by_name,
                          'unknown')

    def testFieldByNumber(self):
        """Test getting field by number."""
        ComplexMessage = self.CreateMessageClass()

        self.assertEquals('a3', ComplexMessage.field_by_number(3).name)
        self.assertEquals('b1', ComplexMessage.field_by_number(1).name)
        self.assertEquals('c2', ComplexMessage.field_by_number(2).name)

        self.assertRaises(KeyError,
                          ComplexMessage.field_by_number,
                          4)

    def testGetAssignedValue(self):
        """Test getting the assigned value of a field."""
        class SomeMessage(messages.Message):
            a_value = messages.StringField(1, default=u'a default')

        message = SomeMessage()
        self.assertEquals(None, message.get_assigned_value('a_value'))

        message.a_value = u'a string'
        self.assertEquals(u'a string', message.get_assigned_value('a_value'))

        message.a_value = u'a default'
        self.assertEquals(u'a default', message.get_assigned_value('a_value'))

        self.assertRaisesWithRegexpMatch(
            AttributeError,
            'Message SomeMessage has no field no_such_field',
            message.get_assigned_value,
            'no_such_field')

    def testReset(self):
        """Test resetting a field value."""
        class SomeMessage(messages.Message):
            a_value = messages.StringField(1, default=u'a default')
            repeated = messages.IntegerField(2, repeated=True)

        message = SomeMessage()

        self.assertRaises(AttributeError, message.reset, 'unknown')

        self.assertEquals(u'a default', message.a_value)
        message.reset('a_value')
        self.assertEquals(u'a default', message.a_value)

        message.a_value = u'a new value'
        self.assertEquals(u'a new value', message.a_value)
        message.reset('a_value')
        self.assertEquals(u'a default', message.a_value)

        message.repeated = [1, 2, 3]
        self.assertEquals([1, 2, 3], message.repeated)
        saved = message.repeated
        message.reset('repeated')
        self.assertEquals([], message.repeated)
        self.assertIsInstance(message.repeated, messages.FieldList)
        self.assertEquals([1, 2, 3], saved)

    def testAllowNestedEnums(self):
        """Test allowing nested enums in a message definition."""
        class Trade(messages.Message):

            class Duration(messages.Enum):
                GTC = 1
                DAY = 2

            class Currency(messages.Enum):
                USD = 1
                GBP = 2
                INR = 3

        # Sorted by name order seems to be the only feasible option.
        self.assertEquals(['Currency', 'Duration'], Trade.__enums__)

        # Message definition will now be set on Enumerated objects.
        self.assertEquals(Trade, Trade.Duration.message_definition())

    def testAllowNestedMessages(self):
        """Test allowing nested messages in a message definition."""
        class Trade(messages.Message):

            class Lot(messages.Message):
                pass

            class Agent(messages.Message):
                pass

        # Sorted by name order seems to be the only feasible option.
        self.assertEquals(['Agent', 'Lot'], Trade.__messages__)
        self.assertEquals(Trade, Trade.Agent.message_definition())
        self.assertEquals(Trade, Trade.Lot.message_definition())

        # But not Message itself.
        def action():
            class Trade(messages.Message):
                NiceTry = messages.Message
        self.assertRaises(messages.MessageDefinitionError, action)

    def testDisallowClassAssignments(self):
        """Test setting class attributes may not happen."""
        class MyMessage(messages.Message):
            pass

        self.assertRaises(AttributeError,
                          setattr,
                          MyMessage,
                          'x',
                          'do not assign')

    def testEquality(self):
        """Test message class equality."""
        # Comparison against enums must work.
        class MyEnum(messages.Enum):
            val1 = 1
            val2 = 2

        # Comparisons against nested messages must work.
        class AnotherMessage(messages.Message):
            string = messages.StringField(1)

        class MyMessage(messages.Message):
            field1 = messages.IntegerField(1)
            field2 = messages.EnumField(MyEnum, 2)
            field3 = messages.MessageField(AnotherMessage, 3)

        message1 = MyMessage()

        self.assertNotEquals('hi', message1)
        self.assertNotEquals(AnotherMessage(), message1)
        self.assertEquals(message1, message1)

        message2 = MyMessage()

        self.assertEquals(message1, message2)

        message1.field1 = 10
        self.assertNotEquals(message1, message2)

        message2.field1 = 20
        self.assertNotEquals(message1, message2)

        message2.field1 = 10
        self.assertEquals(message1, message2)

        message1.field2 = MyEnum.val1
        self.assertNotEquals(message1, message2)

        message2.field2 = MyEnum.val2
        self.assertNotEquals(message1, message2)

        message2.field2 = MyEnum.val1
        self.assertEquals(message1, message2)

        message1.field3 = AnotherMessage()
        message1.field3.string = 'value1'
        self.assertNotEquals(message1, message2)

        message2.field3 = AnotherMessage()
        message2.field3.string = 'value2'
        self.assertNotEquals(message1, message2)

        message2.field3.string = 'value1'
        self.assertEquals(message1, message2)

    def testEqualityWithUnknowns(self):
        """Test message class equality with unknown fields."""

        class MyMessage(messages.Message):
            field1 = messages.IntegerField(1)

        message1 = MyMessage()
        message2 = MyMessage()
        self.assertEquals(message1, message2)
        message1.set_unrecognized_field('unknown1', 'value1',
                                        messages.Variant.STRING)
        self.assertEquals(message1, message2)

        message1.set_unrecognized_field('unknown2', ['asdf', 3],
                                        messages.Variant.STRING)
        message1.set_unrecognized_field('unknown3', 4.7,
                                        messages.Variant.DOUBLE)
        self.assertEquals(message1, message2)

    def testUnrecognizedFieldInvalidVariant(self):
        class MyMessage(messages.Message):
            field1 = messages.IntegerField(1)

        message1 = MyMessage()
        self.assertRaises(
            TypeError, message1.set_unrecognized_field, 'unknown4',
            {'unhandled': 'type'}, None)
        self.assertRaises(
            TypeError, message1.set_unrecognized_field, 'unknown4',
            {'unhandled': 'type'}, 123)

    def testRepr(self):
        """Test represtation of Message object."""
        class MyMessage(messages.Message):
            integer_value = messages.IntegerField(1)
            string_value = messages.StringField(2)
            unassigned = messages.StringField(3)
            unassigned_with_default = messages.StringField(
                4, default=u'a default')

        my_message = MyMessage()
        my_message.integer_value = 42
        my_message.string_value = u'A string'

        pat = re.compile(r"<MyMessage\n integer_value: 42\n"
                         " string_value: [u]?'A string'>")
        self.assertTrue(pat.match(repr(my_message)) is not None)

    def testValidation(self):
        """Test validation of message values."""
        # Test optional.
        class SubMessage(messages.Message):
            pass

        class Message(messages.Message):
            val = messages.MessageField(SubMessage, 1)

        message = Message()

        message_field = messages.MessageField(Message, 1)
        message_field.validate(message)
        message.val = SubMessage()
        message_field.validate(message)
        self.assertRaises(messages.ValidationError,
                          setattr, message, 'val', [SubMessage()])

        # Test required.
        class Message(messages.Message):
            val = messages.MessageField(SubMessage, 1, required=True)

        message = Message()

        message_field = messages.MessageField(Message, 1)
        message_field.validate(message)
        message.val = SubMessage()
        message_field.validate(message)
        self.assertRaises(messages.ValidationError,
                          setattr, message, 'val', [SubMessage()])

        # Test repeated.
        class Message(messages.Message):
            val = messages.MessageField(SubMessage, 1, repeated=True)

        message = Message()

        message_field = messages.MessageField(Message, 1)
        message_field.validate(message)
        self.assertRaisesWithRegexpMatch(
            messages.ValidationError,
            "Field val is repeated. Found: <SubMessage>",
            setattr, message, 'val', SubMessage())
        message.val = [SubMessage()]
        message_field.validate(message)

    def testDefinitionName(self):
        """Test message name."""
        class MyMessage(messages.Message):
            pass

        module_name = test_util.get_module_name(FieldTest)
        self.assertEquals('%s.MyMessage' % module_name,
                          MyMessage.definition_name())
        self.assertEquals(module_name, MyMessage.outer_definition_name())
        self.assertEquals(module_name, MyMessage.definition_package())

        self.assertEquals(six.text_type, type(MyMessage.definition_name()))
        self.assertEquals(six.text_type, type(
            MyMessage.outer_definition_name()))
        self.assertEquals(six.text_type, type(MyMessage.definition_package()))

    def testDefinitionName_OverrideModule(self):
        """Test message module is overriden by module package name."""
        class MyMessage(messages.Message):
            pass

        global package
        package = 'my.package'

        try:
            self.assertEquals('my.package.MyMessage',
                              MyMessage.definition_name())
            self.assertEquals('my.package', MyMessage.outer_definition_name())
            self.assertEquals('my.package', MyMessage.definition_package())

            self.assertEquals(six.text_type, type(MyMessage.definition_name()))
            self.assertEquals(six.text_type, type(
                MyMessage.outer_definition_name()))
            self.assertEquals(six.text_type, type(
                MyMessage.definition_package()))
        finally:
            del package

    def testDefinitionName_NoModule(self):
        """Test what happens when there is no module for message."""
        class MyMessage(messages.Message):
            pass

        original_modules = sys.modules
        sys.modules = dict(sys.modules)
        try:
            del sys.modules[__name__]
            self.assertEquals('MyMessage', MyMessage.definition_name())
            self.assertEquals(None, MyMessage.outer_definition_name())
            self.assertEquals(None, MyMessage.definition_package())

            self.assertEquals(six.text_type, type(MyMessage.definition_name()))
        finally:
            sys.modules = original_modules

    def testDefinitionName_Nested(self):
        """Test nested message names."""
        class MyMessage(messages.Message):

            class NestedMessage(messages.Message):

                class NestedMessage(messages.Message):

                    pass

        module_name = test_util.get_module_name(MessageTest)
        self.assertEquals('%s.MyMessage.NestedMessage' % module_name,
                          MyMessage.NestedMessage.definition_name())
        self.assertEquals('%s.MyMessage' % module_name,
                          MyMessage.NestedMessage.outer_definition_name())
        self.assertEquals(module_name,
                          MyMessage.NestedMessage.definition_package())

        self.assertEquals(
            '%s.MyMessage.NestedMessage.NestedMessage' % module_name,
            MyMessage.NestedMessage.NestedMessage.definition_name())
        self.assertEquals(
            '%s.MyMessage.NestedMessage' % module_name,
            MyMessage.NestedMessage.NestedMessage.outer_definition_name())
        self.assertEquals(
            module_name,
            MyMessage.NestedMessage.NestedMessage.definition_package())

    def testMessageDefinition(self):
        """Test that enumeration knows its enclosing message definition."""
        class OuterMessage(messages.Message):

            class InnerMessage(messages.Message):
                pass

        self.assertEquals(None, OuterMessage.message_definition())
        self.assertEquals(OuterMessage,
                          OuterMessage.InnerMessage.message_definition())

    def testConstructorKwargs(self):
        """Test kwargs via constructor."""
        class SomeMessage(messages.Message):
            name = messages.StringField(1)
            number = messages.IntegerField(2)

        expected = SomeMessage()
        expected.name = 'my name'
        expected.number = 200
        self.assertEquals(expected, SomeMessage(name='my name', number=200))

    def testConstructorNotAField(self):
        """Test kwargs via constructor with wrong names."""
        class SomeMessage(messages.Message):
            pass

        self.assertRaisesWithRegexpMatch(
            AttributeError,
            ('May not assign arbitrary value does_not_exist to message '
             'SomeMessage'),
            SomeMessage,
            does_not_exist=10)

    def testGetUnsetRepeatedValue(self):
        class SomeMessage(messages.Message):
            repeated = messages.IntegerField(1, repeated=True)

        instance = SomeMessage()
        self.assertEquals([], instance.repeated)
        self.assertTrue(isinstance(instance.repeated, messages.FieldList))

    def testCompareAutoInitializedRepeatedFields(self):
        class SomeMessage(messages.Message):
            repeated = messages.IntegerField(1, repeated=True)

        message1 = SomeMessage(repeated=[])
        message2 = SomeMessage()
        self.assertEquals(message1, message2)

    def testUnknownValues(self):
        """Test message class equality with unknown fields."""
        class MyMessage(messages.Message):
            field1 = messages.IntegerField(1)

        message = MyMessage()
        self.assertEquals([], message.all_unrecognized_fields())
        self.assertEquals((None, None),
                          message.get_unrecognized_field_info('doesntexist'))
        self.assertEquals((None, None),
                          message.get_unrecognized_field_info(
                              'doesntexist', None, None))
        self.assertEquals(('defaultvalue', 'defaultwire'),
                          message.get_unrecognized_field_info(
                              'doesntexist', 'defaultvalue', 'defaultwire'))
        self.assertEquals((3, None),
                          message.get_unrecognized_field_info(
                              'doesntexist', value_default=3))

        message.set_unrecognized_field('exists', 9.5, messages.Variant.DOUBLE)
        self.assertEquals(1, len(message.all_unrecognized_fields()))
        self.assertTrue('exists' in message.all_unrecognized_fields())
        self.assertEquals((9.5, messages.Variant.DOUBLE),
                          message.get_unrecognized_field_info('exists'))
        self.assertEquals((9.5, messages.Variant.DOUBLE),
                          message.get_unrecognized_field_info('exists', 'type',
                                                              1234))
        self.assertEquals(
            (1234, None),
            message.get_unrecognized_field_info('doesntexist', 1234))

        message.set_unrecognized_field(
            'another', 'value', messages.Variant.STRING)
        self.assertEquals(2, len(message.all_unrecognized_fields()))
        self.assertTrue('exists' in message.all_unrecognized_fields())
        self.assertTrue('another' in message.all_unrecognized_fields())
        self.assertEquals((9.5, messages.Variant.DOUBLE),
                          message.get_unrecognized_field_info('exists'))
        self.assertEquals(('value', messages.Variant.STRING),
                          message.get_unrecognized_field_info('another'))

        message.set_unrecognized_field('typetest1', ['list', 0, ('test',)],
                                       messages.Variant.STRING)
        self.assertEquals((['list', 0, ('test',)], messages.Variant.STRING),
                          message.get_unrecognized_field_info('typetest1'))
        message.set_unrecognized_field(
            'typetest2', '', messages.Variant.STRING)
        self.assertEquals(('', messages.Variant.STRING),
                          message.get_unrecognized_field_info('typetest2'))

    def testPickle(self):
        """Testing pickling and unpickling of Message instances."""
        global MyEnum
        global AnotherMessage
        global MyMessage

        class MyEnum(messages.Enum):
            val1 = 1
            val2 = 2

        class AnotherMessage(messages.Message):
            string = messages.StringField(1, repeated=True)

        class MyMessage(messages.Message):
            field1 = messages.IntegerField(1)
            field2 = messages.EnumField(MyEnum, 2)
            field3 = messages.MessageField(AnotherMessage, 3)

        message = MyMessage(field1=1, field2=MyEnum.val2,
                            field3=AnotherMessage(string=['a', 'b', 'c']))
        message.set_unrecognized_field(
            'exists', 'value', messages.Variant.STRING)
        message.set_unrecognized_field('repeated', ['list', 0, ('test',)],
                                       messages.Variant.STRING)
        unpickled = pickle.loads(pickle.dumps(message))
        self.assertEquals(message, unpickled)
        self.assertTrue(AnotherMessage.string is unpickled.field3.string.field)
        self.assertTrue('exists' in message.all_unrecognized_fields())
        self.assertEquals(('value', messages.Variant.STRING),
                          message.get_unrecognized_field_info('exists'))
        self.assertEquals((['list', 0, ('test',)], messages.Variant.STRING),
                          message.get_unrecognized_field_info('repeated'))


class FindDefinitionTest(test_util.TestCase):
    """Test finding definitions relative to various definitions and modules."""

    def setUp(self):
        """Set up module-space.  Starts off empty."""
        self.modules = {}

    def DefineModule(self, name):
        """Define a module and its parents in module space.

        Modules that are already defined in self.modules are not re-created.

        Args:
          name: Fully qualified name of modules to create.

        Returns:
          Deepest nested module.  For example:

            DefineModule('a.b.c')  # Returns c.
        """
        name_path = name.split('.')
        full_path = []
        for node in name_path:
            full_path.append(node)
            full_name = '.'.join(full_path)
            self.modules.setdefault(full_name, types.ModuleType(full_name))
        return self.modules[name]

    def DefineMessage(self, module, name, children=None, add_to_module=True):
        """Define a new Message class in the context of a module.

        Used for easily describing complex Message hierarchy. Message
        is defined including all child definitions.

        Args:
          module: Fully qualified name of module to place Message class in.
          name: Name of Message to define within module.
          children: Define any level of nesting of children
            definitions. To define a message, map the name to another
            dictionary. The dictionary can itself contain additional
            definitions, and so on. To map to an Enum, define the Enum
            class separately and map it by name.
          add_to_module: If True, new Message class is added to
            module. If False, new Message is not added.

        """
        children = children or {}
        # Make sure module exists.
        module_instance = self.DefineModule(module)

        # Recursively define all child messages.
        for attribute, value in children.items():
            if isinstance(value, dict):
                children[attribute] = self.DefineMessage(
                    module, attribute, value, False)

        # Override default __module__ variable.
        children['__module__'] = module

        # Instantiate and possibly add to module.
        message_class = type(name, (messages.Message,), dict(children))
        if add_to_module:
            setattr(module_instance, name, message_class)
        return message_class

    # pylint:disable=unused-argument
    # pylint:disable=redefined-builtin
    def Importer(self, module, globals='', locals='', fromlist=None):
        """Importer function.

        Acts like __import__. Only loads modules from self.modules.
        Does not try to load real modules defined elsewhere. Does not
        try to handle relative imports.

        Args:
          module: Fully qualified name of module to load from self.modules.

        """
        if fromlist is None:
            module = module.split('.')[0]
        try:
            return self.modules[module]
        except KeyError:
            raise ImportError()
    # pylint:disable=unused-argument

    def testNoSuchModule(self):
        """Test searching for definitions that do no exist."""
        self.assertRaises(messages.DefinitionNotFoundError,
                          messages.find_definition,
                          'does.not.exist',
                          importer=self.Importer)

    def testRefersToModule(self):
        """Test that referring to a module does not return that module."""
        self.DefineModule('i.am.a.module')
        self.assertRaises(messages.DefinitionNotFoundError,
                          messages.find_definition,
                          'i.am.a.module',
                          importer=self.Importer)

    def testNoDefinition(self):
        """Test not finding a definition in an existing module."""
        self.DefineModule('i.am.a.module')
        self.assertRaises(messages.DefinitionNotFoundError,
                          messages.find_definition,
                          'i.am.a.module.MyMessage',
                          importer=self.Importer)

    def testNotADefinition(self):
        """Test trying to fetch something that is not a definition."""
        module = self.DefineModule('i.am.a.module')
        setattr(module, 'A', 'a string')
        self.assertRaises(messages.DefinitionNotFoundError,
                          messages.find_definition,
                          'i.am.a.module.A',
                          importer=self.Importer)

    def testGlobalFind(self):
        """Test finding definitions from fully qualified module names."""
        A = self.DefineMessage('a.b.c', 'A', {})
        self.assertEquals(A, messages.find_definition('a.b.c.A',
                                                      importer=self.Importer))
        B = self.DefineMessage('a.b.c', 'B', {'C': {}})
        self.assertEquals(
            B.C,
            messages.find_definition('a.b.c.B.C', importer=self.Importer))

    def testRelativeToModule(self):
        """Test finding definitions relative to modules."""
        # Define modules.
        a = self.DefineModule('a')
        b = self.DefineModule('a.b')
        c = self.DefineModule('a.b.c')

        # Define messages.
        A = self.DefineMessage('a', 'A')
        B = self.DefineMessage('a.b', 'B')
        C = self.DefineMessage('a.b.c', 'C')
        D = self.DefineMessage('a.b.d', 'D')

        # Find A, B, C and D relative to a.
        self.assertEquals(A, messages.find_definition(
            'A', a, importer=self.Importer))
        self.assertEquals(B, messages.find_definition(
            'b.B', a, importer=self.Importer))
        self.assertEquals(C, messages.find_definition(
            'b.c.C', a, importer=self.Importer))
        self.assertEquals(D, messages.find_definition(
            'b.d.D', a, importer=self.Importer))

        # Find A, B, C and D relative to b.
        self.assertEquals(A, messages.find_definition(
            'A', b, importer=self.Importer))
        self.assertEquals(B, messages.find_definition(
            'B', b, importer=self.Importer))
        self.assertEquals(C, messages.find_definition(
            'c.C', b, importer=self.Importer))
        self.assertEquals(D, messages.find_definition(
            'd.D', b, importer=self.Importer))

        # Find A, B, C and D relative to c.  Module d is the same case as c.
        self.assertEquals(A, messages.find_definition(
            'A', c, importer=self.Importer))
        self.assertEquals(B, messages.find_definition(
            'B', c, importer=self.Importer))
        self.assertEquals(C, messages.find_definition(
            'C', c, importer=self.Importer))
        self.assertEquals(D, messages.find_definition(
            'd.D', c, importer=self.Importer))

    def testRelativeToMessages(self):
        """Test finding definitions relative to Message definitions."""
        A = self.DefineMessage('a.b', 'A', {'B': {'C': {}, 'D': {}}})
        B = A.B
        C = A.B.C
        D = A.B.D

        # Find relative to A.
        self.assertEquals(A, messages.find_definition(
            'A', A, importer=self.Importer))
        self.assertEquals(B, messages.find_definition(
            'B', A, importer=self.Importer))
        self.assertEquals(C, messages.find_definition(
            'B.C', A, importer=self.Importer))
        self.assertEquals(D, messages.find_definition(
            'B.D', A, importer=self.Importer))

        # Find relative to B.
        self.assertEquals(A, messages.find_definition(
            'A', B, importer=self.Importer))
        self.assertEquals(B, messages.find_definition(
            'B', B, importer=self.Importer))
        self.assertEquals(C, messages.find_definition(
            'C', B, importer=self.Importer))
        self.assertEquals(D, messages.find_definition(
            'D', B, importer=self.Importer))

        # Find relative to C.
        self.assertEquals(A, messages.find_definition(
            'A', C, importer=self.Importer))
        self.assertEquals(B, messages.find_definition(
            'B', C, importer=self.Importer))
        self.assertEquals(C, messages.find_definition(
            'C', C, importer=self.Importer))
        self.assertEquals(D, messages.find_definition(
            'D', C, importer=self.Importer))

        # Find relative to C searching from c.
        self.assertEquals(A, messages.find_definition(
            'b.A', C, importer=self.Importer))
        self.assertEquals(B, messages.find_definition(
            'b.A.B', C, importer=self.Importer))
        self.assertEquals(C, messages.find_definition(
            'b.A.B.C', C, importer=self.Importer))
        self.assertEquals(D, messages.find_definition(
            'b.A.B.D', C, importer=self.Importer))

    def testAbsoluteReference(self):
        """Test finding absolute definition names."""
        # Define modules.
        a = self.DefineModule('a')
        b = self.DefineModule('a.a')

        # Define messages.
        aA = self.DefineMessage('a', 'A')
        aaA = self.DefineMessage('a.a', 'A')

        # Always find a.A.
        self.assertEquals(aA, messages.find_definition('.a.A', None,
                                                       importer=self.Importer))
        self.assertEquals(aA, messages.find_definition('.a.A', a,
                                                       importer=self.Importer))
        self.assertEquals(aA, messages.find_definition('.a.A', aA,
                                                       importer=self.Importer))
        self.assertEquals(aA, messages.find_definition('.a.A', aaA,
                                                       importer=self.Importer))

    def testFindEnum(self):
        """Test that Enums are found."""
        class Color(messages.Enum):
            pass
        A = self.DefineMessage('a', 'A', {'Color': Color})

        self.assertEquals(
            Color,
            messages.find_definition('Color', A, importer=self.Importer))

    def testFalseScope(self):
        """Test Message definitions nested in strange objects are hidden."""
        global X

        class X(object):

            class A(messages.Message):
                pass

        self.assertRaises(TypeError, messages.find_definition, 'A', X)
        self.assertRaises(messages.DefinitionNotFoundError,
                          messages.find_definition,
                          'X.A', sys.modules[__name__])

    def testSearchAttributeFirst(self):
        """Make sure not faked out by module, but continues searching."""
        A = self.DefineMessage('a', 'A')
        module_A = self.DefineModule('a.A')

        self.assertEquals(A, messages.find_definition(
            'a.A', None, importer=self.Importer))


def main():
    unittest.main()


if __name__ == '__main__':
    main()
