# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""General console printing utilities used by the Cloud SDK."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import contextlib
import enum
import getpass
import io
import json
import os
import re
import subprocess
import sys
import textwrap
import threading

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_pager
from googlecloudsdk.core.console import prompt_completer
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms

import six
from six.moves import input  # pylint: disable=redefined-builtin
from six.moves import map  # pylint: disable=redefined-builtin
from six.moves import range  # pylint: disable=redefined-builtin


class Error(exceptions.Error):
  """Base exception for the module."""
  pass


class RequiredPromptError(Error):
  """An exception for when a prompt cannot silenced with the --quiet flag."""

  def __init__(self):
    super(RequiredPromptError, self).__init__(
        'This prompt could not be answered because you are not in an '
        'interactive session.  Please re-run the command without the --quiet '
        'flag to respond to the prompts.')


class UnattendedPromptError(Error):
  """An exception for when a prompt cannot be answered."""

  def __init__(self):
    super(UnattendedPromptError, self).__init__(
        'This prompt could not be answered because you are not in an '
        'interactive session.  You can re-run the command with the --quiet '
        'flag to accept default answers for all prompts.')


class OperationCancelledError(Error):
  """An exception for when a prompt cannot be answered."""

  DEFAULT_MESSAGE = 'Aborted by user.'

  def __init__(self, message=None):
    super(OperationCancelledError, self).__init__(
        message or self.DEFAULT_MESSAGE)


# All wrapping is done by this single global wrapper. If you have different
# wrapping needs, consider the _NarrowWrap context manager, below.
_CONSOLE_WIDTH = console_attr.GetConsoleAttr().GetTermSize()[0]
TEXTWRAP = textwrap.TextWrapper(
    replace_whitespace=False,
    drop_whitespace=False,
    break_on_hyphens=False,
    width=_CONSOLE_WIDTH if _CONSOLE_WIDTH > 0 else 80)


def _DoWrap(message):
  """Text wrap the given message and correctly handle newlines in the middle.

  Args:
    message: str, The message to wrap.  It may have newlines in the middle of
      it.

  Returns:
    str, The wrapped message.
  """
  return '\n'.join([TEXTWRAP.fill(line) for line in message.splitlines()])


@contextlib.contextmanager
def _NarrowWrap(narrow_by):
  """Temporarily narrows the global wrapper."""
  TEXTWRAP.width -= narrow_by
  yield TEXTWRAP
  TEXTWRAP.width += narrow_by


def _GetInput():
  try:
    return input()
  except EOFError:
    return None


def ReadFromFileOrStdin(path, binary):
  """Returns the contents of the specified file or stdin if path is '-'.

  Args:
    path: str, The path of the file to read.
    binary: bool, True to open the file in binary mode.

  Raises:
    Error: If the file cannot be read or is larger than max_bytes.

  Returns:
    The contents of the file.
  """
  if path == '-':
    return ReadStdin(binary=binary)
  if binary:
    return files.ReadBinaryFileContents(path)
  return files.ReadFileContents(path)


def ReadStdin(binary=False):
  """Reads data from stdin, correctly accounting for encoding.

  Anything that needs to read sys.stdin must go through this method.

  Args:
    binary: bool, True to read raw bytes, False to read text.

  Returns:
    A text string if binary is False, otherwise a byte string.
  """
  if binary:
    return files.ReadStdinBytes()
  else:
    data = sys.stdin.read()
    if six.PY2:
      # On Python 2, stdin comes in a a byte string. Convert it to text.
      data = console_attr.Decode(data)
    return data


def IsInteractive(output=False, error=False, heuristic=False):
  """Determines if the current terminal session is interactive.

  sys.stdin must be a terminal input stream.

  Args:
    output: If True then sys.stdout must also be a terminal output stream.
    error: If True then sys.stderr must also be a terminal output stream.
    heuristic: If True then we also do some additional heuristics to check if
               we are in an interactive context. Checking home path for example.

  Returns:
    True if the current terminal session is interactive.
  """
  try:
    if not sys.stdin.isatty():
      return False
    if output and not sys.stdout.isatty():
      return False
    if error and not sys.stderr.isatty():
      return False
  except AttributeError:
    # This should only occur when one of the streams is not open.
    return False

  if heuristic:
    # Check the home path. Most startup scripts for example are executed by
    # users that don't have a home path set. Home is OS dependent though, so
    # check everything.
    # *NIX OS usually sets the HOME env variable. It is usually '/home/user',
    # but can also be '/root'. If it's just '/' we are most likely in an init
    # script.
    # Windows usually sets HOMEDRIVE and HOMEPATH. If they don't exist we are
    # probably being run from a task scheduler context. HOMEPATH can be '\'
    # when a user has a network mapped home directory.
    # Cygwin has it all! Both Windows and Linux. Checking both is perfect.
    home = encoding.GetEncodedValue(os.environ, 'HOME')
    homepath = encoding.GetEncodedValue(os.environ, 'HOMEPATH')
    if not homepath and (not home or home == '/'):
      return False
  return True


