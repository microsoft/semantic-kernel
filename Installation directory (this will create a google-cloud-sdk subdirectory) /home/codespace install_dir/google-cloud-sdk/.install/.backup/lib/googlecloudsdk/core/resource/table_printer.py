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
"""Table format resource printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import json
import re

from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.resource import resource_printer_base
from googlecloudsdk.core.resource import resource_projection_spec
from googlecloudsdk.core.resource import resource_transform

import six
from six.moves import range  # pylint: disable=redefined-builtin


# Table output column padding.
_TABLE_COLUMN_PAD = 2
_BOX_CHAR_LENGTH = 1

# Default min width.
_MIN_WIDTH = 10


def _Stringify(value):  # pylint: disable=invalid-name
  """Represents value as a JSON string if it's not a string."""
  if value is None:
    return ''
  elif isinstance(value, console_attr.Colorizer):
    return value
  elif isinstance(value, six.string_types):
    return console_attr.Decode(value)
  elif isinstance(value, float):
    return resource_transform.TransformFloat(value)
  elif hasattr(value, '__str__'):
    return six.text_type(value)
  else:
    return json.dumps(value, sort_keys=True)


def _Numify(value):  # pylint: disable=invalid-name
  """Represents value as a number, or infinity if it is not a valid number."""
  if isinstance(value, (six.integer_types, float)):
    return value
  return float('inf')


class _Justify(object):
  """Represents a string object for justification using display width.

  Attributes:
    _adjust: The justification width adjustment. The builtin justification
      functions use len() which counts characters, but some character encodings
      require console_attr.DisplayWidth() which returns the encoded character
      display width.
    _string: The output encoded string to justify.
  """

  def __init__(self, attr, string):
    self._string = console_attr.SafeText(
        string, encoding=attr.GetEncoding(), escape=False)
    self._adjust = attr.DisplayWidth(self._string) - len(self._string)

  def ljust(self, width):
    return self._string.ljust(width - self._adjust)

  def rjust(self, width):
    return self._string.rjust(width - self._adjust)

  def center(self, width):
    return self._string.center(width - self._adjust)


class SubFormat(object):
  """A sub format object.

  Attributes:
    index: The parent column index.
    hidden: Column is projected but not displayed.
    printer: The nested printer object.
    out: The nested printer output stream.
    rows: The nested format aggregate rows if the parent has no columns.
    wrap: If column text should be wrapped.
  """

  def __init__(self, index, hidden, printer, out, wrap):
    self.index = index
    self.hidden = hidden
    self.printer = printer
    self.out = out
    self.rows = []
    self.wrap = wrap


