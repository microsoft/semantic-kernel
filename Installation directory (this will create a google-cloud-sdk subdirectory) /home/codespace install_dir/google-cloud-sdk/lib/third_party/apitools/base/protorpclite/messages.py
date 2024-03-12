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

# pylint: disable=too-many-lines

"""Stand-alone implementation of in memory protocol messages.

Public Classes:
  Enum: Represents an enumerated type.
  Variant: Hint for wire format to determine how to serialize.
  Message: Base class for user defined messages.
  IntegerField: Field for integer values.
  FloatField: Field for float values.
  BooleanField: Field for boolean values.
  BytesField: Field for binary string values.
  StringField: Field for UTF-8 string values.
  MessageField: Field for other message type values.
  EnumField: Field for enumerated type values.

Public Exceptions (indentation indications class hierarchy):
  EnumDefinitionError: Raised when enumeration is incorrectly defined.
  FieldDefinitionError: Raised when field is incorrectly defined.
    InvalidVariantError: Raised when variant is not compatible with field type.
    InvalidDefaultError: Raised when default is not compatiable with field.
    InvalidNumberError: Raised when field number is out of range or reserved.
  MessageDefinitionError: Raised when message is incorrectly defined.
    DuplicateNumberError: Raised when field has duplicate number with another.
  ValidationError: Raised when a message or field is not valid.
  DefinitionNotFoundError: Raised when definition not found.
"""
import types
import weakref

import six

from apitools.base.protorpclite import util

__all__ = [
    'MAX_ENUM_VALUE',
    'MAX_FIELD_NUMBER',
    'FIRST_RESERVED_FIELD_NUMBER',
    'LAST_RESERVED_FIELD_NUMBER',

    'Enum',
    'Field',
    'FieldList',
    'Variant',
    'Message',
    'IntegerField',
    'FloatField',
    'BooleanField',
    'BytesField',
    'StringField',
    'MessageField',
    'EnumField',
    'find_definition',

    'Error',
    'DecodeError',
    'EncodeError',
    'EnumDefinitionError',
    'FieldDefinitionError',
    'InvalidVariantError',
    'InvalidDefaultError',
    'InvalidNumberError',
    'MessageDefinitionError',
    'DuplicateNumberError',
    'ValidationError',
    'DefinitionNotFoundError',
]

# pylint:disable=attribute-defined-outside-init
# pylint:disable=protected-access


# TODO(user): Add extended module test to ensure all exceptions
# in services extends Error.
Error = util.Error


class EnumDefinitionError(Error):
    """Enumeration definition error."""


class FieldDefinitionError(Error):
    """Field definition error."""


class InvalidVariantError(FieldDefinitionError):
    """Invalid variant provided to field."""


class InvalidDefaultError(FieldDefinitionError):
    """Invalid default provided to field."""


class InvalidNumberError(FieldDefinitionError):
    """Invalid number provided to field."""


class MessageDefinitionError(Error):
    """Message definition error."""


class DuplicateNumberError(Error):
    """Duplicate number assigned to field."""


class DefinitionNotFoundError(Error):
    """Raised when definition is not found."""


class DecodeError(Error):
    """Error found decoding message from encoded form."""


class EncodeError(Error):
    """Error found when encoding message."""


class ValidationError(Error):
    """Invalid value for message error."""

    def __str__(self):
        """Prints string with field name if present on exception."""
        return Error.__str__(self)


# Attributes that are reserved by a class definition that
# may not be used by either Enum or Message class definitions.
_RESERVED_ATTRIBUTE_NAMES = frozenset(
    ['__module__', '__doc__', '__qualname__'])

_POST_INIT_FIELD_ATTRIBUTE_NAMES = frozenset(
    ['name',
     '_message_definition',
     '_MessageField__type',
     '_EnumField__type',
     '_EnumField__resolved_default'])

_POST_INIT_ATTRIBUTE_NAMES = frozenset(
    ['_message_definition'])

# Maximum enumeration value as defined by the protocol buffers standard.
# All enum values must be less than or equal to this value.
MAX_ENUM_VALUE = (2 ** 29) - 1

# Maximum field number as defined by the protocol buffers standard.
# All field numbers must be less than or equal to this value.
MAX_FIELD_NUMBER = (2 ** 29) - 1

# Field numbers between 19000 and 19999 inclusive are reserved by the
# protobuf protocol and may not be used by fields.
FIRST_RESERVED_FIELD_NUMBER = 19000
LAST_RESERVED_FIELD_NUMBER = 19999


# pylint: disable=no-value-for-parameter
class _DefinitionClass(type):
    """Base meta-class used for definition meta-classes.

    The Enum and Message definition classes share some basic functionality.
    Both of these classes may be contained by a Message definition.  After
    initialization, neither class may have attributes changed
    except for the protected _message_definition attribute, and that attribute
    may change only once.
    """

    __initialized = False  # pylint:disable=invalid-name

    def __init__(cls, name, bases, dct):
        """Constructor."""
        type.__init__(cls, name, bases, dct)
        # Base classes may never be initialized.
        if cls.__bases__ != (object,):
            cls.__initialized = True

    def message_definition(cls):
        """Get outer Message definition that contains this definition.

        Returns:
          Containing Message definition if definition is contained within one,
          else None.
        """
        try:
            return cls._message_definition()
        except AttributeError:
            return None

    def __setattr__(cls, name, value):
        """Overridden to avoid setting variables after init.

        Setting attributes on a class must work during the period of
        initialization to set the enumation value class variables and
        build the name/number maps. Once __init__ has set the
        __initialized flag to True prohibits setting any more values
        on the class. The class is in effect frozen.

        Args:
          name: Name of value to set.
          value: Value to set.

        """
        if cls.__initialized and name not in _POST_INIT_ATTRIBUTE_NAMES:
            raise AttributeError('May not change values: %s' % name)
        else:
            type.__setattr__(cls, name, value)

    def __delattr__(cls, name):
        """Overridden so that cannot delete varaibles on definition classes."""
        raise TypeError('May not delete attributes on definition class')

    def definition_name(cls):
        """Helper method for creating definition name.

        Names will be generated to include the classes package name,
        scope (if the class is nested in another definition) and class
        name.

        By default, the package name for a definition is derived from
        its module name. However, this value can be overriden by
        placing a 'package' attribute in the module that contains the
        definition class. For example:

          package = 'some.alternate.package'

          class MyMessage(Message):
            ...

          >>> MyMessage.definition_name()
          some.alternate.package.MyMessage

        Returns:
          Dot-separated fully qualified name of definition.

        """
        outer_definition_name = cls.outer_definition_name()
        if outer_definition_name is None:
            return six.text_type(cls.__name__)
        return u'%s.%s' % (outer_definition_name, cls.__name__)

    def outer_definition_name(cls):
        """Helper method for creating outer definition name.

        Returns:
          If definition is nested, will return the outer definitions
          name, else the package name.

        """
        outer_definition = cls.message_definition()
        if not outer_definition:
            return util.get_package_for_module(cls.__module__)
        return outer_definition.definition_name()

    def definition_package(cls):
        """Helper method for creating creating the package of a definition.

        Returns:
          Name of package that definition belongs to.
        """
        outer_definition = cls.message_definition()
        if not outer_definition:
            return util.get_package_for_module(cls.__module__)
        return outer_definition.definition_package()


