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

"""Cloud SDK markdown document man page format renderer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.document_renderers import renderer


class ManRenderer(renderer.Renderer):
  """Renders markdown to man(1) input.

  Attributes:
    _BULLET: A list of bullet characters indexed by list level modulo #bullets.
    _ESCAPE: Character element code string dict indexed by input character.
    _FONT_TAG: Font embellishment tag string list indexed by font attribute.
    _example: True if currently rendering an example.
    _fill: The number of characters in the current output line.
    _level: The section or list level counting from 0.
    _th_emitted: True if .TH already emitted.
  """
  _BULLET = (r'\(bu', r'\(em')
  _ESCAPE = {'\\': r'\e', '-': r'\-'}
  _FONT_TAG = (r'\fB', r'\fI', r'\f5')

  def __init__(self, *args, **kwargs):
    super(ManRenderer, self).__init__(*args, **kwargs)
    self._example = False
    self._fill = 0
    self._level = 0
    self._th_emitted = False

  def _Flush(self):
    """Flushes the current collection of Fill() lines."""
    if self._fill:
      self._fill = 0
      self._out.write('\n')
    if self._example:
      self._example = False
      self._out.write('.RE\n')

  def Escape(self, buf):
    """Escapes special characters in normal text.

    Args:
      buf: The normal text that may contain special characters.

    Returns:
      The escaped string.
    """
    return ''.join(self._ESCAPE.get(c, c) for c in buf)

  def Example(self, line):
    """Displays line as an indented example.

    Args:
      line: The example line string.
    """
    if not self._example:
      self._example = True
      self._out.write('.RS 2m\n')
    self._out.write(line + '\n')

  def Fill(self, line):
    """Adds a line to the output, splitting to stay within the output width.

    Args:
      line: The line string.
    """
    escapes = 0
    for word in line.split():
      n = len(word)
      if self._fill + n + escapes >= self._width:
        self._out.write('\n')
        self._fill = 0
        if word[0] == "'":
          self._out.write('\\')
          escapes = 1
        else:
          escapes = 0
      elif self._fill:
        self._fill += 1
        self._out.write(' ')
      elif word[0] == "'":
        self._out.write('\\')
        escapes = 1
      else:
        escapes = 0
      self._fill += n
      self._out.write(word)

  def Finish(self):
    """Finishes all output document rendering."""
    self.Font(out=self._out)
    self.List(0)

  def Font(self, attr=None, out=None):
    """Returns the font embellishment string for attr.

    Args:
      attr: None to reset to the default font, otherwise one of renderer.BOLD,
        renderer.ITALIC, or renderer.CODE.
      out: Writes tags line to this stream if not None.

    Returns:
      The font embellishment string.
    """
    if attr is None:
      if self._font:
        self._font = 0
        tags = r'\fR'
      else:
        tags = ''
    else:
      mask = 1 << attr
      self._font ^= mask
      tags = self._FONT_TAG[attr] if (self._font & mask) else r'\fR'
    if out and tags:
      out.write(tags + '\n')
    return tags

  def Heading(self, level, heading):
    """Renders a heading.

    Args:
      level: The heading level counting from 1.
      heading: The heading text.
    """
    self._Flush()
    self.Font(out=self._out)
    self.List(0)
    if level == 1 and heading.endswith('(1)'):
      self._out.write('\n.TH "%s" 1\n' % heading[:-3])
      self._th_emitted = True
    else:
      if not self._th_emitted:
        self._out.write('\n.TH "%s" ""\n' % (self._title or 'NOTES'))
        self._th_emitted = True
      self._out.write('\n.SH "%s"\n' % heading)

  def Line(self):
    """Renders a paragraph separating line."""
    self._Flush()
    self._out.write('\n')

  def List(self, level, definition=None, end=False):
    """Renders a bullet or definition markdown list item.

    Args:
      level: The markdown list nesting level.
      definition: Bullet markdown list if None, definition markdown list
        otherwise.
      end: End of markdown list if True.
    """
    self._Flush()
    need_sp = False
    while self._level and self._level > level:
      self._out.write('.RE\n')
      self._level -= 1
      need_sp = True
    if need_sp:
      self._out.write('.sp\n')
    # pylint: disable=g-explicit-bool-comparison, '' is different from None here
    if end or not level:
      # End of list.
      return
    if self._level < level:
      self._level += 1
      self._out.write('.RS 2m\n')
    if definition is not None:
      # Definition list item.
      self._out.write('.TP 2m\n' + definition + '\n')
    else:
      # Bullet list item.
      self._out.write('.IP "%s" 2m\n' %
                      self._BULLET[(level - 1) % len(self._BULLET)])

  def Synopsis(self, line, is_synopsis=False):
    """Renders NAME and SYNOPSIS lines as a hanging indent.

    Does not split top-level [...] or (...) groups.

    Args:
      line: The synopsis text.
      is_synopsis: if it is the synopsis section
    """
    self._out.write('.HP\n')
    nest = 0
    for c in line:
      if c in '[(':
        nest += 1
      elif c in ')]':
        nest -= 1
      elif c == ' ' and nest:
        c = r'\ '
      self._out.write(c)
    self._out.write('\n')

  def Table(self, table, rows):
    """Renders a table.

    Nested tables are not supported.

    Args:
      table: renderer.TableAttributes object.
      rows: A list of rows, each row is a list of column strings.
    """
    # Output the preamble.

    self._out.write('\n.TS\ntab(\t);\n')

    # Output the heading.

    head_attr = ''
    data_attr = ''
    for column in table.columns:
      head_attr += ' ' + column.align[0]
      data_attr += ' ' + column.align[0]
      if column.width:
        head_attr += '({})'.format(column.width)
        data_attr += '({})'.format(column.width)
      head_attr += 'B'
    if table.heading:
      self._out.write(head_attr[1:] + '\n')
    self._out.write(data_attr[1:] + '.\n')
    self._out.write('\t'.join([c.label for c in table.columns]) + '\n')

    # Output the row data.

    for row in rows:
      self._out.write('\t'.join(row) + '\n')

    # Output the postamble.

    self._out.write('.TE\n')
