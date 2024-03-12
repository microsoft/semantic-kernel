# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Prompt completion support module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import sys

from googlecloudsdk.core.console import console_attr

from six.moves import range  # pylint: disable=redefined-builtin


def _IntegerCeilingDivide(numerator, denominator):
  """returns numerator/denominator rounded up if there is any remainder."""
  return -(-numerator // denominator)


def _TransposeListToRows(all_items, width=80, height=40, pad='  ', bold=None,
                         normal=None):
  """Returns padded newline terminated column-wise list for items.

  Used by PromptCompleter to pretty print the possible completions for TAB-TAB.

  Args:
    all_items: [str], The ordered list of all items to transpose.
    width: int, The total display width in characters.
    height: int, The total display height in lines.
    pad: str, String inserted before each column.
    bold: str, The bold font highlight control sequence.
    normal: str, The normal font highlight control sequence.

  Returns:
    [str], A padded newline terminated list of colum-wise rows for the ordered
    items list.  The return value is a single list, not a list of row lists.
    Convert the return value to a printable string by ''.join(return_value).
    The first "row" is preceded by a newline and all rows start with the pad.
  """

  def _Dimensions(items):
    """Returns the transpose dimensions for items."""
    longest_item_len = max(len(x) for x in items)
    column_count = int(width / (len(pad) + longest_item_len)) or 1
    row_count = _IntegerCeilingDivide(len(items), column_count)
    return longest_item_len, column_count, row_count

  def _TrimAndAnnotate(item, longest_item_len):
    """Truncates and appends '*' if len(item) > longest_item_len."""
    if len(item) <= longest_item_len:
      return item
    return item[:longest_item_len] + '*'

  def _Highlight(item, longest_item_len, difference_index, bold, normal):
    """Highlights the different part of the completion and left justfies."""
    length = len(item)
    if length > difference_index:
      item = (item[:difference_index] + bold +
              item[difference_index] + normal +
              item[difference_index+1:])
    return item + (longest_item_len - length) * ' '

  # Trim the items list until row_count <= height.
  items = set(all_items)
  longest_item_len, column_count, row_count = _Dimensions(items)
  while row_count > height and longest_item_len > 3:
    items = {_TrimAndAnnotate(x, longest_item_len - 2) for x in all_items}
    longest_item_len, column_count, row_count = _Dimensions(items)
  items = sorted(items)

  # Highlight the start of the differences.
  if bold:
    difference_index = len(os.path.commonprefix(items))
    items = [_Highlight(x, longest_item_len, difference_index, bold, normal)
             for x in items]

  # Do the column-wise transpose with padding and newlines included.
  row_data = ['\n']
  row_index = 0
  while row_index < row_count:
    column_index = row_index
    for _ in range(column_count):
      if column_index >= len(items):
        break
      row_data.append(pad)
      row_data.append(items[column_index])
      column_index += row_count
    row_data.append('\n')
    row_index += 1

  return row_data


def _PrefixMatches(prefix, possible_matches):
  """Returns the subset of possible_matches that start with prefix.

  Args:
    prefix: str, The prefix to match.
    possible_matches: [str], The list of possible matching strings.

  Returns:
    [str], The subset of possible_matches that start with prefix.
  """
  return [x for x in possible_matches if x.startswith(prefix)]


class PromptCompleter(object):
  """Prompt + input + completion.

  Yes, this is a roll-your own implementation.
  Yes, readline is that bad:
    linux: is unaware of the prompt even though it overrise raw_input()
    macos: different implementation than linux, and more brokener
    windows: didn't even try to implement
  """

  _CONTROL_C = '\x03'
  _DELETE = '\x7f'

  def __init__(self, prompt, choices=None, out=None, width=None, height=None,
               pad='  '):
    """Constructor.

    Args:
      prompt: str or None, The prompt string.
      choices: callable or list, A callable with no arguments that returns the
        list of all choices, or the list of choices.
      out: stream, The output stream, sys.stderr by default.
      width: int, The total display width in characters.
      height: int, The total display height in lines.
      pad: str, String inserted before each column.
    """
    self._prompt = prompt
    self._choices = choices
    self._out = out or sys.stderr
    self._attr = console_attr.ConsoleAttr()
    term_width, term_height = self._attr.GetTermSize()
    if width is None:
      width = 80
      if width > term_width:
        width = term_width
    self._width = width
    if height is None:
      height = 40
      if height > term_height:
        height = term_height
    self._height = height
    self._pad = pad

  def Input(self):
    """Reads and returns one line of user input with TAB complation."""
    all_choices = None
    matches = []
    response = []
    if self._prompt:
      self._out.write(self._prompt)
    c = None

    # Loop on input characters read one at a time without echo.
    while True:
      previous_c = c  # for detecting <TAB><TAB>.
      c = self._attr.GetRawKey()

      if c in (None, '\n', '\r', PromptCompleter._CONTROL_C) or len(c) != 1:
        # End of the input line.
        self._out.write('\n')
        break

      elif c in ('\b', PromptCompleter._DELETE):
        # Delete the last response character and reset the matches list.
        if response:
          response.pop()
          self._out.write('\b \b')
          matches = all_choices

      elif c == '\t':
        # <TAB> kicks in completion.
        response_prefix = ''.join(response)

        if previous_c == c:
          # <TAB><TAB> displays all possible completions.
          matches = _PrefixMatches(response_prefix, matches)
          if len(matches) > 1:
            self._Display(response_prefix, matches)

        else:
          # <TAB> complete as much of the current response as possible.

          if all_choices is None:
            if callable(self._choices):
              all_choices = self._choices()
            else:
              all_choices = self._choices
          matches = all_choices

          # Determine the longest prefix match and adjust the matches list.
          matches = _PrefixMatches(response_prefix, matches)
          response_prefix = ''.join(response)
          common_prefix = os.path.commonprefix(matches)

          # If the longest common prefix is longer than the response then the
          # portion past the response prefix chars can be appended.
          if len(common_prefix) > len(response):
            # As long as we are adding chars to the response its safe to prune
            # the matches list to the new common prefix.
            matches = _PrefixMatches(common_prefix, matches)
            self._out.write(common_prefix[len(response):])
            response = list(common_prefix)

      else:
        # Echo and append all remaining chars to the response.
        response.append(c)
        self._out.write(c)

    return ''.join(response)

  def _Display(self, prefix, matches):
    """Displays the possible completions and redraws the prompt and response.

    Args:
      prefix: str, The current response.
      matches: [str], The list of strings that start with prefix.
    """
    row_data = _TransposeListToRows(
        matches, width=self._width, height=self._height, pad=self._pad,
        bold=self._attr.GetFontCode(bold=True), normal=self._attr.GetFontCode())
    if self._prompt:
      row_data.append(self._prompt)
    row_data.append(prefix)
    self._out.write(''.join(row_data))