class _EnumClass(_DefinitionClass):
    """Meta-class used for defining the Enum base class.

    Meta-class enables very specific behavior for any defined Enum
    class.  All attributes defined on an Enum sub-class must be integers.
    Each attribute defined on an Enum sub-class is translated
    into an instance of that sub-class, with the name of the attribute
    as its name, and the number provided as its value.  It also ensures
    that only one level of Enum class hierarchy is possible.  In other
    words it is not possible to delcare sub-classes of sub-classes of
    Enum.

    This class also defines some functions in order to restrict the
    behavior of the Enum class and its sub-classes.  It is not possible
    to change the behavior of the Enum class in later classes since
    any new classes may be defined with only integer values, and no methods.
    """

    def __init__(cls, name, bases, dct):
        # Can only define one level of sub-classes below Enum.
        if not (bases == (object,) or bases == (Enum,)):
            raise EnumDefinitionError(
                'Enum type %s may only inherit from Enum' % name)

        cls.__by_number = {}
        cls.__by_name = {}

        # Enum base class does not need to be initialized or locked.
        if bases != (object,):
            # Replace integer with number.
            for attribute, value in dct.items():

                # Module will be in every enum class.
                if attribute in _RESERVED_ATTRIBUTE_NAMES:
                    continue

                # Reject anything that is not an int.
                if not isinstance(value, six.integer_types):
                    raise EnumDefinitionError(
                        'May only use integers in Enum definitions.  '
                        'Found: %s = %s' %
                        (attribute, value))

                # Protocol buffer standard recommends non-negative values.
                # Reject negative values.
                if value < 0:
                    raise EnumDefinitionError(
                        'Must use non-negative enum values.  Found: %s = %d' %
                        (attribute, value))

                if value > MAX_ENUM_VALUE:
                    raise EnumDefinitionError(
                        'Must use enum values less than or equal %d.  '
                        'Found: %s = %d' %
                        (MAX_ENUM_VALUE, attribute, value))

                if value in cls.__by_number:
                    raise EnumDefinitionError(
                        'Value for %s = %d is already defined: %s' %
                        (attribute, value, cls.__by_number[value].name))

                # Create enum instance and list in new Enum type.
                instance = object.__new__(cls)
                # pylint:disable=non-parent-init-called
                cls.__init__(instance, attribute, value)
                cls.__by_name[instance.name] = instance
                cls.__by_number[instance.number] = instance
                setattr(cls, attribute, instance)

        _DefinitionClass.__init__(cls, name, bases, dct)

    def __iter__(cls):
        """Iterate over all values of enum.

        Yields:
          Enumeration instances of the Enum class in arbitrary order.
        """
        return iter(cls.__by_number.values())

    def names(cls):
        """Get all names for Enum.

        Returns:
          An iterator for names of the enumeration in arbitrary order.
        """
        return cls.__by_name.keys()

    def numbers(cls):
        """Get all numbers for Enum.

        Returns:
          An iterator for all numbers of the enumeration in arbitrary order.
        """
        return cls.__by_number.keys()

    def lookup_by_name(cls, name):
        """Look up Enum by name.

        Args:
          name: Name of enum to find.

        Returns:
          Enum sub-class instance of that value.
        """
        return cls.__by_name[name]

    def lookup_by_number(cls, number):
        """Look up Enum by number.

        Args:
          number: Number of enum to find.

        Returns:
          Enum sub-class instance of that value.
        """
        return cls.__by_number[number]

    def __len__(cls):
        return len(cls.__by_name)


class Enum(six.with_metaclass(_EnumClass, object)):
    """Base class for all enumerated types."""

    __slots__ = set(('name', 'number'))

    def __new__(cls, index):
        """Acts as look-up routine after class is initialized.

        The purpose of overriding __new__ is to provide a way to treat
        Enum subclasses as casting types, similar to how the int type
        functions.  A program can pass a string or an integer and this
        method with "convert" that value in to an appropriate Enum instance.

        Args:
          index: Name or number to look up.  During initialization
            this is always the name of the new enum value.

        Raises:
          TypeError: When an inappropriate index value is passed provided.
        """
        # If is enum type of this class, return it.
        if isinstance(index, cls):
            return index

        # If number, look up by number.
        if isinstance(index, six.integer_types):
            try:
                return cls.lookup_by_number(index)
            except KeyError:
                pass

        # If name, look up by name.
        if isinstance(index, six.string_types):
            try:
                return cls.lookup_by_name(index)
            except KeyError:
                pass

        raise TypeError('No such value for %s in Enum %s' %
                        (index, cls.__name__))

    def __init__(self, name, number=None):
        """Initialize new Enum instance.

        Since this should only be called during class initialization any
        calls that happen after the class is frozen raises an exception.
        """
        # Immediately return if __init__ was called after _Enum.__init__().
        # It means that casting operator version of the class constructor
        # is being used.
        if getattr(type(self), '_DefinitionClass__initialized'):
            return
        object.__setattr__(self, 'name', name)
        object.__setattr__(self, 'number', number)

    def __setattr__(self, name, value):
        raise TypeError('May not change enum values')

    def __str__(self):
        return self.name

    def __int__(self):
        return self.number

    def __repr__(self):
        return '%s(%s, %d)' % (type(self).__name__, self.name, self.number)

    def __reduce__(self):
        """Enable pickling.

        Returns:
          A 2-tuple containing the class and __new__ args to be used
          for restoring a pickled instance.

        """
        return self.__class__, (self.number,)

    def __cmp__(self, other):
        """Order is by number."""
        if isinstance(other, type(self)):
            return cmp(self.number, other.number)
        return NotImplemented

    def __lt__(self, other):
        """Order is by number."""
        if isinstance(other, type(self)):
            return self.number < other.number
        return NotImplemented

    def __le__(self, other):
        """Order is by number."""
        if isinstance(other, type(self)):
            return self.number <= other.number
        return NotImplemented

    def __eq__(self, other):
        """Order is by number."""
        if isinstance(other, type(self)):
            return self.number == other.number
        return NotImplemented

    def __ne__(self, other):
        """Order is by number."""
        if isinstance(other, type(self)):
            return self.number != other.number
        return NotImplemented

    def __ge__(self, other):
        """Order is by number."""
        if isinstance(other, type(self)):
            return self.number >= other.number
        return NotImplemented

    def __gt__(self, other):
        """Order is by number."""
        if isinstance(other, type(self)):
            return self.number > other.number
        return NotImplemented

    def __hash__(self):
        """Hash by number."""
        return hash(self.number)

    @classmethod
    def to_dict(cls):
        """Make dictionary version of enumerated class.

        Dictionary created this way can be used with def_num.

        Returns:
          A dict (name) -> number
        """
        return dict((item.name, item.number) for item in iter(cls))

    @staticmethod
    def def_enum(dct, name):
        """Define enum class from dictionary.

        Args:
          dct: Dictionary of enumerated values for type.
          name: Name of enum.
        """
        return type(name, (Enum,), dct)


