# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

r"""Multiline output for Cloud SDK.

This module contains a set of classes that are useful for managing console
output that can be updated that spans multiple lines.

Currently only SimpleSuffixConsoleOutput is offered which only supports
updating the last added message. SimpleSuffixConsoleOutput is basically a
collection of semantically distinct messages to be outputted to the console.
These messages all have a suffix, and SimpleSuffixConsoleOutput supports
updating the suffix of the last added message. Calling UpdateConsole on
a SimpleSuffixConsoleOutput will update these messages and any changes
to the console.

Example usage:
  # Example for a simple spinner
  spinner = ['|', '/', '-', '\\']
  num_spinner_marks = len(spinner)

  # Define a ConsoleOutput message
  output = SimpleSuffixConsoleOutput(sys.stderr)

  # Add the message you want to be displayed for the spinner and update the
  # console to show the message.
  message = sscm.AddMessage('Instance is being created...')
  output.UpdateConsole()

  > Instance is being created

  # Start the spinner by updating the message and then updating the console.
  for i in range(20):
    output.UpdateMessage(message, spinner[i % num_spinner_marks])
    output.UpdateConsole()
    time.sleep(0.1)

  > Instance is being created...|
  > Instance is being created.../
  > ...

  output.UpdateMessage(message, 'done\n')
  output.UpdateConsole()

  > Instance is being created...done
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import threading

from googlecloudsdk.core.console import console_attr

import six


INDENTATION_WIDTH = 2


class ConsoleOutput(six.with_metaclass(abc.ABCMeta, object)):
  """Manages the printing and formatting of multiline console output.

  It is up to implementations of this metaclass to determine how different
  messages will added to the output.
  """

  def UpdateConsole(self):
    """Updates the console output to show any updated or added messages."""
    pass


class SimpleSuffixConsoleOutput(ConsoleOutput):
  r"""A simple, suffix-only implementation of ConsoleOutput.

  In this context, simple means that only updating the last line is supported.
  This means that this is supported in all ASCII environments as it only relies
  on carriage returns ('\r') for modifying output. Suffix-only means that only
  modifying the ending of messages is supported, either via a
  detail_message_callback or by modifying the suffix of a SuffixConsoleMessage.
  """

  def __init__(self, stream):
    """Constructor.

    Args:
      stream: The output stream to write to.
    """
    self._stream = stream
    self._messages = []
    self._last_print_index = 0
    self._lock = threading.Lock()
    super(SimpleSuffixConsoleOutput, self).__init__()

  def AddMessage(self, message, detail_message_callback=None,
                 indentation_level=0):
    """Adds a SuffixConsoleMessage to the SimpleSuffixConsoleOutput object.

    Args:
      message: str, The message that will be displayed.
      detail_message_callback: func() -> str, A no argument function that will
        be called and the result will be appended to the message on each call
        to UpdateConsole.
      indentation_level: int, The indentation level of the message. Each
        indentation is represented by two spaces.

    Returns:
      SuffixConsoleMessage, a message object that can be used to dynamically
      change the printed message.
    """
    with self._lock:
      return self._AddMessage(
          message,
          detail_message_callback=detail_message_callback,
          indentation_level=indentation_level)

  def _AddMessage(self, message, detail_message_callback=None,
                  indentation_level=0):
    console_message = SuffixConsoleMessage(
        message,
        self._stream,
        detail_message_callback=detail_message_callback,
        indentation_level=indentation_level)
    self._messages.append(console_message)
    return console_message

  def UpdateMessage(self, message, new_suffix):
    """Updates the suffix of the given SuffixConsoleMessage."""
    if not message:
      raise ValueError('A message must be passed.')
    if message not in self._messages:
      raise ValueError(
          'The given message does not belong to this output object.')
    if self._messages and message != self._messages[-1]:
      raise ValueError('Only the last added message can be updated.')
    with self._lock:
      message._UpdateSuffix(new_suffix)  # pylint: disable=protected-access

  def UpdateConsole(self):
    with self._lock:
      self._UpdateConsole()

  def _UpdateConsole(self):
    """Updates the console output to show any updated or added messages."""
    if self._messages:
      # Check if there have been new messages added
      if self._last_print_index < (len(self._messages) - 1):
        # Print all the new messages starting at the last message printed
        # and separate them with newlines.
        for message in self._messages[self._last_print_index:-1]:
          message.Print()
          self._stream.write('\n')
        # Update last print index
        self._last_print_index = len(self._messages) - 1
      self._messages[self._last_print_index].Print()


# TODO(b/123531304): Support text with escape codes.
class SuffixConsoleMessage(object):
  """A suffix-only implementation of ConsoleMessage."""

  def __init__(self, message, stream, suffix='',
               detail_message_callback=None, indentation_level=0):
    """Constructor.

    Args:
      message: str, the message that this object represents.
      stream: The output stream to write to.
      suffix: str, The suffix that will be appended to the very end of the
        message.
      detail_message_callback: func() -> str, A no argument function that will
        be called and the result will be added after the message and before the
        suffix on every call to Print().
      indentation_level: int, The indentation level of the message. Each
        indentation is represented by two spaces.
    """
    self._stream = stream
    self._message = message
    self._suffix = suffix
    # TODO(b/111592003): May be better to get this on demand.
    # TODO(b/112460253): On terminals that don't automatically line wrap, use
    # the entire console width.
    # Some terminals will move the cursor to the next line once console_width
    # characters have been written. So for now we need to use 1 less than the
    # actual console width to prevent automatic wrapping leading to improper
    # text formatting.
    self._console_width = console_attr.ConsoleAttr().GetTermSize()[0] - 1
    if self._console_width < 0:
      self._console_width = 0
    self._detail_message_callback = detail_message_callback
    self._level = indentation_level

    # Private attributes used for printing.
    self._no_output = False
    if (self._console_width - (INDENTATION_WIDTH * indentation_level)) <= 0:
      # The indentation won't fit into the width of the console. In this case
      # just don't output. This should be rare and better than failing the
      # command.
      self._no_output = True
    self._num_lines = 0
    self._lines = []
    self._has_printed = False

  def _UpdateSuffix(self, suffix):
    """Updates the suffix for this message."""
    if not isinstance(suffix, six.string_types):
      raise TypeError('expected a string or other character buffer object')
    self._suffix = suffix

  def Print(self, print_all=False):
    """Prints out the message to the console.

    The implementation of this function assumes that when called, the
    cursor position of the terminal is on the same line as the last line
    that this function printed (and nothing more). The exception for this is if
    this is the first time that print is being called on this message or if
    print_all is True. The implementation should also return the cursor to
    the last line of the printed message. The cursor position in this case
    should be at the end of printed text to avoid text being overwritten.

    Args:
      print_all: bool, if the entire message should be printed instead of just
        updating the message.
    """
    if self._console_width == 0 or self._no_output:
      # This can happen if we're on a pseudo-TTY or if the indentation level
      # cannot be supported; return to prevent the process from being
      # unresponsive.
      return

    message = self.GetMessage()
    if not message:
      # No message, so don't go through the effort of printing.
      return

    # This is the first time we're printing, so set up some variables.
    if not self._has_printed or print_all:
      self._has_printed = True

      # Clear the current line so that our output is as we expect.
      self._ClearLine()
      self._lines = self._SplitMessageIntoLines(message)
      self._num_lines = len(self._lines)
      # Since this is the first print, write out the entire message.
      for line in self._lines:
        self._WriteLine(line)
      return

    new_lines = self._SplitMessageIntoLines(message)
    new_num_lines = len(new_lines)
    if new_num_lines < self._num_lines:
      # This means the callback or suffix created shorter message and the
      # number of lines shrank. The best thing we can do here is just output
      # a new line and reprint everything.
      self._stream.write('\n')
      for line in new_lines:
        self._WriteLine(line)
    else:
      # Here there are a greater or equal amount of lines. However, we do not
      # know if lines are equivalent. We first need to check if n-1 lines have
      # not changed.
      matching_lines = self._GetNumMatchingLines(new_lines)
      if self._num_lines - matching_lines <= 1:
        # All the lines up the last printed line are the same, so we can just
        # update the current line and print out any new lines.
        lines_to_print = new_num_lines - self._num_lines + 1
        self._ClearLine()
        for line in new_lines[-1 * lines_to_print:]:
          self._WriteLine(line)
      else:
        # This (potentially multiline) message has changed on a previous line.
        # No choice but to declare bankruptcy and output a new line and reprint
        # lines.
        self._stream.write('\n')
        for line in new_lines:
          self._WriteLine(line)

    # Update saved state
    self._lines = new_lines
    self._num_lines = new_num_lines

  def GetMessage(self):
    if self._detail_message_callback:
      detail_message = self._detail_message_callback()
      if detail_message:
        return self._message + detail_message + self._suffix
    return self._message + self._suffix

  @property
  def effective_width(self):
    """The effective width when the indentation level is considered."""
    return self._console_width - (INDENTATION_WIDTH * self._level)

  def _GetNumMatchingLines(self, new_lines):
    matching_lines = 0
    for i in range(min(len(new_lines), self._num_lines)):
      if new_lines[i] != self._lines[i]:
        break
      matching_lines += 1
    return matching_lines

  def _SplitMessageIntoLines(self, message):
    """Converts message into a list of strs, each representing a line."""
    lines = []
    pos = 0
    # Add check for width being less than indentation
    while pos < len(message):
      lines.append(message[pos:pos+self.effective_width])
      pos += self.effective_width
      if pos < len(message):
        # Explicit newline is useful for testing.
        lines[-1] += '\n'
    return lines

  def _ClearLine(self):
    self._stream.write('\r{}\r'.format(' ' * self._console_width))

  def _WriteLine(self, line):
    self._stream.write(self._level * INDENTATION_WIDTH * ' ' + line)
    self._stream.flush()


class MultilineConsoleOutput(ConsoleOutput):
  r"""An implementation of ConsoleOutput which supports multiline updates.

  This means all messages can be updated and actually have their output
  be updated on the terminal. The main difference between this class and
  the simple suffix version is that updates here are updates to the entire
  message as this provides more flexibility.

  This class accepts messages containing ANSI escape codes. The width
  calculations will be handled correctly currently only in this class.
  """

  def __init__(self, stream):
    """Constructor.

    Args:
      stream: The output stream to write to.
    """
    self._stream = stream
    self._messages = []
    self._last_print_index = 0
    self._lock = threading.Lock()
    self._last_total_lines = 0
    self._may_have_update = False
    super(MultilineConsoleOutput, self).__init__()

  def AddMessage(self, message, indentation_level=0):
    """Adds a MultilineConsoleMessage to the MultilineConsoleOutput object.

    Args:
      message: str, The message that will be displayed.
      indentation_level: int, The indentation level of the message. Each
        indentation is represented by two spaces.

    Returns:
      MultilineConsoleMessage, a message object that can be used to dynamically
      change the printed message.
    """
    with self._lock:
      return self._AddMessage(
          message,
          indentation_level=indentation_level)

  def _AddMessage(self, message, indentation_level=0):
    self._may_have_update = True
    console_message = MultilineConsoleMessage(
        message,
        self._stream,
        indentation_level=indentation_level)
    self._messages.append(console_message)
    return console_message

  def UpdateMessage(self, message, new_message):
    """Updates the message of the given MultilineConsoleMessage."""
    if not message:
      raise ValueError('A message must be passed.')
    if message not in self._messages:
      raise ValueError(
          'The given message does not belong to this output object.')
    with self._lock:
      message._UpdateMessage(new_message)  # pylint: disable=protected-access
      self._may_have_update = True

  def UpdateConsole(self):
    with self._lock:
      self._UpdateConsole()

  def _GetAnsiCursorUpSequence(self, num_lines):
    """Returns an ANSI control sequences that moves the cursor up num_lines."""
    return '\x1b[{}A'.format(num_lines)

  def _UpdateConsole(self):
    """Updates the console output to show any updated or added messages."""
    if not self._may_have_update:
      return

    # Reset at the start so if gcloud exits, the cursor is in the proper place.
    # We need to track the number of outputted lines of the last update because
    # new messages may have been added so it can't be computed from _messages.
    if self._last_total_lines:
      self._stream.write(self._GetAnsiCursorUpSequence(self._last_total_lines))

    total_lines = 0
    force_print_rest = False
    for message in self._messages:
      num_lines = message.num_lines
      total_lines += num_lines
      if message.has_update or force_print_rest:
        force_print_rest |= message.num_lines_changed
        message.Print()
      else:
        # Move onto next message
        self._stream.write('\n' * num_lines)
    self._last_total_lines = total_lines
    self._may_have_update = False


class MultilineConsoleMessage(object):
  """A multiline implementation of ConsoleMessage."""

  def __init__(self, message, stream, indentation_level=0):
    """Constructor.

    Args:
      message: str, the message that this object represents.
      stream: The output stream to write to.
      indentation_level: int, The indentation level of the message. Each
        indentation is represented by two spaces.
    """
    self._stream = stream
    # Some terminals will move the cursor to the next line once console_width
    # characters have been written. So for now we need to use 1 less than the
    # actual console width to prevent automatic wrapping leading to improper
    # text formatting.
    self._console_attr = console_attr.GetConsoleAttr()
    self._console_width = self._console_attr.GetTermSize()[0] - 1
    if self._console_width < 0:
      self._console_width = 0
    self._level = indentation_level

    # Private attributes used for printing.
    self._no_output = False
    if (self._console_width - (INDENTATION_WIDTH * indentation_level)) <= 0:
      # The indentation won't fit into the width of the console. In this case
      # just don't output. This should be rare and better than failing the
      # command.
      self._no_output = True

    self._message = None
    self._lines = []
    self._has_update = False
    self._num_lines_changed = False
    self._UpdateMessage(message)

  @property
  def lines(self):
    return self._lines

  @property
  def num_lines(self):
    return len(self._lines)

  @property
  def has_update(self):
    return self._has_update

  @property
  def num_lines_changed(self):
    return self._num_lines_changed

  def _UpdateMessage(self, new_message):
    """Updates the message for this Message object."""
    if not isinstance(new_message, six.string_types):
      raise TypeError('expected a string or other character buffer object')
    if new_message != self._message:
      self._message = new_message
      if self._no_output:
        return
      num_old_lines = len(self._lines)
      self._lines = self._SplitMessageIntoLines(self._message)
      self._has_update = True
      self._num_lines_changed = num_old_lines != len(self._lines)

  def _SplitMessageIntoLines(self, message):
    """Converts message into a list of strs, each representing a line."""
    lines = self._console_attr.SplitLine(message, self.effective_width)
    for i in range(len(lines)):
      lines[i] += '\n'
    return lines

  def Print(self):
    """Prints out the message to the console.

    The implementation of this function assumes that when called, the
    cursor position of the terminal is where the message should start printing.
    """
    if self._no_output:
      return

    for line in self._lines:
      self._ClearLine()
      self._WriteLine(line)
    self._has_update = False

  @property
  def effective_width(self):
    """The effective width when the indentation level is considered."""
    return self._console_width - (INDENTATION_WIDTH * self._level)

  def _ClearLine(self):
    self._stream.write('\r{}\r'.format(' ' * self._console_width))

  def _WriteLine(self, line):
    self._stream.write(self._level * INDENTATION_WIDTH * ' ' + line)
