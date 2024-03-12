#!/usr/bin/env python
# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

r"""Table formatting library.

We define a TableFormatter interface, and create subclasses for
several different print formats, including formats intended for both
human and machine consumption:

Human Consumption
-----------------

 PrettyFormatter: This prints ASCII-art bordered tables. Inspired
   by the prettytable python library. Example:

     +-----+---------------+
     | foo | longer header |
     +-----+---------------+
     | a   |             3 |
     |         ...         |
     | abc |           123 |
     +-----+---------------+

 SparsePrettyFormatter: This is a PrettyFormatter which simply
   doesn't print most of the border. Example:

      foo   longer header
     ----- ---------------
      a                 3
              ...
      abc             123

 PrettyJsonFormatter: Prints JSON output in a format easily
   read by a human. Example:

     [
       {
         "foo": "a",
         "longer header": 3
       },
       ...
       {
         "foo": "abc",
         "longer header": 123
       }
     ]

Machine Consumption
-------------------

  CsvFormatter: Prints output in CSV form, with minimal
    quoting, '\n' separation between lines, and including
    a header line. Example:

     foo,longer header
     a,3
     ...
     abc,123

  JsonFormatter: Prints JSON output in the most compact
    form possible. Example:

    [{"foo":"a","longer header":3},...,{"foo":"abc","longer header":123}]

Additional formatters can be added by subclassing TableFormatter and
overriding the following methods:
  __len__, __unicode__, AddRow, column_names, AddColumn

Formatters that require non-empty output to be valid should override
`_empty_output_meaningful`
For example JsonFormatter must emit '[]' to produce valid json.
"""

# These are required by the BigQuery "bq" CLI which still supports Python 2.
# See b/234740725.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import csv
import io
import itertools
import json
import sys

import wcwidth


class FormatterException(Exception):
  pass


class TableFormatter(object):
  """Interface for table formatters."""
  _empty_output_meaningful = False

  def __init__(self, **kwds):
    """Initializes the base class.

    Keyword arguments:
      skip_header_when_empty: If true, does not print the table's header
        if there are zero rows. This argument has no effect on
        PrettyJsonFormatter. Ignored by the Print method, but respected if
        calling str or unicode on the formatter itself. Print will emit nothing
        if there are zero rows, unless the format being emitted requires text
        to be valid (eg json).
    """
    if self.__class__ == TableFormatter:
      raise NotImplementedError(
          'Cannot instantiate abstract class TableFormatter')
    self.skip_header_when_empty = kwds.get('skip_header_when_empty', False)

  def __nonzero__(self):
    return bool(len(self))

  def __len__(self):
    raise NotImplementedError('__len__ must be implemented by subclass')

  def __str__(self):
    return self._EncodedStr(sys.getdefaultencoding())

  def __unicode__(self):
    raise NotImplementedError('__unicode__ must be implemented by subclass')

  def _EncodedStr(self, encoding):
    # Hack to avoid UnicodeEncodeErrors when printing the encoded string.
    return self.__unicode__().encode(encoding,
                                     'backslashreplace').decode(encoding)

  def Print(self, output=None):
    if self or self._empty_output_meaningful:
      # TODO(user): Make encoding a customizable attribute on
      # the TableFormatter.
      file = output if output else sys.stdout
      encoding = sys.stdout.encoding or 'utf8'
      print(self._EncodedStr(encoding), file=file)

  def AddRow(self, row):
    """Add a new row (an iterable) to this formatter."""
    raise NotImplementedError('AddRow must be implemented by subclass')

  def AddRows(self, rows):
    """Add all rows to this table."""
    for row in rows:
      self.AddRow(row)

  def AddField(self, field):
    """Add a field as a new column to this formatter."""
    # TODO(user): Excise this bigquery-specific method.
    align = 'l' if field.get('type', []) == 'STRING' else 'r'
    self.AddColumn(field['name'], align=align)

  def AddFields(self, fields):
    """Convenience method to add a list of fields."""
    for field in fields:
      self.AddField(field)

  def AddDict(self, d):
    """Add a dict as a row by using column names as keys."""
    self.AddRow([d.get(name, '') for name in self.column_names])

  @property
  def column_names(self):
    """Return the ordered list of column names in self."""
    raise NotImplementedError('column_names must be implemented by subclass')

  def AddColumn(self, column_name, align='r', **kwds):
    """Add a new column to this formatter."""
    raise NotImplementedError('AddColumn must be implemented by subclass')

  def AddColumns(self, column_names, kwdss=None):
    """Add a series of columns to this formatter."""
    kwdss = kwdss or [{}] * len(column_names)
    for column_name, kwds in zip(column_names, kwdss):
      self.AddColumn(column_name, **kwds)