# TODO(user): Determine to what degree this enumeration should be compatible
# with FieldDescriptor.Type in https://github.com/google/protobuf.
class Variant(Enum):
    """Wire format variant.

    Used by the 'protobuf' wire format to determine how to transmit
    a single piece of data.  May be used by other formats.

    See: http://code.google.com/apis/protocolbuffers/docs/encoding.html

    Values:
      DOUBLE: 64-bit floating point number.
      FLOAT: 32-bit floating point number.
      INT64: 64-bit signed integer.
      UINT64: 64-bit unsigned integer.
      INT32: 32-bit signed integer.
      BOOL: Boolean value (True or False).
      STRING: String of UTF-8 encoded text.
      MESSAGE: Embedded message as byte string.
      BYTES: String of 8-bit bytes.
      UINT32: 32-bit unsigned integer.
      ENUM: Enum value as integer.
      SINT32: 32-bit signed integer.  Uses "zig-zag" encoding.
      SINT64: 64-bit signed integer.  Uses "zig-zag" encoding.
    """
    DOUBLE = 1
    FLOAT = 2
    INT64 = 3
    UINT64 = 4
    INT32 = 5
    BOOL = 8
    STRING = 9
    MESSAGE = 11
    BYTES = 12
    UINT32 = 13
    ENUM = 14
    SINT32 = 17
    SINT64 = 18


class _MessageClass(_DefinitionClass):
    """Meta-class used for defining the Message base class.

    For more details about Message classes, see the Message class docstring.
    Information contained there may help understanding this class.

    Meta-class enables very specific behavior for any defined Message
    class. All attributes defined on an Message sub-class must be
    field instances, Enum class definitions or other Message class
    definitions. Each field attribute defined on an Message sub-class
    is added to the set of field definitions and the attribute is
    translated in to a slot. It also ensures that only one level of
    Message class hierarchy is possible. In other words it is not
    possible to declare sub-classes of sub-classes of Message.

    This class also defines some functions in order to restrict the
    behavior of the Message class and its sub-classes. It is not
    possible to change the behavior of the Message class in later
    classes since any new classes may be defined with only field,
    Enums and Messages, and no methods.

    """

    # pylint:disable=bad-mcs-classmethod-argument
    def __new__(cls, name, bases, dct):
        """Create new Message class instance.

        The __new__ method of the _MessageClass type is overridden so as to
        allow the translation of Field instances to slots.
        """
        by_number = {}
        by_name = {}

        variant_map = {}  # pylint:disable=unused-variable

        if bases != (object,):
            # Can only define one level of sub-classes below Message.
            if bases != (Message,):
                raise MessageDefinitionError(
                    'Message types may only inherit from Message')

            enums = []
            messages = []
            # Must not use iteritems because this loop will change the state of
            # dct.
            for key, field in dct.items():

                if key in _RESERVED_ATTRIBUTE_NAMES:
                    continue

                if isinstance(field, type) and issubclass(field, Enum):
                    enums.append(key)
                    continue

                if (isinstance(field, type) and
                        issubclass(field, Message) and
                        field is not Message):
                    messages.append(key)
                    continue

                # Reject anything that is not a field.
                # pylint:disable=unidiomatic-typecheck
                if type(field) is Field or not isinstance(field, Field):
                    raise MessageDefinitionError(
                        'May only use fields in message definitions.  '
                        'Found: %s = %s' %
                        (key, field))

                if field.number in by_number:
                    raise DuplicateNumberError(
                        'Field with number %d declared more than once in %s' %
                        (field.number, name))

                field.name = key

                # Place in name and number maps.
                by_name[key] = field
                by_number[field.number] = field

            # Add enums if any exist.
            if enums:
                dct['__enums__'] = sorted(enums)

            # Add messages if any exist.
            if messages:
                dct['__messages__'] = sorted(messages)

        dct['_Message__by_number'] = by_number
        dct['_Message__by_name'] = by_name

        return _DefinitionClass.__new__(cls, name, bases, dct)

    def __init__(cls, name, bases, dct):
        """Initializer required to assign references to new class."""
        if bases != (object,):
            for v in dct.values():
                if isinstance(v, _DefinitionClass) and v is not Message:
                    v._message_definition = weakref.ref(cls)

            for field in cls.all_fields():
                field._message_definition = weakref.ref(cls)

        _DefinitionClass.__init__(cls, name, bases, dct)


