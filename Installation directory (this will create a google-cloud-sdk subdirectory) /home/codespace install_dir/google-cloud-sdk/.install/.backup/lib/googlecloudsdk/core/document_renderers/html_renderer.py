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

"""Cloud SDK markdown document HTML renderer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import re

from googlecloudsdk.core.document_renderers import renderer


class HTMLRenderer(renderer.Renderer):
  """Renders markdown to HTML.

  Attributes:
    _BULLET: A list of bullet type names indexed by list level modulo #bullets.
    _ESCAPE: Character element code name dict indexed by input character.
    _FONT_TAG: A list of font embellishment tag names indexed by font attribute.
    _document_ids: The set of html ids unique in the current document.
    _example: True if currently rendering an example.
    _fill: The number of characters in the current output line.
    _heading: A string of HTML tags that closes out a heading section.
    _level: The section or list level counting from 0.
    _paragraph: True if the output already contains a paragraph tag. Used to
      avoid sequences of 2 or more paragraph tags in the output.
    _pop: A list of list element closing tag names indexed by _level.
    _section: Section heading but no section body yet.
  """
  _BULLET = ('disc', 'circle', 'square')
  _ESCAPE = {'&': '&amp;', '<': '&lt;', '>': '&gt;'}
  _FONT_TAG = (('code',), ('code', 'var'), ('code',))

  def __init__(self, *args, **kwargs):
    super(HTMLRenderer, self).__init__(*args, **kwargs)
    self._document_ids = set()
    self._example = False
    self._fill = 0
    self._global_flags = False
    self._heading = ''
    self._level = 0
    self._paragraph = False
    self._pop = ['']
    self._section = False
    self._Title()
    self._out.write("""\
<!--
        THIS DOC IS GENERATED.  DO NOT EDIT.
  -->
<style>
  dd {
    margin-bottom: 1ex;
  }
  li {
    margin-top: 1ex; margin-bottom: 1ex;
  }
  .flag {
    white-space: nowrap;
  }
  .hangingindent {
    padding-left: 1.5em;
    text-indent: -1.5em;
  }
  .normalfont {
    font-weight: normal;
  }
  .notopmargin {
    margin-top: 0em;
  }
  .sectionbody {
    margin-top: .2em;
  }
</style>
</head>
<body>
<dl>
""")

  def _Title(self):
    """Renders an HTML document title."""
    self._out.write("""\
<html>
<head>
""")
    if self._title:
      self._out.write('<title>%s</title>\n' % self._title)
    self._out.write("""\
<style>
  code { color: green; }
</style>
<script>
  window.onload = function() {
    if (parent.navigation.navigate) {
      parent.navigation.navigate(document.location.href);
    }
  }
