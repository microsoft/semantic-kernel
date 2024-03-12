# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Classes to handle dependencies for concepts.

At runtime, resources can be parsed and initialized using the information given
in the Deps object. All the information given by the user in the command line is
available in the Deps object. It may also access other information (such as
information provided by the user during a prompt or properties that are changed
during runtime before the Deps object is used) when Get() is called for a given
attribute, depending on the fallthroughs.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc

from googlecloudsdk.calliope.concepts import util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class Error(exceptions.Error):
  """Base exception type for this module."""


class FallthroughNotFoundError(Error):
  """Raised when an attribute value is not found by a Fallthrough object."""


class AttributeNotFoundError(Error, AttributeError):
  """Raised when an attribute value cannot be found by a Deps object."""


class _FallthroughBase(object, metaclass=abc.ABCMeta):
  """Represents a way to get information about a concept's attribute.

  Specific implementations of Fallthrough objects must implement the method:

    _Call():
      Get a value from information given to the fallthrough.

  GetValue() is used by the Deps object to attempt to find the value of an
  attribute. The hint property is used to provide an informative error when an
  attribute can't be found.
  """

  def __init__(self, hint, active=False, plural=False):
    """Initializes a fallthrough to an arbitrary function.

    Args:
      hint: str | list[str], The user-facing message for the fallthrough
        when it cannot be resolved.
      active: bool, True if the fallthrough is considered to be "actively"
        specified, i.e. on the command line.
      plural: bool, whether the expected result should be a list. Should be
        False for everything except the "anchor" arguments in a case where a
        resource argument is plural (i.e. parses to a list).
    """
    self._hint = hint
    self.active = active
    self.plural = plural

  def GetValue(self, parsed_args):
    """Gets a value from information given to the fallthrough.

    Args:
      parsed_args: the argparse namespace.

    Raises:
      FallthroughNotFoundError: If the attribute is not found.

    Returns:
      The value of the attribute.
    """
    value = self._Call(parsed_args)
    if value:
      return self._Pluralize(value)
    raise FallthroughNotFoundError()

  @abc.abstractmethod
  def _Call(self, parsed_args):
    pass

  def _Pluralize(self, value):
    """Pluralize the result of calling the fallthrough. May be overridden."""
    if not self.plural or isinstance(value, list):
      return value
    return [value] if value else []

  @property
  def hint(self):
    """String representation of the fallthrough for user-facing messaging."""
    return self._hint

  def __hash__(self):
    return hash(self.hint) + hash(self.active)

  def __eq__(self, other):
    return (isinstance(other, self.__class__) and other.hint == self.hint and
            other.active == self.active and other.plural == self.plural)


class Fallthrough(_FallthroughBase):
  """A fallthrough that can get an attribute value from an arbitrary function."""

  def __init__(self, function, hint, active=False, plural=False):
    """Initializes a fallthrough to an arbitrary function.

    Args:
      function: f() -> value, A no argument function that returns the value of
        the argument or None if it cannot be resolved.
      hint: str, The user-facing message for the fallthrough when it cannot be
        resolved. Should start with a lower-case letter.
      active: bool, True if the fallthrough is considered to be "actively"
        specified, i.e. on the command line.
      plural: bool, whether the expected result should be a list. Should be
        False for everything except the "anchor" arguments in a case where a
        resource argument is plural (i.e. parses to a list).

    Raises:
      ValueError: if no hint is provided
    """
    if not hint:
      raise ValueError('Hint must be provided.')
    super(Fallthrough, self).__init__(hint, active=active, plural=plural)
    self._function = function

  def _Call(self, parsed_args):
    del parsed_args
    return self._function()

  def __eq__(self, other):
    return (super(Fallthrough, self).__eq__(other) and
            other._function == self._function)  # pylint: disable=protected-access

  def __hash__(self):
    return hash(self._function)