def IsRunFromShellScript():
  """Check if command is being run from command line or a script."""
  # Commands run from a shell script typically have getppid() == getpgrp()
  if platforms.OperatingSystem.Current() != platforms.OperatingSystem.WINDOWS:
    if os.getppid() == os.getpgrp():
      return True
  return False


def CanPrompt():
  """Returns true if we can prompt the user for information.

  This combines all checks (IsInteractive(), disable_prompts is False) to
  verify that we can prompt the user for information.

  Returns:
    bool, True if we can prompt the user for information.
  """
  return (IsInteractive(error=True) and
          not properties.VALUES.core.disable_prompts.GetBool())


def PromptContinue(message=None, prompt_string=None, default=True,
                   throw_if_unattended=False, cancel_on_no=False,
                   cancel_string=None):
  """Prompts the user a yes or no question and asks if they want to continue.

  Args:
    message: str, The prompt to print before the question.
    prompt_string: str, An alternate yes/no prompt to display.  If None, it
      defaults to 'Do you want to continue'.
    default: bool, What the default answer should be.  True for yes, False for
      no.
    throw_if_unattended: bool, If True, this will throw if there was nothing
      to consume on stdin and stdin is not a tty.
    cancel_on_no: bool, If True and the user answers no, throw an exception to
      cancel the entire operation.  Useful if you know you don't want to
      continue doing anything and don't want to have to raise your own
      exception.
    cancel_string: str, An alternate error to display on No. If None, it
      defaults to 'Aborted by user.'.

  Raises:
    UnattendedPromptError: If there is no input to consume and this is not
      running in an interactive terminal.
    OperationCancelledError: If the user answers no and cancel_on_no is True.

  Returns:
    bool, False if the user said no, True if the user said anything else or if
    prompts are disabled.
  """
  if properties.VALUES.core.disable_prompts.GetBool():
    if not default and cancel_on_no:
      raise OperationCancelledError()
    return default

  style = properties.VALUES.core.interactive_ux_style.Get()
  prompt_generator = (
      _TestPromptContinuePromptGenerator
      if style == properties.VALUES.core.InteractiveUXStyles.TESTING.name
      else _NormalPromptContinuePromptGenerator)

  prompt, reprompt, ending = prompt_generator(
      message=message, prompt_string=prompt_string, default=default,
      throw_if_unattended=throw_if_unattended, cancel_on_no=cancel_on_no,
      cancel_string=cancel_string)
  sys.stderr.write(prompt)

  def GetAnswer(reprompt):
    """Get answer to input prompt."""
    while True:
      answer = _GetInput()
      # pylint:disable=g-explicit-bool-comparison, We explicitly want to
      # distinguish between empty string and None.
      if answer == '':
        # User just hit enter, return default.
        return default
      elif answer is None:
        # This means we hit EOF, no input or user closed the stream.
        if throw_if_unattended and not IsInteractive():
          raise UnattendedPromptError()
        else:
          return default
      elif answer.strip().lower() in ['y', 'yes']:
        return True
      elif answer.strip().lower() in ['n', 'no']:
        return False
      elif reprompt:
        sys.stderr.write(reprompt)

  try:
    answer = GetAnswer(reprompt)
  finally:
    if ending:
      sys.stderr.write(ending)

  if not answer and cancel_on_no:
    raise OperationCancelledError(cancel_string)
  return answer


