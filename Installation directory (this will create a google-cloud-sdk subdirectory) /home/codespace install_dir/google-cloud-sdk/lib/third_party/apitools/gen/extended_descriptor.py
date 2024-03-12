#!/usr/bin/env python
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

"""Extended protorpc descriptors.

This takes existing protorpc Descriptor classes and adds extra
properties not directly supported in proto itself, notably field and
message descriptions. We need this in order to generate protorpc
message files with comments.

Note that for most of these classes, we can't simply wrap the existing
message, since we need to change the type of the subfields. We could
have a "plain" descriptor attached, but that seems like unnecessary
bookkeeping. Where possible, we purposely reuse existing tag numbers;
for new fields, we start numbering at 100.
"""
import abc
import operator
import textwrap

import six

from apitools.base.protorpclite import descriptor as protorpc_descriptor
from apitools.base.protorpclite import message_types
from apitools.base.protorpclite import messages
from apitools.base.py import extra_types


class ExtendedEnumValueDescriptor(messages.Message):

    """Enum value descriptor with additional fields.

    Fields:
      name: Name of enumeration value.
      number: Number of enumeration value.
      description: Description of this enum value.
    """
    name = messages.StringField(1)
    number = messages.IntegerField(2, variant=messages.Variant.INT32)

    description = messages.StringField(100)


class ExtendedEnumDescriptor(messages.Message):

    """Enum class descriptor with additional fields.

    Fields:
      name: Name of Enum without any qualification.
      values: Values defined by Enum class.
      description: Description of this enum class.
      full_name: Fully qualified name of this enum class.
      enum_mappings: Mappings from python to JSON names for enum values.
    """

    class JsonEnumMapping(messages.Message):

        """Mapping from a python name to the wire name for an enum."""
        python_name = messages.StringField(1)
        json_name = messages.StringField(2)

    name = messages.StringField(1)
    values = messages.MessageField(
        ExtendedEnumValueDescriptor, 2, repeated=True)

    description = messages.StringField(100)
    full_name = messages.StringField(101)
    enum_mappings = messages.MessageField(
        'JsonEnumMapping', 102, repeated=True)


class ExtendedFieldDescriptor(messages.Message):

    """Field descriptor with additional fields.

    Fields:
      field_descriptor: The underlying field descriptor.
      name: The name of this field.
      description: Description of this field.
    """
    field_descriptor = messages.MessageField(
        protorpc_descriptor.FieldDescriptor, 100)
    # We duplicate the names for easier bookkeeping.
    name = messages.StringField(101)
    description = messages.StringField(102)


class ExtendedMessageDescriptor(messages.Message):

    """Message descriptor with additional fields.

    Fields:
      name: Name of Message without any qualification.
      fields: Fields defined for message.
      message_types: Nested Message classes defined on message.
      enum_types: Nested Enum classes defined on message.
      description: Description of this message.
      full_name: Full qualified name of this message.
      decorators: Decorators to include in the definition when printing.
          Printed in the given order from top to bottom (so the last entry
          is the innermost decorator).
      alias_for: This type is just an alias for the named type.
      field_mappings: Mappings from python to json field names.
    """

    class JsonFieldMapping(messages.Message):

        """Mapping from a python name to the wire name for a field."""
        python_name = messages.StringField(1)
        json_name = messages.StringField(2)

    name = messages.StringField(1)
    fields = messages.MessageField(ExtendedFieldDescriptor, 2, repeated=True)
    message_types = messages.MessageField(
        'extended_descriptor.ExtendedMessageDescriptor', 3, repeated=True)
    enum_types = messages.MessageField(
        ExtendedEnumDescriptor, 4, repeated=True)

    description = messages.StringField(100)
    full_name = messages.StringField(101)
    decorators = messages.StringField(102, repeated=True)
    alias_for = messages.StringField(103)
    field_mappings = messages.MessageField(
        'JsonFieldMapping', 104, repeated=True)


class ExtendedFileDescriptor(messages.Message):

    """File descriptor with additional fields.

    Fields:
      package: Fully qualified name of package that definitions belong to.
      message_types: Message definitions contained in file.
      enum_types: Enum definitions contained in file.
      description: Description of this file.
      additional_imports: Extra imports used in this package.
    """
    package = messages.StringField(2)

    message_types = messages.MessageField(
        ExtendedMessageDescriptor, 4, repeated=True)
    enum_types = messages.MessageField(
        ExtendedEnumDescriptor, 5, repeated=True)

    description = messages.StringField(100)
    additional_imports = messages.StringField(101, repeated=True)