class ValueFallthrough(_FallthroughBase):
  """Gets an attribute from a property."""

  def __init__(self, value, hint=None, active=False, plural=False):
    """Initializes a fallthrough for the property associated with the attribute.

    Args:
      value: str, Denoting the fixed value to provide to the attribute.
      hint: str, Optional, If provided, used over default help_text.
      active: bool, Optional, whether the value is specified by the user on
        the command line.
      plural: bool, whether the expected result should be a list. Should be
        False for everything except the "anchor" arguments in a case where a
        resource argument is plural (i.e. parses to a list).
    """
    hint = 'The default is `{}`'.format(value) if hint is None else hint

    super(ValueFallthrough, self).__init__(hint, active=active, plural=plural)
    self.value = value

  def _Call(self, parsed_args):
    del parsed_args  # Not used.
    return self.value

  def __eq__(self, other):
    if not isinstance(other, self.__class__):
      return False
    return other.value == self.value

  def __hash__(self):
    return hash(self.value)


class PropertyFallthrough(_FallthroughBase):
  """Gets an attribute from a property."""

  def __init__(self, prop, plural=False):
    """Initializes a fallthrough for the property associated with the attribute.

    Args:
      prop: googlecloudsdk.core.properties._Property, a property.
      plural: bool, whether the expected result should be a list. Should be
        False for everything except the "anchor" arguments in a case where a
        resource argument is plural (i.e. parses to a list).
    """
    hint = 'set the property `{}`'.format(prop)

    super(PropertyFallthrough, self).__init__(hint, plural=plural)
    self.property = prop

  def _Call(self, parsed_args):
    del parsed_args  # Not used.
    try:
      return self.property.GetOrFail()
    except (properties.InvalidValueError, properties.RequiredPropertyError):
      return None

  def __eq__(self, other):
    if not isinstance(other, self.__class__):
      return False
    return other.property == self.property

  def __hash__(self):
    return hash(self.property)


class ArgFallthrough(_FallthroughBase):
  """Gets an attribute from the argparse parsed values for that arg."""

  def __init__(self, arg_name, plural=False):
    """Initializes a fallthrough for the argument associated with the attribute.

    Args:
      arg_name: str, the name of the flag or positional.
      plural: bool, whether the expected result should be a list. Should be
        False for everything except the "anchor" arguments in a case where a
        resource argument is plural (i.e. parses to a list).
    """
    super(ArgFallthrough, self).__init__(
        'provide the argument `{}` on the command line'.format(arg_name),
        active=True,
        plural=plural)
    self.arg_name = arg_name

  def _Call(self, parsed_args):
    arg_value = getattr(parsed_args, util.NamespaceFormat(self.arg_name), None)
    return arg_value

  def _Pluralize(self, value):
    if not self.plural:
      # Positional arguments will always be stored in argparse as lists, even if
      # nargs=1. If not supposed to be plural, transform into a single value.
      if isinstance(value, list):
        return value[0] if value else None
      return value
    if value and not isinstance(value, list):
      return [value]
    return value if value else []

  def __eq__(self, other):
    if not isinstance(other, self.__class__):
      return False
    return other.arg_name == self.arg_name

  def __hash__(self):
    return hash(self.arg_name)


