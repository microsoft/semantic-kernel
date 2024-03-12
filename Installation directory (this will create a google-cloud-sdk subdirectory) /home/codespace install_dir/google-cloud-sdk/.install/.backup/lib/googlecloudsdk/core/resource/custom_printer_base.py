# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Base class for resource-specific printers."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import abc

from googlecloudsdk.core.console import console_attr as ca
from googlecloudsdk.core.resource import resource_printer_base


import six


# The number of spaces to add in front of a _Marker's content when starting to
# print a nested _Marker.
INDENT_STEP = 2

# String to use to indent lines.
_INDENT_STRING = ''

# Format string to use when printing lines.
_LINE_FORMAT = '{indent: <%d}{line}\n'


def _GenerateLineValue(value, indent_length=0):
  """Returns a formatted, indented line containing the given value."""
  line_format = _LINE_FORMAT % indent_length
  return line_format.format(indent=_INDENT_STRING, line=value)


@six.add_metaclass(abc.ABCMeta)
class _Marker(object):
  """Base class for a marker indicating how to format printer output."""

  @abc.abstractmethod
  def CalculateColumnWidths(self, max_column_width=None, indent_length=0):
    """Calculates the minimum width of any table columns in the record.

    Returns a ColumnWidths object that contains the minimum width of each column
    in any Table markers contained in this record, including Table markers
    nested within other Table markers.

    Args:
      max_column_width: The maximum column width to allow.
      indent_length: The number of spaces of indentation that begin this
        record's lines.

    Returns:
      A ColumnWidths object with the computed columns for this record. Will be
      empty if this record does not contain any tables.
    """

  @abc.abstractmethod
  def Print(self, output, indent_length, column_widths):
    """Prints this record to the given output.

    Prints this record to the given output using this record's print format.

    Args:
      output: An object with a `write` method that takes a string argument. This
        method calls output.write with one string as an argument for each line
        in this record's print format.
      indent_length: The number of spaces of indentation to print at the
        beginning of each line.
      column_widths: A ColumnWidths object containing the minimum width of each
        column in any tables contained in this record.
    """

  @abc.abstractmethod
  def WillPrintOutput(self):
    """Returns true if this record will print non-empty output.

    Blank lines count as non-empty output.
    """


class Table(list, _Marker):
  """Marker class for a table."""

  # String to use to separate table columns.
  _COLUMN_SEPARATOR = ' '

  skip_empty = False
  separator = ''

  def __init__(self, content, console_attr=None):
    super(Table, self).__init__(content)
    self._console_attr = console_attr

  def CalculateColumnWidths(self, max_column_width=None, indent_length=0):
    """See _Marker base class."""
    widths = ColumnWidths(max_column_width=max_column_width)
    for row in self:
      widths = widths.Merge(
          ColumnWidths(row, self.separator, self.skip_empty, max_column_width,
                       indent_length))
    return widths

  def _ShouldSkipPrintingRow(self, row):
    """Returns true if the given row should not be printed."""
    followed_by_empty = (
        _FollowedByEmpty(row, 0) or _FollowedByMarkerWithNoOutput(row, 0))
    return not row or (self.skip_empty and followed_by_empty)

  def _GenerateColumnValue(self, index, row, indent_length, column_widths):
    """Generates the string value for one column in one row."""
    width = column_widths.widths[index]
    if index == 0:
      width -= indent_length
    separator = self.separator if index < len(row) - 1 else ''

    console_attr = self._console_attr
    if self._console_attr is None:
      console_attr = ca.ConsoleAttr()

    # calculate number of ' ' paddings required.
    # avoid using '{: <10}'.format() which doesn't calculate the displaylength
    # of ANSI ecoded sequence correctly.
    n_padding = (
        width - console_attr.DisplayWidth(str(row[index])) - len(separator))
    return str(row[index]) + separator + (n_padding * ' ')

  def _WriteColumns(self, output, indent_length, column_values):
    """Writes generated column values to output with the given indentation."""
    output.write(
        _GenerateLineValue(
            self._COLUMN_SEPARATOR.join(column_values).rstrip(), indent_length))

  def Print(self, output, indent_length, column_widths):
    """See _Marker base class."""
    for row in self:
      if self._ShouldSkipPrintingRow(row):
        continue
      column_values = []
      for i in range(len(row) - 1):
        if isinstance(row[i], _Marker):
          raise TypeError('Markers must be in the last column.')
        column_values.append(
            self._GenerateColumnValue(i, row, indent_length, column_widths))
      if isinstance(row[-1], _Marker):
        self._WriteColumns(output, indent_length, column_values)
        row[-1].Print(output, indent_length + INDENT_STEP, column_widths)
      else:
        column_values.append(
            self._GenerateColumnValue(
                len(row) - 1, row, indent_length, column_widths))
        self._WriteColumns(output, indent_length, column_values)

  def WillPrintOutput(self):
    """See _Marker base class."""
    return any(not self._ShouldSkipPrintingRow(row) for row in self)


