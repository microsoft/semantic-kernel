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

"""Services descriptor definitions.

Contains message definitions and functions for converting
service classes into transmittable message format.

Describing an Enum instance, Enum class, Field class or Message class will
generate an appropriate descriptor object that describes that class.
This message can itself be used to transmit information to clients wishing
to know the description of an enum value, enum, field or message without
needing to download the source code.  This format is also compatible with
other, non-Python languages.

The descriptors are modeled to be binary compatible with
  https://github.com/google/protobuf

NOTE: The names of types and fields are not always the same between these
descriptors and the ones defined in descriptor.proto.  This was done in order
to make source code files that use these descriptors easier to read.  For
example, it is not necessary to prefix TYPE to all the values in
FieldDescriptor.Variant as is done in descriptor.proto
FieldDescriptorProto.Type.

Example:

  class Pixel(messages.Message):

    x = messages.IntegerField(1, required=True)
    y = messages.IntegerField(2, required=True)

    color = messages.BytesField(3)

  # Describe Pixel class using message descriptor.
  fields = []

  field = FieldDescriptor()
  field.name = 'x'
  field.number = 1
  field.label = FieldDescriptor.Label.REQUIRED
  field.variant = FieldDescriptor.Variant.INT64
  fields.append(field)

  field = FieldDescriptor()
  field.name = 'y'
  field.number = 2
  field.label = FieldDescriptor.Label.REQUIRED
  field.variant = FieldDescriptor.Variant.INT64
  fields.append(field)

  field = FieldDescriptor()
  field.name = 'color'
  field.number = 3
  field.label = FieldDescriptor.Label.OPTIONAL
  field.variant = FieldDescriptor.Variant.BYTES
  fields.append(field)

  message = MessageDescriptor()
  message.name = 'Pixel'
  message.fields = fields

  # Describing is the equivalent of building the above message.
  message == describe_message(Pixel)

Public Classes:
  EnumValueDescriptor: Describes Enum values.
  EnumDescriptor: Describes Enum classes.
  FieldDescriptor: Describes field instances.
  FileDescriptor: Describes a single 'file' unit.
  FileSet: Describes a collection of file descriptors.
  MessageDescriptor: Describes Message classes.

Public Functions:
  describe_enum_value: Describe an individual enum-value.
  describe_enum: Describe an Enum class.
  describe_field: Describe a Field definition.
  describe_file: Describe a 'file' unit from a Python module or object.
  describe_file_set: Describe a file set from a list of modules or objects.
  describe_message: Describe a Message definition.
"""
import codecs
import types

import six

from apitools.base.protorpclite import messages
from apitools.base.protorpclite import util


__all__ = [
    'EnumDescriptor',
    'EnumValueDescriptor',
    'FieldDescriptor',
    'MessageDescriptor',
    'FileDescriptor',
    'FileSet',
    'DescriptorLibrary',

    'describe_enum',
    'describe_enum_value',
    'describe_field',
    'describe_message',
    'describe_file',
    'describe_file_set',
    'describe',
    'import_descriptor_loader',
]


# NOTE: MessageField is missing because message fields cannot have
# a default value at this time.
# TODO(user): Support default message values.
#
# Map to functions that convert default values of fields of a given type
# to a string.  The function must return a value that is compatible with
# FieldDescriptor.default_value and therefore a unicode string.
_DEFAULT_TO_STRING_MAP = {
    messages.IntegerField: six.text_type,
    messages.FloatField: six.text_type,
    messages.BooleanField: lambda value: value and u'true' or u'false',
    messages.BytesField: lambda value: codecs.escape_encode(value)[0],
    messages.StringField: lambda value: value,
    messages.EnumField: lambda value: six.text_type(value.number),
}

_DEFAULT_FROM_STRING_MAP = {
    messages.IntegerField: int,
    messages.FloatField: float,
    messages.BooleanField: lambda value: value == u'true',
    messages.BytesField: lambda value: codecs.escape_decode(value)[0],
    messages.StringField: lambda value: value,
    messages.EnumField: int,
}


