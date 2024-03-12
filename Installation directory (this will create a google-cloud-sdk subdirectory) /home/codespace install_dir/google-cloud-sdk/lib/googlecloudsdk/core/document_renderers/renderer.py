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

"""Cloud SDK markdown document renderer base class."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import io

from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_printer

import six
from six.moves import range  # pylint: disable=redefined-builtin


# Font Attributes.
BOLD, ITALIC, CODE = list(range(3))


class TableColumnAttributes(object):
  """Markdown table column attributes.

  Attributes:
    align: Column alignment, one of {'left', 'center', 'right'}.
    label: Column heading label string.
    width: Minimum column width.
  """

  def __init__(self, align='left', label=None, width=0):
    self.align = align
    self.label = label
    self.width = width


class TableAttributes(object):
  """Markdown table attributes.

  Attributes:
    box: True if table and rows framed by box.
    columns: The list of column attributes.
    heading: The number of non-empty headings.
    margin: Extra margin to handle post-processing indent.
  """

  def __init__(self, box=False):
    self.box = box
    self.heading = 0
    self.columns = []

  def AddColumn(self, align='left', label='', width=0):
    """Adds the next column attributes to the table."""
    if label:
      self.heading += 1
    self.columns.append(
        TableColumnAttributes(align=align, label=label, width=width))

  def GetPrintFormat(self, margin=0, width=0):
    """Constructs and returns a resource_printer print format.

    Args:
      margin: Right hand side padding when one or more columns are wrapped.
      width: The table width.

    Returns:
      The resource printer format string.
    """
    fmt = ['table']
    attr = []
    if self.box:
      attr.append('box')
    if not self.heading:
      attr.append('no-heading')
    if margin:
      attr.append('margin={}'.format(margin))
    if width:
      attr.append('width={}'.format(width))
    if attr:
      fmt.append('[' + ','.join(attr) + ']')
    fmt.append('(')
    for index, column in enumerate(self.columns):
      if index:
        fmt.append(',')
      fmt.append('[{}]:label={}:align={}'.format(
          index, repr(column.label or '').lstrip('u'), column.align))
      if column.width:
        fmt.append(':width={}'.format(column.width))
    if margin:
      fmt.append(':wrap')
    fmt.append(')')
    return ''.join(fmt)


@six.add_metaclass(abc.ABCMeta)
class Renderer(object):
  r"""Markdown renderer base class.

  The member functions provide an abstract document model that matches markdown
  entities to output document renderings.

  Attributes:
    _blank: True if the output already contains a blank line. Used to avoid
      sequences of 2 or more blank lines in the output.
    _command: The command split into component names.
    _font: The font attribute bitmask.
    _indent: List of left indentations in characters indexed by _level.
    _lang: ```lang\n...\n``` code block language. None if not in code block,
      '' if in code block with no explicit lang specified.
    _level: The section or list level counting from 0.
    _out: The output stream.
    _title: The document title.
    _width: The output width in characters.
    command_metadata: Optional metadata of command.
    command_node: The command object that the document is being rendered for.
  """

  def __init__(self, out=None, title=None, width=80, command_metadata=None,
               command_node=None):
    self._blank = True
    self._command = ['gcloud']  # use command[0] instead of literal 'gcloud'
    self._font = 0
    self._indent = []
    self._lang = None
    self._level = 0
    self._out = out or log.out
    self._title = title
    self._width = width
    self.command_metadata = command_metadata
    self.command_node = command_node

  @property
  def command(self):
    """Returns the command split into component names."""
    return self._command

  def Blank(self):
    """The last output line is blank."""
    self._blank = True

  def Content(self):
    """Some non-blank line content was added to the output."""
    self._blank = False

  def HaveBlank(self):
    """Returns True if the last output line is blank."""
    return self._blank

  def Entities(self, buf):
    """Converts special characters to their entity tags.

    This is applied after font embellishments.

    Args:
      buf: The normal text that may contain special characters.

    Returns:
      The escaped string.
    """
    return buf

  def Escape(self, buf):
    """Escapes special characters in normal text.

    This is applied before font embellishments.

    Args:
      buf: The normal text that may contain special characters.

    Returns:
      The escaped string.
    """
    return buf

  def Finish(self):
    """Finishes all output document rendering."""
    return None

  def Font(self, unused_attr, unused_out=None):
    """Returns the font embellishment string for attr.

    Args:
      unused_attr: None to reset to the default font, otherwise one of BOLD,
        ITALIC, or CODE.
      unused_out: Writes tags line to this stream if not None.

    Returns:
      The font embellishment string.
    """
    return ''

  def SetCommand(self, command):
    """Sets the document command name.

    Args:
      command: The command split into component names.
    """
    self._command = command

  def SetLang(self, lang):
    """Sets the ```...``` code block language.

    Args:
      lang: The language name, None if not in a code block, '' is no explicit
        language specified.
    """
    self._lang = lang

  def Line(self):
    """Renders a paragraph separating line."""
    pass

  def Link(self, target, text):
    """Renders an anchor.

    Args:
      target: The link target URL.
      text: The text to be displayed instead of the link.

    Returns:
      The rendered link anchor and text.
    """
    if text:
      if target and '://' in target:
        # Show non-local targets.
        return '{0} ({1})'.format(text, target)
      return text
    if target:
      return target
    return '[]()'

  def LinkGlobalFlags(self, line):
    """Add global flags links to line if any.

    Args:
      line: The text line.

    Returns:
      line with annoted global flag links.
    """
    return line

  def TableLine(self, line, indent=0):
    """Adds an indented table line to the output.

    Args:
      line: The line to add. A newline will be added.
      indent: The number of characters to indent the table.
    """
    self._out.write(indent * ' ' + line + '\n')

  def Table(self, table, rows):
    """Renders a table.

    Nested tables are not supported.

    Args:
      table: A TableAttributes object.
      rows: A list of rows where each row is a list of column strings.
    """
    self.Line()
    indent = self._indent[self._level].indent + 2
    margin = indent if any([True for r in rows if ' ' in r[-1]]) else 0
    buf = io.StringIO()
    resource_printer.Print(
        rows,
        table.GetPrintFormat(margin=margin, width=self._width),
        out=buf)
    for line in buf.getvalue().split('\n')[:-1]:
      self.TableLine(line, indent=indent)
    self.Content()
    self.Line()