def _NormalPromptContinuePromptGenerator(
    message, prompt_string, default, throw_if_unattended, cancel_on_no,
    cancel_string):
  """Generates prompts for prompt continue under normal conditions."""
  del throw_if_unattended
  del cancel_on_no
  del cancel_string

  buf = io.StringIO()
  if message:
    buf.write(_DoWrap(message) + '\n\n')

  if not prompt_string:
    prompt_string = 'Do you want to continue'
  if default:
    prompt_string += ' (Y/n)?  '
  else:
    prompt_string += ' (y/N)?  '
  buf.write(_DoWrap(prompt_string))

  return (buf.getvalue(), "Please enter 'y' or 'n':  ", '\n')


def _TestPromptContinuePromptGenerator(
    message, prompt_string, default, throw_if_unattended, cancel_on_no,
    cancel_string):
  """Generates prompts for prompt continue under test."""
  del default
  del throw_if_unattended
  del cancel_on_no
  return (JsonUXStub(
      UXElementType.PROMPT_CONTINUE, message=message,
      prompt_string=prompt_string, cancel_string=cancel_string) + '\n',
          None, None)


def PromptResponse(message=None, choices=None):
  """Prompts the user for a string.

  Args:
    message: str, The prompt to print before the question.
    choices: callable or list, A callable with no arguments that returns the
      list of all choices, or the list of choices.

  Returns:
    str, The string entered by the user, or None if prompts are disabled.
  """
  if properties.VALUES.core.disable_prompts.GetBool():
    return None
  if choices and IsInteractive(error=True):
    return prompt_completer.PromptCompleter(message, choices=choices).Input()
  if (properties.VALUES.core.interactive_ux_style.Get() ==
      properties.VALUES.core.InteractiveUXStyles.TESTING.name):
    sys.stderr.write(JsonUXStub(UXElementType.PROMPT_RESPONSE, message=message))
  else:
    sys.stderr.write(_DoWrap(message))
  return _GetInput()


def PromptWithDefault(message=None, default=None, choices=None):
  """Prompts the user for a string, allowing a default.

  Unlike PromptResponse, this also appends a ':  ' to the prompt.  If 'default'
  is specified, the default is also written written into the prompt (e.g.
  if message is "message" and default is "default", the prompt would be
  "message (default): ").

  The default is returned if the user simply presses enter (no input) or an
  EOF is received.

  Args:
    message: str, The prompt to print before the question.
    default: str, The default value (if any).
    choices: callable or list, A callable with no arguments that returns the
      list of all choices, or the list of choices.

  Returns:
    str, The string entered by the user, or the default if no value was
    entered or prompts are disabled.
  """
  message = message or ''
  if default:
    if message:
      message += ' '
    message += '({default}):  '.format(default=default)
  else:
    message += ':  '
  return PromptResponse(message, choices=choices) or default


def _ParseAnswer(answer, options, allow_freeform):
  """Parses answer and returns 1-based index in options list.

  Args:
    answer: str, The answer input by the user to be parsed as a choice.
    options: [object], A list of objects to select.  Their str()
          method will be used to select them via freeform text.
    allow_freeform: bool, A flag which, if defined, will allow the user to input
          the choice as a str, not just as a number. If not set, only numbers
          will be accepted.

  Returns:
    int, The 1-indexed value in the options list that corresponds to the answer
          that was given, or None if the selection is invalid. Note that this
          function does not do any validation that the value is a valid index
          (in the case that an integer answer was given)
  """
  try:
    # If this fails to parse, will throw a ValueError
    return int(answer)
  except ValueError:
    # Answer is not an int
    pass

  # If the user has specified that they want to allow freeform selections,
  # we will attempt to find a match.
  if not allow_freeform:
    return None

  try:
    return list(map(str, options)).index(answer) + 1
  except ValueError:
    # Answer not an entry in the options list
    pass

  # Couldn't interpret the user's input
  return None


def _SuggestFreeformAnswer(suggester, answer, options):
  """Checks if there is a suitable close choice to suggest.

  Args:
    suggester: object, An object which has methods AddChoices and
      GetSuggestion which is used to detect if an answer which is not present
      in the options list is a likely typo, and to provide a suggestion
      accordingly.
    answer: str, The freeform answer input by the user as a choice.
    options: [object], A list of objects to select.  Their str()
          method will be used to compare them to answer.

  Returns:
    str, the closest option in options to answer, or None otherwise.
  """
  suggester.AddChoices(map(str, options))
  return suggester.GetSuggestion(answer)


