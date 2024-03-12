# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Module for loading location/value YAML objects.

ruamel round trip loading splices, if possible, an lc attribute to each
data item, where lc.line and lc.col are the YAML source line and column for the
data. "if possible" leaves a lot to be desired. Without Python shenanigans it
does not work for str, bool, int or float values. Shenanigans only get str
values to work.

The location/value loader defined here effectively subclasses the following
object in every data item:

  Attributes:
    value: The data value.
    lc.line: The data value YAML source line.
    lc.col: The data value YAML source column.

"effectively" because we do similar Python shenanigans when it's easy.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from ruamel import yaml

import six


class _LvString(yaml.scalarstring.ScalarString):
  """Location/value string type."""

  __slots__ = ('lc', 'value')
  style = ''

  def __new__(cls, value):
    return yaml.scalarstring.ScalarString.__new__(cls, value)


class _LvPreservedScalarString(yaml.scalarstring.PreservedScalarString):
  """Location/value preserved scalar string type."""

  __slots__ = ('lc', 'value')


class _LvDoubleQuotedScalarString(yaml.scalarstring.DoubleQuotedScalarString):
  """Location/value double quoted scalar string type."""

  __slots__ = ('lc', 'value')


class _LvSingleQuotedScalarString(yaml.scalarstring.SingleQuotedScalarString):
  """Location/value single quoted scalar string type."""

  __slots__ = ('lc', 'value')


class _LvObjectConstructor(yaml.constructor.RoundTripConstructor):
  """Location/value object constructor that works for all types.

  The object has these attributes:
    lc.line: The start line of the value in the input file.
    lc.col: The start column of the value in the input file.
    value: The value.
  """

  _initialized = False

  def __init__(self, *args, **kwargs):
    super(_LvObjectConstructor, self).__init__(*args, **kwargs)
    self._Initialize()

  @classmethod
  def _Initialize(cls):
    if not cls._initialized:
      cls._initialized = True
      cls.add_constructor('tag:yaml.org,2002:null', cls.construct_yaml_null)
      cls.add_constructor('tag:yaml.org,2002:bool', cls.construct_yaml_bool)
      cls.add_constructor('tag:yaml.org,2002:int', cls.construct_yaml_int)
      cls.add_constructor('tag:yaml.org,2002:float', cls.construct_yaml_float)
      cls.add_constructor('tag:yaml.org,2002:map', cls.construct_yaml_map)
      cls.add_constructor('tag:yaml.org,2002:omap', cls.construct_yaml_omap)
      cls.add_constructor('tag:yaml.org,2002:seq', cls.construct_yaml_seq)

  def _ScalarType(self, node):
    if isinstance(node.value, six.string_types):
      if node.style == '|':
        return _LvPreservedScalarString(node.value)
      if self._preserve_quotes:
        if node.style == "'":
          return _LvSingleQuotedScalarString(node.value)
        if node.style == '"':
          return _LvDoubleQuotedScalarString(node.value)
    return _LvString(node.value)

  def _ScalarObject(self, node, value, raw=False):
    if not isinstance(node, yaml.nodes.ScalarNode):
      raise yaml.constructor.ConstructorError(
          None, None,
          'expected a scalar node, but found {}'.format(node.id),
          node.start_mark)

    ret_val = node.value if raw else self._ScalarType(node)
    ret_val.lc = yaml.comments.LineCol()
    ret_val.lc.line = node.start_mark.line
    ret_val.lc.col = node.start_mark.column
    ret_val.value = value

    return ret_val

  def construct_scalar(self, node):
    return self._ScalarObject(node, node.value)

  def construct_yaml_null(self, node):
    return self._ScalarObject(node, None)

  def construct_yaml_bool(self, node):
    return self._ScalarObject(node, node.value.lower() == 'true')

  def construct_yaml_int(self, node):
    return self._ScalarObject(node, int(node.value))

  def construct_yaml_float(self, node):
    return self._ScalarObject(node, float(node.value))

  def construct_yaml_map(self, node):
    # The super method is a generator.
    ret_val = list(
        super(_LvObjectConstructor, self).construct_yaml_map(node))[0]
    ret_val.value = ret_val
    return ret_val

  def construct_yaml_omap(self, node):
    # The super method is a generator.
    ret_val = list(
        super(_LvObjectConstructor, self).construct_yaml_omap(node))[0]
    ret_val.value = ret_val
    return ret_val

  def construct_yaml_seq(self, node):
    # The super method is a generator.
    ret_val = list(
        super(_LvObjectConstructor, self).construct_yaml_seq(node))[0]
    ret_val.value = ret_val
    return ret_val


def LocationValueLoad(source):
  """Loads location/value objects from YAML source.

  Call this indirectly by:

    core.yaml.load(source, location_value=True)

  Args:
    source: A file like object or string containing YAML data.

  Returns:
    The YAML data, where each data item is an object with value and lc
    attributes, where lc.line and lc.col are the line and column location for
    the item in the YAML source file.
  """

  yml = yaml.YAML()
  yml.Constructor = _LvObjectConstructor
  return yml.load(source)