def _WriteFile(file_descriptor, package, version, proto_printer):
    """Write the given extended file descriptor to the printer."""
    proto_printer.PrintPreamble(package, version, file_descriptor)
    _PrintEnums(proto_printer, file_descriptor.enum_types)
    _PrintMessages(proto_printer, file_descriptor.message_types)
    custom_json_mappings = _FetchCustomMappings(file_descriptor.enum_types)
    custom_json_mappings.extend(
        _FetchCustomMappings(file_descriptor.message_types))
    for mapping in custom_json_mappings:
        proto_printer.PrintCustomJsonMapping(mapping)


def WriteMessagesFile(file_descriptor, package, version, printer):
    """Write the given extended file descriptor to out as a message file."""
    _WriteFile(file_descriptor, package, version,
               _Proto2Printer(printer))


def WritePythonFile(file_descriptor, package, version, printer):
    """Write the given extended file descriptor to out."""
    _WriteFile(file_descriptor, package, version,
               _ProtoRpcPrinter(printer))


def PrintIndentedDescriptions(printer, ls, name, prefix=''):
    if ls:
        with printer.Indent(indent=prefix):
            with printer.CommentContext():
                width = printer.CalculateWidth() - len(prefix)
                printer()
                printer(name + ':')
                for x in ls:
                    description = '%s: %s' % (x.name, x.description)
                    for line in textwrap.wrap(description, width,
                                              initial_indent='  ',
                                              subsequent_indent='    '):
                        printer(line)


def _FetchCustomMappings(descriptor_ls):
    """Find and return all custom mappings for descriptors in descriptor_ls."""
    custom_mappings = []
    for descriptor in descriptor_ls:
        if isinstance(descriptor, ExtendedEnumDescriptor):
            custom_mappings.extend(
                _FormatCustomJsonMapping('Enum', m, descriptor)
                for m in descriptor.enum_mappings)
        elif isinstance(descriptor, ExtendedMessageDescriptor):
            custom_mappings.extend(
                _FormatCustomJsonMapping('Field', m, descriptor)
                for m in descriptor.field_mappings)
            custom_mappings.extend(
                _FetchCustomMappings(descriptor.enum_types))
            custom_mappings.extend(
                _FetchCustomMappings(descriptor.message_types))
    return custom_mappings


def _FormatCustomJsonMapping(mapping_type, mapping, descriptor):
    return '\n'.join((
        'encoding.AddCustomJson%sMapping(' % mapping_type,
        "    %s, '%s', '%s')" % (descriptor.full_name, mapping.python_name,
                                 mapping.json_name),
    ))


def _EmptyMessage(message_type):
    return not any((message_type.enum_types,
                    message_type.message_types,
                    message_type.fields))


class ProtoPrinter(six.with_metaclass(abc.ABCMeta, object)):

    """Interface for proto printers."""

    @abc.abstractmethod
    def PrintPreamble(self, package, version, file_descriptor):
        """Print the file docstring and import lines."""

    @abc.abstractmethod
    def PrintEnum(self, enum_type):
        """Print the given enum declaration."""

    @abc.abstractmethod
    def PrintMessage(self, message_type):
        """Print the given message declaration."""