def _PrintOptions(options, write, limit=None):
  """Prints the options provided to stderr.

  Args:
    options:  [object], A list of objects to print as choices.  Their str()
      method will be used to display them.
    write: f(x)->None, A function to call to write the data.
    limit: int, If set, will only print the first number of options equal
      to the given limit.
  """
  limited_options = options if limit is None else options[:limit]
  for i, option in enumerate(limited_options):
    write(' [{index}] {option}\n'.format(
        index=i + 1, option=six.text_type(option)))


# This defines the point at which, in a PromptChoice, the options
# will not be listed unless the user enters 'list' and hits enter.
# When too many results are displayed they can cease to be useful.
PROMPT_OPTIONS_OVERFLOW = 50


def PromptChoice(options, default=None, message=None,
                 prompt_string=None, allow_freeform=False,
                 freeform_suggester=None, cancel_option=False):
  """Prompt the user to select a choice from a list of items.

  Args:
    options:  [object], A list of objects to print as choices.  Their
      six.text_type() method will be used to display them.
    default: int, The default index to return if prompting is disabled or if
      they do not enter a choice.
    message: str, An optional message to print before the choices are displayed.
    prompt_string: str, A string to print when prompting the user to enter a
      choice.  If not given, a default prompt is used.
    allow_freeform: bool, A flag which, if defined, will allow the user to input
      the choice as a str, not just as a number. If not set, only numbers will
      be accepted.
    freeform_suggester: object, An object which has methods AddChoices and
      GetSuggestion which is used to detect if an answer which is not present
      in the options list is a likely typo, and to provide a suggestion
      accordingly.
    cancel_option: bool, A flag indicating whether an option to cancel the
      operation should be added to the end of the list of choices.

  Raises:
    ValueError: If no options are given or if the default is not in the range of
      available options.
    OperationCancelledError: If a `cancel` option is selected by user.

  Returns:
    The index of the item in the list that was chosen, or the default if prompts
    are disabled.
  """
  if not options:
    raise ValueError('You must provide at least one option.')
  options = options + ['cancel'] if cancel_option else options
  maximum = len(options)
  if default is not None and not 0 <= default < maximum:
    raise ValueError(
        'Default option [{default}] is not a valid index for the options list '
        '[{maximum} options given]'.format(default=default, maximum=maximum))
  if properties.VALUES.core.disable_prompts.GetBool():
    return default

  style = properties.VALUES.core.interactive_ux_style.Get()
  if style == properties.VALUES.core.InteractiveUXStyles.TESTING.name:
    write = lambda x: None
    sys.stderr.write(JsonUXStub(
        UXElementType.PROMPT_CHOICE, message=message,
        prompt_string=prompt_string,
        choices=[six.text_type(o) for o in options]) + '\n')
  else:
    write = sys.stderr.write

  if message:
    write(_DoWrap(message) + '\n')

  if maximum > PROMPT_OPTIONS_OVERFLOW:
    _PrintOptions(options, write, limit=PROMPT_OPTIONS_OVERFLOW)
    truncated = maximum - PROMPT_OPTIONS_OVERFLOW
    write('Did not print [{truncated}] options.\n'.format(truncated=truncated))
    write('Too many options [{maximum}]. Enter "list" at prompt to print '
          'choices fully.\n'.format(maximum=maximum))
  else:
    _PrintOptions(options, write)

  if not prompt_string:
    if allow_freeform:
      prompt_string = ('Please enter numeric choice or text value (must exactly'
                       ' match list item)')
    else:
      prompt_string = 'Please enter your numeric choice'
  if default is None:
    suffix_string = ':  '
  else:
    suffix_string = ' ({default}):  '.format(default=default + 1)

  def _PrintPrompt():
    write(_DoWrap(prompt_string + suffix_string))
  _PrintPrompt()

  while True:
    answer = _GetInput()
    if answer is None or (not answer and default is not None):
      # Return default if we failed to read from stdin.
      # Return default if the user hit enter and there is a valid default,
      # or raise OperationCancelledError if default is the cancel option.
      # Prompt again otherwise
      write('\n')
      if cancel_option and default == maximum - 1:
        raise OperationCancelledError()
      return default
    if answer == 'list':
      _PrintOptions(options, write)
      _PrintPrompt()
      continue
    num_choice = _ParseAnswer(answer, options, allow_freeform)
    if cancel_option and num_choice == maximum:
      raise OperationCancelledError()
    if num_choice is not None and num_choice >= 1 and num_choice <= maximum:
      write('\n')
      return num_choice - 1

    # Arriving here means that there is no choice matching the answer that
    # was given. We now will provide a suggestion, if one exists.
    if allow_freeform and freeform_suggester:
      suggestion = _SuggestFreeformAnswer(freeform_suggester,
                                          answer,
                                          options)
      if suggestion is not None:
        write('[{answer}] not in list. Did you mean [{suggestion}]?'
              .format(answer=answer, suggestion=suggestion))
        write('\n')

    if allow_freeform:
      write('Please enter a value between 1 and {maximum}, or a value present '
            'in the list:  '.format(maximum=maximum))
    else:
      write('Please enter a value between 1 and {maximum}:  '
            .format(maximum=maximum))