class PrettyFormatter(TableFormatter):
  """Formats output as an ASCII-art table with borders."""

  def __init__(self, **kwds):
    """Initialize a new PrettyFormatter.

    Keyword arguments:
      junction_char: (default: +) Character to use for table junctions.
      horizontal_char: (default: -) Character to use for horizontal lines.
      vertical_char: (default: |) Character to use for vertical lines.
    """
    super(PrettyFormatter, self).__init__(**kwds)

    self.junction_char = kwds.get('junction_char', '+')
    self.horizontal_char = kwds.get('horizontal_char', '-')
    self.vertical_char = kwds.get('vertical_char', '|')

    self.rows = []
    self.row_heights = []
    self._column_names = []
    self.column_widths = []
    self.column_alignments = []
    self.header_height = 1

  def __len__(self):
    return len(self.rows)

  def __unicode__(self):
    if self or not self.skip_header_when_empty:
      lines = itertools.chain(
          self.FormatHeader(), self.FormatRows(), self.FormatHrule())
    else:
      lines = []
    return '\n'.join(lines)

  @staticmethod
  def CenteredPadding(interval, size, left_justify=True):
    """Compute information for centering a string in a fixed space.

    Given two integers interval and size, with size <= interval, this
    function computes two integers left_padding and right_padding with
      left_padding + right_padding + size = interval
    and
      |left_padding - right_padding| <= 1.

    In the case that interval and size have different parity,
    left_padding will be larger iff left_justify is True. (That is,
    iff the string should be left justified in the "center" space.)

    Args:
      interval: Size of the fixed space.
      size: Size of the string to center in that space.
      left_justify: (optional, default: True) Whether the string
        should be left-justified in the center space.

    Returns:
      left_padding, right_padding: The size of the left and right
        margins for centering the string.

    Raises:
      FormatterException: If size > interval.
    """
    if size > interval:
      raise FormatterException('Illegal state in table formatting')
    same_parity = (interval % 2) == (size % 2)
    padding = (interval - size) // 2
    if same_parity:
      return padding, padding
    elif left_justify:
      return padding, padding + 1
    else:
      return padding + 1, padding

  @staticmethod
  def Abbreviate(s, width):
    """Abbreviate a string to at most width characters."""
    suffix = '.' * min(width, 3)
    return s if len(s) <= width else s[:width - len(suffix)] + suffix

  @staticmethod
  def FormatCell(entry, cell_width, cell_height=1, align='c', valign='t'):
    """Format an entry into a list of strings for a fixed cell size.

    Given a (possibly multi-line) entry and a cell height and width,
    we split the entry into a list of lines and format each one into
    the given width and alignment. We then pad the list with
    additional blank lines of the appropriate width so that the
    resulting list has exactly cell_height entries. Each entry
    is also padded with one space on either side.

    We abbreviate strings for width, but we require that the
    number of lines in entry is at most cell_height.

    Args:
      entry: String to format, which may have newlines.
      cell_width: Maximum width for lines in the cell.
      cell_height: Number of lines in the cell.
      align: Alignment to use for lines of text.
      valign: Vertical alignment in the cell. One of 't',
        'c', or 'b' (top, center, and bottom, respectively).

    Returns:
      An iterator yielding exactly cell_height lines, each of
      exact width cell_width + 2, corresponding to this cell.

    Raises:
      FormatterException: If there are too many lines in entry.
      ValueError: If the valign is invalid.
    """
    entry_lines = [PrettyFormatter.Abbreviate(line, cell_width)
                   for line in entry.split('\n')]
    if len(entry_lines) > cell_height:
      raise FormatterException('Too many lines (%s) for a cell of size %s' % (
          len(entry_lines), cell_height))
    if valign == 't':
      top_lines = []
      bottom_lines = itertools.repeat(' ' * (cell_width + 2),
                                      cell_height - len(entry_lines))
    elif valign == 'c':
      top_padding, bottom_padding = PrettyFormatter.CenteredPadding(
          cell_height, len(entry_lines))
      top_lines = itertools.repeat(' ' * (cell_width + 2), top_padding)
      bottom_lines = itertools.repeat(' ' * (cell_width + 2), bottom_padding)
    elif valign == 'b':
      bottom_lines = []
      top_lines = itertools.repeat(' ' * (cell_width + 2),
                                   cell_height - len(entry_lines))
    else:
      raise ValueError('Unknown value for valign: %s' % (valign,))
    content_lines = []
    for line in entry_lines:
      if align == 'c':
        left_padding, right_padding = PrettyFormatter.CenteredPadding(
            cell_width, wcwidth.wcswidth(line))
        content_lines.append(' %s%s%s ' % (
            ' ' * left_padding, line, ' ' * right_padding))
      elif align in ('l', 'r'):
        padding = ' ' * (cell_width - wcwidth.wcswidth(line))
        fmt = ' %s%s '
        if align == 'l':
          output = fmt % (line, padding)
        else:
          output = fmt % (padding, line)
        content_lines.append(output)
      else:
        raise FormatterException('Unknown alignment: %s' % (align,))
    return itertools.chain(top_lines, content_lines, bottom_lines)

  def FormatRow(self, entries, row_height,
                column_alignments=None, column_widths=None):
    """Format a row into a list of strings.

    Given a list of entries, which must be the same length as the
    number of columns in this table, and a desired row height, we
    generate a list of strings corresponding to the printed
    representation of that row.

    Args:
      entries: List of entries to format.
      row_height: Number of printed lines corresponding to this row.
      column_alignments: (optional, default self.column_alignments)
        The alignment to use for each column.
      column_widths: (optional, default self.column_widths) The widths
        of each column.

    Returns:
      An iterator over the strings in the printed representation
      of this row.
    """
    column_alignments = column_alignments or self.column_alignments
    column_widths = column_widths or self.column_widths

    # pylint: disable=g-long-lambda
    curried_format = lambda entry, width, align: self.__class__.FormatCell(
        str(entry), width, cell_height=row_height, align=align)
    printed_rows = zip(
        *map(curried_format, entries, column_widths, column_alignments))
    return (self.vertical_char.join(itertools.chain([''], cells, ['']))
            for cells in printed_rows)

  def HeaderLines(self):
    """Return an iterator over the row(s) for the column names."""
    aligns = itertools.repeat('c')
    return self.FormatRow(self.column_names, self.header_height,
                          column_alignments=aligns)

  def FormatHrule(self):
    """Return a list containing an hrule for this table."""
    entries = (''.join(itertools.repeat('-', width + 2))
               for width in self.column_widths)
    return [self.junction_char.join(itertools.chain([''], entries, ['']))]

  def FormatHeader(self):
    """Return an iterator over the lines for the header of this table."""
    return itertools.chain(
        self.FormatHrule(), self.HeaderLines(), self.FormatHrule())

  def FormatRows(self):
    """Return an iterator over all the rows in this table."""
    return itertools.chain(*map(self.FormatRow, self.rows, self.row_heights))

  def AddRow(self, row):
    """Add a row to this table.

    Args:
      row: A list of length equal to the number of columns in this table.

    Raises:
      FormatterException: If the row length is invalid.
    """
    if len(row) != len(self.column_names):
      raise FormatterException('Invalid row length: %s' % (len(row),))
    split_rows = [str(entry).split('\n') for entry in row]
    self.row_heights.append(max(len(lines) for lines in split_rows))
    column_widths = (
        max(wcwidth.wcswidth(line) for line in entry) for entry in split_rows)
    self.column_widths = [
        max(width, current)
        for width, current in zip(column_widths, self.column_widths)
    ]
    self.rows.append(row)

  def AddColumn(self, column_name, align='l', **kwds):
    """Add a column to this table.

    Args:
      column_name: Name for the new column.
      align: (optional, default: 'l') Alignment for the new column entries.

    Raises:
      FormatterException: If the table already has any rows, or if the
        provided alignment is invalid.
    """
    if self:
      raise FormatterException(
          'Cannot add a new column to an initialized table')
    if align not in ('l', 'c', 'r'):
      raise FormatterException('Invalid column alignment: %s' % (align,))
    lines = str(column_name).split('\n')
    self.column_widths.append(max(wcwidth.wcswidth(line) for line in lines))
    self.column_alignments.append(align)
    self.column_names.append(column_name)
    self.header_height = max(len(lines), self.header_height)

  @property
  def column_names(self):
    return self._column_names