class Labeled(Table):
  """Marker class for a list of "Label: value" 2-tuples."""
  skip_empty = True
  separator = ':'


# This class exists for API compatibility.
class Mapped(Table):
  """Marker class for a list of key-value 2-tuples."""


class Lines(list, _Marker):
  """Marker class for a list of lines."""

  def CalculateColumnWidths(self, max_column_width=None, indent_length=0):
    """See _Marker base class."""
    widths = ColumnWidths(max_column_width=max_column_width)
    for line in self:
      if isinstance(line, _Marker):
        widths = widths.Merge(
            line.CalculateColumnWidths(max_column_width, indent_length))
    return widths

  def Print(self, output, indent_length, column_widths):
    """See _Marker base class."""
    for line in self:
      if isinstance(line, _Marker):
        line.Print(output, indent_length, column_widths)
      elif line:
        output.write(_GenerateLineValue(line, indent_length))

  def WillPrintOutput(self):
    """See _Marker base class."""
    for line in self:
      if not isinstance(line, _Marker):
        # Lines always prints non-Marker lines. If the line is empty, this will
        # result in a blank line, which counts as non-empty output.
        return True
      if line.WillPrintOutput():
        return True
    return False


class Section(_Marker):
  """Marker class for a section.

  A section is a list of lines. Section differs from Line in that Section
  introduces an alignment break into the layout and allows overriding the global
  maximum column width within the section. An alignment break causes all columns
  in Table markers within a Section to be aligned but columns in Table markers
  outside of a specific Section marker are not aligned with the columns inside
  the Section.
  """

  def __init__(self, lines, max_column_width=None):
    """Initializes a section.

    Args:
      lines: A list of lines to include in the section.
      max_column_width: An optional maximum column width to use for this
        section. Overrides the global maximum column width if specified.
    """
    self._lines = Lines(lines)
    self._max_column_width = max_column_width
    self._column_widths = None

  def CalculateColumnWidths(self, max_column_width=None, indent_length=0):
    """See _Marker base class.

    Args:
      max_column_width: The maximum column width to allow. Overriden by the
        instance's max_column_width, if the instance has a max_column_width
        specified.
      indent_length: See _Marker base class.

    Returns:
      An empty ColumnWidths object.
    """
    effective_max_column_width = self._max_column_width or max_column_width
    self._column_widths = self._lines.CalculateColumnWidths(
        effective_max_column_width, indent_length)
    return ColumnWidths()

  def Print(self, output, indent_length, column_widths):
    """See _Marker base class.

    Args:
      output: See _Marker base class.
      indent_length: See _Marker base class.
      column_widths: Ignored by Section. Section computes its own column widths
        to align columns within the section independently from columns outside
        the section.
    """
    del column_widths  # Unused by Section.
    if not self._column_widths:
      self.CalculateColumnWidths(indent_length=indent_length)
    self._lines.Print(output, indent_length, self._column_widths)

  def WillPrintOutput(self):
    """See _Marker base class."""
    return self._lines.WillPrintOutput()


def _FollowedByEmpty(row, index):
  """Returns true if all columns after the given index are empty."""
  return not any(row[index + 1:])


def _FollowedByMarkerWithNoOutput(row, index):
  """Returns true if the column after the given index is a no-output _Marker."""
  next_index = index + 1
  return (len(row) > next_index and isinstance(row[next_index], _Marker) and
          not row[next_index].WillPrintOutput())


def _IsLastColumnInRow(row, column_index, last_index, skip_empty):
  """Returns true if column_index is considered the last column in the row."""
  # A column is considered the last column in the row if it is:
  #   1) The last column in the row.
  #   2) Only followed by empty columns and skip_empty is true.
  #   3) Followed by a _Marker.
  #        - This is because _Marker's must be in the last column in their row
  #          and get printed on a new line).
  return (column_index == last_index or
          (skip_empty and _FollowedByEmpty(row, column_index)) or
          isinstance(row[column_index + 1], _Marker))