def PromptWithValidator(validator, error_message, prompt_string,
                        message=None, allow_invalid=False):
  """Prompts the user for a string that must pass a validator.

  Args:
    validator: function, A validation function that accepts a string and returns
      a boolean value indicating whether or not the user input is valid.
    error_message: str, Error message to display when user input does not pass
      in a valid string.
    prompt_string: str, A string to print when prompting the user to enter a
      choice.  If not given, a default prompt is used.
    message: str, An optional message to print before prompting.
    allow_invalid: bool, Allow returning the answer if validation fails.

  Returns:
    str, The string entered by the user, or the default if no value was
    entered or prompts are disabled.
  """
  if properties.VALUES.core.disable_prompts.GetBool():
    return None

  # Display prompts in detailed JSON format when running tests.
  style = properties.VALUES.core.interactive_ux_style.Get()
  if style == properties.VALUES.core.InteractiveUXStyles.TESTING.name:
    write = lambda x: None
    sys.stderr.write(JsonUXStub(
        UXElementType.PROMPT_WITH_VALIDATOR, error_message=error_message,
        prompt_string=prompt_string, message=message,
        allow_invalid=allow_invalid) + '\n')
  else:
    write = sys.stderr.write

  if message:
    write(_DoWrap(message) + '\n')

  while True:
    write(_DoWrap(prompt_string))
    answer = _GetInput()
    if validator(answer):
      return answer
    else:
      write(_DoWrap(error_message) + '\n')
      if allow_invalid and PromptContinue(default=False):
        return answer


def LazyFormat(s, **kwargs):
  """Expands {key} => value for key, value in kwargs.

  Details:
    * {{<identifier>}} expands to {<identifier>}
    * {<unknown-key>} expands to {<unknown-key>}
    * {key} values are recursively expanded before substitution into the result

  Args:
    s: str, The string to format.
    **kwargs: {str:str}, A dict of strings for named parameters.

  Returns:
    str, The lazily-formatted string.
  """

  def _Replacement(match):
    """Returns one replacement string for LazyFormat re.sub()."""
    prefix = match.group(1)[1:]
    name = match.group(2)
    suffix = match.group(3)[1:]
    if prefix and suffix:
      # {{name}} => {name}
      return prefix + name + suffix
    value = kwargs.get(name)
    if value is None:
      # {unknown} => {unknown}
      return match.group(0)
    if callable(value):
      value = value()
    # The substituted value is expanded too.
    return prefix + LazyFormat(value, **kwargs) + suffix

  return re.sub(r'(\{+)(\w+)(\}+)', _Replacement, s)


def FormatRequiredUserAction(s):
  """Formats an action a user must initiate to complete a command.

  Some actions can't be prompted or initiated by gcloud itself, but they must
  be completed to accomplish the task requested of gcloud; the canonical example
  is that after installation or update, the user must restart their shell for
  all aspects of the update to take effect. Unlike most console output, such
  instructions need to be highlighted in some way. Using this function ensures
  that all such instances are highlighted the *same* way.

  Args:
    s: str, The message to format. It shouldn't begin or end with newlines.

  Returns:
    str, The formatted message. This should be printed starting on its own
      line, and followed by a newline.
  """
  with _NarrowWrap(4) as wrapper:
    separator = '\n==> '
    prefix = separator
    screen_reader = properties.VALUES.accessibility.screen_reader.GetBool()
    if screen_reader:
      separator = '\n '
      prefix = '\n'
    return prefix + separator.join(wrapper.wrap(s)) + '\n'


