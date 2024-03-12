# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Collection of classes for converting and transforming an input dictionary.

Conversions are defined statically using subclasses of SchemaField (Message,
Value, RepeatedField) which transform a source dictionary input to the target
schema. The source dictionary is expected to be parsed from a JSON
representation.

Only fields listed in the schema will be converted (i.e. an allowlist).
A SchemaField is a recursive structure and employs the visitor pattern to
convert an input structure.

# Schema to use for transformation
SAMPLE_SCHEMA = Message(
    foo=Value(target_name='bar'),
    list_of_things=RepeatedField(target_name='bar_list_of_things',
                                 element=Value()))

# Input dictionary:
input_dict = {
    'foo': '1234',
    'list_of_things': [1, 4, 5],
    'some_other_field': "hello"
}

# To convert:
result = SAMPLE_SCHEMA.ConvertValue(input_dict)

# The resulting dictionary will be:
{
    'bar': '1234',
    'bar_list_of_things': [1, 4, 5]
}

Note that both fields were renamed according to the rules in the schema. Fields
not listed in the schema will not be copied. In this example, "some_other_field"
was not copied.

If further transformation is required on the value itself, a converter can be
specified, which is simply a function which takes an input value and transforms
it according to whatever logic it wants.

For example, to convert a string value to an integer value, one could construct
a schema as follows:
CONVERTER_SCHEMA = Message(
    foo=Value(target_name='bar', converter=int))