class ColumnWidths(object):
  """Computes and stores column widths for a table and any nested tables.

  A nested table is a table defined in the last column of a row in another
  table. ColumnWidths includes any nested tables when computing column widths
  so that the width of each column will be based on the contents of that column
  in the parent table and all nested tables.

  Attributes:
    widths: A list containing the computed minimum width of each column in the
      table and any nested tables.
  """

  def __init__(self,
               row=None,
               separator='',
               skip_empty=False,
               max_column_width=None,
               indent_length=0,
               console_attr=None):
    """Computes the width of each column in row and in any nested tables.

    Args:
      row: An optional list containing the columns in a table row. Any marker
        classes nested within the row must be in the last column of the row.
      separator: An optional separator string to place between columns.
      skip_empty: A boolean indicating whether columns followed only by empty
        columns should be skipped.
      max_column_width: An optional maximum column width.
      indent_length: The number of indent spaces that precede `row`. Added to
        the width of the first column in `row`.
      console_attr: The console attribute for width calculation

    Returns:
      A ColumnWidths object containing the computed column widths.
    """
    self._widths = []
    self._max_column_width = max_column_width
    self._separator_width = len(separator)
    self._skip_empty = skip_empty
    self._indent_length = indent_length
    self._console_attr = console_attr
    if row:
      for i in range(len(row)):
        self._ProcessColumn(i, row)

  @property
  def widths(self):
    """A list containing the minimum width of each column."""
    return self._widths

  def __repr__(self):
    """Returns a string representation of a ColumnWidths object."""
    return '<widths: {}>'.format(self.widths)

  def _SetWidth(self, column_index, content_length):
    """Adjusts widths to account for the length of new column content.

    Args:
      column_index: The column index to potentially update. Must be between 0
        and len(widths).
      content_length: The column content's length to consider when updating
        widths.
    """
    # Updates the width at position column_index to be the max of the existing
    # value and the new content's length, or this instance's max_column_width if
    # the value would be greater than max_column_width.
    if column_index == len(self._widths):
      self._widths.append(0)

    new_width = max(self._widths[column_index], content_length)
    if self._max_column_width is not None:
      new_width = min(self._max_column_width, new_width)
    self._widths[column_index] = new_width

  def _ProcessColumn(self, index, row):
    """Processes a single column value when computing column widths."""
    record = row[index]
    last_index = len(row) - 1
    if isinstance(record, _Marker):
      if index == last_index:
        self._MergeColumnWidths(
            record.CalculateColumnWidths(self._max_column_width,
                                         self._indent_length + INDENT_STEP))
        return
      else:
        raise TypeError('Markers can only be used in the last column.')

    if _IsLastColumnInRow(row, index, last_index, self._skip_empty):
      self._SetWidth(index, 0)
    else:
      console_attr = self._console_attr
      if self._console_attr is None:
        console_attr = ca.ConsoleAttr()
      width = console_attr.DisplayWidth(str(record)) + self._separator_width
      if index == 0:
        width += self._indent_length
      self._SetWidth(index, width)

  def _MergeColumnWidths(self, other):
    """Merges another ColumnWidths into this instance."""
    for i, width in enumerate(other.widths):
      self._SetWidth(i, width)

  def Merge(self, other):
    """Merges this object and another ColumnWidths into a new ColumnWidths.

    Combines the computed column widths for self and other into a new
    ColumnWidths. Uses the larger maximum column width between the two
    ColumnWidths objects for the merged ColumnWidths. If one or both
    ColumnWidths objects have unlimited max column width (max_column_width is
    None), sets the merged ColumnWidths max column width to unlimited (None).

    Args:
      other: A ColumnWidths object to merge with this instance.

    Returns:
      A new ColumnWidths object containing the combined column widths.
    """
    if not isinstance(other, ColumnWidths):
      raise TypeError('other must be a ColumnWidths object.')
    # pylint: disable=protected-access
    if self._max_column_width is None or other._max_column_width is None:
      merged_max_column_width = None
    else:
      merged_max_column_width = max(self._max_column_width,
                                    other._max_column_width)
    merged = ColumnWidths(max_column_width=merged_max_column_width)
    merged._MergeColumnWidths(self)
    merged._MergeColumnWidths(other)
    return merged


@six.add_metaclass(abc.ABCMeta)
class CustomPrinterBase(resource_printer_base.ResourcePrinter):
  """Base to extend to custom-format a resource.

  Instead of using a format string, uses the "Transform" method to build a
  structure of marker classes that represent how to print out the resource
  in a structured way, and then prints it out in that way.

  A string prints out as a string; the marker classes above print out as an
  indented aligned table.
  """

  MAX_COLUMN_WIDTH = 20

  def __init__(self, *args, **kwargs):
    kwargs['process_record'] = self.Transform
    super(CustomPrinterBase, self).__init__(*args, **kwargs)

  def _AddRecord(self, record, delimit=True):
    if isinstance(record, _Marker):
      column_widths = record.CalculateColumnWidths(self.MAX_COLUMN_WIDTH)
      record.Print(self._out, 0, column_widths)
    elif record:
      self._out.write(_GenerateLineValue(record))
    if delimit:
      self._out.write('------\n')

  @abc.abstractmethod
  def Transform(self, record):
    """Override to describe the format of the record.

    Takes in the raw record, returns a structure of "marker classes" (above in
    this file) that will describe how to print it.

    Args:
      record: The record to transform
    Returns:
      A structure of "marker classes" that describes how to print the record.
    """