def ProgressBar(label, stream=log.status, total_ticks=60, first=True,
                last=True, screen_reader=False):
  """A simple progress bar for tracking completion of an action.

  This progress bar works without having to use any control characters.  It
  prints the action that is being done, and then fills a progress bar below it.
  You should not print anything else on the output stream during this time as it
  will cause the progress bar to break on lines.

  Progress bars can be stacked into a group. first=True marks the first bar in
  the group and last=True marks the last bar in the group. The default assumes
  a singleton bar with first=True and last=True.

  This class can also be used in a context manager.

  Args:
    label: str, The action that is being performed.
    stream: The output stream to write to, stderr by default.
    total_ticks: int, The number of ticks wide to make the progress bar.
    first: bool, True if this is the first bar in a stacked group.
    last: bool, True if this is the last bar in a stacked group.
    screen_reader: bool, override for screen reader accessibility property
      toggle.

  Returns:
    The progress bar.
  """
  style = properties.VALUES.core.interactive_ux_style.Get()
  if style == properties.VALUES.core.InteractiveUXStyles.OFF.name:
    return NoOpProgressBar()
  elif style == properties.VALUES.core.InteractiveUXStyles.TESTING.name:
    return _StubProgressBar(label, stream)
  elif screen_reader or properties.VALUES.accessibility.screen_reader.GetBool():
    return _TextPercentageProgressBar(label, stream)
  else:
    return _NormalProgressBar(label, stream, total_ticks, first, last)


def SplitProgressBar(original_callback, weights):
  """Splits a progress bar into logical sections.

  Wraps the original callback so that each of the subsections can use the full
  range of 0 to 1 to indicate its progress.  The overall progress bar will
  display total progress based on the weights of the tasks.

  Args:
    original_callback: f(float), The original callback for the progress bar.
    weights: [float], The weights of the tasks to create.  These can be any
      numbers you want and the split will be based on their proportions to
      each other.

  Raises:
    ValueError: If the weights don't add up to 1.

  Returns:
    (f(float), ), A tuple of callback functions, in order, for the subtasks.
  """
  if (original_callback is None or
      original_callback == DefaultProgressBarCallback):
    return tuple([DefaultProgressBarCallback for _ in range(len(weights))])

  def MakeCallback(already_done, weight):
    def Callback(done_fraction):
      original_callback(already_done + (done_fraction * weight))
    return Callback

  total = sum(weights)
  callbacks = []
  already_done = 0
  for weight in weights:
    normalized_weight = weight / total
    callbacks.append(MakeCallback(already_done, normalized_weight))
    already_done += normalized_weight

  return tuple(callbacks)


def DefaultProgressBarCallback(progress_factor):
  del progress_factor


