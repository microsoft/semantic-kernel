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

"""Test utilities for message testing.

Includes module interface test to ensure that public parts of module are
correctly declared in __all__.

Includes message types that correspond to those defined in
services_test.proto.

Includes additional test utilities to make sure encoding/decoding libraries
conform.
"""
import cgi
import datetime
import inspect
import os
import re
import socket
import types
import unittest

import six
from six.moves import range  # pylint: disable=redefined-builtin

from apitools.base.protorpclite import message_types
from apitools.base.protorpclite import messages
from apitools.base.protorpclite import util

# Unicode of the word "Russian" in cyrillic.
RUSSIAN = u'\u0440\u0443\u0441\u0441\u043a\u0438\u0439'

# All characters binary value interspersed with nulls.
BINARY = b''.join(six.int2byte(value) + b'\0' for value in range(256))


class TestCase(unittest.TestCase):

    def assertRaisesWithRegexpMatch(self,
                                    exception,
                                    regexp,
                                    function,
                                    *params,
                                    **kwargs):
        """Check that exception is raised and text matches regular expression.

        Args:
          exception: Exception type that is expected.
          regexp: String regular expression that is expected in error message.
          function: Callable to test.
          params: Parameters to forward to function.
          kwargs: Keyword arguments to forward to function.
        """
        try:
            function(*params, **kwargs)
            self.fail('Expected exception %s was not raised' %
                      exception.__name__)
        except exception as err:
            match = bool(re.match(regexp, str(err)))
            self.assertTrue(match, 'Expected match "%s", found "%s"' % (regexp,
                                                                        err))

    def assertHeaderSame(self, header1, header2):
        """Check that two HTTP headers are the same.

        Args:
          header1: Header value string 1.
          header2: header value string 2.
        """
        value1, params1 = cgi.parse_header(header1)
        value2, params2 = cgi.parse_header(header2)
        self.assertEqual(value1, value2)
        self.assertEqual(params1, params2)

    def assertIterEqual(self, iter1, iter2):
        """Check two iterators or iterables are equal independent of order.

        Similar to Python 2.7 assertItemsEqual.  Named differently in order to
        avoid potential conflict.

        Args:
          iter1: An iterator or iterable.
          iter2: An iterator or iterable.
        """
        list1 = list(iter1)
        list2 = list(iter2)

        unmatched1 = list()

        while list1:
            item1 = list1[0]
            del list1[0]
            for index in range(len(list2)):
                if item1 == list2[index]:
                    del list2[index]
                    break
            else:
                unmatched1.append(item1)

        error_message = []
        for item in unmatched1:
            error_message.append(
                '  Item from iter1 not found in iter2: %r' % item)
        for item in list2:
            error_message.append(
                '  Item from iter2 not found in iter1: %r' % item)
        if error_message:
            self.fail('Collections not equivalent:\n' +
                      '\n'.join(error_message))