class Message(six.with_metaclass(_MessageClass, object)):
    """Base class for user defined message objects.

    Used to define messages for efficient transmission across network or
    process space.  Messages are defined using the field classes (IntegerField,
    FloatField, EnumField, etc.).

    Messages are more restricted than normal classes in that they may
    only contain field attributes and other Message and Enum
    definitions. These restrictions are in place because the structure
    of the Message class is intentended to itself be transmitted
    across network or process space and used directly by clients or
    even other servers. As such methods and non-field attributes could
    not be transmitted with the structural information causing
    discrepancies between different languages and implementations.

    Initialization and validation:

      A Message object is considered to be initialized if it has all required
      fields and any nested messages are also initialized.

      Calling 'check_initialized' will raise a ValidationException if it is not
      initialized; 'is_initialized' returns a boolean value indicating if it is
      valid.

      Validation automatically occurs when Message objects are created
      and populated.  Validation that a given value will be compatible with
      a field that it is assigned to can be done through the Field instances
      validate() method.  The validate method used on a message will check that
      all values of a message and its sub-messages are valid.  Assingning an
      invalid value to a field will raise a ValidationException.

    Example:

      # Trade type.
      class TradeType(Enum):
        BUY = 1
        SELL = 2
        SHORT = 3
        CALL = 4

      class Lot(Message):
        price = IntegerField(1, required=True)
        quantity = IntegerField(2, required=True)

      class Order(Message):
        symbol = StringField(1, required=True)
        total_quantity = IntegerField(2, required=True)
        trade_type = EnumField(TradeType, 3, required=True)
        lots = MessageField(Lot, 4, repeated=True)
        limit = IntegerField(5)

      order = Order(symbol='GOOG',
                    total_quantity=10,
                    trade_type=TradeType.BUY)

      lot1 = Lot(price=304,
                 quantity=7)

      lot2 = Lot(price = 305,
                 quantity=3)

      order.lots = [lot1, lot2]

      # Now object is initialized!
      order.check_initialized()

    """

    def __init__(self, **kwargs):
        """Initialize internal messages state.

        Args:
          A message can be initialized via the constructor by passing
          in keyword arguments corresponding to fields. For example:

            class Date(Message):
              day = IntegerField(1)
              month = IntegerField(2)
              year = IntegerField(3)

          Invoking:

            date = Date(day=6, month=6, year=1911)

          is the same as doing:

            date = Date()
            date.day = 6
            date.month = 6
            date.year = 1911

        """
        # Tag being an essential implementation detail must be private.
        self.__tags = {}
        self.__unrecognized_fields = {}

        assigned = set()
        for name, value in kwargs.items():
            setattr(self, name, value)
            assigned.add(name)

        # initialize repeated fields.
        for field in self.all_fields():
            if field.repeated and field.name not in assigned:
                setattr(self, field.name, [])

    def check_initialized(self):
        """Check class for initialization status.

        Check that all required fields are initialized

        Raises:
          ValidationError: If message is not initialized.
        """
        for name, field in self.__by_name.items():
            value = getattr(self, name)
            if value is None:
                if field.required:
                    raise ValidationError(
                        "Message %s is missing required field %s" %
                        (type(self).__name__, name))
            else:
                try:
                    if (isinstance(field, MessageField) and
                            issubclass(field.message_type, Message)):
                        if field.repeated:
                            for item in value:
                                item_message_value = field.value_to_message(
                                    item)
                                item_message_value.check_initialized()
                        else:
                            message_value = field.value_to_message(value)
                            message_value.check_initialized()
                except ValidationError as err:
                    if not hasattr(err, 'message_name'):
                        err.message_name = type(self).__name__
                    raise

    def is_initialized(self):
        """Get initialization status.

        Returns:
          True if message is valid, else False.
        """
        try:
            self.check_initialized()
        except ValidationError:
            return False
        else:
            return True

    @classmethod
    def all_fields(cls):
        """Get all field definition objects.

        Ordering is arbitrary.

        Returns:
          Iterator over all values in arbitrary order.
        """
        return cls.__by_name.values()

    @classmethod
    def field_by_name(cls, name):
        """Get field by name.

        Returns:
          Field object associated with name.

        Raises:
          KeyError if no field found by that name.
        """
        return cls.__by_name[name]

    @classmethod
    def field_by_number(cls, number):
        """Get field by number.

        Returns:
          Field object associated with number.

        Raises:
          KeyError if no field found by that number.
        """
        return cls.__by_number[number]

    def get_assigned_value(self, name):
        """Get the assigned value of an attribute.

        Get the underlying value of an attribute. If value has not
        been set, will not return the default for the field.

        Args:
          name: Name of attribute to get.

        Returns:
          Value of attribute, None if it has not been set.

        """
        message_type = type(self)
        try:
            field = message_type.field_by_name(name)
        except KeyError:
            raise AttributeError('Message %s has no field %s' % (
                message_type.__name__, name))
        return self.__tags.get(field.number)

    def reset(self, name):
        """Reset assigned value for field.

        Resetting a field will return it to its default value or None.

        Args:
          name: Name of field to reset.
        """
        message_type = type(self)
        try:
            field = message_type.field_by_name(name)
        except KeyError:
            if name not in message_type.__by_name:
                raise AttributeError('Message %s has no field %s' % (
                    message_type.__name__, name))
        if field.repeated:
            self.__tags[field.number] = FieldList(field, [])
        else:
            self.__tags.pop(field.number, None)

    def all_unrecognized_fields(self):
        """Get the names of all unrecognized fields in this message."""
        return list(self.__unrecognized_fields.keys())

    def get_unrecognized_field_info(self, key, value_default=None,
                                    variant_default=None):
        """Get the value and variant of an unknown field in this message.

        Args:
          key: The name or number of the field to retrieve.
          value_default: Value to be returned if the key isn't found.
          variant_default: Value to be returned as variant if the key isn't
            found.

        Returns:
          (value, variant), where value and variant are whatever was passed
          to set_unrecognized_field.
        """
        value, variant = self.__unrecognized_fields.get(key, (value_default,
                                                              variant_default))
        return value, variant

    def set_unrecognized_field(self, key, value, variant):
        """Set an unrecognized field, used when decoding a message.

        Args:
          key: The name or number used to refer to this unknown value.
          value: The value of the field.
          variant: Type information needed to interpret the value or re-encode
            it.

        Raises:
          TypeError: If the variant is not an instance of messages.Variant.
        """
        if not isinstance(variant, Variant):
            raise TypeError('Variant type %s is not valid.' % variant)
        self.__unrecognized_fields[key] = value, variant

    def __setattr__(self, name, value):
        """Change set behavior for messages.

        Messages may only be assigned values that are fields.

        Does not try to validate field when set.

        Args:
          name: Name of field to assign to.
          value: Value to assign to field.

        Raises:
          AttributeError when trying to assign value that is not a field.
        """
        if name in self.__by_name or name.startswith('_Message__'):
            object.__setattr__(self, name, value)
        else:
            raise AttributeError("May not assign arbitrary value %s "
                                 "to message %s" % (name, type(self).__name__))

    def __repr__(self):
        """Make string representation of message.

        Example:

          class MyMessage(messages.Message):
            integer_value = messages.IntegerField(1)
            string_value = messages.StringField(2)

          my_message = MyMessage()
          my_message.integer_value = 42
          my_message.string_value = u'A string'

          print my_message
          >>> <MyMessage
          ...  integer_value: 42
          ...  string_value: u'A string'>

        Returns:
          String representation of message, including the values
          of all fields and repr of all sub-messages.
        """
        body = ['<', type(self).__name__]
        for field in sorted(self.all_fields(),
                            key=lambda f: f.number):
            attribute = field.name
            value = self.get_assigned_value(field.name)
            if value is not None:
                body.append('\n %s: %s' % (attribute, repr(value)))
        body.append('>')
        return ''.join(body)

    def __eq__(self, other):
        """Equality operator.

        Does field by field comparison with other message.  For
        equality, must be same type and values of all fields must be
        equal.

        Messages not required to be initialized for comparison.

        Does not attempt to determine equality for values that have
        default values that are not set.  In other words:

          class HasDefault(Message):

            attr1 = StringField(1, default='default value')

          message1 = HasDefault()
          message2 = HasDefault()
          message2.attr1 = 'default value'

          message1 != message2

        Does not compare unknown values.

        Args:
          other: Other message to compare with.
        """
        # TODO(user): Implement "equivalent" which does comparisons
        # taking default values in to consideration.
        if self is other:
            return True

        if type(self) is not type(other):
            return False

        return self.__tags == other.__tags

    def __ne__(self, other):
        """Not equals operator.

        Does field by field comparison with other message.  For
        non-equality, must be different type or any value of a field must be
        non-equal to the same field in the other instance.

        Messages not required to be initialized for comparison.

        Args:
          other: Other message to compare with.
        """
        return not self.__eq__(other)


