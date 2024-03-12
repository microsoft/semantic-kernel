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

"""gcloud shell completion."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum


SHELL_ESCAPE_CHAR = '\\'
SHELL_QUOTE_CHARS = ('"', "'")
SHELL_TERMINATOR_CHARS = (';', '&', '|', '(')
SHELL_REDIRECTION_CHARS = ('<', '>')


class ShellTokenType(enum.Enum):
  ARG = 1
  FLAG = 2
  TERMINATOR = 3
  IO = 4
  REDIRECTION = 5
  FILE = 6
  TRAILING_BACKSLASH = 7  # backslash at end of line


def UnquoteShell(s):
  r"""Processes a quoted shell argument from the lexer.

  Args:
    s: the raw quoted string (ex: "\"foo\" \\ 'bar'")

  Returns:
    An argument as would be passed from a shell to a process it forks
    (ex: "foo" \ 'bar').

  """
  # TODO(b/35347000): implement this function
  return s


class ShellToken(object):
  """Shell token info.

  Attributes:
    value: The token string with quotes and escapes preserved.
    lex: Instance of ShellTokenType
    start: the index of the first char of the raw value
    end: the index directly after the last char of the raw value
  """

  def __init__(self, value, lex=ShellTokenType.ARG, start=None, end=None):
    self.value = value
    self.lex = lex
    self.start = start
    self.end = end

  def UnquotedValue(self):
    if self.lex is ShellTokenType.ARG or self.lex is ShellTokenType.FLAG:
      return UnquoteShell(self.value)
    else:
      return self.value

  def __eq__(self, other):
    """Equality based on properties."""
    if isinstance(other, self.__class__):
      return self.__dict__ == other.__dict__
    return False

  def __repr__(self):
    """Improve debugging during tests."""
    return 'ShellToken({}, {}, {}, {})'.format(self.value, self.lex,
                                               self.start, self.end)


def GetShellToken(i, s):
  """Returns the next shell token at s[i:].

  Args:
    i: The index of the next character in s.
    s: The string to parse for shell tokens.

  Returns:
   A ShellToken, None if there are no more token in s.
  """
  # skip leading space
  index = i
  while True:
    if i >= len(s):
      if i > index:
        return ShellToken('', ShellTokenType.ARG, i - 1, i)
      return None
    c = s[i]
    if not c.isspace():
      break
    i += 1
  index = i

  # check for trailing backslash
  if len(s) - 1 == i and s[i] == '\\':
    i += 1
    return ShellToken(s[index:i], ShellTokenType.TRAILING_BACKSLASH, index, i)

  # check for IO redirection
  if (c in SHELL_REDIRECTION_CHARS or c.isdigit() and i + 1 < len(s) and
      s[i + 1] in SHELL_REDIRECTION_CHARS):
    index = i
    if s[i].isdigit():
      i += 1
    if i < len(s) and s[i] in SHELL_REDIRECTION_CHARS:
      i += 1
      while i < len(s) and s[i] in SHELL_REDIRECTION_CHARS:
        i += 1
      if i < len(s) - 1 and s[i] == '&' and s[i + 1].isdigit():
        i += 2
        lex = ShellTokenType.IO
      else:
        lex = ShellTokenType.REDIRECTION
      return ShellToken(s[index:i], lex, start=index, end=i)
    i = index

  # check for command terminators
  if c in SHELL_TERMINATOR_CHARS:
    i += 1
    return ShellToken(s[index:i], ShellTokenType.TERMINATOR, start=index, end=i)

  # find the next word
  quote = None
  while i < len(s):
    c = s[i]
    if c == quote:
      quote = None
    elif quote is None:
      if c in SHELL_QUOTE_CHARS:
        quote = c
      elif c == SHELL_ESCAPE_CHAR:
        if i+1 < len(s):
          i += 1
        else:
          # reached a trailing backslash
          break
      elif c.isspace():
        break
      elif c in SHELL_TERMINATOR_CHARS:
        break
    i += 1
  lex = ShellTokenType.FLAG if s[index] == '-' else ShellTokenType.ARG
  return ShellToken(s[index:i], lex, start=index, end=i)


def GetShellTokens(s):
  """Returns the list of ShellTokens in s.

  Args:
    s: The string to parse for shell tokens.

  Returns:
    The list of ShellTokens in s.
  """
  tokens = []
  i = 0
  while True:
    token = GetShellToken(i, s)
    if not token:
      break
    i = token.end
    tokens.append(token)
    if token.lex == ShellTokenType.REDIRECTION:
      token = GetShellToken(i, s)
      if not token:
        break
      i = token.end
      token.lex = ShellTokenType.FILE
      tokens.append(token)
  return tokens
