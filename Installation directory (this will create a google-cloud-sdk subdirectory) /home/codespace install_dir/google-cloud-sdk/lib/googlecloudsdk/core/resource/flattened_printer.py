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

"""Flattened tree resource printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_lex
from googlecloudsdk.core.resource import resource_printer_base
from googlecloudsdk.core.resource import resource_transform

import six


def _Flatten(obj, labels):
  """Flattens a JSON-serializable object into a list of tuples.

  The first element of each tuple will be a key and the second element
  will be a simple value.

  For example, _Flatten({'a': ['hello', 'world'], 'b': {'x': 'bye'}})
  will produce:

    [
        ('a[0]', 'hello'),
        ('a[1]', 'world'),
        ('b.x', 'bye'),
    ]

  Args:
    obj: A JSON-serializable object.
    labels: An object mapping keys to projection labels.

  Returns:
    A list of tuples.
  """
  res = []

  def AppendResult(name, result):
    """Appends key/value pairs from obj into res.

    Adds projection label if defined.

    Args:
      name: Name of key.
      result: Value of key in obj.
    """
    use_legacy = properties.VALUES.core.use_legacy_flattened_format.GetBool()
    if not use_legacy and labels and name in labels:
      res.append((labels[name].lower(), result))
    else:
      res.append((name, result))

  def Flatten(obj, name, res):
    """Recursively appends keys in path from obj into res.

    Args:
      obj: The object to flatten.
      name: The key name of the current obj.
      res: The ordered result value list.
    """
    if isinstance(obj, list):
      if obj:
        for i, item in enumerate(obj):
          Flatten(item, '{name}[{index}]'.format(name=name, index=i), res)
      else:
        AppendResult(name, [])
    elif isinstance(obj, dict):
      if obj:
        for k, v in sorted(six.iteritems(obj)):
          Flatten(v, '{name}{dot}{key}'.format(
              name=name, dot='.' if name else '', key=k), res)
      else:
        AppendResult(name, {})
    elif isinstance(obj, float):
      AppendResult(name, resource_transform.TransformFloat(obj))
    else:
      AppendResult(name, obj)

  Flatten(obj, '', res)
  return res


def _StringQuote(s, quote='"', escape='\\'):
  """Returns <quote>s<quote> with <escape> and <quote> in s escaped.

  s.encode('string-escape') does not work with type(s) == unicode.

  Args:
    s: The string to quote.
    quote: The outer quote character.
    escape: The enclosed escape character.

  Returns:
    <quote>s<quote> with <escape> and <quote> in s escaped.
  """
  entity = {'\f': '\\f', '\n': '\\n', '\r': '\\r', '\t': '\\t'}
  chars = []
  if quote:
    chars.append(quote)
  for c in s:
    if c in (escape, quote):
      chars.append(escape)
    elif c in entity:
      c = entity[c]
    chars.append(c)
  if quote:
    chars.append(quote)
  return ''.join(chars)


class FlattenedPrinter(resource_printer_base.ResourcePrinter):
  """Prints a flattened tree representation of JSON-serializable objects.

  A flattened tree. Each output line contains one *key*:*value* pair.

  Printer attributes:
    no-pad: Don't print space after the separator. The default adjusts the
      space to align the values into the same output column. Use *no-pad*
      for comparing resource outputs.
    separator=_SEPARATOR_: Print _SEPARATOR_ between the *key* and *value*.
      The default is ": ".

  For example:

    printer = resource_printer.Printer('flattened', out=sys.stdout)
    printer.AddRecord({'a': ['hello', 'world'], 'b': {'x': 'bye'}})

  produces:

    ---
    a[0]: hello
    a[1]: world
    b.x:  bye
  """

  def __init__(self, *args, **kwargs):
    super(FlattenedPrinter, self).__init__(*args, retain_none_values=False,
                                           **kwargs)

  def _LabelsByKey(self):
    """Returns an object that maps keys to projection labels.

    Returns:
      An object of keys to projection labels, None if all labels are empty.
    """
    labels = {}
    for c in self.column_attributes.Columns():
      key_name = resource_lex.GetKeyName(c.key)
      labels[key_name] = c.attribute.label
    return labels if any(labels) else None

  def _AddRecord(self, record, delimit=True):
    """Immediately prints the record as flattened a flattened tree.

    Args:
      record: A JSON-serializable object.
      delimit: Prints resource delimiters if True.
    """
    if delimit:
      self._out.write('---\n')
    labels = self._LabelsByKey()
    flattened_record = _Flatten(record, labels)
    if flattened_record:
      pad = 'no-pad' not in self.attributes
      separator = self.attributes.get('separator', ': ')
      if pad:
        max_key_len = max(len(key) for key, _ in flattened_record)
      for key, value in flattened_record:
        self._out.write(key)
        self._out.write(separator)
        if pad:
          self._out.write(' ' * (max_key_len - len(key)))
        val = six.text_type(value)
        # Value must be one text line with leading/trailing space quoted.
        if '\n' in val or val[0:1].isspace() or val[-1:].isspace():
          val = _StringQuote(val)
        self._out.write(val + '\n')