class FieldList(list):
    """List implementation that validates field values.

    This list implementation overrides all methods that add values in
    to a list in order to validate those new elements. Attempting to
    add or set list values that are not of the correct type will raise
    ValidationError.

    """

    def __init__(self, field_instance, sequence):
        """Constructor.

        Args:
          field_instance: Instance of field that validates the list.
          sequence: List or tuple to construct list from.
        """
        if not field_instance.repeated:
            raise FieldDefinitionError(
                'FieldList may only accept repeated fields')
        self.__field = field_instance
        self.__field.validate(sequence)
        list.__init__(self, sequence)

    def __getstate__(self):
        """Enable pickling.

        The assigned field instance can't be pickled if it belongs to
        a Message definition (message_definition uses a weakref), so
        the Message class and field number are returned in that case.

        Returns:
          A 3-tuple containing:
            - The field instance, or None if it belongs to a Message class.
            - The Message class that the field instance belongs to, or None.
            - The field instance number of the Message class it belongs to, or
                None.

        """
        message_class = self.__field.message_definition()
        if message_class is None:
            return self.__field, None, None
        return None, message_class, self.__field.number

    def __setstate__(self, state):
        """Enable unpickling.

        Args:
          state: A 3-tuple containing:
            - The field instance, or None if it belongs to a Message class.
            - The Message class that the field instance belongs to, or None.
            - The field instance number of the Message class it belongs to, or
                None.
        """
        field_instance, message_class, number = state
        if field_instance is None:
            self.__field = message_class.field_by_number(number)
        else:
            self.__field = field_instance

    @property
    def field(self):
        """Field that validates list."""
        return self.__field

    def __setslice__(self, i, j, sequence):
        """Validate slice assignment to list."""
        self.__field.validate(sequence)
        list.__setslice__(self, i, j, sequence)

    def __setitem__(self, index, value):
        """Validate item assignment to list."""
        if isinstance(index, slice):
            self.__field.validate(value)
        else:
            self.__field.validate_element(value)
        list.__setitem__(self, index, value)

    def append(self, value):
        """Validate item appending to list."""
        if getattr(self, '_FieldList__field', None):
            self.__field.validate_element(value)
        return list.append(self, value)

    def extend(self, sequence):
        """Validate extension of list."""
        if getattr(self, '_FieldList__field', None):
            self.__field.validate(sequence)
        return list.extend(self, sequence)

    def insert(self, index, value):
        """Validate item insertion to list."""
        self.__field.validate_element(value)
        return list.insert(self, index, value)


class _FieldMeta(type):

    def __init__(cls, name, bases, dct):
        getattr(cls, '_Field__variant_to_type').update(
            (variant, cls) for variant in dct.get('VARIANTS', []))
        type.__init__(cls, name, bases, dct)


