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

"""Cloud SDK markdown document text renderer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.document_renderers import renderer


class TextRenderer(renderer.Renderer):
  """Renders markdown to text.

  Attributes:
    _attr: console_attr.ConsoleAttr object.
    _bullet: List of bullet characters indexed by list level modulo #bullets.
    _csi_char: The first control sequence indicator character or None if control
      sequences are not supported.
    _fill: The number of characters in the current output line.
    _ignore_width: True if the next output word should ignore _width.
    _indent: List of left indentations in characters indexed by _level.
    _level: The section or list level counting from 0.
  """
  INDENT = 4
  SPLIT_INDENT = 2

  class Indent(object):
    """Second line indent stack."""

    def __init__(self):
      self.indent = TextRenderer.INDENT
      self.second_line_indent = self.indent

  def __init__(self, *args, **kwargs):
    super(TextRenderer, self).__init__(*args, **kwargs)
    self._attr = console_attr.GetConsoleAttr()
    self._bullet = self._attr.GetBullets()
    self._csi_char = self._attr.GetControlSequenceIndicator()
    if self._csi_char:
      self._csi_char = self._csi_char[0]
    self._fill = 0
    self._ignore_width = False
    self._indent = [self.Indent()]
    self._level = 0

  def _Flush(self):
    """Flushes the current collection of Fill() lines."""
    self._ignore_width = False
    if self._fill:
      self._out.write('\n')
      self.Content()
      self._fill = 0

  def _SetIndent(self, level, indent=0, second_line_indent=None):
    """Sets the markdown list level and indentations.

    Args:
      level: int, The desired markdown list level.
      indent: int, The new indentation.
      second_line_indent: int, The second line indentation. This is subtracted
        from the prevailing indent to decrease the indentation of the next input
        line for this effect:
            SECOND LINE INDENT ON THE NEXT LINE
               PREVAILING INDENT
               ON SUBSEQUENT LINES
    """
    if self._level < level:
      # The level can increase by 1 or more. Loop through each so that
      # intervening levels are handled the same.
      while self._level < level:
        prev_level = self._level
        self._level += 1
        if self._level >= len(self._indent):
          self._indent.append(self.Indent())
        self._indent[self._level].indent = (
            self._indent[prev_level].indent + indent)
        if (self._level > 1 and
            self._indent[prev_level].second_line_indent ==
            self._indent[prev_level].indent):
          # Bump the indent by 1 char for nested indentation. Top level looks
          # fine (aesthetically) without it.
          self._indent[self._level].indent += 1
        self._indent[self._level].second_line_indent = (
            self._indent[self._level].indent)
        if second_line_indent is not None:
          # Adjust the second line indent if specified.
          self._indent[self._level].second_line_indent -= second_line_indent
    else:
      # Decreasing level just sets the indent stack level, no state to clean up.
      self._level = level
      if second_line_indent is not None:
        # Change second line indent on existing level.
        self._indent[self._level].indent = (
            self._indent[self._level].second_line_indent + second_line_indent)

  def Example(self, line):
    """Displays line as an indented example.

    Args:
      line: The example line text.
    """
    self._fill = self._indent[self._level].indent + self.INDENT
    self._out.write(' ' * self._fill + line + '\n')
    self.Content()
    self._fill = 0

  def Fill(self, line):
    """Adds a line to the output, splitting to stay within the output width.

    This is close to textwrap.wrap() except that control sequence characters
    don't count in the width computation.

    Args:
      line: The text line.
    """
    self.Blank()
    for word in line.split():
      if not self._fill:
        self._fill = self._indent[self._level].indent - 1
        self._out.write(' ' * self._fill)
      width = self._attr.DisplayWidth(word)
      if self._fill + width + 1 >= self._width and not self._ignore_width:
        self._out.write('\n')
        self._fill = self._indent[self._level].indent
        self._out.write(' ' * self._fill)
      else:
        self._ignore_width = False
        if self._fill:
          self._fill += 1
          self._out.write(' ')
      self._fill += width
      self._out.write(word)

  def Finish(self):
    """Finishes all output document rendering."""
    self._Flush()
    self.Font(out=self._out)

  def Font(self, attr=None, out=None):
    """Returns the font embellishment string for attr.

    Args:
      attr: None to reset to the default font, otherwise one of renderer.BOLD,
        renderer.ITALIC, or renderer.CODE.
      out: Writes tags to this stream if not None.

    Returns:
      The font embellishment string.
    """
    if attr is None:
      self._font = 0
    else:
      mask = 1 << attr
      self._font ^= mask
    bold = self._font & ((1 << renderer.BOLD) | (1 << renderer.CODE))
    italic = self._font & (1 << renderer.ITALIC)
    code = self._attr.GetFontCode(bold=bold, italic=italic)
    if out:
      out.write(code)
    return code

  def Heading(self, level, heading):
    """Renders a heading.

    Args:
      level: The heading level counting from 1.
      heading: The heading text.
    """
    if level == 1 and heading.endswith('(1)'):
      # Ignore man page TH.
      return
    self._Flush()
    self.Line()
    self.Font(out=self._out)
    if level > 2:
      self._out.write('  ' * (level - 2))
    self._out.write(self.Font(renderer.BOLD) + heading +
                    self.Font(renderer.BOLD) + '\n')
    if level == 1:
      self._out.write('\n')
    self.Blank()
    self._level = 0
    self._rows = []

  def Line(self):
    """Renders a paragraph separating line."""
    self._Flush()
    if not self.HaveBlank():
      self.Blank()
      self._out.write('\n')

  def List(self, level, definition=None, end=False):
    """Renders a bullet or definition list item.

    Args:
      level: The list nesting level, 0 if not currently in a list.
      definition: Bullet list if None, definition list item otherwise.
      end: End of list if True.
    """
    self._Flush()
    if not level:
      self._level = level
    elif end:
      # End of list.
      self._SetIndent(level)
    elif definition is not None:
      # Definition list item.
      if definition:
        self._SetIndent(level, indent=4, second_line_indent=3)
        self._out.write(
            ' ' * self._indent[level].second_line_indent + definition + '\n')
      else:
        self._SetIndent(level, indent=1, second_line_indent=0)
        self.Line()
    else:
      # Bullet list item.
      indent = 2 if level > 1 else 4
      self._SetIndent(level, indent=indent, second_line_indent=2)
      self._out.write(' ' * self._indent[level].second_line_indent +
                      self._bullet[(level - 1) % len(self._bullet)])
      self._fill = self._indent[level].indent + 1
      self._ignore_width = True

  def _SkipSpace(self, line, index):
    """Skip space characters starting at line[index].

    Args:
      line: The string.
      index: The starting index in string.

    Returns:
      The index in line after spaces or len(line) at end of string.
    """
    while index < len(line):
      c = line[index]
      if c != ' ':
        break
      index += 1
    return index

  def _SkipControlSequence(self, line, index):
    """Skip the control sequence at line[index].

    Args:
      line: The string.
      index: The starting index in string.

    Returns:
      The index in line after the control sequence or len(line) at end of
      string.
    """
    n = self._attr.GetControlSequenceLen(line[index:])
    if not n:
      n = 1
    return index + n

  def _SkipNest(self, line, index, open_chars='[(', close_chars=')]'):
    """Skip a [...] nested bracket group starting at line[index].

    Args:
      line: The string.
      index: The starting index in string.
      open_chars: The open nesting characters.
      close_chars: The close nesting characters.

    Returns:
      The index in line after the nesting group or len(line) at end of string.
    """
    nest = 0
    while index < len(line):
      c = line[index]
      index += 1
      if c in open_chars:
        nest += 1
      elif c in close_chars:
        nest -= 1
        if nest <= 0:
          break
      elif c == self._csi_char:
        index = self._SkipControlSequence(line, index)
    return index

  def _SplitWideSynopsisGroup(self, group, indent, running_width):
    """Splits a wide SYNOPSIS section group string to self._out.

    Args:
      group: The wide group string to split.
      indent: The prevailing left indent.
      running_width: The width of the self._out line in progress.

    Returns:
      The running_width after the group has been split and written to self._out.
    """
    prev_delimiter = ' '
    while group:
      # Check split delimiters in order for visual emphasis.
      for delimiter in (' | ', ' : ', ' ', ','):
        part, _, remainder = group.partition(delimiter)
        w = self._attr.DisplayWidth(part)
        if ((running_width + len(prev_delimiter) + w) >= self._width or
            prev_delimiter != ',' and delimiter == ','):
          if delimiter != ',' and (indent +
                                   self.SPLIT_INDENT +
                                   len(prev_delimiter) +
                                   w) >= self._width:
            # The next delimiter may produce a smaller first part.
            continue
          if prev_delimiter == ',':
            self._out.write(prev_delimiter)
            prev_delimiter = ' '
          if running_width != indent:
            running_width = indent + self.SPLIT_INDENT
            self._out.write('\n' + ' ' * running_width)
        self._out.write(prev_delimiter + part)
        running_width += len(prev_delimiter) + w
        prev_delimiter = delimiter
        group = remainder
        break
    return running_width

  def Synopsis(self, line, is_synopsis=False):
    """Renders NAME and SYNOPSIS lines as a second line indent.

    Collapses adjacent spaces to one space, deletes trailing space, and doesn't
    split top-level nested [...] or (...) groups. Also detects and does not
    count terminal control sequences.

    Args:
      line: The NAME or SYNOPSIS text.
      is_synopsis: if it is the synopsis section
    """
    # Split the line into token, token | token, and [...] groups.
    groups = []
    i = self._SkipSpace(line, 0)
    beg = i
    while i < len(line):
      c = line[i]
      if c == ' ':
        end = i
        i = self._SkipSpace(line, i)
        if i <= (len(line) - 1) and line[i] == '|' and line[i + 1] == ' ':
          i = self._SkipSpace(line, i + 1)
        else:
          groups.append(line[beg:end])
          beg = i
      elif c in '[(':
        i = self._SkipNest(line, i)
      elif c == self._csi_char:
        i = self._SkipControlSequence(line, i)
      else:
        i += 1
    if beg < len(line):
      groups.append(line[beg:])

    # Output the groups.
    indent = self._indent[0].indent - 1
    running_width = indent
    self._out.write(' ' * running_width)
    indent += self.INDENT
    for group in groups:
      w = self._attr.DisplayWidth(group) + 1
      if (running_width + w) >= self._width:
        running_width = indent
        self._out.write('\n' + ' ' * running_width)
        if (running_width + w) >= self._width:
          # The group is wider than the available width and must be split.
          running_width = self._SplitWideSynopsisGroup(
              group, indent, running_width)
          continue
      self._out.write(' ' + group)
      running_width += w
    self._out.write('\n\n')
