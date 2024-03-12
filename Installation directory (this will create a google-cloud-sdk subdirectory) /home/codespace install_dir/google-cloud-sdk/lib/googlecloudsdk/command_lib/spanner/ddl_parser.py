# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Provides ddl preprocessing for the Spanner ddl."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging

from googlecloudsdk.core import exceptions


class DDLSyntaxError(exceptions.Error):
  pass


class DDLParser:
  """Parser for splitting ddl statements preserving GoogleSQL strings literals.

  DDLParse has a list of modes. If any mode is selected, control is given to the
  mode. If no mode is selected, the parser trys to enter the first mode that
  could it could enter. The parser handles splitting statements upon ';'.

  During parsing, a DDL has the following parts:
    * parts that has been processed: emitted or skipped.
    * followed by a buffer that has been matched by the current mode, which
      could be emitted or skipped by a mode. The start index of which is
      mode_start_index_.
    * followed by the next character indexed by next_index_, which could direct
      the parser to enter or exit a mode.
    * followed by the unprocessed character.

  DDLParser:
    * acts as a default mode.
    * provides utilities uesd by ParserMode to drive the parsing.
  """

  def __init__(self, ddl):
    self.ddl_ = ddl
    # Index of the current character to process
    self.next_index_ = 0
    # Mode the parser is in now.
    self.mode_ = None
    # Start index of the buffer that has been matched by a mode or the parser.
    self.mode_start_index_ = 0
    # List of modes. The first one that the parser could enter wins in case of
    # conflict.
    self.modes_ = [
        self.SkippingMode('--', ['\n', '\r']),
        # For all the string modes below, we need to escape \\. If we don't, \\"
        # will trigger mode exiting.
        # Triple double quote.
        # We need escape \", or \""" will be treated trigger mode exiting.
        self.PreservingMode('"""', ['"""'], ['\\"', '\\\\']),
        # Triple single quote.
        # We need escape \', or \''' will be treated trigger mode exiting.
        self.PreservingMode("'''", ["'''"], ["\\'", '\\\\']),
        # Single double quote.
        self.PreservingMode('"', ['"'], ['\\"', '\\\\']),
        # Single single quote.
        self.PreservingMode("'", ["'"], ["\\'", '\\\\']),
        # Single back quote.
        self.PreservingMode('`', ['`'], ['\\`', '\\\\']),
    ]
    # A list of statements. A statement is a list of ddl fragments.
    self.statements_ = []
    self.StartNewStatement()
    self.logger_ = logging.getLogger('SpannerDDLParser')

  def SkippingMode(self, enter_seq, exit_seqs):
    return DDLParserMode(self, enter_seq, exit_seqs, None, True)

  def PreservingMode(self, enter_seq, exit_seqs, escape_sequences):
    return DDLParserMode(self, enter_seq, exit_seqs, escape_sequences, False)

  def IsEof(self):
    return self.next_index_ == len(self.ddl_)

  def Advance(self, l):
    self.next_index_ += l

  def StartNewStatement(self):
    self.ddl_parts_ = []
    self.statements_.append(self.ddl_parts_)

  def EmitBuffer(self):
    if self.mode_start_index_ >= self.next_index_:
      # Buffer is empty.
      return
    self.ddl_parts_.append(
        self.ddl_[self.mode_start_index_:self.next_index_])
    self.SkipBuffer()
    self.logger_.debug('emitted: %s', self.ddl_parts_[-1])

  def SkipBuffer(self):
    self.mode_start_index_ = self.next_index_

  def EnterMode(self, mode):
    self.logger_.debug('enter mode: %s at index: %d',
                       mode.enter_seq_, self.next_index_)
    self.mode_ = mode

  def ExitMode(self):
    self.logger_.debug('exit mode: %s at index: %d',
                       self.mode_.enter_seq_, self.next_index_)
    self.mode_ = None

  def StartsWith(self, s):
    return self.ddl_[self.next_index_:].startswith(s)

  def Process(self):
    """Process the DDL."""
    while not self.IsEof():
      # Delegate to active mode if we have any.
      if self.mode_:
        self.mode_.Process()
        continue
      # Check statement break.
      if self.ddl_[self.next_index_] == ';':
        self.EmitBuffer()
        self.StartNewStatement()
        self.mode_start_index_ += 1
        self.Advance(1)
        continue
      # If we could enter any mode.
      for m in self.modes_:
        if m.TryEnter():
          self.EnterMode(m)
          break
      # No mode is found, consume the character.
      if not self.mode_:
        self.Advance(1)

    # At the end of parsing, we close the unclosed mode.
    if self.mode_ is not None:
      m = self.mode_
      if not m.is_to_skip_:
        raise DDLSyntaxError(
            'Unclosed %s start at index: %d, %s' %
            (m.enter_seq_, self.mode_start_index_, self.ddl_))
      self.mode_.Exit()
    else:
      self.EmitBuffer()
    self.logger_.debug('ddls: %s', self.statements_)
    res = [''.join(frags) for frags in self.statements_ if frags]
    # See https://stackoverflow.com/q/67857941
    if res and res[-1].isspace():
      return res[:-1]
    return res


class DDLParserMode:
  """A mode in DDLParser.

  A mode has one entering sequence, a list of exit sequences and one escape
  sequence. A mode could be:
    * skipping (e.x. comments), which skips the matched text.
    * non-skpping, (e.x. strings), which emits the matched text.
  """

  def __init__(self, parser, enter_seq, exit_seqs, escape_sequences,
               is_to_skip):
    self.parser_ = parser
    self.enter_seq_ = enter_seq
    self.exit_seqs_ = exit_seqs
    self.escape_sequences_ = escape_sequences
    self.is_to_skip_ = is_to_skip

  def TryEnter(self):
    """Trys to enter into the mode."""
    res = self.parser_.StartsWith(self.enter_seq_)
    if res:
      self.parser_.EmitBuffer()
      self.parser_.Advance(len(self.enter_seq_))
    return res

  def Exit(self):
    if self.is_to_skip_:
      self.parser_.SkipBuffer()
    else:
      self.parser_.EmitBuffer()
    self.parser_.ExitMode()

  def FindExitSeqence(self):
    """Finds a matching exit sequence."""
    for s in self.exit_seqs_:
      if self.parser_.StartsWith(s):
        return s
    return None

  def Process(self):
    """Process the ddl at the current parser index."""
    # Put escape sequence into buffer
    if self.escape_sequences_:
      for seq in self.escape_sequences_:
        if self.parser_.StartsWith(seq):
          self.parser_.Advance(len(self.escape_sequences_))
          return
    # Check if we should exit the current mode
    exit_seq = self.FindExitSeqence()
    if not exit_seq:
      self.parser_.Advance(1)
      return

    # Before exit, put exit_seq into buffer for non skipping mode
    if not self.is_to_skip_:
      self.parser_.Advance(len(exit_seq))
    self.Exit()


def PreprocessDDLWithParser(ddl_text):
  return DDLParser(ddl_text).Process()