class ModuleInterfaceTest(object):
    """Test to ensure module interface is carefully constructed.

    A module interface is the set of public objects listed in the
    module __all__ attribute. Modules that that are considered public
    should have this interface carefully declared. At all times, the
    __all__ attribute should have objects intended to be publically
    used and all other objects in the module should be considered
    unused.

    Protected attributes (those beginning with '_') and other imported
    modules should not be part of this set of variables. An exception
    is for variables that begin and end with '__' which are implicitly
    part of the interface (eg. __name__, __file__, __all__ itself,
    etc.).

    Modules that are imported in to the tested modules are an
    exception and may be left out of the __all__ definition. The test
    is done by checking the value of what would otherwise be a public
    name and not allowing it to be exported if it is an instance of a
    module. Modules that are explicitly exported are for the time
    being not permitted.

    To use this test class a module should define a new class that
    inherits first from ModuleInterfaceTest and then from
    test_util.TestCase. No other tests should be added to this test
    case, making the order of inheritance less important, but if setUp
    for some reason is overidden, it is important that
    ModuleInterfaceTest is first in the list so that its setUp method
    is invoked.

    Multiple inheritance is required so that ModuleInterfaceTest is
    not itself a test, and is not itself executed as one.

    The test class is expected to have the following class attributes
    defined:

      MODULE: A reference to the module that is being validated for interface
        correctness.

    Example:
      Module definition (hello.py):

        import sys

        __all__ = ['hello']

        def _get_outputter():
          return sys.stdout

        def hello():
          _get_outputter().write('Hello\n')

      Test definition:

        import unittest
        from protorpc import test_util

        import hello

        class ModuleInterfaceTest(test_util.ModuleInterfaceTest,
                                  test_util.TestCase):

          MODULE = hello


        class HelloTest(test_util.TestCase):
          ... Test 'hello' module ...


        if __name__ == '__main__':
          unittest.main()

    """

    def setUp(self):
        """Set up makes sure that MODULE and IMPORTED_MODULES is defined.

        This is a basic configuration test for the test itself so does not
        get it's own test case.
        """
        if not hasattr(self, 'MODULE'):
            self.fail(
                "You must define 'MODULE' on ModuleInterfaceTest sub-class "
                "%s." % type(self).__name__)

    def testAllExist(self):
        """Test that all attributes defined in __all__ exist."""
        missing_attributes = []
        for attribute in self.MODULE.__all__:
            if not hasattr(self.MODULE, attribute):
                missing_attributes.append(attribute)
        if missing_attributes:
            self.fail('%s of __all__ are not defined in module.' %
                      missing_attributes)

    def testAllExported(self):
        """Test that all public attributes not imported are in __all__."""
        missing_attributes = []
        for attribute in dir(self.MODULE):
            if not attribute.startswith('_'):
                if (attribute not in self.MODULE.__all__ and
                        not isinstance(getattr(self.MODULE, attribute),
                                       types.ModuleType) and
                        attribute != 'with_statement'):
                    missing_attributes.append(attribute)
        if missing_attributes:
            self.fail('%s are not modules and not defined in __all__.' %
                      missing_attributes)

    def testNoExportedProtectedVariables(self):
        """Test that there are no protected variables listed in __all__."""
        protected_variables = []
        for attribute in self.MODULE.__all__:
            if attribute.startswith('_'):
                protected_variables.append(attribute)
        if protected_variables:
            self.fail('%s are protected variables and may not be exported.' %
                      protected_variables)

    def testNoExportedModules(self):
        """Test that no modules exist in __all__."""
        exported_modules = []
        for attribute in self.MODULE.__all__:
            try:
                value = getattr(self.MODULE, attribute)
            except AttributeError:
                # This is a different error case tested for in testAllExist.
                pass
            else:
                if isinstance(value, types.ModuleType):
                    exported_modules.append(attribute)
        if exported_modules:
            self.fail('%s are modules and may not be exported.' %
                      exported_modules)


class NestedMessage(messages.Message):
    """Simple message that gets nested in another message."""

    a_value = messages.StringField(1, required=True)


class HasNestedMessage(messages.Message):
    """Message that has another message nested in it."""

    nested = messages.MessageField(NestedMessage, 1)
    repeated_nested = messages.MessageField(NestedMessage, 2, repeated=True)


class HasDefault(messages.Message):
    """Has a default value."""

    a_value = messages.StringField(1, default=u'a default')


class OptionalMessage(messages.Message):
    """Contains all message types."""

    class SimpleEnum(messages.Enum):
        """Simple enumeration type."""
        VAL1 = 1
        VAL2 = 2

    double_value = messages.FloatField(1, variant=messages.Variant.DOUBLE)
    float_value = messages.FloatField(2, variant=messages.Variant.FLOAT)
    int64_value = messages.IntegerField(3, variant=messages.Variant.INT64)
    uint64_value = messages.IntegerField(4, variant=messages.Variant.UINT64)
    int32_value = messages.IntegerField(5, variant=messages.Variant.INT32)
    bool_value = messages.BooleanField(6, variant=messages.Variant.BOOL)
    string_value = messages.StringField(7, variant=messages.Variant.STRING)
    bytes_value = messages.BytesField(8, variant=messages.Variant.BYTES)
    enum_value = messages.EnumField(SimpleEnum, 10)