class EnumValueDescriptor(messages.Message):
    """Enum value descriptor.

    Fields:
      name: Name of enumeration value.
      number: Number of enumeration value.
    """

    # TODO(user): Why are these listed as optional in descriptor.proto.
    # Harmonize?
    name = messages.StringField(1, required=True)
    number = messages.IntegerField(2,
                                   required=True,
                                   variant=messages.Variant.INT32)


class EnumDescriptor(messages.Message):
    """Enum class descriptor.

    Fields:
      name: Name of Enum without any qualification.
      values: Values defined by Enum class.
    """

    name = messages.StringField(1)
    values = messages.MessageField(EnumValueDescriptor, 2, repeated=True)


class FieldDescriptor(messages.Message):
    """Field definition descriptor.

    Enums:
      Variant: Wire format hint sub-types for field.
      Label: Values for optional, required and repeated fields.

    Fields:
      name: Name of field.
      number: Number of field.
      variant: Variant of field.
      type_name: Type name for message and enum fields.
      default_value: String representation of default value.
    """

    Variant = messages.Variant  # pylint:disable=invalid-name

    class Label(messages.Enum):
        """Field label."""

        OPTIONAL = 1
        REQUIRED = 2
        REPEATED = 3

    name = messages.StringField(1, required=True)
    number = messages.IntegerField(3,
                                   required=True,
                                   variant=messages.Variant.INT32)
    label = messages.EnumField(Label, 4, default=Label.OPTIONAL)
    variant = messages.EnumField(Variant, 5)
    type_name = messages.StringField(6)

    # For numeric types, contains the original text representation of
    #   the value.
    # For booleans, "true" or "false".
    # For strings, contains the default text contents (not escaped in any
    #   way).
    # For bytes, contains the C escaped value.  All bytes < 128 are that are
    #   traditionally considered unprintable are also escaped.
    default_value = messages.StringField(7)


class MessageDescriptor(messages.Message):
    """Message definition descriptor.

    Fields:
      name: Name of Message without any qualification.
      fields: Fields defined for message.
      message_types: Nested Message classes defined on message.
      enum_types: Nested Enum classes defined on message.
    """

    name = messages.StringField(1)
    fields = messages.MessageField(FieldDescriptor, 2, repeated=True)

    message_types = messages.MessageField(
        'apitools.base.protorpclite.descriptor.MessageDescriptor', 3,
        repeated=True)
    enum_types = messages.MessageField(EnumDescriptor, 4, repeated=True)


class FileDescriptor(messages.Message):
    """Description of file containing protobuf definitions.

    Fields:
      package: Fully qualified name of package that definitions belong to.
      message_types: Message definitions contained in file.
      enum_types: Enum definitions contained in file.
    """

    package = messages.StringField(2)

    # TODO(user): Add dependency field

    message_types = messages.MessageField(MessageDescriptor, 4, repeated=True)
    enum_types = messages.MessageField(EnumDescriptor, 5, repeated=True)


class FileSet(messages.Message):
    """A collection of FileDescriptors.

    Fields:
      files: Files in file-set.
    """

    files = messages.MessageField(FileDescriptor, 1, repeated=True)


def describe_enum_value(enum_value):
    """Build descriptor for Enum instance.

    Args:
      enum_value: Enum value to provide descriptor for.

    Returns:
      Initialized EnumValueDescriptor instance describing the Enum instance.
    """
    enum_value_descriptor = EnumValueDescriptor()
    enum_value_descriptor.name = six.text_type(enum_value.name)
    enum_value_descriptor.number = enum_value.number
    return enum_value_descriptor


def describe_enum(enum_definition):
    """Build descriptor for Enum class.

    Args:
      enum_definition: Enum class to provide descriptor for.

    Returns:
      Initialized EnumDescriptor instance describing the Enum class.
    """
    enum_descriptor = EnumDescriptor()
    enum_descriptor.name = enum_definition.definition_name().split('.')[-1]

    values = []
    for number in sorted(enum_definition.numbers()):
        value = enum_definition.lookup_by_number(number)
        values.append(describe_enum_value(value))

    if values:
        enum_descriptor.values = values

    return enum_descriptor


