# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Resource property Get."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import re

import six
from six.moves import range  # pylint: disable=redefined-builtin


_SNAKE_RE = re.compile(
    '((?<=[a-z0-9])[A-Z]+(?=[A-Z][a-z]|$)|(?!^)[A-Z](?=[a-z]))')


def _GetMetaDict(items, key, value):
  """Gets the dict in items that contains key==value.

  A metadict object is a list of dicts of the form:
    [
      {key: value-1, ...},
      {key: value-2, ...},
      ...
    ]

  Args:
    items: A list of dicts.
    key: The dict key name.
    value: The dict key value.

  Returns:
    The dict in items that contains key==value or None if no match or not a
    metadict.
  """
  try:
    for item in items:
      if item.get(key) == value:
        return item
  except (AttributeError, IndexError, TypeError, ValueError):
    pass
  return None


def _GetMetaDataValue(items, name, deserialize=False):
  """Gets the metadata value for the item in items with key == name.

  A metadata object is a list of dicts of the form:
    [
      {'key': key-name-1, 'value': field-1-value-string},
      {'key': key-name-2, 'value': field-2-value-string},
      ...
    ]

  Examples:
    x.metadata[windows-keys].email
      Deserializes the 'windows-keys' metadata value and gets the email value.
    x.metadata[windows-keys]
      Gets the 'windows-key' metadata string value.
    x.metadata[windows-keys][]
      Gets the deserialized 'windows-key' metadata value.

  Args:
    items: The metadata items list.
    name: The metadata name (which must match one of the 'key' values).
    deserialize: If True then attempt to deserialize a compact JSON string.

  Returns:
    The metadata value for name or None if not found or if items is not a
    metadata dict list.
  """
  item = _GetMetaDict(items, 'key', name)
  if item is None:
    return None
  value = item.get('value', None)
  if deserialize:
    try:
      return json.loads(value)
    except (TypeError, ValueError):
      pass
  return value


def ConvertToCamelCase(name):
  """Converts snake_case name to camelCase."""
  part = name.split('_')
  return part[0] + ''.join(x.title() for x in part[1:])


def ConvertToSnakeCase(name):
  """Converts camelCase name to snake_case."""
  return _SNAKE_RE.sub(r'_\1', name).lower()


def ConvertToAngrySnakeCase(name):
  """Converts camelCase name to ANGRY_SNAKE_CASE."""
  return _SNAKE_RE.sub(r'_\1', name).upper()


def GetMatchingIndex(index, func):
  """Returns index converted to a case that satisfies func."""
  if func(index):
    return index
  if not isinstance(index, six.string_types):
    return None
  for convert in [ConvertToCamelCase, ConvertToSnakeCase]:
    name = convert(index)
    if func(name):
      return name
  return None


def GetMatchingIndexValue(index, func):
  """Returns the first non-None func value for case-converted index."""
  value = func(index)
  if value:
    return value
  if not isinstance(index, six.string_types):
    return None
  for convert in [ConvertToCamelCase, ConvertToSnakeCase]:
    value = func(convert(index))
    if value:
      return value
  return None


def GetMessageFieldType(resource_key, message):
  """Returns the messages module type for key in message and the actual key.

  Handles camelCase/snake_case key name variants for OnePlatform compatibility.
  Indices and slices in resource_key are ignored -- they are not needed for
  repeated field queries.

  Args:
    resource_key: Ordered list of key names/indices, applied left to right. Each
      element in the list may be one of:
        str - A resource property name. This could be a class attribute name or
          a dict index.
        int - A list index. Selects one member is the list. Negative indices
          count from the end of the list, starting with -1 for the last element
          in the list. An out of bounds index is not an error; it produces the
          value None.
        None - A list slice. Selects all members of a list or dict like object.
          A slice of an empty dict or list is an empty dict or list.
    message: The known proto message type if not None.

  Raises:
    KeyError: If key is not in message.

  Returns:
    (type, actual_key), the messages module type for key in message and the
      actual key (names in the proper case, indices omitted).
  """
  actual_key = []
  for name in resource_key:
    if not isinstance(name, six.string_types):
      # Ignore indices and slices.
      continue
    for convert in (lambda x: x, ConvertToCamelCase, ConvertToSnakeCase):
      actual_name = convert(name)
      try:
        message = message.field_by_name(actual_name).type
      except (AttributeError, KeyError):
        pass
      else:
        break
    else:
      raise KeyError('Field {} not in message.'.format(name))
    actual_key.append(actual_name)
  if message == six.integer_types:
    # A distinction we don't need, especially since python 3 only has "int".
    # Also, dealing with a type tuple is a pain for callers.
    message = int
  return message, actual_key