class SparsePrettyFormatter(PrettyFormatter):
  """Formats output as a table with a header and separator line."""

  def __init__(self, **kwds):
    """Initialize a new SparsePrettyFormatter."""
    default_kwds = {'junction_char': ' ',
                    'vertical_char': ' '}
    default_kwds.update(kwds)
    super(SparsePrettyFormatter, self).__init__(**default_kwds)

  def __unicode__(self):
    if self or not self.skip_header_when_empty:
      lines = itertools.chain(self.FormatHeader(), self.FormatRows())
    else:
      lines = []
    return '\n'.join(lines)

  def FormatHeader(self):
    """Return an iterator over the header lines for this table."""
    return itertools.chain(self.HeaderLines(), self.FormatHrule())


class CsvFormatter(TableFormatter):
  """Formats output as CSV with header lines.

  The resulting CSV file includes a header line, uses Unix-style
  newlines, and only quotes those entries which require it, namely
  those that contain quotes, newlines, or commas.
  """

  def __init__(self, **kwds):
    super(CsvFormatter, self).__init__(**kwds)
    self._buffer = io.StringIO()
    self._header = []
    self._table = csv.writer(
        self._buffer, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')

  def __nonzero__(self):
    return bool(self._buffer.tell())

  def __bool__(self):
    return bool(self._buffer.getvalue())

  def __len__(self):
    return len(str(self).splitlines())

  def __unicode__(self):
    if self or not self.skip_header_when_empty:
      lines = [','.join(self._header), self._buffer.getvalue()]
    else:
      lines = []
    # Note that we need to explicitly decode here to work around
    # the fact that the CSV module does not work with unicode.
    return '\n'.join(lines).rstrip()

  @property
  def column_names(self):
    return self._header[:]

  def AddColumn(self, column_name, **kwds):
    if self:
      raise FormatterException(
          'Cannot add a new column to an initialized table')
    self._header.append(column_name)

  def AddRow(self, row):
    self._table.writerow(row)


class JsonFormatter(TableFormatter):
  """Formats output in maximally compact JSON."""
  _empty_output_meaningful = True

  def __init__(self, **kwds):
    super(JsonFormatter, self).__init__(**kwds)
    self._field_names = []
    self._table = []

  def __len__(self):
    return len(self._table)

  def __unicode__(self):
    return json.dumps(
        self._table, separators=(',', ':'), sort_keys=True, ensure_ascii=False)

  @property
  def column_names(self):
    return self._field_names[:]

  def AddColumn(self, column_name, **kwds):
    if self:
      raise FormatterException(
          'Cannot add a new column to an initialized table')
    self._field_names.append(column_name)

  def AddRow(self, row):
    if len(row) != len(self._field_names):
      raise FormatterException('Invalid row: %s' % (row,))
    self._table.append(dict(zip(self._field_names, row)))


class PrettyJsonFormatter(JsonFormatter):
  """Formats output in human-legible JSON."""

  def __unicode__(self):
    return json.dumps(
        self._table,
        separators=(', ', ': '),
        sort_keys=True,
        indent=2,
        ensure_ascii=False)


class NullFormatter(TableFormatter):
  """Formatter that prints no output at all."""

  def __init__(self, **kwds):
    super(NullFormatter, self).__init__(**kwds)
    self._column_names = []
    self._rows = []

  def __nonzero__(self):
    return bool(self._rows)

  def __len__(self):
    return len(self._rows)

  def __unicode__(self):
    return ''

  def AddRow(self, row):
    self._rows.append(row)

  def AddRows(self, rows):
    for row in rows:
      self.AddRow(row)

  @property
  def column_names(self):
    return self._column_names[:]

  def AddColumn(self, column_name, **kwds):
    self._column_names.append(column_name)


def GetFormatter(table_format):
  """Map a format name to a TableFormatter object."""
  if table_format == 'csv':
    table_formatter = CsvFormatter()
  elif table_format == 'pretty':
    table_formatter = PrettyFormatter()
  elif table_format == 'json':
    table_formatter = JsonFormatter()
  elif table_format == 'prettyjson':
    table_formatter = PrettyJsonFormatter()
  elif table_format == 'sparse':
    table_formatter = SparsePrettyFormatter()
  elif table_format == 'none':
    table_formatter = NullFormatter()
  else:
    raise FormatterException('Unknown format: %s' % table_format)
  return table_formatter