class TablePrinter(resource_printer_base.ResourcePrinter):
  """A printer for printing human-readable tables.

  Aligned left-adjusted columns with optional title, column headings and
  sorting. This format requires a projection to define the table columns. The
  default column headings are the disambiguated right hand components of the
  column keys in ANGRY_SNAKE_CASE. For example, the projection keys
  (first.name, last.name) produce the default column heading
  ('NAME', 'LAST_NAME').

  If *--page-size*=_N_ is specified then output is grouped into tables with
  at most _N_ rows. Headings, alignment and sorting are done per-page. The
  title, if any, is printed before the first table.

  If screen reader option is True, you may observe flattened list output instead
  of a table with columns. Please refer to $ gcloud topic accessibility to turn
  it off.

  Printer attributes:
    all-box: Prints a box around the entire table and each cell, including the
      title if any.
    box: Prints a box around the entire table and the title cells if any.
    format=_FORMAT-STRING_: Prints the key data indented by 4 spaces using
      _FORMAT-STRING_ which can reference any of the supported formats.
    no-heading: Disables the column headings.
    margin=N: Right hand side padding when one or more columns are wrapped.
    pad=N: Sets the column horizontal pad to _N_ spaces. The default is 1 for
      box, 2 otherwise.
    title=_TITLE_: Prints a centered _TITLE_ at the top of the table, within
      the table box if *box* is enabled.

  Attributes:
    _optional: True if at least one column is optional. An optional column is
      not displayed if it contains no data.
    _page_count: The output page count, incremented before each page.
    _rows: The list of all resource columns indexed by row.
    _visible: Ordered list of visible column indexes.
    _wrap: True if at least one column can be text wrapped.
  """

  def __init__(self, *args, **kwargs):
    """Creates a new TablePrinter."""
    self._rows = []
    super(TablePrinter, self).__init__(
        *args, by_columns=True, non_empty_projection_required=True, **kwargs)
    encoding = None
    for name in ['ascii', 'utf-8', 'win']:
      if name in self.attributes:
        encoding = name
        break
    if not self._console_attr:
      self._console_attr = console_attr.GetConsoleAttr(encoding=encoding)
    self._csi = self._console_attr.GetControlSequenceIndicator()
    self._page_count = 0

    # Check for subformat columns.
    self._optional = False
    self._subformats = []
    self._has_subprinters = False
    has_subformats = False
    self._aggregate = True
    if self.column_attributes:
      for col in self.column_attributes.Columns():
        if col.attribute.subformat or col.attribute.hidden:
          has_subformats = True
        else:
          self._aggregate = False
        if col.attribute.optional:
          self._optional = True
        if col.attribute.wrap:
          self._wrap = True
      defaults = resource_projection_spec.ProjectionSpec(
          symbols=self.column_attributes.symbols)
      index = 0
      for col in self.column_attributes.Columns():
        if col.attribute.subformat:
          # This initializes a nested Printer to a string stream.
          out = self._out if self._aggregate else io.StringIO()
          wrap = None
          printer = self.Printer(
              col.attribute.subformat,
              out=out,
              console_attr=self._console_attr,
              defaults=defaults)
          self._has_subprinters = True
        else:
          out = None
          printer = None
          wrap = col.attribute.wrap
        self._subformats.append(
            SubFormat(index, col.attribute.hidden, printer, out, wrap))
        index += 1
    self._visible = None
    if not has_subformats:
      self._subformats = None
      self._aggregate = False
    elif self._subformats and not self._aggregate:
      self._visible = []
      for subformat in self._subformats:
        if not subformat.hidden and not subformat.printer:
          self._visible.append(subformat.index)

  def _AddRecord(self, record, delimit=True):
    """Adds a list of columns.

    Output delayed until Finish().

    Args:
      record: A JSON-serializable object.
      delimit: Prints resource delimiters if True.
    """
    self._rows.append(record)

  def _Visible(self, row):
    """Return the visible list items in row."""
    if not self._visible or not row:
      return row
    visible = []
    for index in self._visible:
      visible.append(row[index])
    return visible

  def _GetNextLineAndRemainder(self,
                               s,
                               max_width,
                               include_all_whitespace=False):
    """Helper function to get next line of wrappable text."""
    # Get maximum split index where the next line will be wider than max.
    current_width = 0
    split = 0
    prefix = ''  # Track any control sequence to use to start next line.
    while split < len(s):
      if self._csi and s[split:].startswith(self._csi):
        seq_length = self._console_attr.GetControlSequenceLen(s[split:])
        prefix = s[split:split + seq_length]
        split += seq_length
      else:
        current_width += console_attr.GetCharacterDisplayWidth(s[split])
        if current_width > max_width:
          break
        split += 1
    if not include_all_whitespace:
      split += len(s[split:]) - len(s[split:].lstrip())

    # Check if there is a newline character before the split.
    first_newline = re.search('\\n', s)
    if first_newline and first_newline.end() <= split:
      split = first_newline.end()
    # If not, split on the last whitespace character before the split
    # (if possible)
    else:
      max_whitespace = None
      for r in re.finditer(r'\s+', s):
        if r.end() > split:
          if include_all_whitespace and r.start() <= split:
            max_whitespace = split
          break
        max_whitespace = r.end()
      if max_whitespace:
        split = max_whitespace

    if not include_all_whitespace:
      next_line = s[:split].rstrip()
    else:
      next_line = s[:split]
    remaining_value = s[split:]
    # Reset font on this line if needed and add prefix to the remainder.
    if prefix and prefix != self._console_attr.GetFontCode():
      next_line += self._console_attr.GetFontCode()
      remaining_value = prefix + remaining_value
    return next_line, remaining_value

  def _GetSubformatIndexes(self):
    # Get indexes of all columns with subformat
    subs = []
    if self._subformats:
      for subformat in self._subformats:
        if subformat.printer:
          subs.append(subformat.index)
    return subs

  def _GetVisibleLabels(self):
    # Get visible labels
    if 'no-heading' not in self.attributes:
      if self._heading:
        return self._heading
      elif self.column_attributes:
        return self._Visible(self.column_attributes.Labels())
    return None

  def Finish(self):
    """Prints the table."""
    if not self._rows:
      # Table is empty.
      return

    if self._aggregate:
      # No parent columns, only nested formats. Aggregate each subformat
      # column to span all records.
      self._empty = True
      for subformat in self._subformats:
        for row in self._rows:
          record = row[subformat.index]
          if record:
            subformat.printer.Print(record, intermediate=True)
        subformat.printer.Finish()
        if subformat.printer.ResourcesWerePrinted():
          self._empty = False
      return

    # Border box decorations.
    all_box = 'all-box' in self.attributes
    if all_box or 'box' in self.attributes:
      box = self._console_attr.GetBoxLineCharacters()
      table_column_pad = 1
    else:
      box = None
      table_column_pad = self.attributes.get('pad', _TABLE_COLUMN_PAD)

    # Sort by columns if requested.
    rows = self._rows
    if self.column_attributes:
      # Order() is a list of (key,reverse) tuples from highest to lowest key
      # precedence. This loop partitions the keys into groups with the same
      # reverse value. The groups are then applied in reverse order to maintain
      # the original precedence.
      groups = []  # [(keys, reverse)] LIFO to preserve precedence
      keys = []  # keys for current group
      for key_index, key_reverse in self.column_attributes.Order():
        if not keys:
          # This only happens the first time through the loop.
          reverse = key_reverse
        if reverse != key_reverse:
          groups.insert(0, (keys, reverse))
          keys = []
          reverse = key_reverse
        keys.append(key_index)
      if keys:
        groups.insert(0, (keys, reverse))
      for keys, reverse in groups:
        # For reverse sort of multiple keys we reverse the entire table, sort by
        # each key ascending, and then reverse the entire table again. If we
        # sorted by each individual column in descending order, we would end up
        # flip-flopping between ascending and descending as we went.
        if reverse:
          rows = reversed(rows)
        for key in reversed(keys):
          decorated = [(_Numify(row[key]), _Stringify(row[key]), i, row)
                       for i, row in enumerate(rows)]
          decorated.sort()
          rows = [row for _, _, _, row in decorated]
        if reverse:
          rows = reversed(rows)
      align = self.column_attributes.Alignments()
    else:
      align = None

    # Flatten the table under screen reader mode for accessibility,
    # ignore box wrappers if any.
    screen_reader = properties.VALUES.accessibility.screen_reader.GetBool()
    if screen_reader:
      # Print the title if specified.
      title = self.attributes.get('title')
      if title is not None:
        self._out.write(title)
        self._out.write('\n\n')

      # Get indexes of all columns with no data
      if self._optional:
        # Delete optional columns that have no data.
        optional = False
        visible = []
        for i, col in enumerate(
            self._Visible(self.column_attributes.Columns())):
          if not col.attribute.optional:
            visible.append(i)
          else:
            optional = True
        if optional:
          # At least one optional column has no data. Adjust all column lists.
          if not visible:
            # All columns are optional and have no data => no output.
            self._empty = True
            return
          self._visible = visible

      labels = self._GetVisibleLabels()
      subs = self._GetSubformatIndexes()

      # Print items
      for i, row in enumerate(rows):
        if i:
          self._out.write('\n')
        for j in range(len(row)):
          # Skip columns that have no data in entire column
          if self._visible is not None and j not in self._visible:
            continue
          # Skip columns with subformats, which will be printed lastly
          if j in subs:
            continue
          content = six.text_type(_Stringify(row[j]))
          if labels and j < len(labels) and labels[j]:
            self._out.write('{0}: {1}'.format(labels[j], content))
          else:
            self._out.write(content)
          self._out.write('\n')
        if self._subformats:
          for subformat in self._subformats:
            if subformat.printer:
              subformat.printer.Print(row[subformat.index])
              nested_output = subformat.out.getvalue()
              # Indent the nested printer lines.
              for k, line in enumerate(nested_output.split('\n')[:-1]):
                if not k:
                  self._out.write('\n')
                self._out.write(line + '\n')
              # Rewind the output buffer.
              subformat.out.truncate(0)
              subformat.out.seek(0)
              self._out.write('\n')
      self._rows = []
      super(TablePrinter, self).Finish()
      return

    # Stringify all column cells for all rows.
    rows = [[_Stringify(cell) for cell in row] for row in rows]
    if not self._has_subprinters:
      self._rows = []

    # Remove the hidden/subformat alignments and columns from rows.
    if self._visible:
      rows = [self._Visible(row) for row in rows]
      align = self._Visible(align)

    # Determine the max column widths of heading + rows
    heading = []
    if 'no-heading' not in self.attributes:
      if self._heading:
        labels = self._heading
      elif self.column_attributes:
        labels = self._Visible(self.column_attributes.Labels())
      else:
        labels = None
      if labels:
        if self._subformats:
          cells = []
          for subformat in self._subformats:
            if not subformat.printer and subformat.index < len(labels):
              cells.append(_Stringify(labels[subformat.index]))
          heading = [cells]
        else:
          heading = [[_Stringify(cell) for cell in labels]]
    col_widths = [0] * max(len(x) for x in rows + heading)
    for row in rows:
      for i, col in enumerate(row):
        col_widths[i] = max(col_widths[i], self._console_attr.DisplayWidth(col))
    if self._optional:
      # Delete optional columns that have no data.
      optional = False
      visible = []
      # col_widths[i] == 0 => column i has no data.
      for i, col in enumerate(self._Visible(self.column_attributes.Columns())):
        if not col.attribute.optional or col_widths[i]:
          visible.append(i)
        else:
          optional = True
      if optional:
        # At least one optional column has no data. Adjust all column lists.
        if not visible:
          # All columns are optional and have no data => no output.
          self._empty = True
          return
        self._visible = visible
        rows = [self._Visible(row) for row in rows]
        align = self._Visible(align)
        heading = [self._Visible(heading[0])] if heading else []
        col_widths = self._Visible(col_widths)
    if heading:
      # Check the heading widths too.
      for i, col in enumerate(heading[0]):
        col_widths[i] = max(col_widths[i], self._console_attr.DisplayWidth(col))
    if self.column_attributes:
      # Finally check the fixed column widths.
      for i, col in enumerate(self.column_attributes.Columns()):
        if col.attribute.width and col_widths[i] < col.attribute.width:
          col_widths[i] = col.attribute.width

    # If table is wider than the console and columns can be wrapped,
    # change wrapped column widths to fit within the available space.
    wrap = {}
    for i, col in enumerate(self._Visible(self.column_attributes.Columns())):
      if col.attribute.wrap:
        if isinstance(col.attribute.wrap, bool):
          wrap[i] = _MIN_WIDTH
        else:
          wrap[i] = col.attribute.wrap
    if wrap:
      visible_cols = len(self._Visible(self.column_attributes.Columns()))
      table_padding = (visible_cols - 1) * table_column_pad
      if box:
        table_padding = (
            _BOX_CHAR_LENGTH * (visible_cols + 1) +
            visible_cols * table_column_pad * 2)
      table_padding += self.attributes.get('margin', 0)
      table_width = self.attributes.get('width',
                                        self._console_attr.GetTermSize()[0])
      total_col_width = table_width - table_padding
      if total_col_width < sum(col_widths):
        non_wrappable_width = sum([
            col_width for (i, col_width) in enumerate(col_widths)
            if i not in wrap
        ])
        available_width = total_col_width - non_wrappable_width
        for i, col_width in enumerate(col_widths):
          if i in wrap:
            min_width = min(wrap[i], col_widths[i])
            col_widths[i] = max(available_width // len(wrap), min_width)

    # Print the title if specified.
    title = self.attributes.get('title') if self._page_count <= 1 else None
    if title is not None:
      if box:
        line = box.dr
      width = 0
      sep = 2
      for i in range(len(col_widths)):
        width += col_widths[i]
        if box:
          line += box.h * (col_widths[i] + sep)
        sep = 3
      if width < self._console_attr.DisplayWidth(title) and not wrap:
        # Title is wider than the table => pad each column to make room.
        pad = ((self._console_attr.DisplayWidth(title) + len(col_widths) - 1) //
               len(col_widths))
        width += len(col_widths) * pad
        if box:
          line += box.h * len(col_widths) * pad
        for i in range(len(col_widths)):
          col_widths[i] += pad
      if box:
        width += 3 * len(col_widths) - 1
        line += box.dl
        self._out.write(line)
        self._out.write('\n')
        line = '{0}{1}{2}'.format(
            box.v,
            _Justify(self._console_attr, title).center(width), box.v)
      else:
        width += table_column_pad * (len(col_widths) - 1)
        line = _Justify(self._console_attr, title).center(width).rstrip()
      self._out.write(line)
      self._out.write('\n')

    # Set up box borders.
    if box:
      t_sep = box.vr if title else box.dr
      m_sep = box.vr
      b_sep = box.ur
      t_rule = ''
      m_rule = ''
      b_rule = ''
      for i in range(len(col_widths)):
        cell = box.h * (col_widths[i] + 2)
        t_rule += t_sep + cell
        t_sep = box.hd
        m_rule += m_sep + cell
        m_sep = box.vh
        b_rule += b_sep + cell
        b_sep = box.hu
      t_rule += box.vl if title else box.dl
      m_rule += box.vl
      b_rule += box.ul
      self._out.write(t_rule)
      self._out.write('\n')
      if heading:
        line = []
        row = heading[0]
        heading = []
        for i in range(len(row)):
          line.append(box.v)
          line.append(row[i].center(col_widths[i]))
        line.append(box.v)
        self._out.write(' '.join(line))
        self._out.write('\n')
        self._out.write(m_rule)
        self._out.write('\n')

    # Print the left-adjusted columns with space stripped from rightmost column.
    # We must flush directly to the output just in case there is a Windows-like
    # colorizer. This complicates the trailing space logic.
    first = True
    # Used for boxed tables to determine whether any subformats are visible.
    has_visible_subformats = box and self._subformats and any(
        [(not subformat.hidden and subformat.printer)
         for subformat in self._subformats])
    for row in heading + rows:
      if first:
        first = False
      elif box:
        if has_visible_subformats:
          self._out.write(t_rule)
          self._out.write('\n')
        elif all_box:
          self._out.write(m_rule)
          self._out.write('\n')
      row_finished = False
      while not row_finished:
        pad = 0
        row_finished = True
        for i in range(len(row)):
          width = col_widths[i]
          if box:
            self._out.write(box.v + ' ')
          justify = align[i] if align else lambda s, w: s.ljust(w)
          # Wrap text if needed.
          s = row[i]
          is_colorizer = isinstance(s, console_attr.Colorizer)
          if (self._console_attr.DisplayWidth(s) > width or
              '\n' in six.text_type(s)):
            cell_value, remainder = self._GetNextLineAndRemainder(
                six.text_type(s), width, include_all_whitespace=is_colorizer)
            if is_colorizer:
              # pylint:disable=protected-access
              cell = console_attr.Colorizer(cell_value, s._color, s._justify)
              row[i] = console_attr.Colorizer(remainder, s._color, s._justify)
              # pylint:disable=protected-access
            else:
              cell = cell_value
              row[i] = remainder
            if remainder:
              row_finished = False
          else:
            cell = s
            row[i] = ' '
          if is_colorizer:
            if pad:
              self._out.write(' ' * pad)
              pad = 0
            # NOTICE: This may result in trailing space after the last column.
            cell.Render(self._out, justify=lambda s: justify(s, width))  # pylint: disable=cell-var-from-loop
            if box:
              self._out.write(' ' * table_column_pad)
            else:
              pad = table_column_pad
          else:
            value = justify(_Justify(self._console_attr, cell), width)
            if box:
              self._out.write(value)
              self._out.write(' ' * table_column_pad)
            elif value.strip():
              if pad:
                self._out.write(' ' * pad)
                pad = 0
              stripped = value.rstrip()
              self._out.write(stripped)
              pad = (
                  table_column_pad + self._console_attr.DisplayWidth(value) -
                  self._console_attr.DisplayWidth(stripped))
            else:
              pad += table_column_pad + self._console_attr.DisplayWidth(value)
        if box:
          self._out.write(box.v)
        if self._rows:
          self._out.write('\n')
          if heading:
            heading = []
            continue
          if row_finished:
            if box:
              self._out.write(b_rule)
              self._out.write('\n')
            r = self._rows.pop(0)
            for subformat in self._subformats:
              if subformat.printer:
                # Indent the nested printer lines.
                subformat.printer.Print(r[subformat.index])
                nested_output = subformat.out.getvalue()
                for line in nested_output.split('\n')[:-1]:
                  self._out.write('    ' + line + '\n')
                # Rewind the output buffer.
                subformat.out.truncate(0)
                subformat.out.seek(0)
        else:
          self._out.write('\n')
    if box:
      if not has_visible_subformats:
        self._out.write(b_rule)
        self._out.write('\n')

    super(TablePrinter, self).Finish()

  def Page(self):
    """Flushes the current resource page output."""
    self._page_count += 1
    self.Finish()
    self._out.write('\n')
    self._rows = []