def describe_field(field_definition):
    """Build descriptor for Field instance.

    Args:
      field_definition: Field instance to provide descriptor for.

    Returns:
      Initialized FieldDescriptor instance describing the Field instance.
    """
    field_descriptor = FieldDescriptor()
    field_descriptor.name = field_definition.name
    field_descriptor.number = field_definition.number
    field_descriptor.variant = field_definition.variant

    if isinstance(field_definition, messages.EnumField):
        field_descriptor.type_name = field_definition.type.definition_name()

    if isinstance(field_definition, messages.MessageField):
        field_descriptor.type_name = (
            field_definition.message_type.definition_name())

    if field_definition.default is not None:
        field_descriptor.default_value = _DEFAULT_TO_STRING_MAP[
            type(field_definition)](field_definition.default)

    # Set label.
    if field_definition.repeated:
        field_descriptor.label = FieldDescriptor.Label.REPEATED
    elif field_definition.required:
        field_descriptor.label = FieldDescriptor.Label.REQUIRED
    else:
        field_descriptor.label = FieldDescriptor.Label.OPTIONAL

    return field_descriptor


def describe_message(message_definition):
    """Build descriptor for Message class.

    Args:
      message_definition: Message class to provide descriptor for.

    Returns:
      Initialized MessageDescriptor instance describing the Message class.
    """
    message_descriptor = MessageDescriptor()
    message_descriptor.name = message_definition.definition_name().split(
        '.')[-1]

    fields = sorted(message_definition.all_fields(),
                    key=lambda v: v.number)
    if fields:
        message_descriptor.fields = [describe_field(field) for field in fields]

    try:
        nested_messages = message_definition.__messages__
    except AttributeError:
        pass
    else:
        message_descriptors = []
        for name in nested_messages:
            value = getattr(message_definition, name)
            message_descriptors.append(describe_message(value))

        message_descriptor.message_types = message_descriptors

    try:
        nested_enums = message_definition.__enums__
    except AttributeError:
        pass
    else:
        enum_descriptors = []
        for name in nested_enums:
            value = getattr(message_definition, name)
            enum_descriptors.append(describe_enum(value))

        message_descriptor.enum_types = enum_descriptors

    return message_descriptor


def describe_file(module):
    """Build a file from a specified Python module.

    Args:
      module: Python module to describe.

    Returns:
      Initialized FileDescriptor instance describing the module.
    """
    descriptor = FileDescriptor()
    descriptor.package = util.get_package_for_module(module)

    if not descriptor.package:
        descriptor.package = None

    message_descriptors = []
    enum_descriptors = []

    # Need to iterate over all top level attributes of the module looking for
    # message and enum definitions.  Each definition must be itself described.
    for name in sorted(dir(module)):
        value = getattr(module, name)

        if isinstance(value, type):
            if issubclass(value, messages.Message):
                message_descriptors.append(describe_message(value))

            elif issubclass(value, messages.Enum):
                enum_descriptors.append(describe_enum(value))

    if message_descriptors:
        descriptor.message_types = message_descriptors

    if enum_descriptors:
        descriptor.enum_types = enum_descriptors

    return descriptor


def describe_file_set(modules):
    """Build a file set from a specified Python modules.

    Args:
      modules: Iterable of Python module to describe.

    Returns:
      Initialized FileSet instance describing the modules.
    """
    descriptor = FileSet()
    file_descriptors = []
    for module in modules:
        file_descriptors.append(describe_file(module))

    if file_descriptors:
        descriptor.files = file_descriptors

    return descriptor


def describe(value):
    """Describe any value as a descriptor.

    Helper function for describing any object with an appropriate descriptor
    object.

    Args:
      value: Value to describe as a descriptor.

    Returns:
      Descriptor message class if object is describable as a descriptor, else
      None.
    """
    if isinstance(value, types.ModuleType):
        return describe_file(value)
    elif isinstance(value, messages.Field):
        return describe_field(value)
    elif isinstance(value, messages.Enum):
        return describe_enum_value(value)
    elif isinstance(value, type):
        if issubclass(value, messages.Message):
            return describe_message(value)
        elif issubclass(value, messages.Enum):
            return describe_enum(value)
    return None