# TODO(user): Prevent additional field subclasses.
class Field(six.with_metaclass(_FieldMeta, object)):
    """Definition for message field."""

    __initialized = False  # pylint:disable=invalid-name
    __variant_to_type = {}  # pylint:disable=invalid-name

    @util.positional(2)
    def __init__(self,
                 number,
                 required=False,
                 repeated=False,
                 variant=None,
                 default=None):
        """Constructor.

        The required and repeated parameters are mutually exclusive.
        Setting both to True will raise a FieldDefinitionError.

        Sub-class Attributes:
          Each sub-class of Field must define the following:
            VARIANTS: Set of variant types accepted by that field.
            DEFAULT_VARIANT: Default variant type if not specified in
              constructor.

        Args:
          number: Number of field.  Must be unique per message class.
          required: Whether or not field is required.  Mutually exclusive with
            'repeated'.
          repeated: Whether or not field is repeated.  Mutually exclusive with
            'required'.
          variant: Wire-format variant hint.
          default: Default value for field if not found in stream.

        Raises:
          InvalidVariantError when invalid variant for field is provided.
          InvalidDefaultError when invalid default for field is provided.
          FieldDefinitionError when invalid number provided or mutually
            exclusive fields are used.
          InvalidNumberError when the field number is out of range or reserved.

        """
        if not isinstance(number, int) or not 1 <= number <= MAX_FIELD_NUMBER:
            raise InvalidNumberError(
                'Invalid number for field: %s\n'
                'Number must be 1 or greater and %d or less' %
                (number, MAX_FIELD_NUMBER))

        if FIRST_RESERVED_FIELD_NUMBER <= number <= LAST_RESERVED_FIELD_NUMBER:
            raise InvalidNumberError('Tag number %d is a reserved number.\n'
                                     'Numbers %d to %d are reserved' %
                                     (number, FIRST_RESERVED_FIELD_NUMBER,
                                      LAST_RESERVED_FIELD_NUMBER))

        if repeated and required:
            raise FieldDefinitionError('Cannot set both repeated and required')

        if variant is None:
            variant = self.DEFAULT_VARIANT

        if repeated and default is not None:
            raise FieldDefinitionError('Repeated fields may not have defaults')

        if variant not in self.VARIANTS:
            raise InvalidVariantError(
                'Invalid variant: %s\nValid variants for %s are %r' %
                (variant, type(self).__name__, sorted(self.VARIANTS)))

        self.number = number
        self.required = required
        self.repeated = repeated
        self.variant = variant

        if default is not None:
            try:
                self.validate_default(default)
            except ValidationError as err:
                try:
                    name = self.name
                except AttributeError:
                    # For when raising error before name initialization.
                    raise InvalidDefaultError(
                        'Invalid default value for %s: %r: %s' %
                        (self.__class__.__name__, default, err))
                else:
                    raise InvalidDefaultError(
                        'Invalid default value for field %s: '
                        '%r: %s' % (name, default, err))

        self.__default = default
        self.__initialized = True

    def __setattr__(self, name, value):
        """Setter overidden to prevent assignment to fields after creation.

        Args:
          name: Name of attribute to set.
          value: Value to assign.
        """
        # Special case post-init names.  They need to be set after constructor.
        if name in _POST_INIT_FIELD_ATTRIBUTE_NAMES:
            object.__setattr__(self, name, value)
            return

        # All other attributes must be set before __initialized.
        if not self.__initialized:
            # Not initialized yet, allow assignment.
            object.__setattr__(self, name, value)
        else:
            raise AttributeError('Field objects are read-only')

    def __set__(self, message_instance, value):
        """Set value on message.

        Args:
          message_instance: Message instance to set value on.
          value: Value to set on message.
        """
        # Reaches in to message instance directly to assign to private tags.
        if value is None:
            if self.repeated:
                raise ValidationError(
                    'May not assign None to repeated field %s' % self.name)
            else:
                message_instance._Message__tags.pop(self.number, None)
        else:
            if self.repeated:
                value = FieldList(self, value)
            else:
                value = self.validate(value)
            message_instance._Message__tags[self.number] = value

    def __get__(self, message_instance, message_class):
        if message_instance is None:
            return self

        result = message_instance._Message__tags.get(self.number)
        if result is None:
            return self.default
        return result

    def validate_element(self, value):
        """Validate single element of field.

        This is different from validate in that it is used on individual
        values of repeated fields.

        Args:
          value: Value to validate.

        Returns:
          The value casted in the expected type.

        Raises:
          ValidationError if value is not expected type.
        """
        if not isinstance(value, self.type):

            # Authorize int values as float.
            if isinstance(value, six.integer_types) and self.type == float:
                return float(value)

            if value is None:
                if self.required:
                    raise ValidationError('Required field is missing')
            else:
                try:
                    name = self.name
                except AttributeError:
                    raise ValidationError('Expected type %s for %s, '
                                          'found %s (type %s)' %
                                          (self.type, self.__class__.__name__,
                                           value, type(value)))
                else:
                    raise ValidationError(
                        'Expected type %s for field %s, found %s (type %s)' %
                        (self.type, name, value, type(value)))
        return value

    def __validate(self, value, validate_element):
        """Internal validation function.

        Validate an internal value using a function to validate
        individual elements.

        Args:
          value: Value to validate.
          validate_element: Function to use to validate individual elements.

        Raises:
          ValidationError if value is not expected type.

        """
        if not self.repeated:
            return validate_element(value)
        else:
            # Must be a list or tuple, may not be a string.
            if isinstance(value, (list, tuple)):
                result = []
                for element in value:
                    if element is None:
                        try:
                            name = self.name
                        except AttributeError:
                            raise ValidationError(
                                'Repeated values for %s '
                                'may not be None' % self.__class__.__name__)
                        else:
                            raise ValidationError(
                                'Repeated values for field %s '
                                'may not be None' % name)
                    result.append(validate_element(element))
                return result
            elif value is not None:
                try:
                    name = self.name
                except AttributeError:
                    raise ValidationError('%s is repeated. Found: %s' % (
                        self.__class__.__name__, value))
                else:
                    raise ValidationError(
                        'Field %s is repeated. Found: %s' % (name, value))
        return value

    def validate(self, value):
        """Validate value assigned to field.

        Args:
          value: Value to validate.

        Returns:
          the value in casted in the correct type.

        Raises:
          ValidationError if value is not expected type.
        """
        return self.__validate(value, self.validate_element)

    def validate_default_element(self, value):
        """Validate value as assigned to field default field.

        Some fields may allow for delayed resolution of default types
        necessary in the case of circular definition references. In
        this case, the default value might be a place holder that is
        resolved when needed after all the message classes are
        defined.

        Args:
          value: Default value to validate.

        Returns:
          the value in casted in the correct type.

        Raises:
          ValidationError if value is not expected type.

        """
        return self.validate_element(value)

    def validate_default(self, value):
        """Validate default value assigned to field.

        Args:
          value: Value to validate.

        Returns:
          the value in casted in the correct type.

        Raises:
          ValidationError if value is not expected type.
        """
        return self.__validate(value, self.validate_default_element)

    def message_definition(self):
        """Get Message definition that contains this Field definition.

        Returns:
          Containing Message definition for Field. Will return None if
          for some reason Field is defined outside of a Message class.

        """
        try:
            return self._message_definition()
        except AttributeError:
            return None

    @property
    def default(self):
        """Get default value for field."""
        return self.__default

    @classmethod
    def lookup_field_type_by_variant(cls, variant):
        return cls.__variant_to_type[variant]


class IntegerField(Field):
    """Field definition for integer values."""

    VARIANTS = frozenset([
        Variant.INT32,
        Variant.INT64,
        Variant.UINT32,
        Variant.UINT64,
        Variant.SINT32,
        Variant.SINT64,
    ])

    DEFAULT_VARIANT = Variant.INT64

    type = six.integer_types


class FloatField(Field):
    """Field definition for float values."""

    VARIANTS = frozenset([
        Variant.FLOAT,
        Variant.DOUBLE,
    ])

    DEFAULT_VARIANT = Variant.DOUBLE

    type = float


class BooleanField(Field):
    """Field definition for boolean values."""

    VARIANTS = frozenset([Variant.BOOL])

    DEFAULT_VARIANT = Variant.BOOL

    type = bool


class BytesField(Field):
    """Field definition for byte string values."""

    VARIANTS = frozenset([Variant.BYTES])

    DEFAULT_VARIANT = Variant.BYTES

    type = bytes


