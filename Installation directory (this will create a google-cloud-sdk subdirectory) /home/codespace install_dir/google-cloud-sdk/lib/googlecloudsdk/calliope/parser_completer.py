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

"""Calliope argparse argument completer objects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.core.cache import resource_cache
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import progress_tracker
import six


class ArgumentCompleter(object):
  """Argument completer wrapper to delay instantiation until first use.

  Attributes:
    _argument: The argparse argument object.
    _completer_class: The uninstantiated completer class.
    _parsed_args: argparse parsed_args, used here if not known at __call__ time.
  """

  def __init__(self, completer_class, parsed_args=None, argument=None):
    self._completer_class = completer_class
    self._argument = argument
    self._parsed_args = parsed_args
    if '_ARGCOMPLETE' in os.environ:
      # This progress tracker lets long completions run in a separate process.
      # That can only happen when calliope is in argcomplete mode.
      self._progress_tracker = progress_tracker.CompletionProgressTracker
    else:
      self._progress_tracker = progress_tracker.ProgressTracker

  @property
  def completer_class(self):
    return self._completer_class

  @classmethod
  def _MakeCompletionErrorMessages(cls, msgs):
    """Returns a msgs list that will display 1 per line as completions."""
    attr = console_attr.GetConsoleAttr()
    width, _ = attr.GetTermSize()
    # No worries for long msg: negative_integer * ' ' yields ''.
    return [msg + (width // 2 - len(msg)) * ' ' for msg in msgs]

  def _HandleCompleterException(self, exception, prefix, completer=None):
    """Handles completer errors by crafting two "completions" from exception.

    Fatal completer errors return two "completions", each an error
    message that is displayed by the shell completers, and look more
    like a pair of error messages than completions. This is much better than
    the default that falls back to the file completer with no indication of
    errors, typically yielding the list of all files in the current directory.

    NOTICE: Each message must start with different characters, otherwise they
    will be taken as valid completions. Also, the messages are sorted in the
    display, so the messages here are displayed with ERROR first and REASON
    second.

    Args:
      exception: The completer exception.
      prefix: The current prefix string to be matched by the completer.
      completer: The instantiated completer object or None.

    Returns:
      Two "completions" crafted from the completer exception.
    """
    if completer and hasattr(completer, 'collection'):
      completer_name = completer.collection
    else:
      completer_name = self._completer_class.__name__
    return self._MakeCompletionErrorMessages([
        '{}ERROR: {} resource completer failed.'.format(
            prefix, completer_name),
        '{}REASON: {}'.format(prefix, six.text_type(exception)),
    ])

  def __call__(self, prefix='', parsed_args=None, **kwargs):
    """A completer function suitable for argparse."""
    if not isinstance(self._completer_class, type):
      # A function-type completer.
      return self._CompleteFromFunction(prefix=prefix)
    if not parsed_args:
      parsed_args = self._parsed_args
    with self._progress_tracker():
      with resource_cache.ResourceCache() as cache:
        return self._CompleteFromCompleterClass(
            prefix=prefix, cache=cache, parsed_args=parsed_args)

  def _CompleteFromFunction(self, prefix=''):
    """Helper to complete from a function completer."""
    try:
      return self._completer_class(prefix)
    except BaseException as e:  # pylint: disable=broad-except, e shall not pass
      return self._HandleCompleterException(e, prefix=prefix)

  def _CompleteFromGenericCompleterClass(self, prefix=''):
    """Helper to complete from a class that isn't a cache completer."""
    completer = None
    try:
      completer = self._completer_class()
      return completer(prefix=prefix)
    except BaseException as e:  # pylint: disable=broad-except, e shall not pass
      return self._HandleCompleterException(e, prefix=prefix,
                                            completer=completer)

  def _CompleteFromCompleterClass(self, prefix='', cache=None,
                                  parsed_args=None):
    """Helper to complete from a class."""
    if parsed_args and len(
        parsed_args._GetCommand().ai.positional_completers) > 1:  # pylint: disable=protected-access
      qualified_parameter_names = {'collection'}
    else:
      qualified_parameter_names = set()
    completer = None
    try:
      completer = self._completer_class(
          cache=cache,
          qualified_parameter_names=qualified_parameter_names)
      parameter_info = completer.ParameterInfo(parsed_args, self._argument)
      return completer.Complete(prefix, parameter_info)
    except BaseException as e:  # pylint: disable=broad-except, e shall not pass
      if isinstance(e, TypeError) and not completer:
        # This isn't a cache completer.
        return self._CompleteFromGenericCompleterClass(prefix=prefix)
      return self._HandleCompleterException(
          e, prefix=prefix, completer=completer)