class RepeatedMessage(messages.Message):
    """Contains all message types as repeated fields."""

    class SimpleEnum(messages.Enum):
        """Simple enumeration type."""
        VAL1 = 1
        VAL2 = 2

    double_value = messages.FloatField(1,
                                       variant=messages.Variant.DOUBLE,
                                       repeated=True)
    float_value = messages.FloatField(2,
                                      variant=messages.Variant.FLOAT,
                                      repeated=True)
    int64_value = messages.IntegerField(3,
                                        variant=messages.Variant.INT64,
                                        repeated=True)
    uint64_value = messages.IntegerField(4,
                                         variant=messages.Variant.UINT64,
                                         repeated=True)
    int32_value = messages.IntegerField(5,
                                        variant=messages.Variant.INT32,
                                        repeated=True)
    bool_value = messages.BooleanField(6,
                                       variant=messages.Variant.BOOL,
                                       repeated=True)
    string_value = messages.StringField(7,
                                        variant=messages.Variant.STRING,
                                        repeated=True)
    bytes_value = messages.BytesField(8,
                                      variant=messages.Variant.BYTES,
                                      repeated=True)
    enum_value = messages.EnumField(SimpleEnum,
                                    10,
                                    repeated=True)


class HasOptionalNestedMessage(messages.Message):

    nested = messages.MessageField(OptionalMessage, 1)
    repeated_nested = messages.MessageField(OptionalMessage, 2, repeated=True)