class StringField(Field):
    """Field definition for unicode string values."""

    VARIANTS = frozenset([Variant.STRING])

    DEFAULT_VARIANT = Variant.STRING

    type = six.text_type

    def validate_element(self, value):
        """Validate StringField allowing for str and unicode.

        Raises:
          ValidationError if a str value is not UTF-8.
        """
        # If value is str is it considered valid.  Satisfies "required=True".
        if isinstance(value, bytes):
            try:
                six.text_type(value, 'UTF-8')
            except UnicodeDecodeError as err:
                try:
                    _ = self.name
                except AttributeError:
                    validation_error = ValidationError(
                        'Field encountered non-UTF-8 string %r: %s' % (value,
                                                                       err))
                else:
                    validation_error = ValidationError(
                        'Field %s encountered non-UTF-8 string %r: %s' % (
                            self.name, value, err))
                    validation_error.field_name = self.name
                raise validation_error
        else:
            return super(StringField, self).validate_element(value)
        return value


class MessageField(Field):
    """Field definition for sub-message values.

    Message fields contain instance of other messages.  Instances stored
    on messages stored on message fields  are considered to be owned by
    the containing message instance and should not be shared between
    owning instances.

    Message fields must be defined to reference a single type of message.
    Normally message field are defined by passing the referenced message
    class in to the constructor.

    It is possible to define a message field for a type that does not
    yet exist by passing the name of the message in to the constructor
    instead of a message class. Resolution of the actual type of the
    message is deferred until it is needed, for example, during
    message verification. Names provided to the constructor must refer
    to a class within the same python module as the class that is
    using it. Names refer to messages relative to the containing
    messages scope. For example, the two fields of OuterMessage refer
    to the same message type:

      class Outer(Message):

        inner_relative = MessageField('Inner', 1)
        inner_absolute = MessageField('Outer.Inner', 2)

        class Inner(Message):
          ...

    When resolving an actual type, MessageField will traverse the
    entire scope of nested messages to match a message name. This
    makes it easy for siblings to reference siblings:

      class Outer(Message):

        class Inner(Message):

          sibling = MessageField('Sibling', 1)

        class Sibling(Message):
          ...

    """

    VARIANTS = frozenset([Variant.MESSAGE])

    DEFAULT_VARIANT = Variant.MESSAGE

    @util.positional(3)
    def __init__(self,
                 message_type,
                 number,
                 required=False,
                 repeated=False,
                 variant=None):
        """Constructor.

        Args:
          message_type: Message type for field.  Must be subclass of Message.
          number: Number of field.  Must be unique per message class.
          required: Whether or not field is required.  Mutually exclusive to
            'repeated'.
          repeated: Whether or not field is repeated.  Mutually exclusive to
            'required'.
          variant: Wire-format variant hint.

        Raises:
          FieldDefinitionError when invalid message_type is provided.
        """
        valid_type = (isinstance(message_type, six.string_types) or
                      (message_type is not Message and
                       isinstance(message_type, type) and
                       issubclass(message_type, Message)))

        if not valid_type:
            raise FieldDefinitionError(
                'Invalid message class: %s' % message_type)

        if isinstance(message_type, six.string_types):
            self.__type_name = message_type
            self.__type = None
        else:
            self.__type = message_type

        super(MessageField, self).__init__(number,
                                           required=required,
                                           repeated=repeated,
                                           variant=variant)

    def __set__(self, message_instance, value):
        """Set value on message.

        Args:
          message_instance: Message instance to set value on.
          value: Value to set on message.
        """
        t = self.type
        if isinstance(t, type) and issubclass(t, Message):
            if self.repeated:
                if value and isinstance(value, (list, tuple)):
                    value = [(t(**v) if isinstance(v, dict) else v)
                             for v in value]
            elif isinstance(value, dict):
                value = t(**value)
        super(MessageField, self).__set__(message_instance, value)

    @property
    def type(self):
        """Message type used for field."""
        if self.__type is None:
            message_type = find_definition(
                self.__type_name, self.message_definition())
            if not (message_type is not Message and
                    isinstance(message_type, type) and
                    issubclass(message_type, Message)):
                raise FieldDefinitionError(
                    'Invalid message class: %s' % message_type)
            self.__type = message_type
        return self.__type

    @property
    def message_type(self):
        """Underlying message type used for serialization.

        Will always be a sub-class of Message.  This is different from type
        which represents the python value that message_type is mapped to for
        use by the user.
        """
        return self.type

    def value_from_message(self, message):
        """Convert a message to a value instance.

        Used by deserializers to convert from underlying messages to
        value of expected user type.

        Args:
          message: A message instance of type self.message_type.

        Returns:
          Value of self.message_type.
        """
        if not isinstance(message, self.message_type):
            raise DecodeError('Expected type %s, got %s: %r' %
                              (self.message_type.__name__,
                               type(message).__name__,
                               message))
        return message

    def value_to_message(self, value):
        """Convert a value instance to a message.

        Used by serializers to convert Python user types to underlying
        messages for transmission.

        Args:
          value: A value of type self.type.

        Returns:
          An instance of type self.message_type.
        """
        if not isinstance(value, self.type):
            raise EncodeError('Expected type %s, got %s: %r' %
                              (self.type.__name__,
                               type(value).__name__,
                               value))
        return value


