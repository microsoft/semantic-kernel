# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utilities for adding help text for flags with an argparser type."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


import abc
import six


class ArgTypeUsage(six.with_metaclass(abc.ABCMeta, object)):
  """Interface for flags types that need to provide additional usage info."""

  @property
  @abc.abstractmethod
  def hidden(self):
    """Whether the argument is hidden."""

  @abc.abstractmethod
  def GetUsageMetavar(self, is_custom_metavar, metavar):
    """Returns the metavar for flag with type self."""

  @abc.abstractmethod
  def GetUsageExample(self, shorthand):
    """Returns the example user input value for flag with type self."""

  @abc.abstractmethod
  def GetUsageHelpText(self, field_name, required, flag_name):
    """Returns the help text for flag with type self."""


class DefaultArgTypeWrapper(ArgTypeUsage):
  """Base class for processing arg_type output but maintaining usage help text.

  Attributes:
    arg_type: type function used to parse input string into correct type
      ie ArgObject(value_type=int, repeating=true), int, bool, etc
  """

  def __init__(self, arg_type):
    super(DefaultArgTypeWrapper, self).__init__()
    self.arg_type = arg_type

  @property
  def _is_usage_type(self):
    return isinstance(self.arg_type, ArgTypeUsage)

  @property
  def hidden(self):
    if self._is_usage_type:
      return self.arg_type.hidden
    else:
      return None

  def GetUsageMetavar(self, *args, **kwargs):
    """Forwards default usage metavar for arg_type."""
    if self._is_usage_type:
      return self.arg_type.GetUsageMetavar(*args, **kwargs)
    else:
      return None

  def GetUsageExample(self, *args, **kwargs):
    """Forwards default usage example for arg_type."""
    if self._is_usage_type:
      return self.arg_type.GetUsageExample(*args, **kwargs)
    else:
      return None

  def GetUsageHelpText(self, *args, **kwargs):
    """Forwards default help text for arg_type."""
    if self._is_usage_type:
      return self.arg_type.GetUsageHelpText(*args, **kwargs)
    else:
      return None


def IsHidden(arg_type):
  """Returns whether arg_type is hidden.

  Args:
    arg_type: Callable, arg type that may contain hidden attribute

  Returns:
    bool, whether the type is considered hidden
  """
  return (isinstance(arg_type, ArgTypeUsage) and arg_type.hidden) or False


ASCII_INDENT = '::\n'


def IndentAsciiDoc(text, depth=0):
  """Tabs over all lines in text using ascii doc syntax."""
  additional_tabs = ':' * depth
  return text.replace(ASCII_INDENT, additional_tabs + ASCII_INDENT)


def _FormatBasicTypeStr(arg_type):
  """Returns a user friendly name of a primitive arg_type.

  Args:
    arg_type: type | str | None, expected user input type

  Returns:
    String representation of the type
  """
  if not arg_type:
    return None
  if isinstance(arg_type, str):
    # If arg_type is a string literal, return string literal
    return arg_type

  # Return string representation of common built in callable types
  if arg_type is int:
    return 'int'
  if arg_type is float:
    return 'float'
  if arg_type is bool:
    return 'boolean'

  # Default to string
  # TODO(b/296409952) Add common complex types such as enum or resource args
  return 'string'


def FormatHelpText(field_name, required, help_text=None):
  """Defaults and formats specific attribute of help text.

  Args:
    field_name: None | str, attribute that is being set by flag
    required: bool, whether the flag is required
    help_text: None | str, text that describes the flag

  Returns:
    help text formatted as `{type} {required}, {help}`
  """
  if help_text:
    defaulted_help_text = help_text
  elif field_name:
    defaulted_help_text = 'Sets `{}` value.'.format(field_name)
  else:
    defaulted_help_text = 'Sets value.'

  if required:
    return 'Required, {}'.format(defaulted_help_text)
  else:
    return defaulted_help_text


def FormatCodeSnippet(arg_name, arg_value, append=False):
  """Formats flag in markdown code snippet.

  Args:
    arg_name: str, name of the flag in snippet
    arg_value: str, flag value in snippet
    append: bool, whether to use append syntax for flag

  Returns:
    markdown string of example user input
  """
  if ' ' in arg_value:
    example_flag = "{}='{}'".format(arg_name, arg_value)
  else:
    example_flag = '{}={}'.format(arg_name, arg_value)

  if append:
    return '```\n\n{input} {input}\n\n```'.format(input=example_flag)
  else:
    return '```\n\n{}\n\n```'.format(example_flag)


def _GetNestedValueExample(arg_type, shorthand):
  """Gets an example input value for flag of arg_type.

  Args:
    arg_type: Callable[[str], Any] | str | None, expected user input type
    shorthand: bool, whether to display example in shorthand

  Returns:
    string representation of user input for type arg_type
  """
  if not arg_type:
    return None

  if isinstance(arg_type, ArgTypeUsage):
    arg_str = arg_type.GetUsageExample(shorthand=shorthand)
  else:
    arg_str = _FormatBasicTypeStr(arg_type)

  is_string_literal = isinstance(arg_type, str)
  is_string_type = arg_str == _FormatBasicTypeStr(str)
  if not shorthand and (is_string_literal or is_string_type):
    return '"{}"'.format(arg_str)
  else:
    return arg_str


def GetNestedKeyValueExample(key_type, value_type, shorthand):
  """Formats example key-value input for flag of arg_type.

  If key_type and value_type are callable types str, returns

    string=string (shorthand) or
    "string": "string" (non-shorthand)

  If key_type is a static string value such as x, returns

    x=string (shorthand) or
    "x": "string" (non-shorthand).

  If key_type or value_type are None, returns string representation of
  key or value

  Args:
    key_type: Callable[[str], Any] | str | None, type function for the key
    value_type: Callable[[str], Any] | None, type function for the value
    shorthand: bool, whether to display the example in shorthand

  Returns:
    str, example of key-value pair
  """
  key_str = _GetNestedValueExample(key_type, shorthand)
  value_str = _GetNestedValueExample(value_type, shorthand)

  if IsHidden(key_type) or IsHidden(value_type):
    return None
  elif not key_str or not value_str:
    return key_str or value_str
  elif shorthand:
    return '{}={}'.format(key_str, value_str)
  else:
    return '{}: {}'.format(key_str, value_str)


def GetNestedUsageHelpText(field_name, arg_type, required=False):
  """Returns help text for flag with arg_type.

  Generates help text based on schema such that the final output will
  look something like...

    *Foo*
        Required, Foo help text

  Args:
    field_name: str, attribute we are generating help text for
    arg_type: Callable[[str], Any] | None, type of the attribute we are getting
      help text for
    required: bool, whether the attribute is required

  Returns:
    string help text for specific attribute
  """
  if isinstance(arg_type, ArgTypeUsage):
    usage = arg_type.GetUsageHelpText(field_name, required=required)
  else:
    usage = FormatHelpText(field_name=field_name, required=required)

  # Shift (indent) nested content over to the right by one
  if usage:
    return '*{}*{}{}'.format(
        field_name, ASCII_INDENT, IndentAsciiDoc(usage, depth=1))
  else:
    return None