# pylint:disable=anomalous-unicode-escape-in-string
class ProtoConformanceTestBase(object):
    """Protocol conformance test base class.

    Each supported protocol should implement two methods that support encoding
    and decoding of Message objects in that format:

      encode_message(message) - Serialize to encoding.
      encode_message(message, encoded_message) - Deserialize from encoding.

    Tests for the modules where these functions are implemented should extend
    this class in order to support basic behavioral expectations.  This ensures
    that protocols correctly encode and decode message transparently to the
    caller.

    In order to support these test, the base class should also extend
    the TestCase class and implement the following class attributes
    which define the encoded version of certain protocol buffers:

      encoded_partial:
        <OptionalMessage
          double_value: 1.23
          int64_value: -100000000000
          string_value: u"a string"
          enum_value: OptionalMessage.SimpleEnum.VAL2
          >

      encoded_full:
        <OptionalMessage
          double_value: 1.23
          float_value: -2.5
          int64_value: -100000000000
          uint64_value: 102020202020
          int32_value: 1020
          bool_value: true
          string_value: u"a string\u044f"
          bytes_value: b"a bytes\xff\xfe"
          enum_value: OptionalMessage.SimpleEnum.VAL2
          >

      encoded_repeated:
        <RepeatedMessage
          double_value: [1.23, 2.3]
          float_value: [-2.5, 0.5]
          int64_value: [-100000000000, 20]
          uint64_value: [102020202020, 10]
          int32_value: [1020, 718]
          bool_value: [true, false]
          string_value: [u"a string\u044f", u"another string"]
          bytes_value: [b"a bytes\xff\xfe", b"another bytes"]
          enum_value: [OptionalMessage.SimpleEnum.VAL2,
                       OptionalMessage.SimpleEnum.VAL 1]
          >

      encoded_nested:
        <HasNestedMessage
          nested: <NestedMessage
            a_value: "a string"
            >
          >

      encoded_repeated_nested:
        <HasNestedMessage
          repeated_nested: [
              <NestedMessage a_value: "a string">,
              <NestedMessage a_value: "another string">
            ]
          >

      unexpected_tag_message:
        An encoded message that has an undefined tag or number in the stream.

      encoded_default_assigned:
        <HasDefault
          a_value: "a default"
          >

      encoded_nested_empty:
        <HasOptionalNestedMessage
          nested: <OptionalMessage>
          >

      encoded_invalid_enum:
        <OptionalMessage
          enum_value: (invalid value for serialization type)
          >
    """

    encoded_empty_message = ''

    def testEncodeInvalidMessage(self):
        message = NestedMessage()
        self.assertRaises(messages.ValidationError,
                          self.PROTOLIB.encode_message, message)

    def CompareEncoded(self, expected_encoded, actual_encoded):
        """Compare two encoded protocol values.

        Can be overridden by sub-classes to special case comparison.
        For example, to eliminate white space from output that is not
        relevant to encoding.

        Args:
          expected_encoded: Expected string encoded value.
          actual_encoded: Actual string encoded value.
        """
        self.assertEquals(expected_encoded, actual_encoded)

    def EncodeDecode(self, encoded, expected_message):
        message = self.PROTOLIB.decode_message(type(expected_message), encoded)
        self.assertEquals(expected_message, message)
        self.CompareEncoded(encoded, self.PROTOLIB.encode_message(message))

    def testEmptyMessage(self):
        self.EncodeDecode(self.encoded_empty_message, OptionalMessage())

    def testPartial(self):
        """Test message with a few values set."""
        message = OptionalMessage()
        message.double_value = 1.23
        message.int64_value = -100000000000
        message.int32_value = 1020
        message.string_value = u'a string'
        message.enum_value = OptionalMessage.SimpleEnum.VAL2

        self.EncodeDecode(self.encoded_partial, message)

    def testFull(self):
        """Test all types."""
        message = OptionalMessage()
        message.double_value = 1.23
        message.float_value = -2.5
        message.int64_value = -100000000000
        message.uint64_value = 102020202020
        message.int32_value = 1020
        message.bool_value = True
        message.string_value = u'a string\u044f'
        message.bytes_value = b'a bytes\xff\xfe'
        message.enum_value = OptionalMessage.SimpleEnum.VAL2

        self.EncodeDecode(self.encoded_full, message)

    def testRepeated(self):
        """Test repeated fields."""
        message = RepeatedMessage()
        message.double_value = [1.23, 2.3]
        message.float_value = [-2.5, 0.5]
        message.int64_value = [-100000000000, 20]
        message.uint64_value = [102020202020, 10]
        message.int32_value = [1020, 718]
        message.bool_value = [True, False]
        message.string_value = [u'a string\u044f', u'another string']
        message.bytes_value = [b'a bytes\xff\xfe', b'another bytes']
        message.enum_value = [RepeatedMessage.SimpleEnum.VAL2,
                              RepeatedMessage.SimpleEnum.VAL1]

        self.EncodeDecode(self.encoded_repeated, message)

    def testNested(self):
        """Test nested messages."""
        nested_message = NestedMessage()
        nested_message.a_value = u'a string'

        message = HasNestedMessage()
        message.nested = nested_message

        self.EncodeDecode(self.encoded_nested, message)

    def testRepeatedNested(self):
        """Test repeated nested messages."""
        nested_message1 = NestedMessage()
        nested_message1.a_value = u'a string'
        nested_message2 = NestedMessage()
        nested_message2.a_value = u'another string'

        message = HasNestedMessage()
        message.repeated_nested = [nested_message1, nested_message2]

        self.EncodeDecode(self.encoded_repeated_nested, message)

    def testStringTypes(self):
        """Test that encoding str on StringField works."""
        message = OptionalMessage()
        message.string_value = 'Latin'
        self.EncodeDecode(self.encoded_string_types, message)

    def testEncodeUninitialized(self):
        """Test that cannot encode uninitialized message."""
        required = NestedMessage()
        self.assertRaisesWithRegexpMatch(messages.ValidationError,
                                         "Message NestedMessage is missing "
                                         "required field a_value",
                                         self.PROTOLIB.encode_message,
                                         required)

    def testUnexpectedField(self):
        """Test decoding and encoding unexpected fields."""
        loaded_message = self.PROTOLIB.decode_message(
            OptionalMessage, self.unexpected_tag_message)
        # Message should be equal to an empty message, since unknown
        # values aren't included in equality.
        self.assertEquals(OptionalMessage(), loaded_message)
        # Verify that the encoded message matches the source, including the
        # unknown value.
        self.assertEquals(self.unexpected_tag_message,
                          self.PROTOLIB.encode_message(loaded_message))

    def testDoNotSendDefault(self):
        """Test that default is not sent when nothing is assigned."""
        self.EncodeDecode(self.encoded_empty_message, HasDefault())

    def testSendDefaultExplicitlyAssigned(self):
        """Test that default is sent when explcitly assigned."""
        message = HasDefault()

        message.a_value = HasDefault.a_value.default

        self.EncodeDecode(self.encoded_default_assigned, message)

    def testEncodingNestedEmptyMessage(self):
        """Test encoding a nested empty message."""
        message = HasOptionalNestedMessage()
        message.nested = OptionalMessage()

        self.EncodeDecode(self.encoded_nested_empty, message)

    def testEncodingRepeatedNestedEmptyMessage(self):
        """Test encoding a nested empty message."""
        message = HasOptionalNestedMessage()
        message.repeated_nested = [OptionalMessage(), OptionalMessage()]

        self.EncodeDecode(self.encoded_repeated_nested_empty, message)

    def testContentType(self):
        self.assertTrue(isinstance(self.PROTOLIB.CONTENT_TYPE, str))

    def testDecodeInvalidEnumType(self):
        # Since protos need to be able to add new enums, a message should be
        # successfully decoded even if the enum value is invalid. Encoding the
        # decoded message should result in equivalence with the original
        # encoded message containing an invalid enum.
        decoded = self.PROTOLIB.decode_message(OptionalMessage,
                                               self.encoded_invalid_enum)
        message = OptionalMessage()
        self.assertEqual(message, decoded)
        encoded = self.PROTOLIB.encode_message(decoded)
        self.assertEqual(self.encoded_invalid_enum, encoded)

    def testDateTimeNoTimeZone(self):
        """Test that DateTimeFields are encoded/decoded correctly."""

        class MyMessage(messages.Message):
            value = message_types.DateTimeField(1)

        value = datetime.datetime(2013, 1, 3, 11, 36, 30, 123000)
        message = MyMessage(value=value)
        decoded = self.PROTOLIB.decode_message(
            MyMessage, self.PROTOLIB.encode_message(message))
        self.assertEquals(decoded.value, value)

    def testDateTimeWithTimeZone(self):
        """Test DateTimeFields with time zones."""

        class MyMessage(messages.Message):
            value = message_types.DateTimeField(1)

        value = datetime.datetime(2013, 1, 3, 11, 36, 30, 123000,
                                  util.TimeZoneOffset(8 * 60))
        message = MyMessage(value=value)
        decoded = self.PROTOLIB.decode_message(
            MyMessage, self.PROTOLIB.encode_message(message))
        self.assertEquals(decoded.value, value)


def pick_unused_port():
    """Find an unused port to use in tests.

      Derived from Damon Kohlers example:

        http://code.activestate.com/recipes/531822-pick-unused-port
    """
    temp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        temp.bind(('localhost', 0))
        port = temp.getsockname()[1]
    finally:
        temp.close()
    return port


def get_module_name(module_attribute):
    """Get the module name.

    Args:
      module_attribute: An attribute of the module.

    Returns:
      The fully qualified module name or simple module name where
      'module_attribute' is defined if the module name is "__main__".
    """
    if module_attribute.__module__ == '__main__':
        module_file = inspect.getfile(module_attribute)
        default = os.path.basename(module_file).split('.')[0]
        return default
    return module_attribute.__module__
