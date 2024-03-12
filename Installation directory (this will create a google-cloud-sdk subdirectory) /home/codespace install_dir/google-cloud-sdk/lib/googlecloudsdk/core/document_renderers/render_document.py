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

"""Cloud SDK markdown document renderer.

This module marshals markdown renderers to convert Cloud SDK markdown to text,
HTML and manpage documents. The renderers are self-contained, allowing the
Cloud SDK runtime to generate documents on the fly for all target architectures.

The MarkdownRenderer class parses markdown from an input stream and renders it
using the Renderer class. The Renderer member functions provide an abstract
document model that matches markdown entities to the output document, e.g., font
embellishment, section headings, lists, hanging indents, text margins, tables.
There is a Renderer derived class for each output style that writes the result
on an output stream returns Rendere.Finish().
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import re
import sys

from googlecloudsdk.core import argv_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.document_renderers import devsite_renderer
from googlecloudsdk.core.document_renderers import html_renderer
from googlecloudsdk.core.document_renderers import linter_renderer
from googlecloudsdk.core.document_renderers import man_renderer
from googlecloudsdk.core.document_renderers import markdown_renderer
from googlecloudsdk.core.document_renderers import renderer
from googlecloudsdk.core.document_renderers import text_renderer


STYLES = {
    'devsite': devsite_renderer.DevSiteRenderer,
    'html': html_renderer.HTMLRenderer,
    'man': man_renderer.ManRenderer,
    'markdown': markdown_renderer.MarkdownRenderer,
    'text': text_renderer.TextRenderer,
    'linter': linter_renderer.LinterRenderer
}


def _GetNestedGroup(buf, i, beg, end):
  """Returns the index in buf of the end of the nested beg...end group.

  Args:
    buf: Input buffer.
    i: The buf[] index of the first beg character.
    beg: The group begin character.
    end: The group end character.

  Returns:
    The index in buf of the end of the nested beg...end group, 0 if there is
    no group.
  """
  if buf[i] != beg:
    return 0
  nesting = 0
  while i < len(buf):
    if buf[i] == beg:
      nesting += 1
    elif buf[i] == end:
      nesting -= 1
      if nesting <= 0:
        return i
    i += 1
  return 0


def _IsValidTarget(target):
  """Returns True if target is a valid anchor/link target."""
  return not any(c in target for c in ' ,()[]')


def _IsFlagValueLink(buf, i):
  """Return True if the link is set as the flag value."""
  return re.search('--.*=https?$', buf[:i])


class DocumentStyleError(exceptions.Error):
  """An exception for unknown document styles."""

  def __init__(self, style):
    message = ('Unknown markdown document style [{style}] -- must be one of:'
               ' {styles}.'.format(style=style,
                                   styles=', '.join(sorted(STYLES.keys()))))
    super(DocumentStyleError, self).__init__(message)


class _ListElementState(object):
  """List element state.

  Attributes:
    bullet: True if the current element is a bullet.
    ignore_line: The number of blank line requests to ignore.
    level: List element nesting level counting from 0.
    line_break_seen: True if line break has been seen for bulleted lists.
  """

  def __init__(self):
    self.bullet = False
    self.ignore_line = 0
    self.level = 0
    self.line_break_seen = False


class MarkdownRenderer(object):
  """Reads markdown and renders to a document.

  Attributes:
    _EMPHASIS: The font emphasis attribute dict indexed by markdown character.
    _buf: The current output line.
    _code_block_indent: ```...``` code block indent if >= 0.
    _depth: List nesting depth counting from 0.
    _edit: True if NOTES edits are required.
    _example: The current example indentation space count.
    _fin: The markdown input stream.
    _line: The current input line.
    _lists: _ListElementState list element state stack indexed by _depth.
    _next_example: The next example indentation space count.
    _notes: Additional text for the NOTES section.
    _paragraph: True if the last line was ``+'' paragraph at current indent.
    _next_paragraph: The next line starts a new paragraph at same indentation.
    _renderer: The document_renderer.Renderer subclass.
    command_metadata: Optional metadata of command.
    command_node: The command object that the document is being rendered for.
  """
  _EMPHASIS = {'*': renderer.BOLD, '_': renderer.ITALIC, '`': renderer.CODE}

  def __init__(self, style_renderer, fin=sys.stdin, notes=None,
               command_metadata=None, command_node=None):
    """Initializes the renderer.

    Args:
      style_renderer: The document_renderer.Renderer subclass.
      fin: The markdown input stream.
      notes: Optional sentences for the NOTES section.
      command_metadata: Optional metadata of command.
      command_node: The command object that the document is being rendered for.
    """
    self._renderer = style_renderer
    self._buf = ''
    self._fin = fin
    self._notes = notes
    self._edit = self._notes
    self._lists = [_ListElementState()]
    self._code_block_indent = -1
    self._depth = 0
    self._example = 0
    self._next_example = 0
    self._paragraph = False
    self._peek = None
    self._next_paragraph = False
    self._line = None
    self.command_metadata = command_metadata
    self._example_regex = '$ gcloud'
    self._last_list_level = None
    self._in_example_section = False
    self.command_node = command_node

  def _AnchorStyle1(self, buf, i):
    """Checks for link:target[text] hyperlink anchor markdown.

    Hyperlink anchors are of the form:
      <link> ':' <target> [ '[' <text> ']' ]
    For example:
      http://www.google.com[Google Search]
    The underlying renderer determines how the parts are displayed.

    Args:
      buf: Input buffer.
      i: The buf[] index of ':'.

    Returns:
      (i, back, target, text)
        i: The buf[] index just past the link, 0 if no link.
        back: The number of characters to retain before buf[i].
        target: The link target.
        text: The link text.
    """
    if i >= 3 and buf[i - 3:i] == 'ftp':
      back = 3
      target_beg = i - 3
    elif i >= 4 and buf[i - 4:i] == 'http':
      back = 4
      target_beg = i - 4
    elif i >= 4 and buf[i - 4:i] == 'link':
      back = 4
      target_beg = i + 1
    elif i >= 5 and buf[i - 5:i] == 'https':
      back = 5
      target_beg = i - 5
    elif i >= 6 and buf[i - 6:i] == 'mailto':
      back = 6
      target_beg = i - 6
    else:
      return 0, 0, None, None
    text_beg = 0
    text_end = 0
    while True:
      if i >= len(buf) or buf[i].isspace():
        # Just a link with no text.
        if buf[i - 1] == '.':
          # Drop trailing '.' that is probably a sentence-ending period.
          i -= 1
        target_end = i
        text_beg = i
        text_end = i - 1
        break
      if buf[i] == '[':
        # Explicit link text inside [...].
        target_end = i
        text_beg = i + 1
        text_end = _GetNestedGroup(buf, i, '[', ']')
        break
      if buf[i] in '{}()<>\'"`*':
        # Reject code sample or parameterized links
        break
      i += 1
    if not text_end:
      return 0, 0, None, None
    return (text_end + 1, back, buf[target_beg:target_end],
            buf[text_beg:text_end])

  def _AnchorStyle2(self, buf, i):
    """Checks for [text](target) hyperlink anchor markdown.

    Hyperlink anchors are of the form:
      '[' <text> ']' '(' <target> ')'
    For example:
      [Google Search](http://www.google.com)
      [](http://www.show.the.link)
    The underlying renderer determines how the parts are displayed.

    Args:
      buf: Input buffer.
      i: The buf[] index of ':'.

    Returns:
      (i, target, text)
        i: The buf[] index just past the link, 0 if no link.
        target: The link target.
        text: The link text.
    """
    text_beg = i + 1
    text_end = _GetNestedGroup(buf, i, '[', ']')
    if not text_end or text_end >= len(buf) - 1 or buf[text_end + 1] != '(':
      return 0, None, None
    target_beg = text_end + 2
    target_end = _GetNestedGroup(buf, target_beg - 1, '(', ')')
    if not target_end or target_end <= target_beg:
      return 0, None, None
    return (target_end + 1, buf[target_beg:target_end], buf[text_beg:text_end])

  def _Attributes(self, buf=None):
    """Converts inline markdown attributes in self._buf.

    Args:
      buf: Convert markdown from this string instead of self._buf.

    Returns:
      A string with markdown attributes converted to render properly.
    """
    # String append used on ret below because of anchor text look behind.
    emphasis = '' if self._code_block_indent >= 0 or self._example else '*_`'
    ret = ''
    if buf is None:
      buf = self._buf
      self._buf = ''
    if buf:
      buf = self._renderer.Escape(buf)
      i = 0
      is_literal = False
      while i < len(buf):
        c = buf[i]
        if c == ':':
          index_after_anchor, back, target, text = self._AnchorStyle1(buf, i)
          if (index_after_anchor and _IsValidTarget(target) and
              not _IsFlagValueLink(buf, i)):
            ret = ret[:-back]
            i = index_after_anchor - 1
            c = self._renderer.Link(target, text)
        elif c == '[':
          index_after_anchor, target, text = self._AnchorStyle2(buf, i)
          if index_after_anchor and _IsValidTarget(target):
            i = index_after_anchor - 1
            c = self._renderer.Link(target, text)
        elif c in emphasis:
          # Treating some apparent font embelishment markdown as literal input
          # is the hairiest part of markdown. This code catches the common
          # programming clash of '*' as a literal globbing character in path
          # matching examples. It basically works for the current use cases.
          l = buf[i - 1] if i else ' '  # The char before c.
          r = buf[i + 1] if i < len(buf) - 1 else ' '  # The char after c.
          if l != '`' and c == '`' and r == '`':
            x = buf[i + 2] if i < len(buf) - 2 else ' '  # The char after r.
            if x == '`':
              # Render inline ```...``` code block enclosed literals.
              index_at_code_block_quote = buf.find('```', i + 2)
              if index_at_code_block_quote > 0:
                ret += self._renderer.Font(renderer.CODE)
                ret += buf[i + 3:index_at_code_block_quote]
                ret += self._renderer.Font(renderer.CODE)
                i = index_at_code_block_quote + 3
                continue
            else:
              # Render inline air quotes along with the enclosed literals.
              index_at_air_quote = buf.find("''", i)
              if index_at_air_quote > 0:
                index_at_air_quote += 2
                ret += buf[i:index_at_air_quote]
                i = index_at_air_quote
                continue
          if r == c:
            # Doubled markers are literal.
            c += c
            i += 1
          elif (c == '*' and l in ' /' and r in ' ./' or
                c != '`' and l in ' /' and r in ' .'):
            # Path-like glob patterns are literal.
            pass
          elif l.isalnum() and r.isalnum():
            # No embellishment switching in words.
            pass
          elif is_literal and c == '*':
            # '*' should be considered as literal when contained in code block
            pass
          else:
            if c == '`':
              # mark code block start or end
              is_literal = not is_literal
            c = self._renderer.Font(self._EMPHASIS[c])
        ret += c
        i += 1
    return self._renderer.Entities(ret)

  def _Example(self, i):
    """Renders self._line[i:] as an example.

    This is a helper function for _ConvertCodeBlock() and _ConvertExample().

    Args:
      i: The current character index in self._line.
    """
    if self._line[i:]:
      self._Fill()
      if not self._example or self._example > i:
        self._example = i
      self._next_example = self._example
      self._buf = self._line[self._example:]
      self._renderer.Example(self._Attributes())

  def _Fill(self):
    """Sends self._buf to the renderer and clears self._buf."""
    if self._buf:
      self._renderer.Fill(self._Attributes())

  def _ReadLine(self):
    """Reads and possibly preprocesses the next markdown line from self._fin.

    Returns:
      The next markdown input line.
    """
    if self._peek is not None:
      line = self._peek
      self._peek = None
      return line
    return self._fin.readline()

  def _PushBackLine(self, line):
    """Pushes back one lookahead line. The next _ReadlLine will return line."""
    self._peek = line

  def _ConvertMarkdownToMarkdown(self):
    """Generates markdown with additonal NOTES if requested."""
    if not self._edit:
      self._renderer.Write(self._fin.read())
      return
    while True:
      line = self._ReadLine()
      if not line:
        break
      self._renderer.Write(line)
      if self._notes and line == '## NOTES\n':
        self._renderer.Write('\n' + self._notes + '\n')
        self._notes = ''
    if self._notes:
      self._renderer.Write('\n\n## NOTES\n\n' + self._notes + '\n')

  def _ConvertBlankLine(self, i):
    """Detects and converts a blank markdown line (length 0).

    Resets the indentation to the default and emits a blank line. Multiple
    blank lines are suppressed in the output.

    Args:
      i: The current character index in self._line.

    Returns:
      -1 if the input line is a blank markdown, i otherwise.
    """
    if self._line:
      return i
    self._Fill()
    if self._lists[self._depth].bullet:
      self._renderer.List(self._depth - 1, end=True)
      if self._depth:
        self._depth -= 1
      else:
        self._lists[self._depth].bullet = False
    if self._lists[self._depth].ignore_line:
      self._lists[self._depth].ignore_line -= 1
    if not self._lists[self._depth].line_break_seen:
      self._lists[self._depth].line_break_seen = True
    if not self._depth or not self._lists[
        self._depth].ignore_line or self._lists[self._depth].line_break_seen:
      self._renderer.Line()
    return -1

  def _ConvertParagraph(self, i):
    """Detects and converts + markdown line (length 1).

    Emits a blank line but retains the current indent.

    Args:
      i: The current character index in self._line.

    Returns:
      -1 if the input line is a '+' markdown, i otherwise.
    """
    if len(self._line) != 1 or self._line[0] != '+':
      return i
    self._Fill()
    self._lists[self._depth].line_break_seen = True
    if self._lists[self._depth].bullet:
      self._renderer.List(self._depth - 1, end=True)
      if self._depth:
        self._depth -= 1
      else:
        self._lists[self._depth].bullet = False
    self._renderer.Line()
    self._next_paragraph = True
    return -1

  def _ConvertHeading(self, i):
    """Detects and converts a markdown heading line.

    = level-1 [=]
    # level-1 [#]
    == level-2 [==]
    ## level-2 [##]

    Args:
      i: The current character index in self._line.

    Returns:
      -1 if the input line is a heading markdown, i otherwise.
    """
    start_index = i
    marker = self._line[i]
    if marker not in ('=', '#'):
      return start_index
    while i < len(self._line) and self._line[i] == marker:
      i += 1
    if i >= len(self._line) or self._line[i] != ' ':
      return start_index
    if self._line[-1] == marker:
      if (not self._line.endswith(self._line[start_index:i]) or
          self._line[-(i - start_index + 1)] != ' '):
        return start_index
      end_index = -(i - start_index + 1)
    else:
      end_index = len(self._line)
    self._Fill()
    self._buf = self._line[i + 1:end_index]
    heading = self._Attributes()
    if i == 1 and heading.endswith('(1)'):
      self._renderer.SetCommand(heading[:-3].lower().split('_'))
    self._renderer.Heading(i, heading)
    self._depth = 0
    if heading in ['NAME', 'SYNOPSIS']:
      if heading == 'SYNOPSIS':
        is_synopsis_section = True
      else:
        is_synopsis_section = False
      while True:
        self._buf = self._ReadLine()
        if not self._buf:
          break
        self._buf = self._buf.rstrip()
        if self._buf:
          self._renderer.Synopsis(self._Attributes(),
                                  is_synopsis=is_synopsis_section)
          break
    elif self._notes and heading == 'NOTES':
      self._buf = self._notes
      self._notes = None
    self._in_example_section = (heading == 'EXAMPLES')
    return -1

  def _ConvertOldTable(self, i):
    """Detects and converts a sequence of markdown table lines.

    This method will consume multiple input lines if the current line is a
    table heading. The table markdown sequence is:

       [...format="csv"...]
       |====*
       col-1-data-item,col-2-data-item...
         ...
       <blank line ends table>

    Args:
      i: The current character index in self._line.

    Returns:
      -1 if the input lines are table markdown, i otherwise.
    """
    if (self._line[0] != '[' or self._line[-1] != ']' or
        'format="csv"' not in self._line):
      return i
    line = self._ReadLine()
    if not line:
      return i
    if not line.startswith('|===='):
      self._PushBackLine(line)
      return i

    rows = []
    while True:
      self._buf = self._ReadLine()
      if not self._buf:
        break
      self._buf = self._buf.rstrip()
      if self._buf.startswith('|===='):
        break
      rows.append(self._Attributes().split(','))
    self._buf = ''

    table = renderer.TableAttributes()
    if len(rows) > 1:
      for label in rows[0]:
        table.AddColumn(label=label)
      rows = rows[1:]
    if table.columns and rows:
      self._renderer.Table(table, rows)
    return -1

  def _ConvertTable(self, i):
    """Detects and converts a sequence of markdown table lines.

    Markdown attributes are not supported in headings or column data.

    This method will consume multiple input lines if the current line is a
    table heading or separator line. The table markdown sequence is:

      heading line

        heading-1 | ... | heading-n
          OR for boxed table
        | heading-1 | ... | heading-n |

      separator line

        --- | ... | ---
          OR for boxed table
        | --- | ... | --- |
          WHERE
        :---  align left
        :---: align center
        ---:  align right
        ----* length >= fixed_width_length sets column fixed width

      row data lines

        col-1-data-item | ... | col-n-data-item
          ...

      blank line ends table

    Args:
      i: The current character index in self._line.

    Returns:
      -1 if the input lines are table markdown, i otherwise.
    """
    fixed_width_length = 8

    if ' | ' not in self._line:
      return self._ConvertOldTable(i)
    if '---' in self._line:
      head = False
      line = self._line
    else:
      head = True
      line = self._ReadLine()
    if not line or '---' not in line:
      if line is not self._line:
        self._PushBackLine(line)
      return self._ConvertOldTable(i)

    # Parse the heading and separator lines.

    box = False
    if head:
      heading = re.split(r' *\| *', self._line.strip())
      if not heading[0] and not heading[-1]:
        heading = heading[1:-1]
        box = True
    else:
      heading = []
    sep = re.split(r' *\| *', line.strip())
    if not sep[0] and not sep[-1]:
      sep = sep[1:-1]
      box = True
    if heading and len(heading) != len(sep):
      if line is not self._line:
        self._PushBackLine(line)
      return self._ConvertOldTable(i)

    # Committed to table markdown now.

    table = renderer.TableAttributes(box=box)

    # Determine the column attributes.

    for index in range(len(sep)):
      align = 'left'
      s = sep[index]
      if s.startswith(':'):
        if s.endswith(':'):
          align = 'center'
      elif s.endswith(':'):
        align = 'right'
      label = heading[index] if index < len(heading) else None
      width = len(s) if len(s) >= fixed_width_length else 0
      table.AddColumn(align=align, label=label, width=width)

    # Collect the column data by rows. Blank or + line terminates the data.

    rows = []
    while True:
      line = self._ReadLine()
      if line in (None, '', '\n', '+\n'):
        self._PushBackLine(line)
        break
      row = re.split(r' *\| *', line.rstrip())
      rows.append(row)

    if rows:
      self._renderer.Table(table, rows)
    self._buf = ''
    return -1

  def _ConvertIndentation(self, i):
    """Advances i past any indentation spaces.

    Args:
      i: The current character index in self._line.

    Returns:
      i after indentation spaces skipped.
    """
    while i < len(self._line) and self._line[i] == ' ':
      i += 1
    return i

  def _ConvertCodeBlock(self, i):
    """Detects and converts a ```...``` code block markdown.

    Args:
      i: The current character index in self._line.

    Returns:
      -1 if the input line is part of a code block markdown, i otherwise.
    """
    if self._line[i:].startswith('```'):
      lang = self._line[i+3:]
      if not lang:
        if self._code_block_indent >= 0:
          self._code_block_indent = -1
        else:
          self._code_block_indent = i
        self._renderer.SetLang('' if self._code_block_indent >= 0 else None)
        return -1
      if self._code_block_indent < 0 and lang.isalnum():
        self._renderer.SetLang(lang)
        self._code_block_indent = i
        return -1
    if self._code_block_indent < 0:
      return i
    self._Example(self._code_block_indent)
    return -1

  def _ConvertDefinitionList(self, i):
    """Detects and converts a definition list item markdown line.

         [item-level-1]:: [definition-line]
         [definition-lines]
         [item-level-2]::: [definition-line]
         [definition-lines]

    Args:
      i: The current character index in self._line.

    Returns:
      -1 if the input line is a definition list item markdown, i otherwise.
    """
    if i:
      return i
    index_at_definition_markdown = self._line.find('::')
    if index_at_definition_markdown < 0:
      return i
    level = 1
    list_level = None
    original_i = i
    i = index_at_definition_markdown + 2
    while i < len(self._line) and self._line[i] == ':':
      i += 1
      level += 1
    # If the multiple colons are not followed by whitespace, assume that this
    # is content, not markdown. (Important for IPv6 notation, etc.)
    if i < len(self._line) and not self._line[i].isspace():
      return original_i
    while i < len(self._line) and self._line[i].isspace():
      i += 1
    end = i >= len(self._line) and not index_at_definition_markdown
    if end:
      # Bare ^:::$ is end of list which pops to previous list level.
      level -= 1
    if self._line.endswith('::'):
      self._last_list_level = level
    elif self._last_list_level and not self._line.startswith('::'):
      list_level = self._last_list_level + 1
    if (self._lists[self._depth].bullet or
        self._lists[self._depth].level < level):
      self._depth += 1
      if self._depth >= len(self._lists):
        self._lists.append(_ListElementState())
    else:
      while self._lists[self._depth].level > level:
        self._depth -= 1
    self._Fill()
    if end:
      i = len(self._line)
      definition = None
    else:
      self._lists[self._depth].bullet = False
      self._lists[self._depth].ignore_line = 2
      self._lists[self._depth].level = level
      self._buf = self._line[:index_at_definition_markdown]
      definition = self._Attributes()
    if list_level:
      level = list_level
    self._renderer.List(level, definition=definition, end=end)
    if i < len(self._line):
      self._buf += self._line[i:]
    return -1

  def _ConvertBulletList(self, i):
    """Detects and converts a bullet list item markdown line.

    The list item indicator may be '-' or '*'. nesting by multiple indicators:

        - level-1
        -- level-2
        - level-1

    or nesting by indicator indentation:

        * level-1
          * level-2
        * level-1

    Args:
      i: The current character index in self._line.

    Returns:
      -1 if the input line is a bullet list item markdown, i otherwise.
    """
    if self._example or self._line[i] not in '-*':
      return i
    bullet = self._line[i]
    level = i / 2
    start_index = i
    while i < len(self._line) and self._line[i] == bullet:
      i += 1
      level += 1
    if i >= len(self._line) or self._line[i] != ' ':
      return start_index
    if (self._lists[self._depth].bullet and
        self._lists[self._depth].level >= level):
      while self._lists[self._depth].level > level:
        self._depth -= 1
    else:
      self._depth += 1
      if self._depth >= len(self._lists):
        self._lists.append(_ListElementState())
    self._lists[self._depth].bullet = True
    self._lists[self._depth].ignore_line = 0
    self._lists[self._depth].line_break_seen = False
    self._lists[self._depth].level = level
    self._Fill()
    self._renderer.List(self._depth)
    while i < len(self._line) and self._line[i] == ' ':
      i += 1
    self._buf += self._line[i:]
    return -1

  def _ConvertExample(self, i):
    """Detects and converts an example markdown line.

    Example lines are indented by one or more space characters.

    Args:
      i: The current character index in self._line.

    Returns:
      -1 if the input line is is an example line markdown, i otherwise.
    """
    example_allowed = False if self._lists[self._depth].bullet else True
    if not self._in_example_section:
      example_allowed = example_allowed and (not self._buf.strip())
    if not i or not example_allowed and not (self._example or self._paragraph):
      return i
    self._Example(i)
    return -1

  def _ConvertEndOfList(self, i):
    """Detects and converts an end of list markdown line.

    Args:
      i: The current character index in self._line.

    Returns:
      -1 if the input line is an end of list markdown, i otherwise.
    """
    if i or not self._depth:
      return i
    if not self._lists[self._depth].line_break_seen:
      return i
    if self._lists[self._depth].ignore_line > 1:
      self._lists[self._depth].ignore_line -= 1
    if not self._lists[self._depth].ignore_line:
      self._Fill()
      self._renderer.List(self._depth - 1, end=True)
    return i  # More conversion possible.

  def _ConvertRemainder(self, i):
    """Detects and converts any remaining markdown text.

    The input line is always consumed by this method. It should be the last
    _Convert*() method called for each input line.

    Args:
      i: The current character index in self._line.

    Returns:
      -1
    """
    self._lists[self._depth].line_break_seen = False
    self._buf += ' ' + self._line[i:]
    return -1

  def _Finish(self):
    """Flushes the fill buffer and checks for NOTES.

    A previous _ConvertHeading() will have cleared self._notes if a NOTES
    section has already been seen.

    Returns:
      The renderer Finish() value.
    """
    self._Fill()
    if self._notes:
      self._renderer.Line()
      self._renderer.Heading(2, 'NOTES')
      self._buf += self._notes
      self._Fill()
    return self._renderer.Finish()

  def Run(self):
    """Renders the markdown from fin to out and returns renderer.Finish()."""
    if isinstance(self._renderer, markdown_renderer.MarkdownRenderer):
      self._ConvertMarkdownToMarkdown()
      return
    while True:
      self._example = self._next_example
      self._next_example = 0
      self._paragraph = self._next_paragraph
      self._next_paragraph = False
      self._line = self._ReadLine()
      if not self._line:
        break
      if self._line.startswith(self._example_regex):
        self._line = ' ' * self._example + '  ' + self._line
      self._line = self._line.rstrip()
      i = 0
      # Each _Convert*() function can:
      # - consume the markdown at self._line[i:] and return -1
      # - ignore self._line[i:] and return i
      # - change the class state, optionally advance i, and return i
      # Conversion on the current state._line stop when -1 is returned.
      for detect_and_convert in [
          self._ConvertBlankLine,
          self._ConvertParagraph,
          self._ConvertHeading,
          self._ConvertTable,
          self._ConvertIndentation,
          self._ConvertCodeBlock,
          self._ConvertDefinitionList,
          self._ConvertBulletList,
          self._ConvertExample,
          self._ConvertEndOfList,
          self._ConvertRemainder]:
        i = detect_and_convert(i)
        if i < 0:
          break
    return self._Finish()


def RenderDocument(style='text', fin=None, out=None, width=80, notes=None,
                   title=None, command_metadata=None, command_node=None):
  """Renders markdown to a selected document style.

  Args:
    style: The rendered document style name, must be one of the STYLES keys.
    fin: The input stream containing the markdown.
    out: The output stream for the rendered document.
    width: The page width in characters.
    notes: Optional sentences inserted in the NOTES section.
    title: The document title.
    command_metadata: Optional metadata of command, including available flags.
    command_node: The command object that the document is being rendered for.

  Raises:
    DocumentStyleError: The markdown style was unknown.
  """

  if style not in STYLES:
    raise DocumentStyleError(style)
  style_renderer = STYLES[style](out=out or sys.stdout, title=title,
                                 width=width, command_metadata=command_metadata,
                                 command_node=command_node)
  MarkdownRenderer(style_renderer, fin=fin or sys.stdin, notes=notes,
                   command_metadata=command_metadata).Run()


class CommandMetaData(object):
  """Object containing metadata of command to be passed into linter renderer."""

  def __init__(self, flags=None, bool_flags=None, is_group=True):
    self.flags = flags if flags else []
    self.bool_flags = bool_flags if bool_flags else []
    self.is_group = is_group


def main(argv):
  """Standalone markdown document renderer."""

  parser = argparse.ArgumentParser(
      description='Renders markdown on the standard input into a document on '
      'the standard output.')

  parser.add_argument(
      '--notes',
      metavar='SENTENCES',
      help='Inserts SENTENCES into the NOTES section which is created if '
      'needed.')

  parser.add_argument(
      '--style',
      metavar='STYLE',
      choices=sorted(STYLES.keys()),
      default='text',
      help='The output style.')

  parser.add_argument(
      '--title',
      metavar='TITLE',
      help='The document title.')

  args = parser.parse_args(argv[1:])

  RenderDocument(args.style, notes=args.notes, title=args.title,
                 command_metadata=None)


if __name__ == '__main__':
  main(argv_utils.GetDecodedArgv())
