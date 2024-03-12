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

"""A basic command line parser.

This command line parser does the bare minimum required to understand the
commands and flags being used as well as perform completion. This is not a
replacement for argparse (yet).
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum

from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.command_lib.interactive import lexer

import six


LOOKUP_COMMANDS = cli_tree.LOOKUP_COMMANDS
LOOKUP_CHOICES = cli_tree.LOOKUP_CHOICES
LOOKUP_COMPLETER = cli_tree.LOOKUP_COMPLETER
LOOKUP_FLAGS = cli_tree.LOOKUP_FLAGS
LOOKUP_GROUPS = cli_tree.LOOKUP_GROUPS
LOOKUP_IS_GROUP = cli_tree.LOOKUP_IS_GROUP
LOOKUP_IS_HIDDEN = cli_tree.LOOKUP_IS_HIDDEN
LOOKUP_IS_SPECIAL = 'interactive.is_special'
LOOKUP_NAME = cli_tree.LOOKUP_NAME
LOOKUP_NARGS = cli_tree.LOOKUP_NARGS
LOOKUP_POSITIONALS = cli_tree.LOOKUP_POSITIONALS
LOOKUP_TYPE = cli_tree.LOOKUP_TYPE

LOOKUP_CLI_VERSION = cli_tree.LOOKUP_CLI_VERSION


class ArgTokenType(enum.Enum):
  UNKNOWN = 0  # Unknown token type in any position
  PREFIX = 1  # Potential command name, maybe after lex.SHELL_TERMINATOR_CHARS
  GROUP = 2  # Command arg with subcommands
  COMMAND = 3  # Command arg
  FLAG = 4  # Flag arg
  FLAG_ARG = 5  # Flag value arg
  POSITIONAL = 6  # Positional arg
  SPECIAL = 7  # Special keyword that is followed by PREFIX.


class ArgToken(object):
  """Shell token info.

  Attributes:
    value: A string associated with the token.
    token_type: Instance of ArgTokenType
    tree: A subtree of CLI root.
    start: The index of the first char in the original string.
    end: The index directly after the last char in the original string.
  """

  def __init__(self, value, token_type=ArgTokenType.UNKNOWN, tree=None,
               start=None, end=None):
    self.value = value
    self.token_type = token_type
    self.tree = tree
    self.start = start
    self.end = end

  def __eq__(self, other):
    """Equality based on properties."""
    if isinstance(other, self.__class__):
      return self.__dict__ == other.__dict__
    return False

  def __repr__(self):
    """Improve debugging during tests."""
    return 'ArgToken({}, {}, {}, {})'.format(self.value, self.token_type,
                                             self.start, self.end)


class Parser(object):
  """Shell command line parser.

  Attributes:
    args:
    context:
    cmd:
    hidden:
    positionals_seen:
    root:
    statement:
    tokens:
  """

  def __init__(self, root, context=None, hidden=False):
    self.root = root
    self.hidden = hidden

    self.args = []
    self.cmd = self.root
    self.positionals_seen = 0
    self.previous_line = None
    self.statement = 0
    self.tokens = None

    self.SetContext(context)

  def SetContext(self, context=None):
    """Sets the default command prompt context."""
    self.context = six.text_type(context or '')

  def ParseCommand(self, line):
    """Parses the next command from line and returns a list of ArgTokens.

    The parse stops at the first token that is not an ARG or FLAG. That token is
    not consumed. The caller can examine the return value to determine the
    parts of the line that were ignored and the remainder of the line that was
    not lexed/parsed yet.

    Args:
      line: a string containing the current command line

    Returns:
      A list of ArgTokens.
    """
    self.tokens = lexer.GetShellTokens(line)
    self.cmd = self.root
    self.positionals_seen = 0

    self.args = []

    unknown = False
    while self.tokens:
      token = self.tokens.pop(0)
      value = token.UnquotedValue()

      if token.lex == lexer.ShellTokenType.TERMINATOR:
        unknown = False
        self.cmd = self.root
        self.args.append(ArgToken(value, ArgTokenType.SPECIAL, self.cmd,
                                  token.start, token.end))

      elif token.lex == lexer.ShellTokenType.FLAG:
        self.ParseFlag(token, value)

      elif token.lex == lexer.ShellTokenType.ARG and not unknown:
        if value in self.cmd[LOOKUP_COMMANDS]:
          self.cmd = self.cmd[LOOKUP_COMMANDS][value]
          if self.cmd[LOOKUP_IS_GROUP]:
            token_type = ArgTokenType.GROUP
          elif LOOKUP_IS_SPECIAL in self.cmd:
            token_type = ArgTokenType.SPECIAL
            self.cmd = self.root
          else:
            token_type = ArgTokenType.COMMAND
          self.args.append(ArgToken(value, token_type, self.cmd,
                                    token.start, token.end))

        elif self.cmd == self.root and '=' in value:
          token_type = ArgTokenType.SPECIAL
          self.cmd = self.root
          self.args.append(ArgToken(value, token_type, self.cmd,
                                    token.start, token.end))

        elif self.positionals_seen < len(self.cmd[LOOKUP_POSITIONALS]):
          positional = self.cmd[LOOKUP_POSITIONALS][self.positionals_seen]
          self.args.append(ArgToken(value, ArgTokenType.POSITIONAL,
                                    positional, token.start, token.end))
          if positional[LOOKUP_NARGS] not in ('*', '+'):
            self.positionals_seen += 1

        elif not value:  # trailing space
          break

        else:
          unknown = True
          if self.cmd == self.root:
            token_type = ArgTokenType.PREFIX
          else:
            token_type = ArgTokenType.UNKNOWN
          self.args.append(ArgToken(value, token_type, self.cmd,
                                    token.start, token.end))

      else:
        unknown = True
        self.args.append(ArgToken(value, ArgTokenType.UNKNOWN, self.cmd,
                                  token.start, token.end))

    return self.args

  def ParseFlag(self, token, name):
    """Parses the flag token and appends it to the arg list."""

    name_start = token.start
    name_end = token.end
    value = None
    value_start = None
    value_end = None

    if '=' in name:
      # inline flag value
      name, value = name.split('=', 1)
      name_end = name_start + len(name)
      value_start = name_end + 1
      value_end = value_start + len(value)

    flag = self.cmd[LOOKUP_FLAGS].get(name)
    if not flag or not self.hidden and flag[LOOKUP_IS_HIDDEN]:
      self.args.append(ArgToken(name, ArgTokenType.UNKNOWN, self.cmd,
                                token.start, token.end))
      return

    if flag[LOOKUP_TYPE] != 'bool' and value is None and self.tokens:
      # next arg is the flag value
      token = self.tokens.pop(0)
      value = token.UnquotedValue()
      value_start = token.start
      value_end = token.end

    self.args.append(ArgToken(name, ArgTokenType.FLAG, flag,
                              name_start, name_end))
    if value is not None:
      self.args.append(ArgToken(value, ArgTokenType.FLAG_ARG, None,
                                value_start, value_end))