</script>
""")

  def _Flush(self):
    """Flushes the current collection of Fill() lines."""
    self._paragraph = False
    if self._fill:
      self._section = False
      if self._example:
        self._example = False
        self._out.write('</code>\n')
      self._fill = 0
      self._out.write('\n')
      self.Content()

  def GetDocumentID(self, name):
    """Returns a unique document id for name."""

    # name might already have HTML tags. The leading tags are stripped out,
    # along with everything from the first trailing tag to the end of name.
    #
    # After stripping name can be:
    #
    #   -- .*     Notation for 'the remaining args interpreted verbatim'. The
    #             -- and next space separated word are retained.
    #   --.*      A flag. Just the flag name is retained.
    #   [-.0-9]+  A version number heading.
    #   .*        A heading or definition list item. All words are retained.
    #
    # Finally, any remaining spaces are converted to '-'.

    def SingularizeCommandAndGroupDocumentID(name):
      """Returns singlularized name if name is 'COMMANDS' or 'GROUPS'."""

      # Our html docs self reference COMMAND and GROUP from the synopsis
      # using a local anchor tag. The section in markdown is pluralized,
      # This leads to a broken anchor link. This method fixes that by ensuring
      # that the DocumentID (section id) for COMMAND or GROUP is singular.

      return re.sub(r'(COMMAND|GROUP)S$', r'\1', name)

    m = re.match(r'(-- |\[)*'
                 '(<[^>]*>)*'
                 r'(?P<anchor>-[-_a-z0-9\[\]]+|[_A-Za-z.0-9 ][-_A-Za-z.0-9 ]*|'
                 r'[-.0-9]+)'
                 '.*',
                 name)
    if m:
      name = m.group('anchor')
    name = name.strip(' ').replace(' ', '-')

    name = SingularizeCommandAndGroupDocumentID(name)

    # Make sure the document_id return value is unique within this document.
    attempt = name
    number = 0
    while True:
      if attempt not in self._document_ids:
        self._document_ids.add(attempt)
        return attempt
      number += 1
      attempt = '{name}-{number}'.format(name=name, number=number)

  def Entities(self, buf):
    """Escapes special characters to their entity tags.

    This is applied after font embellishments.

    Args:
      buf: Normal text that may contain special characters.

    Returns:
      The string with special characters converted to entity tags.
    """
    # Translate ``...'' => ``...&acute;&actute;.
    esc = re.sub("(``[^`]*)''", r'\1&acute;&acute;', buf)
    return esc.replace('...', '&hellip;')

  def Escape(self, buf):
    """Escapes special characters in normal text.

    This is applied before font embellishments.

    Args:
      buf: Normal text that may contain special characters.

    Returns:
      The escaped string.
    """
    return ''.join(self._ESCAPE.get(c, c) for c in buf)

  def Example(self, line):
    """Displays line as an indented example.

    Args:
      line: The example line.
    """
    self.Blank()
    if not self._example:
      self._example = True
      self._fill = 2
      self._out.write('<p><code>\n')
    indent = len(line)
    line = line.lstrip()
    indent -= len(line)
    self._out.write('&nbsp;' * (self._fill + indent))
    self._out.write(line)
    self._out.write('<br>\n')

  def Fill(self, line):
    """Adds a line to the output, splitting to stay within the output width.

    Args:
      line: The text line.
    """
    if self._paragraph:
      self._paragraph = False
      self._out.write('<p>\n')
    self.Blank()
    if self._global_flags:
      self._global_flags = False
      line = self.LinkGlobalFlags(line)
    for word in line.split():
      n = len(word)
      if self._fill + n >= self._width:
        self._out.write('\n')
        self._fill = 0
      elif self._fill:
        self._fill += 1
        self._out.write(' ')
      self._fill += n
      self._out.write(word)

  def Finish(self):
    """Finishes all output document rendering."""
    self.Font(out=self._out)
    self.List(0)
    if self._heading:
      self._out.write(self._heading)
    self._out.write('\n</dl>\n</body>\n</html>\n')

  def Font(self, attr=None, out=None):
    """Returns the font embellishment string for attr.

    Args:
      attr: None to reset to the default font, otherwise one of renderer.BOLD,
        renderer.ITALIC, or renderer.CODE.
      out: Writes tags line to this stream if not None.

    Returns:
      The font embellishment HTML tag string.
    """
    tags = []
    if attr is None:
      for attr in (renderer.BOLD, renderer.ITALIC, renderer.CODE):
        mask = 1 << attr
        if self._font & mask:
          self._font ^= mask
          for tag in reversed(self._FONT_TAG[attr]):
            tags.append('</%s>' % tag)
    else:
      mask = 1 << attr
      self._font ^= mask
      if self._font & mask:
        for tag in self._FONT_TAG[attr]:
          tags.append('<%s>' % tag)
      else:
        for tag in reversed(self._FONT_TAG[attr]):
          tags.append('</%s>' % tag)
    embellishment = ''.join(tags)
    if out and embellishment:
      out.write(embellishment + '\n')
    return embellishment

  def _Heading(self, level, heading):
    """Renders an HTML heading.

    Args:
      level: The heading level counting from 1.
      heading: The heading text.
    """
    self._heading = '</dd>\n'
    level += 2
    if level > 9:
      level = 9
    self._out.write('\n<dt><h%d>%s</h%d></dt>\n<dd class="sectionbody">\n' % (
        level, heading, level))

  def Heading(self, level, heading):
    """Renders a heading.

    Args:
      level: The heading level counting from 1.
      heading: The heading text.
    """
    if level == 1 and heading.endswith('(1)'):
      return
    self._Flush()
    self.Font(out=self._out)
    self.List(0)
    if self._heading:
      self._out.write(self._heading)
    self._Heading(level, heading)
    self._section = True
    if heading.endswith(' WIDE FLAGS'):
      self._global_flags = True

  def Line(self):
    """Renders a paragraph separating line."""
    self._Flush()
    if not self.HaveBlank():
      self.Blank()
      self._paragraph = True

  def Link(self, target, text):
    """Renders an anchor.

    Args:
      target: The link target URL.
      text: The text to be displayed instead of the link.

    Returns:
      The rendered link anchor and text.
    """
    if ':' in target or target.startswith('www.'):
      return '<a href="{target}" target=_top>{text}</a>'.format(
          target=target, text=text or target)
    if '#' in target or target.endswith('..'):
      return '<a href="{target}">{text}</a>'.format(
          target=target, text=text or target)
    if not text:
      text = target.replace('/', ' ')
    tail = '/help'
    if target.endswith(tail):
      target = target[:-len(tail)]
    target = target.replace('/', '_') + '.html'
    return '<a href="{target}">{text}</a>'.format(target=target, text=text)

  def LinkGlobalFlags(self, line):
    """Add global flags links to line if any.

    Args:
      line: The text line.

    Returns:
      line with annoted global flag links.
    """
    return re.sub(
        r'(--[-a-z]+)',
        r'<a href="/#\1">\1</a>',
        line)

  def List(self, level, definition=None, end=False):
    """Renders a bullet or definition list item.

    Args:
      level: The list nesting level.
      definition: Bullet list if None, definition list otherwise.
      end: End of list if True.
    """
    self._Flush()
    while self._level and self._level > level:
      self._out.write(self._pop[self._level])
      self._level -= 1
    # pylint: disable=g-explicit-bool-comparison, '' is different from None here
    if end or not level:
      # End of list.
      return
    if definition is not None:
      # Definition list item.
      # Blank definition can be used for nested paragraphs.
      if self._level < level:
        self._level += 1
        if self._level >= len(self._pop):
          self._pop.append('')
        self._pop[self._level] = '</dd>\n</dl>\n'
        if self._section:
          self._section = False
          self._out.write('<dl class="notopmargin">\n')
        else:
          self._out.write('<dl>\n')
      elif 'dt' in self._pop[self._level]:
        self._out.write('</dt>\n')
        self._pop[self._level] = '</dd>\n</dl>\n'
      else:
        self._out.write('</dd>\n')
      if definition:
        self._out.write('<dt id="{document_id}"><span class="normalfont">'
                        '{definition}</span></dt>\n<dd>\n'.format(
                            document_id=self.GetDocumentID(definition),
                            definition=definition))
      elif self._level > 1 and 'dt' in self._pop[self._level]:
        self._out.write('<dd>\n')
      else:
        self._out.write('<dt><span class="normalfont">\n')
        self._pop[self._level] = '</span></dt>\n</dl>\n'
    else:  # definition is None
      # Bullet list item.
      if self._level < level:
        self._level += 1
        if self._level >= len(self._pop):
          self._pop.append('')
        self._pop[self._level] = '</li>\n</ul>\n'
        self._out.write('<ul style="list-style-type:' +
                        self._BULLET[(level - 1) % len(self._BULLET)] +
                        '">\n')
      else:
        self._out.write('</li>\n')
      self._out.write('<li>\n')

  def Synopsis(self, line, is_synopsis=False):
    """Renders NAME and SYNOPSIS lines as a hanging indent.

    Does not split top-level [...] or (...) groups.

    Args:
      line: The NAME or SYNOPSIS section text.
      is_synopsis: if it is the synopsis section
    """
    self._out.write('<dl class="notopmargin"><dt class="hangingindent">'
                    '<span class="normalfont">\n')

    # Add flag local links. NOTE: --no-foo defined under --foo.

    line = re.sub(r'(<code>)([-a-z0-9\[\]]+)(</code>)',
                  r'\1<a href="#\2">\2</a>\3',
                  line)
    line = re.sub('href="#--no-', 'href="#--', line)

    # Add positional local links.

    line = re.sub(r'([^[=]\[*<code><var>)([_A-Z0-9]+)(</var></code>)',
                  r'\1<a href="#\2">\2</a>\3',
                  line)

    line = re.sub(r'(<code><a href="#[-a-z0-9\[\]]+">[-a-z0-9\[\]]+'
                  r'(<[^>]*>|\S)*)',
                  r'<span class="flag">\1</span>',
                  line)
    # Because there are long argdicts, and this is only looking at the
    # synopsis section, lets end and start a new flag class at a comma so it
    # doesn't overflow the width
    if is_synopsis:
      line = re.sub('(,)',
                    r'\1</span><span class="flag">',
                    line)

    # Add self.command[0].upper() WIDE FLAGS local link.

    root = self.command[0].upper()
    line = re.sub(
        '>{root}_WIDE_FLAG '.format(root=root),
        '><a href="#{root}-WIDE-FLAGS">{root}_WIDE_FLAG</a> '.format(root=root),
        line)

    nest = 0
    chars = collections.deque(line)
    while chars:
      c = chars.popleft()
      if c in '[(':
        nest += 1
        if nest == 1:
          c = '<span>' + c
      elif c in ')]':
        nest -= 1
        if not nest:
          c += '</span>'
      elif nest == 1 and c == ' ' and chars and chars[0] == '|':
        # A top level group has nest == 1. 4 &nbsp; is aesthetically pleasing.
        c = '</span> <span>&nbsp;&nbsp;&nbsp;&nbsp;' + chars.popleft()
      self._out.write(c)
    self._out.write('\n</span></dt></dl>\n')

  def Table(self, table, rows):
    """Renders a table.

    Nested tables are not supported.

    Args:
      table: renderer.TableAttributes object.
      rows: A list of rows, each row is a list of column strings.
    """

    # Output the preamble.

    self._out.write('\n<blockquote>\n<table>\n')

    # Output the heading.

    if table.heading:
      self._out.write('<tr>\n')
      for column in table.columns:
        self._out.write('<th>{}</th>\n'.format(column.label or ''))
      self._out.write('</tr>\n')

    # Output the row data.

    for row in rows:
      self._out.write('<tr>\n')
      for index, col in enumerate(row):
        align = 'left'
        width = ''
        if index < len(table.columns):
          column = table.columns[index]
          align = column.align
          if column.width:
            width = ' width={}em'.format(column.width)
        self._out.write('<td align={}{}>{}</td>\n'.format(align, width, col))
      self._out.write('</tr>\n')

    # Output the postamble.

    self._out.write('</table>\n</blockquote>\n')
