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

"""JSON format resource printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.core.resource import resource_printer_base

import six


class JsonPrinter(resource_printer_base.ResourcePrinter):
  """Prints resource records as a JSON list.

  [JSON](http://www.json.org), JavaScript Object Notation.

  Printer attributes:
    no-undefined: Does not display resource data items with null values.

  Attributes:
    _buffer: Buffer stream for record item indentation.
    _delimiter: Delimiter string before the next record.
    _empty: True if no records were output.
    _indent: Resource item indentation.
  """

  # json.dump() does not have a streaming mode. In order to print a resource`
  # list it requires the complete list contents. To get around that limitation
  # and print each resource list item, _AddRecord() prints the initial "[", the
  # intervening ",", the final "]", captures the json.dump() output for each
  # resource list item and prints it indented by STRUCTURED_INDENTATION spaces.

  _BEGIN_DELIMITER = '[\n'

  def __init__(self, *args, **kwargs):
    super(JsonPrinter, self).__init__(*args, retain_none_values=True, **kwargs)
    self._empty = True
    self._delimiter = self._BEGIN_DELIMITER
    self._indent = ' ' * resource_printer_base.STRUCTURED_INDENTATION

  def __Dump(self, resource):
    data = json.dumps(
        resource,
        ensure_ascii=False,
        indent=resource_printer_base.STRUCTURED_INDENTATION,
        separators=(',', ': '),
        sort_keys=True)
    # In python 3, json.dumps returns a unicode string regardless of the value
    # for ensure_ascii. In python 2, things are messy. It returns unicode
    # string when ensure_ascii=False and there are unicode characters in the
    # result. Otherwise, it will return a python 2 str. Here, we make the
    # behavior consistent.
    return six.text_type(data)

  def _AddRecord(self, record, delimit=True):
    """Prints one element of a JSON-serializable Python object resource list.

    Allows intermingled delimit=True and delimit=False.

    Args:
      record: A JSON-serializable object.
      delimit: Dump one record if False, used by PrintSingleRecord().
    """
    self._empty = False
    output = self.__Dump(record)
    if delimit:
      delimiter = self._delimiter + self._indent
      self._delimiter = ',\n'
      for line in output.split('\n'):
        self._out.write(delimiter + line)
        delimiter = '\n' + self._indent
    else:
      if self._delimiter != self._BEGIN_DELIMITER:
        self._out.write('\n]\n')
        self._delimiter = self._BEGIN_DELIMITER
      self._out.write(output)
      self._out.write('\n')

  def Finish(self):
    """Prints the final delimiter and preps for the next resource list."""
    if self._empty:
      self._out.write('[]\n')
    elif self._delimiter != self._BEGIN_DELIMITER:
      self._out.write('\n]\n')
      self._delimiter = self._BEGIN_DELIMITER

    super(JsonPrinter, self).Finish()