class _NormalProgressBar(object):
  """A simple progress bar for tracking completion of an action.

  This progress bar works without having to use any control characters.  It
  prints the action that is being done, and then fills a progress bar below it.
  You should not print anything else on the output stream during this time as it
  will cause the progress bar to break on lines.

  Progress bars can be stacked into a group. first=True marks the first bar in
  the group and last=True marks the last bar in the group. The default assumes
  a singleton bar with first=True and last=True.

  This class can also be used in a context manager.
  """

  def __init__(self, label, stream, total_ticks, first, last):
    """Creates a progress bar for the given action.

    Args:
      label: str, The action that is being performed.
      stream: The output stream to write to, stderr by default.
      total_ticks: int, The number of ticks wide to make the progress bar.
      first: bool, True if this is the first bar in a stacked group.
      last: bool, True if this is the last bar in a stacked group.
    """
    self._raw_label = label
    self._stream = stream
    self._ticks_written = 0
    self._total_ticks = total_ticks
    self._first = first
    self._last = last
    attr = console_attr.ConsoleAttr()
    self._box = attr.GetBoxLineCharacters()
    self._redraw = (self._box.d_dr != self._box.d_vr or
                    self._box.d_dl != self._box.d_vl)
    # If not interactive, we can't use carriage returns, so treat every progress
    # bar like it is independent, do not try to merge and redraw them. We only
    # need to do this if it was going to attempt to redraw them in the first
    # place (there is no redraw if the character set does not support different
    # characters for the corners).
    if self._redraw and not IsInteractive(error=True):
      self._first = True
      self._last = True

    max_label_width = self._total_ticks - 4
    if len(label) > max_label_width:
      label = label[:max_label_width - 3] + '...'
    elif len(label) < max_label_width:
      diff = max_label_width - len(label)
      label += ' ' * diff
    left = self._box.d_vr + self._box.d_h
    right = self._box.d_h + self._box.d_vl
    self._label = '{left} {label} {right}'.format(
        left=left, label=label, right=right)

  def Start(self):
    """Starts the progress bar by writing the top rule and label."""
    if self._first or self._redraw:
      left = self._box.d_dr if self._first else self._box.d_vr
      right = self._box.d_dl if self._first else self._box.d_vl
      rule = '{left}{middle}{right}\n'.format(
          left=left, middle=self._box.d_h * self._total_ticks, right=right)
      self._Write(rule)
    self._Write(self._label + '\n')
    self._Write(self._box.d_ur)
    self._ticks_written = 0

  def SetProgress(self, progress_factor):
    """Sets the current progress of the task.

    This method has no effect if the progress bar has already progressed past
    the progress you call it with (since the progress bar cannot back up).

    Args:
      progress_factor: float, The current progress as a float between 0 and 1.
    """
    expected_ticks = int(self._total_ticks * progress_factor)
    new_ticks = expected_ticks - self._ticks_written
    # Don't allow us to go over 100%.
    new_ticks = min(new_ticks, self._total_ticks - self._ticks_written)

    if new_ticks > 0:
      self._Write(self._box.d_h * new_ticks)
      self._ticks_written += new_ticks
      if expected_ticks == self._total_ticks:
        end = '\n' if self._last or not self._redraw else '\r'
        self._Write(self._box.d_ul + end)
      self._stream.flush()

  def Finish(self):
    """Mark the progress as done."""
    self.SetProgress(1)

  def _Write(self, msg):
    self._stream.write(msg)

  def __enter__(self):
    self.Start()
    return self

  def __exit__(self, *args):
    self.Finish()


class _TextPercentageProgressBar(object):
  """A progress bar that outputs nothing at all."""

  def __init__(self, label, stream, percentage_display_increments=5.0):
    """Creates a progress bar for the given action.

    Args:
      label: str, The action that is being performed.
      stream: The output stream to write to, stderr by default.
      percentage_display_increments: Minimum change in percetnage to display new
        progress
    """
    self._label = label
    self._stream = stream
    self._last_percentage = 0
    self._percentage_display_increments = percentage_display_increments / 100.0

  def Start(self):
    self._Write(self._label)

  def SetProgress(self, progress_factor):
    progress_factor = min(progress_factor, 1.0)
    should_update_progress = (
        progress_factor >
        self._last_percentage + self._percentage_display_increments)
    if (should_update_progress or progress_factor == 1.0):
      self._Write('{0:.0f}%'.format(progress_factor * 100.0))
      self._last_percentage = progress_factor

  def Finish(self):
    """Mark the progress as done."""
    self.SetProgress(1)

  def _Write(self, msg):
    self._stream.write(msg + '\n')

  def __enter__(self):
    self.Start()
    return self

  def __exit__(self, *args):
    self.Finish()


class NoOpProgressBar(object):
  """A progress bar that outputs nothing at all."""

  def __init__(self):
    pass

  def Start(self):
    pass

  def SetProgress(self, progress_factor):
    pass

  def Finish(self):
    """Mark the progress as done."""
    self.SetProgress(1)

  def __enter__(self):
    self.Start()
    return self

  def __exit__(self, *args):
    self.Finish()


class _StubProgressBar(object):
  """A progress bar that only prints deterministic start and end points.

  No UX about progress should be exposed here. This is strictly for being able
  to tell that the progress bar was invoked, not what it actually looks like.
  """

  def __init__(self, label, stream):
    self._raw_label = label
    self._stream = stream

  def Start(self):
    self._stream.write(
        JsonUXStub(UXElementType.PROGRESS_BAR, message=self._raw_label))

  def SetProgress(self, progress_factor):
    pass

  def Finish(self):
    """Mark the progress as done."""
    self.SetProgress(1)
    self._stream.write('\n')

  def __enter__(self):
    self.Start()
    return self

  def __exit__(self, *args):
    self.Finish()


