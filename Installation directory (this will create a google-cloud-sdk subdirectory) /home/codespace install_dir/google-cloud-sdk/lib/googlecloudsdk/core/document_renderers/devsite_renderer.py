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

import re

from googlecloudsdk.core.document_renderers import devsite_scripts
from googlecloudsdk.core.document_renderers import html_renderer


class DevSiteRenderer(html_renderer.HTMLRenderer):
  """Renders markdown to DevSiteHTML.

  Devsite-Specific Attributes:
  _opentag: True if <code> tag on Example command is not closed, False otherwise
  """

  def __init__(self, *args, **kwargs):
    super(DevSiteRenderer, self).__init__(*args, **kwargs)
    self._opentag = False
    self._whole_example = ''

  def _Title(self):
    """Renders an HTML document title."""
    self._out.write(
        '<html devsite="">\n'
        '<head>\n')
    if self._title:
      self._out.write(
          '<title>' + self._title + '</title>\n')
    self._out.write(
        '<meta http-equiv="Content-Type" content="text/html; '
        'charset=UTF-8">\n'
        '<meta name="project_path" value="/sdk/docs/_project.yaml">\n'
        '<meta name="book_path" value="/sdk/_book.yaml">\n')
    for comment, script in devsite_scripts.SCRIPTS:
      self._out.write('<!-- {comment} -->\n{script}\n'.format(comment=comment,
                                                              script=script))

  def _Heading(self, unused_level, heading):
    """Renders a DevSite heading.

    Args:
      unused_level: The heading level counting from 1.
      heading: The heading text.
    """
    self._heading = '</dd>\n</section>\n'

    if heading == 'INFORMATION':
      # Wrap INFORMATION section with is_tpc dynamic var to display on TPC only.
      self._out.write('{% dynamic if request.is_tpc %}')
      self._heading += '{% dynamic endif %}'

    self._out.write('\n<section id="{document_id}">\n'
                    '<dt>{heading}</dt>\n<dd class="sectionbody">\n'.format(
                        document_id=self.GetDocumentID(heading),
                        heading=heading))

  def _Flush(self):
    """Flushes the current collection of Fill() lines."""
    if self._example and self._lang is not None:
      self._out.write('\n')
      return
    self._paragraph = False
    if self._fill:
      self._section = False
      if self._example:
        self._example = False
        self._out.write('</pre>\n')
      self._fill = 0
      self._out.write('\n')
      self._blank = False

  def WrapFlags(self, tag, match_regex, css_classes):
    """Wraps all regex matches from example in tag with classes."""
    matches = [m.span() for m in re.finditer(match_regex, self._whole_example)]
    wrapped_example = ''
    # Two pointer flag wrapping
    left = 0
    for match_left, match_right in matches:
      wrapped_example += self._whole_example[left:match_left]
      wrapped_example += '<' + tag + ' class="' + ' '.join(css_classes) + '">'
      wrapped_example += self._whole_example[match_left:match_right]
      wrapped_example += '</' + tag + '>'
      left = match_right
    wrapped_example += self._whole_example[left:]
    return wrapped_example

  def FlushExample(self):
    """Prints full example string with devsite tags to output stream."""
    self._out.write('<code class="devsite-terminal">')
    self._out.write(self.WrapFlags('span', r'-(-\w+)+', ['flag']))
    self._out.write('</code>\n')
    self._whole_example = ''

  def Example(self, line):
    """Displays line as an indented example.

    Args:
      line: The example line.
    """
    self._blank = True
    if not self._example:
      self._example = True
      self._in_command_block = False
      # Set self._fill to indicate that we need to close a section in
      # _Flush()
      self._fill = 2
      if not self._lang:
        self._out.write('<pre class="prettyprint lang-sh wrap-code">\n')
      elif self._lang in ('pretty', 'yaml'):
        self._out.write('<pre class="prettyprint lang-sh wrap-code">\n')
      else:
        self._out.write(
            '<pre class="prettyprint lang-{lang} wrap-code">\n'.format(
                lang=self._lang))
    indent = len(line)
    line = line.lstrip()
    indent -= len(line)
    command_pattern = re.compile(r'\A\$\s+')
    if command_pattern.match(line):
      self._in_command_block = True
    if self._in_command_block:
      line = command_pattern.sub('', line)
      if line.endswith('\\'):
        # stripping '\' because devsite-terminal class is always on one line
        self._whole_example += line[:-1]
      else:
        self._whole_example += line
        self.FlushExample()

        self._in_command_block = False
    else:
      self._out.write(' ' * indent + line + '\n')

  def Link(self, target, text):
    """Renders an anchor.

    Args:
      target: The link target URL.
      text: The text to be displayed instead of the link.

    Returns:
      The rendered link anchor and text.
    """
    if target != self.command[0] and (
        '/' not in target or ':' in target or '#' in target or
        target.startswith('www.') or target.endswith('/..')):
      return '<a href="{target}">{text}</a>'.format(target=target,
                                                    text=text or target)

    # Massage the target href to match the DevSite layout.
    target_parts = target.split('/')
    if target_parts[-1] == 'help':
      target_parts.pop()
    if len(target_parts) > 1 and target_parts[1] == 'meta':
      return target + ' --help'
    return '<a href="/sdk/{head}/{tail}">{text}</a>'.format(
        head=target_parts[0], tail='/'.join(['reference'] + target_parts[1:]),
        text=text or target)

  def LinkGlobalFlags(self, line):
    """Add global flags links to line if any.

    Args:
      line: The text line.

    Returns:
      line with annoted global flag links.
    """
    return re.sub(
        r'(--[-a-z]+)',
        r'<code><a href="/sdk/{}/reference/#\1">\1</a></code>'.format(
            self.command[0]), line)