class _Proto2Printer(ProtoPrinter):

    """Printer for proto2 definitions."""

    def __init__(self, printer):
        self.__printer = printer

    def __PrintEnumCommentLines(self, enum_type):
        description = enum_type.description or '%s enum type.' % enum_type.name
        for line in textwrap.wrap(description,
                                  self.__printer.CalculateWidth() - 3):
            self.__printer('// %s', line)
        PrintIndentedDescriptions(self.__printer, enum_type.values, 'Values',
                                  prefix='// ')

    def __PrintEnumValueCommentLines(self, enum_value):
        if enum_value.description:
            width = self.__printer.CalculateWidth() - 3
            for line in textwrap.wrap(enum_value.description, width):
                self.__printer('// %s', line)

    def PrintEnum(self, enum_type):
        self.__PrintEnumCommentLines(enum_type)
        self.__printer('enum %s {', enum_type.name)
        with self.__printer.Indent():
            enum_values = sorted(
                enum_type.values, key=operator.attrgetter('number'))
            for enum_value in enum_values:
                self.__printer()
                self.__PrintEnumValueCommentLines(enum_value)
                self.__printer('%s = %s;', enum_value.name, enum_value.number)
        self.__printer('}')
        self.__printer()

    def PrintPreamble(self, package, version, file_descriptor):
        self.__printer('// Generated message classes for %s version %s.',
                       package, version)
        self.__printer('// NOTE: This file is autogenerated and should not be '
                       'edited by hand.')
        description_lines = textwrap.wrap(file_descriptor.description, 75)
        if description_lines:
            self.__printer('//')
            for line in description_lines:
                self.__printer('// %s', line)
        self.__printer()
        self.__printer('syntax = "proto2";')
        self.__printer('package %s;', file_descriptor.package)

    def __PrintMessageCommentLines(self, message_type):
        """Print the description of this message."""
        description = message_type.description or '%s message type.' % (
            message_type.name)
        width = self.__printer.CalculateWidth() - 3
        for line in textwrap.wrap(description, width):
            self.__printer('// %s', line)
        PrintIndentedDescriptions(self.__printer, message_type.enum_types,
                                  'Enums', prefix='// ')
        PrintIndentedDescriptions(self.__printer, message_type.message_types,
                                  'Messages', prefix='// ')
        PrintIndentedDescriptions(self.__printer, message_type.fields,
                                  'Fields', prefix='// ')

    def __PrintFieldDescription(self, description):
        for line in textwrap.wrap(description,
                                  self.__printer.CalculateWidth() - 3):
            self.__printer('// %s', line)

    def __PrintFields(self, fields):
        for extended_field in fields:
            field = extended_field.field_descriptor
            field_type = messages.Field.lookup_field_type_by_variant(
                field.variant)
            self.__printer()
            self.__PrintFieldDescription(extended_field.description)
            label = str(field.label).lower()
            if field_type in (messages.EnumField, messages.MessageField):
                proto_type = field.type_name
            else:
                proto_type = str(field.variant).lower()
            default_statement = ''
            if field.default_value:
                if field_type in [messages.BytesField, messages.StringField]:
                    default_value = '"%s"' % field.default_value
                elif field_type is messages.BooleanField:
                    default_value = str(field.default_value).lower()
                else:
                    default_value = str(field.default_value)

                default_statement = ' [default = %s]' % default_value
            self.__printer(
                '%s %s %s = %d%s;',
                label, proto_type, field.name, field.number, default_statement)

    def PrintMessage(self, message_type):
        self.__printer()
        self.__PrintMessageCommentLines(message_type)
        if _EmptyMessage(message_type):
            self.__printer('message %s {}', message_type.name)
            return
        self.__printer('message %s {', message_type.name)
        with self.__printer.Indent():
            _PrintEnums(self, message_type.enum_types)
            _PrintMessages(self, message_type.message_types)
            self.__PrintFields(message_type.fields)
        self.__printer('}')

    def PrintCustomJsonMapping(self, mapping_lines):
        raise NotImplementedError(
            'Custom JSON encoding not supported for proto2')


class _ProtoRpcPrinter(ProtoPrinter):

    """Printer for ProtoRPC definitions."""

    def __init__(self, printer):
        self.__printer = printer

    def __PrintClassSeparator(self):
        self.__printer()
        if not self.__printer.indent:
            self.__printer()

    def __PrintEnumDocstringLines(self, enum_type):
        description = enum_type.description or '%s enum type.' % enum_type.name
        for line in textwrap.wrap('r"""%s' % description,
                                  self.__printer.CalculateWidth()):
            self.__printer(line)
        PrintIndentedDescriptions(self.__printer, enum_type.values, 'Values')
        self.__printer('"""')

    def PrintEnum(self, enum_type):
        self.__printer('class %s(_messages.Enum):', enum_type.name)
        with self.__printer.Indent():
            self.__PrintEnumDocstringLines(enum_type)
            enum_values = sorted(
                enum_type.values, key=operator.attrgetter('number'))
            for enum_value in enum_values:
                self.__printer('%s = %s', enum_value.name, enum_value.number)
            if not enum_type.values:
                self.__printer('pass')
        self.__PrintClassSeparator()

    def __PrintAdditionalImports(self, imports):
        """Print additional imports needed for protorpc."""
        google_imports = [x for x in imports if 'google' in x]
        other_imports = [x for x in imports if 'google' not in x]
        if other_imports:
            for import_ in sorted(other_imports):
                self.__printer(import_)
            self.__printer()
        # Note: If we ever were going to add imports from this package, we'd
        # need to sort those out and put them at the end.
        if google_imports:
            for import_ in sorted(google_imports):
                self.__printer(import_)
            self.__printer()

    def PrintPreamble(self, package, version, file_descriptor):
        self.__printer('"""Generated message classes for %s version %s.',
                       package, version)
        self.__printer()
        for line in textwrap.wrap(file_descriptor.description, 78):
            self.__printer(line)
        self.__printer('"""')
        self.__printer('# NOTE: This file is autogenerated and should not be '
                       'edited by hand.')
        self.__printer()
        self.__printer('from __future__ import absolute_import')
        self.__printer()
        self.__PrintAdditionalImports(file_descriptor.additional_imports)
        self.__printer()
        self.__printer("package = '%s'", file_descriptor.package)
        self.__printer()
        self.__printer()

    def __PrintMessageDocstringLines(self, message_type):
        """Print the docstring for this message."""
        description = message_type.description or '%s message type.' % (
            message_type.name)
        short_description = (
            _EmptyMessage(message_type) and
            len(description) < (self.__printer.CalculateWidth() - 6))
        with self.__printer.CommentContext():
            if short_description:
                # Note that we use explicit string interpolation here since
                # we're in comment context.
                self.__printer('r"""%s"""' % description)
                return
            for line in textwrap.wrap('r"""%s' % description,
                                      self.__printer.CalculateWidth()):
                self.__printer(line)

            PrintIndentedDescriptions(self.__printer, message_type.enum_types,
                                      'Enums')
            PrintIndentedDescriptions(
                self.__printer, message_type.message_types, 'Messages')
            PrintIndentedDescriptions(
                self.__printer, message_type.fields, 'Fields')
            self.__printer('"""')
            self.__printer()

    def PrintMessage(self, message_type):
        if message_type.alias_for:
            self.__printer(
                '%s = %s', message_type.name, message_type.alias_for)
            self.__PrintClassSeparator()
            return
        for decorator in message_type.decorators:
            self.__printer('@%s', decorator)
        self.__printer('class %s(_messages.Message):', message_type.name)
        with self.__printer.Indent():
            self.__PrintMessageDocstringLines(message_type)
            _PrintEnums(self, message_type.enum_types)
            _PrintMessages(self, message_type.message_types)
            _PrintFields(message_type.fields, self.__printer)
        self.__PrintClassSeparator()

    def PrintCustomJsonMapping(self, mapping):
        self.__printer(mapping)


