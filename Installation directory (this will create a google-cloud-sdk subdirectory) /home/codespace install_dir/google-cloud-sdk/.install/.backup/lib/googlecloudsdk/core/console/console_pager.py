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

"""Simple console pager."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
import sys

from googlecloudsdk.core.console import console_attr


class Pager(object):
  """A simple console text pager.

  This pager requires the entire contents to be available. The contents are
  written one page of lines at a time. The prompt is written after each page of
  lines. A one character response is expected. See HELP_TEXT below for more
  info.

  The contents are written as is. For example, ANSI control codes will be in
  effect. This is different from pagers like more(1) which is ANSI control code
  agnostic and miscalculates line lengths, and less(1) which displays control
  character names by default.

  Attributes:
    _attr: The current ConsoleAttr handle.
    _clear: A string that clears the prompt when written to _out.
    _contents: The entire contents of the text lines to page.
    _height: The terminal height in characters.
    _out: The output stream, log.out (effectively) if None.
    _prompt: The page break prompt.
    _search_direction: The search direction command, n:forward, N:reverse.
    _search_pattern: The current forward/reverse search compiled RE.
    _width: The termonal width in characters.
  """

  HELP_TEXT = """
  Simple pager commands:

    b, ^B, <PAGE-UP>, <LEFT-ARROW>
      Back one page.
    f, ^F, <SPACE>, <PAGE-DOWN>, <RIGHT-ARROW>
      Forward one page. Does not quit if there are no more lines.
    g, <HOME>
      Back to the first page.
    <number>g
      Go to <number> lines from the top.
    G, <END>
      Forward to the last page.
    <number>G
      Go to <number> lines from the bottom.
    h
      Print pager command help.
    j, +, <DOWN-ARROW>
      Forward one line.
    k, -, <UP-ARROW>
      Back one line.
    /pattern
      Forward search for pattern.
    ?pattern
      Backward search for pattern.
    n
      Repeat current search.
    N
      Repeat current search in the opposite direction.
    q, Q, ^C, ^D, ^Z
      Quit return to the caller.
    any other character
      Prompt again.

  Hit any key to continue:"""

  PREV_POS_NXT_REPRINT = -1, -1

  def __init__(self, contents, out=None, prompt=None):
    """Constructor.

    Args:
      contents: The entire contents of the text lines to page.
      out: The output stream, log.out (effectively) if None.
      prompt: The page break prompt, a defalt prompt is used if None..
    """
    self._contents = contents
    self._out = out or sys.stdout
    self._search_pattern = None
    self._search_direction = None

    # prev_pos, prev_next values to force reprint
    self.prev_pos, self.prev_nxt = self.PREV_POS_NXT_REPRINT
    # Initialize the console attributes.
    self._attr = console_attr.GetConsoleAttr()
    self._width, self._height = self._attr.GetTermSize()

    # Initialize the prompt and the prompt clear string.
    if not prompt:
      prompt = '{bold}--({{percent}}%)--{normal}'.format(
          bold=self._attr.GetFontCode(bold=True),
          normal=self._attr.GetFontCode())
    self._clear = '\r{0}\r'.format(' ' * (self._attr.DisplayWidth(prompt) - 6))
    self._prompt = prompt

    # Initialize a list of lines with long lines split into separate display
    # lines.
    self._lines = []
    for line in contents.splitlines():
      self._lines += self._attr.SplitLine(line, self._width)

  def _Write(self, s):
    """Mockable helper that writes s to self._out."""
    self._out.write(s)

  def _GetSearchCommand(self, c):
    """Consumes a search command and returns the equivalent pager command.

    The search pattern is an RE that is pre-compiled and cached for subsequent
    /<newline>, ?<newline>, n, or N commands.

    Args:
      c: The search command char.

    Returns:
      The pager command char.
    """
    self._Write(c)
    buf = ''
    while True:
      p = self._attr.GetRawKey()
      if p in (None, '\n', '\r') or len(p) != 1:
        break
      self._Write(p)
      buf += p
    self._Write('\r' + ' ' * len(buf) + '\r')
    if buf:
      try:
        self._search_pattern = re.compile(buf)
      except re.error:
        # Silently ignore pattern errors.
        self._search_pattern = None
        return ''
    self._search_direction = 'n' if c == '/' else 'N'
    return 'n'

  def _Help(self):
    """Print command help and wait for any character to continue."""
    clear = self._height - (len(self.HELP_TEXT) -
                            len(self.HELP_TEXT.replace('\n', '')))
    if clear > 0:
      self._Write('\n' * clear)
    self._Write(self.HELP_TEXT)
    self._attr.GetRawKey()
    self._Write('\n')

  def Run(self):
    """Run the pager."""
    # No paging if the contents are small enough.
    if len(self._lines) <= self._height:
      self._Write(self._contents)
      return

    # We will not always reset previous values.
    reset_prev_values = True
    # Save room for the prompt at the bottom of the page.
    self._height -= 1

    # Loop over all the pages.
    pos = 0
    while pos < len(self._lines):
      # Write a page of lines.
      nxt = pos + self._height
      if nxt > len(self._lines):
        nxt = len(self._lines)
        pos = nxt - self._height
      # Checks if the starting position is in between the current printed lines
      # so we don't need to reprint all the lines.
      if self.prev_pos < pos < self.prev_nxt:
        # we start where the previous page ended.
        self._Write('\n'.join(self._lines[self.prev_nxt:nxt]) + '\n')
      elif pos != self.prev_pos and nxt != self.prev_nxt:
        self._Write('\n'.join(self._lines[pos:nxt]) + '\n')

      # Handle the prompt response.
      percent = self._prompt.format(percent=100 * nxt // len(self._lines))
      digits = ''
      while True:
        # We want to reset prev values if we just exited out of the while loop
        if reset_prev_values:
          self.prev_pos, self.prev_nxt = pos, nxt
          reset_prev_values = False
        self._Write(percent)
        c = self._attr.GetRawKey()
        self._Write(self._clear)

        # Parse the command.
        if c in (None,    # EOF.
                 'q',     # Quit.
                 'Q',     # Quit.
                 '\x03',  # ^C  (unix & windows terminal interrupt)
                 '\x1b',  # ESC.
                ):
          # Quit.
          return
        elif c in ('/', '?'):
          c = self._GetSearchCommand(c)
        elif c.isdigit():
          # Collect digits for operation count.
          digits += c
          continue

        # Set the optional command count.
        if digits:
          count = int(digits)
          digits = ''
        else:
          count = 0

        # Finally commit to command c.
        if c in ('<PAGE-UP>', '<LEFT-ARROW>', 'b', '\x02'):
          # Previous page.
          nxt = pos - self._height
          if nxt < 0:
            nxt = 0
        elif c in ('<PAGE-DOWN>', '<RIGHT-ARROW>', 'f', '\x06', ' '):
          # Next page.
          if nxt >= len(self._lines):
            continue
          nxt = pos + self._height
          if nxt >= len(self._lines):
            nxt = pos
        elif c in ('<HOME>', 'g'):
          # First page.
          nxt = count - 1
          if nxt > len(self._lines) - self._height:
            nxt = len(self._lines) - self._height
          if nxt < 0:
            nxt = 0
        elif c in ('<END>', 'G'):
          # Last page.
          nxt = len(self._lines) - count
          if nxt > len(self._lines) - self._height:
            nxt = len(self._lines) - self._height
          if nxt < 0:
            nxt = 0
        elif c == 'h':
          self._Help()
          # Special case when we want to reprint the previous display.
          self.prev_pos, self.prev_nxt = self.PREV_POS_NXT_REPRINT
          nxt = pos
          break
        elif c in ('<DOWN-ARROW>', 'j', '+', '\n', '\r'):
          # Next line.
          if nxt >= len(self._lines):
            continue
          nxt = pos + 1
          if nxt >= len(self._lines):
            nxt = pos
        elif c in ('<UP-ARROW>', 'k', '-'):
          # Previous line.
          nxt = pos - 1
          if nxt < 0:
            nxt = 0
        elif c in ('n', 'N'):
          # Next pattern match search.
          if not self._search_pattern:
            continue
          nxt = pos
          i = pos
          direction = 1 if c == self._search_direction else -1
          while True:
            i += direction
            if i < 0 or i >= len(self._lines):
              break
            if self._search_pattern.search(self._lines[i]):
              nxt = i
              break
        else:
          # Silently ignore everything else.
          continue
        if nxt != pos:
          # We will exit the while loop because position changed so we can reset
          # prev values.
          reset_prev_values = True
          break
      pos = nxt