class FullySpecifiedAnchorFallthrough(_FallthroughBase):
  """A fallthrough that gets a parameter from the value of the anchor."""

  def __init__(self,
               fallthroughs,
               collection_info,
               parameter_name,
               plural=False):
    """Initializes a fallthrough getting a parameter from the anchor.

    For anchor arguments which can be plural, returns the list.

    Args:
      fallthroughs: list[_FallthroughBase], any fallthrough for an anchor arg.
      collection_info: the info of the collection to parse the anchor as.
      parameter_name: str, the name of the parameter
      plural: bool, whether the expected result should be a list. Should be
        False for everything except the "anchor" arguments in a case where a
    """
    if plural:
      hint_suffix = 'with fully specified names'
    else:
      hint_suffix = 'with a fully specified name'

    hint = [f'{f.hint} {hint_suffix}' for f in fallthroughs]
    active = all(f.active for f in fallthroughs)
    super(FullySpecifiedAnchorFallthrough, self).__init__(
        hint, active=active, plural=plural)
    self.parameter_name = parameter_name
    self.collection_info = collection_info
    self._fallthroughs = tuple(fallthroughs)  # Make list immutable
    self._resources = resources.REGISTRY.Clone()
    self._resources.RegisterApiByName(self.collection_info.api_name,
                                      self.collection_info.api_version)

  def _GetFromAnchor(self, anchor_value):
    try:
      resource_ref = self._resources.Parse(
          anchor_value, collection=self.collection_info.full_name)
    except resources.Error:
      return None
    # This should only be called for final parsing when the anchor attribute
    # has been split up into non-plural fallthroughs; thus, if an AttributeError
    # results from the parser being passed a list, skip it for now.
    except AttributeError:
      return None
    return getattr(resource_ref, self.parameter_name, None)

  def _Call(self, parsed_args):
    try:
      anchor_value = GetFromFallthroughs(
          self._fallthroughs, parsed_args, attribute_name=self.parameter_name)
    except AttributeNotFoundError:
      return None
    return self._GetFromAnchor(anchor_value)

  def __eq__(self, other):
    return (isinstance(other, self.__class__) and
            other._fallthroughs == self._fallthroughs and
            other.collection_info == self.collection_info and
            other.parameter_name == self.parameter_name)

  def __hash__(self):
    return sum(
        map(hash, [
            self._fallthroughs,
            str(self.collection_info),
            self.parameter_name
        ]))


def Get(attribute_name, attribute_to_fallthroughs_map, parsed_args=None):
  """Gets the value of an attribute based on fallthrough information.

    If the attribute value is not provided by any of the fallthroughs, an
    error is raised with a list of ways to provide information about the
    attribute.

  Args:
    attribute_name: str, the name of the attribute.
    attribute_to_fallthroughs_map: {str: [_FallthroughBase], a map of attribute
      names to lists of fallthroughs.
    parsed_args: a parsed argparse namespace.

  Returns:
    the value of the attribute.

  Raises:
    AttributeNotFoundError: if no value can be found.
  """
  fallthroughs = attribute_to_fallthroughs_map.get(attribute_name, [])
  return GetFromFallthroughs(
      fallthroughs, parsed_args, attribute_name=attribute_name)


def GetFromFallthroughs(fallthroughs, parsed_args, attribute_name=None):
  """Gets the value of an attribute based on fallthrough information.

    If the attribute value is not provided by any of the fallthroughs, an
    error is raised with a list of ways to provide information about the
    attribute.

  Args:
    fallthroughs: [_FallthroughBase], list of fallthroughs.
    parsed_args: a parsed argparse namespace.
    attribute_name: str, the name of the attribute. Used for error message,
      omitted if not provided.

  Returns:
    the value of the attribute.

  Raises:
    AttributeNotFoundError: if no value can be found.
  """
  for fallthrough in fallthroughs:
    try:
      return fallthrough.GetValue(parsed_args)
    except FallthroughNotFoundError:
      continue

  hints = GetHints(fallthroughs)

  fallthroughs_summary = '\n'.join(
      ['- {}'.format(hint) for hint in hints])
  raise AttributeNotFoundError(
      'Failed to find attribute{}. The attribute can be set in the '
      'following ways: \n{}'.format(
          '' if attribute_name is None else ' [{}]'.format(attribute_name),
          fallthroughs_summary))


def GetHints(fallthroughs):
  """Gathers deduped hints from list of fallthroughs."""
  # Create list of non-repeating hints. Dictionary preserves order.
  # This is needed when more than one fallthrough has the same hint.
  # Usually occurs for FullySpecifiedFallthroughs with different
  # resource collections.
  hints_set = {}
  for f in fallthroughs:
    new_hints = f.hint if isinstance(f.hint, list) else [f.hint]
    for hint in new_hints:
      if hint in hints_set:
        continue
      hints_set[hint] = True

  return list(hints_set.keys())