def _PrintEnums(proto_printer, enum_types):
    """Print all enums to the given proto_printer."""
    enum_types = sorted(enum_types, key=operator.attrgetter('name'))
    for enum_type in enum_types:
        proto_printer.PrintEnum(enum_type)


def _PrintMessages(proto_printer, message_list):
    message_list = sorted(message_list, key=operator.attrgetter('name'))
    for message_type in message_list:
        proto_printer.PrintMessage(message_type)


_MESSAGE_FIELD_MAP = {
    message_types.DateTimeMessage.definition_name(): (
        message_types.DateTimeField),
}


def _PrintFields(fields, printer):
    for extended_field in fields:
        field = extended_field.field_descriptor
        printed_field_info = {
            'name': field.name,
            'module': '_messages',
            'type_name': '',
            'type_format': '',
            'number': field.number,
            'label_format': '',
            'variant_format': '',
            'default_format': '',
        }

        message_field = _MESSAGE_FIELD_MAP.get(field.type_name)
        if message_field:
            printed_field_info['module'] = '_message_types'
            field_type = message_field
        elif field.type_name == 'extra_types.DateField':
            printed_field_info['module'] = 'extra_types'
            field_type = extra_types.DateField
        else:
            field_type = messages.Field.lookup_field_type_by_variant(
                field.variant)

        if field_type in (messages.EnumField, messages.MessageField):
            printed_field_info['type_format'] = "'%s', " % field.type_name

        if field.label == protorpc_descriptor.FieldDescriptor.Label.REQUIRED:
            printed_field_info['label_format'] = ', required=True'
        elif field.label == protorpc_descriptor.FieldDescriptor.Label.REPEATED:
            printed_field_info['label_format'] = ', repeated=True'

        if field_type.DEFAULT_VARIANT != field.variant:
            printed_field_info['variant_format'] = (
                ', variant=_messages.Variant.%s' % field.variant)

        if field.default_value:
            if field_type in [messages.BytesField, messages.StringField]:
                default_value = repr(field.default_value)
            elif field_type is messages.EnumField:
                try:
                    default_value = str(int(field.default_value))
                except ValueError:
                    default_value = repr(field.default_value)
            else:
                default_value = field.default_value

            printed_field_info[
                'default_format'] = ', default=%s' % (default_value,)

        printed_field_info['type_name'] = field_type.__name__
        args = ''.join('%%(%s)s' % field for field in (
            'type_format',
            'number',
            'label_format',
            'variant_format',
            'default_format'))
        format_str = '%%(name)s = %%(module)s.%%(type_name)s(%s)' % args
        printer(format_str % printed_field_info)