class EnumField(Field):
    """Field definition for enum values.

    Enum fields may have default values that are delayed until the
    associated enum type is resolved. This is necessary to support
    certain circular references.

    For example:

      class Message1(Message):

        class Color(Enum):

          RED = 1
          GREEN = 2
          BLUE = 3

        # This field default value  will be validated when default is accessed.
        animal = EnumField('Message2.Animal', 1, default='HORSE')

      class Message2(Message):

        class Animal(Enum):

          DOG = 1
          CAT = 2
          HORSE = 3

        # This fields default value will be validated right away since Color
        # is already fully resolved.
        color = EnumField(Message1.Color, 1, default='RED')
    """

    VARIANTS = frozenset([Variant.ENUM])

    DEFAULT_VARIANT = Variant.ENUM

    def __init__(self, enum_type, number, **kwargs):
        """Constructor.

        Args:
          enum_type: Enum type for field.  Must be subclass of Enum.
          number: Number of field.  Must be unique per message class.
          required: Whether or not field is required.  Mutually exclusive to
            'repeated'.
          repeated: Whether or not field is repeated.  Mutually exclusive to
            'required'.
          variant: Wire-format variant hint.
          default: Default value for field if not found in stream.

        Raises:
          FieldDefinitionError when invalid enum_type is provided.
        """
        valid_type = (isinstance(enum_type, six.string_types) or
                      (enum_type is not Enum and
                       isinstance(enum_type, type) and
                       issubclass(enum_type, Enum)))

        if not valid_type:
            raise FieldDefinitionError('Invalid enum type: %s' % enum_type)

        if isinstance(enum_type, six.string_types):
            self.__type_name = enum_type
            self.__type = None
        else:
            self.__type = enum_type

        super(EnumField, self).__init__(number, **kwargs)

    def validate_default_element(self, value):
        """Validate default element of Enum field.

        Enum fields allow for delayed resolution of default values
        when the type of the field has not been resolved. The default
        value of a field may be a string or an integer. If the Enum
        type of the field has been resolved, the default value is
        validated against that type.

        Args:
          value: Value to validate.

        Raises:
          ValidationError if value is not expected message type.

        """
        if isinstance(value, (six.string_types, six.integer_types)):
            # Validation of the value does not happen for delayed resolution
            # enumerated types.  Ignore if type is not yet resolved.
            if self.__type:
                self.__type(value)
            return value

        return super(EnumField, self).validate_default_element(value)

    @property
    def type(self):
        """Enum type used for field."""
        if self.__type is None:
            found_type = find_definition(
                self.__type_name, self.message_definition())
            if not (found_type is not Enum and
                    isinstance(found_type, type) and
                    issubclass(found_type, Enum)):
                raise FieldDefinitionError(
                    'Invalid enum type: %s' % found_type)

            self.__type = found_type
        return self.__type

    @property
    def default(self):
        """Default for enum field.

        Will cause resolution of Enum type and unresolved default value.
        """
        try:
            return self.__resolved_default
        except AttributeError:
            resolved_default = super(EnumField, self).default
            if isinstance(resolved_default, (six.string_types,
                                             six.integer_types)):
                # pylint:disable=not-callable
                resolved_default = self.type(resolved_default)
            self.__resolved_default = resolved_default
            return self.__resolved_default


@util.positional(2)
def find_definition(name, relative_to=None, importer=__import__):
    """Find definition by name in module-space.

    The find algorthm will look for definitions by name relative to a
    message definition or by fully qualfied name. If no definition is
    found relative to the relative_to parameter it will do the same
    search against the container of relative_to. If relative_to is a
    nested Message, it will search its message_definition(). If that
    message has no message_definition() it will search its module. If
    relative_to is a module, it will attempt to look for the
    containing module and search relative to it. If the module is a
    top-level module, it will look for the a message using a fully
    qualified name. If no message is found then, the search fails and
    DefinitionNotFoundError is raised.

    For example, when looking for any definition 'foo.bar.ADefinition'
    relative to an actual message definition abc.xyz.SomeMessage:

      find_definition('foo.bar.ADefinition', SomeMessage)

    It is like looking for the following fully qualified names:

      abc.xyz.SomeMessage. foo.bar.ADefinition
      abc.xyz. foo.bar.ADefinition
      abc. foo.bar.ADefinition
      foo.bar.ADefinition

    When resolving the name relative to Message definitions and modules, the
    algorithm searches any Messages or sub-modules found in its path.
    Non-Message values are not searched.

    A name that begins with '.' is considered to be a fully qualified
    name. The name is always searched for from the topmost package.
    For example, assume two message types:

      abc.xyz.SomeMessage
      xyz.SomeMessage

    Searching for '.xyz.SomeMessage' relative to 'abc' will resolve to
    'xyz.SomeMessage' and not 'abc.xyz.SomeMessage'.  For this kind of name,
    the relative_to parameter is effectively ignored and always set to None.

    For more information about package name resolution, please see:

      http://code.google.com/apis/protocolbuffers/docs/proto.html#packages

    Args:
      name: Name of definition to find.  May be fully qualified or relative
        name.
      relative_to: Search for definition relative to message definition or
        module. None will cause a fully qualified name search.
      importer: Import function to use for resolving modules.

    Returns:
      Enum or Message class definition associated with name.

    Raises:
      DefinitionNotFoundError if no definition is found in any search path.

    """
    # Check parameters.
    if not (relative_to is None or
            isinstance(relative_to, types.ModuleType) or
            isinstance(relative_to, type) and
            issubclass(relative_to, Message)):
        raise TypeError(
            'relative_to must be None, Message definition or module.'
            '  Found: %s' % relative_to)

    name_path = name.split('.')

    # Handle absolute path reference.
    if not name_path[0]:
        relative_to = None
        name_path = name_path[1:]

    def search_path():
        """Performs a single iteration searching the path from relative_to.

        This is the function that searches up the path from a relative object.

          fully.qualified.object . relative.or.nested.Definition
                                   ---------------------------->
                                                      ^
                                                      |
                                this part of search --+

        Returns:
          Message or Enum at the end of name_path, else None.
        """
        next_part = relative_to
        for node in name_path:
            # Look for attribute first.
            attribute = getattr(next_part, node, None)

            if attribute is not None:
                next_part = attribute
            else:
                # If module, look for sub-module.
                if (next_part is None or
                        isinstance(next_part, types.ModuleType)):
                    if next_part is None:
                        module_name = node
                    else:
                        module_name = '%s.%s' % (next_part.__name__, node)

                    try:
                        fromitem = module_name.split('.')[-1]
                        next_part = importer(module_name, '', '',
                                             [str(fromitem)])
                    except ImportError:
                        return None
                else:
                    return None

            if not isinstance(next_part, types.ModuleType):
                if not (isinstance(next_part, type) and
                        issubclass(next_part, (Message, Enum))):
                    return None

        return next_part

    while True:
        found = search_path()
        if isinstance(found, type) and issubclass(found, (Enum, Message)):
            return found
        else:
            # Find next relative_to to search against.
            #
            #   fully.qualified.object . relative.or.nested.Definition
            #   <---------------------
            #           ^
            #           |
            #   does this part of search
            if relative_to is None:
                # Fully qualified search was done.  Nothing found.  Fail.
                raise DefinitionNotFoundError(
                    'Could not find definition for %s' % name)
            else:
                if isinstance(relative_to, types.ModuleType):
                    # Find parent module.
                    module_path = relative_to.__name__.split('.')[:-1]
                    if not module_path:
                        relative_to = None
                    else:
                        # Should not raise ImportError. If it does...
                        # weird and unexpected. Propagate.
                        relative_to = importer(
                            '.'.join(module_path), '', '', [module_path[-1]])
                elif (isinstance(relative_to, type) and
                      issubclass(relative_to, Message)):
                    parent = relative_to.message_definition()
                    if parent is None:
                        last_module_name = relative_to.__module__.split(
                            '.')[-1]
                        relative_to = importer(
                            relative_to.__module__, '', '', [last_module_name])
                    else:
                        relative_to = parent