def LookupField(resource_key, fields):
  """Returns the actual_key match of resource_key in fields.

  Handles camelCase/snake_case key name variants for OnePlatform compatibility.
  Indices and slices in resource_key are ignored to normalize the lookup. This
  means that the lookup can determine the existence of an attribute name, but
  not a specific value among all repeated values.

  Args:
    resource_key: Ordered list of key names/indices, applied left to right. Each
      element in the list may be one of:
        str - A resource property name. This could be a class attribute name or
          a dict index.
        int - A list index. Selects one member is the list. Negative indices
          count from the end of the list, starting with -1 for the last element
          in the list. An out of bounds index is not an error; it produces the
          value None.
        None - A list slice. Selects all members of a list or dict like object.
          A slice of an empty dict or list is an empty dict or list.
    fields: The set of dotted field names to match against.

  Returns:
    The actual_key match of resource_key in fields or None if no match.
  """
  for convert in (lambda x: x, ConvertToCamelCase, ConvertToSnakeCase):
    actual_key = [convert(name) if isinstance(name, six.string_types) else name
                  for name in resource_key]
    lookup_key = '.'.join([name for name in actual_key
                           if isinstance(name, six.string_types)])
    if lookup_key in fields:
      return actual_key
  return None


def Get(resource_obj, resource_key, default=None):
  """Gets the value referenced by key in the object resource.

  Since it is common for resource instances to be sparse it is not an error if
  a key is not present in a particular resource instance, or if an index does
  not match the resource type.

  Args:
    resource_obj: The resource object possibly containing a value for key.
    resource_key: Ordered list of key names/indices, applied left to right. Each
      element in the list may be one of:
        str - A resource property name. This could be a class attribute name or
          a dict index.
        int - A list index. Selects one member is the list. Negative indices
          count from the end of the list, starting with -1 for the last element
          in the list. An out of bounds index is not an error; it produces the
          value None.
        None - A list slice. Selects all members of a list or dict like object.
          A slice of an empty dict or list is an empty dict or list.
    default: Get() returns this value if key is not in resource.

  Returns:
    The value, None if any of the given keys are not found. This is
      intentionally not an error. In this context a value can be any data
      object: dict, list, tuple, class, str, int, float, ...
  """
  key = list(resource_key)
  resource = resource_obj
  while key:

    # Get the next key index. Some iterations may access the next key.
    index = key.pop(0)

    # Serialized sets are sorted lists.
    if isinstance(resource, set):
      resource = sorted(resource)

    # This if ordering checks builtin object attributes last. For
    # example, with resource = {'items': ...}, Get() treats 'items' as a dict
    # key rather than the builtin 'items' attribute of resource.

    if resource is None:
      # None is different than an empty dict or list.
      return default

    if hasattr(resource, 'items'):
      # dict-like
      if index is None:
        if key:
          # Inner slice: *.[].*
          return [Get(resource, [k] + key, default) for k in resource]
        # Trailing slice: *.[]
        return resource

      name = GetMatchingIndex(index, lambda x: x in resource)
      if name:
        resource = resource[name]
        continue

      if 'items' in resource:
        # It would be nice if there were a better metadata indicator.
        # _GetMetaDataValue() returns None if resource['items'] isn't really
        # metadata, so there is a bit more verification than just 'items' in
        # resource.

        def _GetValue(index):
          # pylint: disable=cell-var-from-loop
          return _GetMetaDataValue(
              resource['items'], index, deserialize=bool(key))

        resource = GetMatchingIndexValue(index, _GetValue)
        continue

      return default

    if isinstance(index, six.string_types):
      # class-like?
      name = GetMatchingIndex(index, lambda x: hasattr(resource, x))
      if name:
        r = getattr(resource, name, default)
        if not callable(r):
          resource = r
          continue

    if hasattr(resource, '__iter__') or isinstance(resource, six.string_types):
      # list-like
      if index is None:
        if key:
          # explicit inner slice: *.[].*
          return [Get(resource, [k] + key, default)
                  for k in range(len(resource))]
        # explicit trailing slice: *.[]
        return resource

      if not isinstance(index, six.integer_types):
        if isinstance(index, six.string_types) and isinstance(resource, list):
          if len(resource) and isinstance(resource[0], dict):
            if key:
              # See the _GetMetaDict docstring for the proto meta dict layout.
              r = _GetMetaDict(resource, index, key[0])
              if r is not None:
                # meta-dict-like
                resource = r
                index = key.pop(0)
                continue
            else:
              # Handle leaf node [{'key': k, 'value': v}, ...] metadata to
              # support r.k:v filter terms.
              r = _GetMetaDataValue(resource, index)
              if r is not None:
                return r
            if index in resource[0]:
              # implicit inner slice
              # resource is a list. An explicit reference would be
              # "resource[].foo" which would be caught above. Implicit
              # "resource.foo" references are handled here.
              return [Get(resource, [k, index] + key, default)
                      for k in range(len(resource))]

            # This is the last chance for index. If we fell through the index
            # would be ignored and the resource would be returned (incorrect).
            # Instead we return the list of non-None index values from the list
            # of dicts. See
            # resource_property_test.PropertyGetTest.testGetLastDictSlice for
            # an example.
            return ([f for f in [d.get(index) for d in resource] if f]
                    or default)

        # Index mismatch.
        return default

      if index in range(-len(resource), len(resource)):
        resource = resource[index]
        continue

    # Resource or index mismatch.
    return default

  # Sets serialize to sorted lists.
  if isinstance(resource, set):
    resource = sorted(resource)

  return resource


