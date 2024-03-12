# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
r"""A module for extracting properties from Python dicts.

A property is a string that represents a value in a JSON-serializable
dict. For example, "x.y" matches 1 in {'x': {'y': 1, 'z': 2}, 'y': [1,
2, 3]}.

See PropertySelector and PropertyGetter's docstrings for example
usage.

The grammar for properties is as follows:

    path
        ::= primary
        ::= primary '.' path

    primary
        ::= attribute
        ::= attribute '[' ']'
        ::= attribute '[' index ']'

    index
        ::= Any non-negative integer. Integers beginning with 0 are
            interpreted as base-10.

    attribute
        := Any non-empty sequence of characters; The special characters
           '[', ']', and '.' may appear if they are preceded by '\'.
           The literal '\' may appear if it is itself preceded by a '\'.

There are three operators in the language of properties:

    '.': Attribute access which allows one to select the key of
        a dict.

    '[]': List operator which allows one to apply the rest of the
        property to each element of a list.

    '[INDEX]': List access which allows one to select an element of
        a list.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import copy
from googlecloudsdk.core.util import tokenizer
import six


class Error(Exception):
  """Base class for exceptions raised by this module."""


class IllegalProperty(Error):
  """Raised for properties that are syntactically incorrect."""


class ConflictingProperties(Error):
  """Raised when a property conflicts with another.

  Examples of conflicting properties:

      - "a.b" and "a[0].b"
      - "a[0].b" and "a[].b"
  """


class _Key(str):
  pass


class _Index(int):
  pass


class _Slice(object):

  def __eq__(self, other):
    return type(self) == type(other)

  def __hash__(self):
    return 0


def _Parse(prop):
  """Parses the given tokens that represent a property."""
  tokens = tokenizer.Tokenize(prop, ['[', ']', '.'])
  tokens = [token for token in tokens if token]
  if not tokens:
    raise IllegalProperty('illegal property: {0}'.format(prop))

  res = []

  while tokens:
    if not isinstance(tokens[0], tokenizer.Literal):
      raise IllegalProperty('illegal property: {0}'.format(prop))

    res.append(_Key(tokens[0]))
    tokens = tokens[1:]

    # At this point, we expect to be either at the end of the input
    # stream or we expect to see a "." or "[".

    # We've reached the end of the input stream.
    if not tokens:
      break

    if not isinstance(tokens[0], tokenizer.Separator):
      raise IllegalProperty('illegal property: {0}'.format(prop))

    if isinstance(tokens[0], tokenizer.Separator) and tokens[0] == '[':
      if len(tokens) < 2:
        raise IllegalProperty('illegal property: {0}'.format(prop))

      tokens = tokens[1:]

      # Handles list slices (i.e., "[]").
      if (isinstance(tokens[0], tokenizer.Separator) and
          tokens[0] == ']'):
        res.append(_Slice())
        tokens = tokens[1:]

      # Handles index accesses (e.g., "[1]").
      elif (isinstance(tokens[0], tokenizer.Literal) and
            tokens[0].isdigit() and
            len(tokens) >= 2 and
            isinstance(tokens[1], tokenizer.Separator) and
            tokens[1] == ']'):
        res.append(_Index(tokens[0]))
        tokens = tokens[2:]

      else:
        raise IllegalProperty('illegal property: {0}'.format(prop))

    # We've reached the end of input.
    if not tokens:
      break

    # We expect a "."; we also expect that the "." is not the last
    # token in the input.
    if (len(tokens) > 1 and
        isinstance(tokens[0], tokenizer.Separator) and
        tokens[0] == '.'):
      tokens = tokens[1:]
      continue
    else:
      raise IllegalProperty('illegal property: {0}'.format(prop))

  return res


def _GetProperty(obj, components):
  """Grabs a property from obj."""
  if obj is None:
    return None

  elif not components:
    return obj

  elif (isinstance(components[0], _Key) and
        isinstance(obj, dict)):
    return _GetProperty(obj.get(components[0]), components[1:])

  elif (isinstance(components[0], _Index) and isinstance(obj, list) and
        components[0] < len(obj)):
    return _GetProperty(obj[components[0]], components[1:])

  elif (isinstance(components[0], _Slice) and
        isinstance(obj, list)):
    return [_GetProperty(item, components[1:]) for item in obj]

  else:
    return None


def _DictToOrderedDict(obj):
  """Recursively converts a JSON-serializable dict to an OrderedDict."""
  if isinstance(obj, dict):
    new_obj = collections.OrderedDict(sorted(obj.items()))
    for key, value in six.iteritems(new_obj):
      new_obj[key] = _DictToOrderedDict(value)
    return new_obj
  elif isinstance(obj, list):
    return [_DictToOrderedDict(item) for item in obj]
  else:
    return copy.deepcopy(obj)


def _Filter(obj, properties):
  """Retains the data specified by properties in a JSON-serializable dict."""
  # If any property is empty, then the client wants everything, so
  # return obj without filtering it.
  if not all(properties):
    return _DictToOrderedDict(obj)

  head_to_tail = collections.OrderedDict()
  for prop in properties:
    if prop:
      head, tail = prop[0], prop[1:]
      if head in head_to_tail:
        head_to_tail[head].append(tail)
      else:
        head_to_tail[head] = [tail]

  if isinstance(obj, dict):
    filtered_obj = collections.OrderedDict()
    for key, value in six.iteritems(head_to_tail):
      if key in obj:
        # Note that the keys are converted to strings. This is
        # necessary because the keys are of type _Key and we want to
        # avoid leaking implementation details.
        if all(value):
          res = _Filter(obj[key], value)
          if res is not None:
            filtered_obj[str(key)] = res
        else:
          filtered_obj[str(key)] = _DictToOrderedDict(obj[key])

    if filtered_obj:
      return filtered_obj
    else:
      return None

  elif isinstance(obj, list):
    if not head_to_tail:
      return obj

    indices = set([])
    for key in head_to_tail:
      if isinstance(key, _Index) and key < len(obj):
        indices.add(key)

    slice_tail = head_to_tail.get(_Slice())
    if slice_tail:
      res = []
      for i, item in enumerate(obj):
        if i in indices:
          properties = head_to_tail[i] + slice_tail
        else:
          properties = slice_tail
        res.append(_Filter(item, properties))

    else:
      res = [None] * len(obj)

      for index in indices:
        properties = head_to_tail[index]
        if all(properties):
          res[index] = _Filter(obj[index], properties)
        else:
          res[index] = _DictToOrderedDict(obj[index])

    # If all items are None, return None, otherwise return a list.
    if [item for item in res if item is not None]:
      return res
    else:
      return None

  else:
    return _DictToOrderedDict(obj)

  return None


def _ApplyTransformation(components, func, obj):
  """Applies the given function to the property pointed to by components.

  For example:

      obj = {'x': {'y': 1, 'z': 2}, 'y': [1, 2, 3]}
      _ApplyTransformation(_Parse('x.y'), lambda x: x* 2, obj)

  results in obj becoming:

      {'x': {'y': 2, 'z': 2}, 'y': [1, 2, 3]}

  Args:
    components: A parsed property.
    func: The function to apply.
    obj: A JSON-serializable dict to apply the function to.
  """
  if isinstance(obj, dict) and isinstance(components[0], _Key):
    val = obj.get(components[0])
    if val is None:
      return

    if len(components) == 1:
      obj[components[0]] = func(val)
    else:
      _ApplyTransformation(components[1:], func, val)

  elif isinstance(obj, list) and isinstance(components[0], _Index):
    idx = components[0]
    if idx > len(obj) - 1:
      return

    if len(components) == 1:
      obj[idx] = func(obj[idx])
    else:
      _ApplyTransformation(components[1:], func, obj[idx])

  elif isinstance(obj, list) and isinstance(components[0], _Slice):
    for i, val in enumerate(obj):
      if len(components) == 1:
        obj[i] = func(val)
      else:
        _ApplyTransformation(components[1:], func, val)


class PropertySelector(object):
  """Extracts and/or transforms values in JSON-serializable dicts.

  For example:

      selector = PropertySelector(
          properties=['x.y', 'y[0]'],
          transformations=[
              ('x.y', lambda x: x + 5),
              ('y[]', lambda x: x * 5),
      ])
      selector.SelectProperties(
          {'x': {'y': 1, 'z': 2}, 'y': [1, 2, 3]})

  returns:

      collections.OrderedDict([
          ('x', collections.OrderedDict([('y', 6)])),
          ('y', [5])
      ])

  Items are extracted in the order requested. Transformations are applied
  in the order they appear.
  """

  def __init__(self, properties=None, transformations=None):
    """Creates a new PropertySelector with the given properties."""
    if properties:
      self._compiled_properties = [_Parse(p) for p in properties]
    else:
      self._compiled_properties = None

    if transformations:
      self._compiled_transformations = [
          (_Parse(p), func) for p, func in transformations]
    else:
      self._compiled_transformations = None

    self.properties = properties
    self.transformations = transformations

  def Apply(self, obj):
    """An OrderedDict resulting from filtering and transforming obj."""
    if self._compiled_properties:
      res = _Filter(obj, self._compiled_properties) or collections.OrderedDict()
    else:
      res = _DictToOrderedDict(obj)

    if self._compiled_transformations:
      for compiled_property, func in self._compiled_transformations:
        _ApplyTransformation(compiled_property, func, res)

    return res


class PropertyGetter(object):
  """Extracts a single field from JSON-serializable dicts.

  For example:

      getter = PropertyGetter('x.y')
      getter.Get({'x': {'y': 1, 'z': 2}, 'y': [1, 2, 3]})

  returns:

      1
  """

  def __init__(self, p):
    """Creates a new PropertyGetter with the given property."""
    self._compiled_property = _Parse(p)

  def Get(self, obj):
    """Returns the property in obj or None if the property does not exist."""
    return copy.deepcopy(_GetProperty(obj, self._compiled_property))
