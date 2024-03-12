# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Functions for parsing SQL query parameters from the command line."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import json
from googlecloudsdk.api_lib.dataflow import exceptions
from googlecloudsdk.core.util import files
import six


def ParseParametersFile(path):
  """Reads a JSON file specified by path and returns its contents as a string."""
  with files.FileReader(path) as parameters_file:
    parameters = json.load(parameters_file)
    # Dict order only matters for predictable test output.
    results = [
        collections.OrderedDict(sorted(param.items())) for param in parameters
    ]
    return json.dumps(results)


def ParseParametersList(parameters):
  """Parses a list of parameters.

  Arguments:
    parameters: A list of parameter strings with the format name:type:value,
      for example min_word_count:INT64:250.

  Returns:
    A JSON string containing the parameters.
  """
  results = []
  for parameter in parameters:
    results.append(_ParseParameter(parameter))
  return json.dumps(results)


def _SplitParam(param_string):
  split = param_string.split(':', 1)
  if len(split) != 2:
    raise exceptions.Error(
        'Query parameters must be of the form: '
        '"name:type:value", ":type:value", or "name::value". '
        'An empty name produces a positional parameter. '
        'An empty type produces a STRING parameter.')
  return split


def _ParseParameter(param_string):
  name, param_string = _SplitParam(param_string)
  type_dict, value_dict = _ParseParameterTypeAndValue(param_string)
  result = collections.OrderedDict()
  if name:
    result['name'] = name
  result['parameterType'] = type_dict
  result['parameterValue'] = value_dict
  return result


def _ParseParameterTypeAndValue(param_string):
  """Parse a string of the form <recursive_type>:<value> into each part."""
  type_string, value_string = _SplitParam(param_string)
  if not type_string:
    type_string = 'STRING'
  type_dict = _ParseParameterType(type_string)
  return type_dict, _ParseParameterValue(type_dict, value_string)


def _ParseParameterType(type_string):
  """Parse a parameter type string into a JSON dict for the DF SQL launcher."""
  type_dict = {'type': type_string.upper()}
  if type_string.upper().startswith('ARRAY<') and type_string.endswith('>'):
    type_dict = collections.OrderedDict([
        ('arrayType', _ParseParameterType(type_string[6:-1])), ('type', 'ARRAY')
    ])
  if type_string.startswith('STRUCT<') and type_string.endswith('>'):
    type_dict = collections.OrderedDict([('structTypes',
                                          _ParseStructType(type_string[7:-1])),
                                         ('type', 'STRUCT')])
  if not type_string:
    raise exceptions.Error('Query parameter missing type')
  return type_dict


def _ParseStructType(type_string):
  """Parse a Struct QueryParameter type into a JSON dict form."""
  subtypes = []
  for name, sub_type in _StructTypeSplit(type_string):
    entry = collections.OrderedDict([('name', name),
                                     ('type', _ParseParameterType(sub_type))])
    subtypes.append(entry)
  return subtypes


def _StructTypeSplit(type_string):
  """Yields single field-name, sub-types tuple from a StructType string."""
  while type_string:
    next_span = type_string.split(',', 1)[0]
    if '<' in next_span:
      angle_count = 0
      i = 0
      for i in range(next_span.find('<'), len(type_string)):
        if type_string[i] == '<':
          angle_count += 1
        if type_string[i] == '>':
          angle_count -= 1
        if angle_count == 0:
          break
      if angle_count != 0:
        raise exceptions.Error('Malformatted struct type')
      next_span = type_string[:i + 1]
    type_string = type_string[len(next_span) + 1:]
    splits = next_span.split(None, 1)
    if len(splits) != 2:
      raise exceptions.Error('Struct parameter missing name for field')
    yield splits


def _IsString(val):
  try:
    # Python 2
    return isinstance(val, unicode)
  except NameError:
    return isinstance(val, str)


def _ParseParameterValue(type_dict, value_input):
  """Parse a parameter value of type `type_dict` from value_input.

  Arguments:
    type_dict: The JSON-dict type as which to parse `value_input`.
    value_input: Either a string representing the value, or a JSON dict for
      array and value types.

  Returns:
    A dict with one of value, arrayValues, or structValues populated depending
    on the type.

  """
  if 'structTypes' in type_dict:
    if _IsString(value_input):
      if value_input == 'NULL':
        return {'structValues': None}
      value_input = json.loads(value_input)
    value_input = collections.OrderedDict(sorted(value_input.items()))
    type_map = collections.OrderedDict([
        (x['name'], x['type']) for x in type_dict['structTypes']
    ])
    values = collections.OrderedDict()
    for (field_name, value) in six.iteritems(value_input):
      values[field_name] = _ParseParameterValue(type_map[field_name], value)
    return {'structValues': values}
  if 'arrayType' in type_dict:
    if _IsString(value_input):
      if value_input == 'NULL':
        return {'arrayValues': None}
      value_input = json.loads(value_input)
    values = [
        _ParseParameterValue(type_dict['arrayType'], x) for x in value_input
    ]
    return {'arrayValues': values}
  return {'value': value_input if value_input != 'NULL' else None}