Using the above input dictionary, the result would be:
{
    'bar': 1234
}
"""

from __future__ import absolute_import
import logging

from googlecloudsdk.third_party.appengine.admin.tools.conversion import converters

# TODO(user) Better error handling patterns.


def UnderscoreToLowerCamelCase(text):
  """Convert underscores to lower camel case (e.g. 'foo_bar' --> 'fooBar')."""
  parts = text.lower().split('_')
  return parts[0] + ''.join(part.capitalize() for part in parts[1:])


def ValidateType(source_value, expected_type):
  if not isinstance(source_value, expected_type):
    raise ValueError(
        'Expected a %s, but got %s for value %s' % (expected_type,
                                                    type(source_value),
                                                    source_value))


def ValidateNotType(source_value, non_expected_type):
  if isinstance(source_value, non_expected_type):
    raise ValueError(
        'Did not expect %s for value %s' % (non_expected_type, source_value))


def MergeDictionaryValues(old_dict, new_dict):
  """Attempts to merge the given dictionaries.

  Warns if a key exists with different values in both dictionaries. In this
  case, the new_dict value trumps the previous value.

  Args:
    old_dict: Existing dictionary.
    new_dict: New dictionary.

  Returns:
    Result of merging the two dictionaries.

  Raises:
    ValueError: If the keys in each dictionary are not unique.
  """
  common_keys = set(old_dict) & set(new_dict)
  if common_keys:
    conflicting_keys = set(key for key in common_keys
                           if old_dict[key] != new_dict[key])
    if conflicting_keys:
      def FormatKey(key):
        return ('\'{key}\' has conflicting values \'{old}\' and \'{new}\'. '
                'Using \'{new}\'.').format(key=key,
                                           old=old_dict[key],
                                           new=new_dict[key])
      for conflicting_key in conflicting_keys:
        logging.warning(FormatKey(conflicting_key))
  result = old_dict.copy()
  result.update(new_dict)
  return result


class SchemaField(object):
  """Transformation strategy from input dictionary to an output dictionary.

  Each subclass defines a different strategy for how an input value is converted
  to an output value. ConvertValue() makes a copy of the input with the proper
  transformations applied. Additionally, constraints about the input structure
  are validated while doing the transformation.
  """

  def __init__(self, target_name=None, converter=None):
    """Constructor.

    Args:
      target_name: New field name to use when creating an output dictionary. If
        None is specified, then the original name is used.
      converter: A function which performs a transformation on the value of the
        field.
    """
    self.target_name = target_name
    self.converter = converter

  def ConvertValue(self, value):
    """Convert an input value using the given schema and converter.

    This method is not meant to be overwritten. Update _VisitInternal to change
    the behavior.

    Args:
      value: Input value.

    Returns:
      Output which has been transformed using the given schema for renaming and
      converter, if specified.
    """
    result = self._VisitInternal(value)
    return self._PerformConversion(result)

  def _VisitInternal(self, value):
    """Shuffles the input value using the renames specified in the schema.

    Only structural changes are made (e.g. renaming keys, copying lists, etc.).
    Subclasses are expected to override this.

    Args:
      value: Input value.

    Returns:
      Output which has been transformed using the given schema.
    """
    raise NotImplementedError()

  def _PerformConversion(self, result):
    """Transforms the result value if a converter is specified."""
    return self.converter(result) if self.converter else result


class Message(SchemaField):
  """A message has a collection of fields which should be converted.

  Expected input type: Dictionary
  Output type: Dictionary
  """

  def __init__(self, target_name=None, converter=None, **kwargs):
    """Constructor.

    Args:
      target_name: New field name to use when creating an output dictionary. If
        None is specified, then the original name is used.
      converter: A function which performs a transformation on the value of the
        field.
      **kwargs: Kwargs where the keys are names of the fields and values are
        FieldSchemas for each child field.

    Raises:
      ValueError: If the message has no child fields specified.
    """
    super(Message, self).__init__(target_name, converter)
    self.fields = kwargs
    if not self.fields:
      raise ValueError('Message must contain fields')

  def _VisitInternal(self, value):
    """Convert each child field and put the result in a new dictionary."""
    ValidateType(value, dict)
    result = {}
    for source_key, field_schema in self.fields.items():
      if source_key not in value:
        continue

      source_value = value[source_key]
      target_key = field_schema.target_name or source_key
      target_key = UnderscoreToLowerCamelCase(target_key)

      result_value = field_schema.ConvertValue(source_value)
      if target_key not in result:
        result[target_key] = result_value
      # Only know how to merge dicts right now.
      elif isinstance(result[target_key], dict) and isinstance(result_value,
                                                               dict):
        result[target_key] = MergeDictionaryValues(result[target_key],
                                                   result_value)
      else:
        raise ValueError('Target key "%s" already exists.' % target_key)

    return result


class Value(SchemaField):
  """Represents a leaf node. Only the value itself is copied.

  A primitive value corresponds to any non-string, non-dictionary value which
  can be represented in JSON.

  Expected input type: Primitive value type (int, string, boolean, etc.).
  Output type: Same primitive value type.
  """

  def _VisitInternal(self, value):
    ValidateNotType(value, list)
    ValidateNotType(value, dict)
    return value


class Map(SchemaField):
  """Represents a leaf node where the value itself is a map.

  Expected input type: Dictionary
  Output type: Dictionary
  """

  def __init__(self, target_name=None, converter=None,
               key_converter=converters.ToJsonString,
               value_converter=converters.ToJsonString):
    """Constructor.

    Args:
      target_name: New field name to use when creating an output dictionary. If
        None is specified, then the original name is used.
      converter: A function which performs a transformation on the value of the
        field.
      key_converter: A function which performs a transformation on the keys.
      value_converter: A function which performs a transformation on the values.
    """
    super(Map, self).__init__(target_name, converter)
    self.key_converter = key_converter
    self.value_converter = value_converter

  def _VisitInternal(self, value):
    ValidateType(value, dict)
    result = {}
    for key, dict_value in value.items():
      if self.key_converter:
        key = self.key_converter(key)
      if self.value_converter:
        dict_value = self.value_converter(dict_value)
      result[key] = dict_value

    return result


class RepeatedField(SchemaField):
  """Represents a list of nested elements. Each item in the list is copied.

  The type of each element in the list is specified in the constructor.

  Expected input type: List
  Output type: List
  """

  def __init__(self, target_name=None, converter=None, element=None):
    """Constructor.

    Args:
      target_name: New field name to use when creating an output dictionary. If
        None is specified, then the original name is used.
      converter: A function which performs a transformation on the value of the
        field.
      element: A SchemaField element defining the type of every element in the
        list. The input structure is expected to be homogenous.

    Raises:
      ValueError: If an element has not been specified or if the element type is
      incompatible with a repeated field.
    """
    super(RepeatedField, self).__init__(target_name, converter)
    self.element = element

    if not self.element:
      raise ValueError('Element required for a repeated field')

    if isinstance(self.element, Map):
      raise ValueError('Repeated maps are not supported')

  def _VisitInternal(self, value):
    ValidateType(value, list)
    result = []
    for item in value:
      result.append(self.element.ConvertValue(item))
    return result