@util.positional(1)
def import_descriptor_loader(definition_name, importer=__import__):
    """Find objects by importing modules as needed.

    A definition loader is a function that resolves a definition name to a
    descriptor.

    The import finder resolves definitions to their names by importing modules
    when necessary.

    Args:
      definition_name: Name of definition to find.
      importer: Import function used for importing new modules.

    Returns:
      Appropriate descriptor for any describable type located by name.

    Raises:
      DefinitionNotFoundError when a name does not refer to either a definition
      or a module.
    """
    # Attempt to import descriptor as a module.
    if definition_name.startswith('.'):
        definition_name = definition_name[1:]
    if not definition_name.startswith('.'):
        leaf = definition_name.split('.')[-1]
        if definition_name:
            try:
                module = importer(definition_name, '', '', [leaf])
            except ImportError:
                pass
            else:
                return describe(module)

    try:
        # Attempt to use messages.find_definition to find item.
        return describe(messages.find_definition(definition_name,
                                                 importer=__import__))
    except messages.DefinitionNotFoundError as err:
        # There are things that find_definition will not find, but if
        # the parent is loaded, its children can be searched for a
        # match.
        split_name = definition_name.rsplit('.', 1)
        if len(split_name) > 1:
            parent, child = split_name
            try:
                parent_definition = import_descriptor_loader(
                    parent, importer=importer)
            except messages.DefinitionNotFoundError:
                # Fall through to original error.
                pass
            else:
                # Check the parent definition for a matching descriptor.
                if isinstance(parent_definition, EnumDescriptor):
                    search_list = parent_definition.values or []
                elif isinstance(parent_definition, MessageDescriptor):
                    search_list = parent_definition.fields or []
                else:
                    search_list = []

                for definition in search_list:
                    if definition.name == child:
                        return definition

        # Still didn't find.  Reraise original exception.
        raise err


class DescriptorLibrary(object):
    """A descriptor library is an object that contains known definitions.

    A descriptor library contains a cache of descriptor objects mapped by
    definition name.  It contains all types of descriptors except for
    file sets.

    When a definition name is requested that the library does not know about
    it can be provided with a descriptor loader which attempt to resolve the
    missing descriptor.
    """

    @util.positional(1)
    def __init__(self,
                 descriptors=None,
                 descriptor_loader=import_descriptor_loader):
        """Constructor.

        Args:
          descriptors: A dictionary or dictionary-like object that can be used
            to store and cache descriptors by definition name.
          definition_loader: A function used for resolving missing descriptors.
            The function takes a definition name as its parameter and returns
            an appropriate descriptor.  It may raise DefinitionNotFoundError.
        """
        self.__descriptor_loader = descriptor_loader
        self.__descriptors = descriptors or {}

    def lookup_descriptor(self, definition_name):
        """Lookup descriptor by name.

        Get descriptor from library by name.  If descriptor is not found will
        attempt to find via descriptor loader if provided.

        Args:
          definition_name: Definition name to find.

        Returns:
          Descriptor that describes definition name.

        Raises:
          DefinitionNotFoundError if not descriptor exists for definition name.
        """
        try:
            return self.__descriptors[definition_name]
        except KeyError:
            pass

        if self.__descriptor_loader:
            definition = self.__descriptor_loader(definition_name)
            self.__descriptors[definition_name] = definition
            return definition
        else:
            raise messages.DefinitionNotFoundError(
                'Could not find definition for %s' % definition_name)

    def lookup_package(self, definition_name):
        """Determines the package name for any definition.

        Determine the package that any definition name belongs to. May
        check parent for package name and will resolve missing
        descriptors if provided descriptor loader.

        Args:
          definition_name: Definition name to find package for.

        """
        while True:
            descriptor = self.lookup_descriptor(definition_name)
            if isinstance(descriptor, FileDescriptor):
                return descriptor.package
            else:
                index = definition_name.rfind('.')
                if index < 0:
                    return None
                definition_name = definition_name[:index]
