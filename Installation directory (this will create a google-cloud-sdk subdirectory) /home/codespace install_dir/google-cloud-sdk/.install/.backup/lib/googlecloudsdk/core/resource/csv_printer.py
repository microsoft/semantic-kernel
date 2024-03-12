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

"""CSV resource printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_printer_base
from googlecloudsdk.core.resource import resource_transform
from googlecloudsdk.core.util import encoding

import six


class CsvPrinter(resource_printer_base.ResourcePrinter):
  r"""A printer for printing CSV data.

  [Comma Separated Values](http://www.ietf.org/rfc/rfc4180.txt) with no keys.
  This format requires a projection to define the values to be printed.

  To use *\n* or *\t* as an attribute value please escape the *\* with your
  shell's escape sequence, example *separator="\\n"* for bash.

  Printer attributes:
    delimiter="string": The string printed between list value items,
      default ";".
    no-heading: Disables the initial key name heading record.
    separator="string": The string printed between values, default ",".
    terminator="string": The string printed after each record, default
      "\n" (newline).
  """

  def __init__(self, *args, **kwargs):
    super(CsvPrinter, self).__init__(*args, by_columns=True,
                                     non_empty_projection_required=True,
                                     **kwargs)
    self._heading_printed = False
    self._delimiter = self.attributes.get('delimiter', ';')
    self._quote = None if self.attributes.get('no-quote', 0) else '"'
    self._separator = self.attributes.get('separator', ',')
    self._terminator = self.attributes.get('terminator', '\n')

  def _QuoteField(self, field):
    """Returns field quoted by self._quote if necessary.

    The Python 2.7 csv module does not support unicode "yet". What are they
    waiting for?

    Args:
      field: The unicode string to quote.

    Returns:
      field quoted by self._quote if necessary.
    """
    if not field or not self._quote:
      return field
    if not (self._delimiter in field or
            self._quote in field or
            self._separator in field or
            self._terminator in field or
            field[0].isspace() or field[-1].isspace()):
      return field
    return (self._quote +
            field.replace(self._quote, self._quote * 2) +
            self._quote)

  def _AddRecord(self, record, delimit=False):
    """Prints the current record as CSV.

    Printer attributes:
      noheading: bool, Disable the initial key name heading record.

    Args:
      record: A list of JSON-serializable object columns.
      delimit: bool, Print resource delimiters -- ignored.

    Raises:
      ToolException: A data value has a type error.
    """
    # The CSV heading has three states:
    #   1: No heading, used by ValuePrinter and CSV when 2. and 3. are empty.
    #   2: Heading via AddHeading().
    #   3: Default heading from format labels, if specified.
    if not self._heading_printed:
      self._heading_printed = True
      if 'no-heading' not in self.attributes:
        if self._heading:
          labels = self._heading
        else:
          labels = self.column_attributes.Labels()
          if labels:
            labels = [x.lower() for x in self.RemoveHiddenColumns(labels)]
        if labels:
          self._out.write(
              self._separator.join([
                  self._QuoteField(label)
                  for label in self.RemoveHiddenColumns(labels)
              ]) + self._terminator)
    line = []
    for col in self.RemoveHiddenColumns(record):
      if col is None:
        val = ''
      elif isinstance(col, dict):
        val = self._delimiter.join(
            [self._QuoteField('{0}={1}'.format(
                encoding.Decode(k), encoding.Decode(v)))
             for k, v in sorted(six.iteritems(col))])
      elif isinstance(col, list):
        val = self._delimiter.join(
            [self._QuoteField(encoding.Decode(x)) if x else '' for x in col])
      elif isinstance(col, float):
        val = self._QuoteField(resource_transform.TransformFloat(col))
      else:
        val = self._QuoteField(encoding.Decode(col))
      line.append(val)
    self._out.write(self._separator.join(line) + self._terminator)


class ValuePrinter(CsvPrinter):
  r"""A printer for printing value data.

  CSV with no heading and <TAB> separator instead of <COMMA>. Used to retrieve
  individual resource values. This format requires a projection to define the
  value(s) to be printed.

  To use *\n* or *\t* as an attribute value please escape the *\* with your
  shell's escape sequence, example *separator="\\n"* for bash.

  Printer attributes:
    delimiter="string": The string printed between list value items,
      default ";".
    quote: "..." quote values that contain delimiter, separator or terminator
      strings.
    separator="string": The string printed between values, default
      "\t" (tab).
    terminator="string": The string printed after each record, default
      "\n" (newline).
  """

  def __init__(self, *args, **kwargs):
    super(ValuePrinter, self).__init__(*args, **kwargs)
    self._heading_printed = True
    self._delimiter = self.attributes.get('delimiter', ';')
    self._quote = '"' if self.attributes.get('quote', 0) else None
    self._separator = self.attributes.get('separator', '\t')
    self._terminator = self.attributes.get('terminator', '\n')


class GetPrinter(ValuePrinter):
  r"""A printer for printing value data with transforms disabled.

  Equivalent to the *value[no-transforms]* format. Default transforms are
  not applied to the displayed values.
  """

  def __init__(self, *args, **kwargs):
    super(GetPrinter, self).__init__(*args, ignore_default_transforms=True,
                                     **kwargs)