def ResourceContainsKey(resource, key):
  """True if resource contains key, else False."""
  return Get(resource, key, None) is not None


def EvaluateGlobalRestriction(resource, restriction, pattern):
  """Returns True if any attribute value in resource matches the RE pattern.

  This function is called to evaluate a global restriction on a resource. For
  example, --filter="Foo.Bar" results in a call like this on each resource item:

    resource_property.EvaluateGlobalRestriction(
      resource,
      'Foo.Bar',
      re.compile(re.escape('Foo.Bar'), re.IGNORECASE),
    )

  Args:
    resource: The object to check.
    restriction: The global restriction string.
    pattern: The global restriction pattern for matcing resource values.

  Returns:
    True if any attribute value in resource matches the RE pattern.
  """
  if not resource:
    return False
  if isinstance(resource, six.string_types):
    try:
      return bool(pattern.search(resource))
    except TypeError:
      pass
  if isinstance(resource, (float, int)):
    try:
      return bool(pattern.search(str(resource)))
    except TypeError:
      pass
  try:
    for key, value in six.iteritems(resource):
      if not key.startswith('_') and EvaluateGlobalRestriction(
          value, restriction, pattern):
        return True
  except AttributeError:
    try:
      for value in resource:
        if EvaluateGlobalRestriction(value, restriction, pattern):
          return True
      return False
    except TypeError:
      pass
  try:
    for key, value in six.iteritems(resource.__dict__):
      if not key.startswith('_') and EvaluateGlobalRestriction(
          value, restriction, pattern):
        return True
  except AttributeError:
    pass
  return False


def IsListLike(resource):
  """Checks if resource is a list-like iterable object.

  Args:
    resource: The object to check.

  Returns:
    True if resource is a list-like iterable object.
  """
  return (isinstance(resource, list) or
          (hasattr(resource, '__iter__') and
           (hasattr(resource, 'next') or hasattr(resource, '__next__'))))