def More(contents, out=None, prompt=None, check_pager=True):
  """Run a user specified pager or fall back to the internal pager.

  Args:
    contents: The entire contents of the text lines to page.
    out: The output stream, log.out (effectively) if None.
    prompt: The page break prompt.
    check_pager: Checks the PAGER env var and uses it if True.
  """
  if not IsInteractive(output=True):
    if not out:
      out = log.out
    out.write(contents)
    return
  if not out:
    # Rendered help to the log file.
    log.file_only_logger.info(contents)
    # Paging shenanigans to stdout.
    out = sys.stdout
  if check_pager:
    pager = encoding.GetEncodedValue(os.environ, 'PAGER', None)
    if pager == '-':
      # Use the fallback Pager.
      pager = None
    elif not pager:
      # Search for a pager that handles ANSI escapes.
      for command in ('less', 'pager'):
        if files.FindExecutableOnPath(command):
          pager = command
          break
    if pager:
      # If the pager is less(1) then instruct it to display raw ANSI escape
      # sequences to enable colors and font embellishments.
      less_orig = encoding.GetEncodedValue(os.environ, 'LESS', None)
      less = '-R' + (less_orig or '')
      encoding.SetEncodedValue(os.environ, 'LESS', less)
      p = subprocess.Popen(pager, stdin=subprocess.PIPE, shell=True)
      enc = console_attr.GetConsoleAttr().GetEncoding()
      p.communicate(input=contents.encode(enc))
      p.wait()
      if less_orig is None:
        encoding.SetEncodedValue(os.environ, 'LESS', None)
      return
  # Fall back to the internal pager.
  console_pager.Pager(contents, out, prompt).Run()


class TickableProgressBar(object):
  """A thread safe progress bar with a discrete number of tasks."""

  def __init__(self, total, *args, **kwargs):
    self.completed = 0
    self.total = total
    self._progress_bar = ProgressBar(*args, **kwargs)
    self._lock = threading.Lock()

  def __enter__(self):
    self._progress_bar.__enter__()
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self._progress_bar.__exit__(exc_type, exc_value, traceback)

  def Tick(self):
    with self._lock:
      self.completed += 1
      self._progress_bar.SetProgress(self.completed / self.total)


def JsonUXStub(ux_type, **kwargs):
  """Generates a stub message for UX console output."""
  output = collections.OrderedDict()
  output['ux'] = ux_type.name
  extra_args = list(set(kwargs) - set(ux_type.GetDataFields()))
  if extra_args:
    raise ValueError('Extraneous args for Ux Element {}: {}'.format(
        ux_type.name, extra_args))
  for field in ux_type.GetDataFields():
    val = kwargs.get(field, None)
    if val:
      output[field] = val
  return json.dumps(output)


class UXElementType(enum.Enum):
  """Describes the type of a ux element."""
  PROGRESS_BAR = (0, 'message')
  PROGRESS_TRACKER = (1, 'message', 'aborted_message', 'status')
  STAGED_PROGRESS_TRACKER = (2, 'message', 'status',
                             'succeeded_stages', 'failed_stage')
  PROMPT_CONTINUE = (3, 'message', 'prompt_string', 'cancel_string')
  PROMPT_RESPONSE = (4, 'message')
  PROMPT_CHOICE = (5, 'message', 'prompt_string', 'choices')
  PROMPT_WITH_VALIDATOR = (6, 'error_message', 'prompt_string', 'message',
                           'allow_invalid')

  def __init__(self, ordinal, *data_fields):
    # We need to pass in something unique here because if two event types
    # happen to have the same attributes, the Enum class interprets them to be
    # the same and sets one value as an alias of the other.
    del ordinal
    self._data_fields = data_fields

  def GetDataFields(self):
    """Returns the ordered list of additional fields in the UX Element."""
    return self._data_fields


def PromptPassword(prompt,
                   error_message='Invalid Password',
                   validation_callable=None,
                   encoder_callable=None):
  """Prompt user for password with optional validation."""
  if properties.VALUES.core.disable_prompts.GetBool():
    return None

  str_prompt = six.ensure_str(prompt)
  pass_wd = getpass.getpass(str_prompt)
  encoder = encoder_callable if callable(encoder_callable) else six.ensure_str
  if callable(validation_callable):
    while not validation_callable(pass_wd):
      sys.stderr.write(_DoWrap(error_message) + '\n')
      pass_wd = getpass.getpass(str_prompt)

  return encoder(pass_wd)
