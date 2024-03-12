# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Calliope parsing errors for logging and collecting metrics.

Refer to the calliope.parser_extensions module for a detailed overview.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import six


class ArgumentError(argparse.ArgumentError):
  """Base class for argument errors with metrics.

  ArgumentError instances are intercepted by
  parser_extensions.ArgumentParser.error(), which
    1. reports a failed command to metrics
    2. prints a usage diagnostic to the standard error
    3. exits with status 2, bypassing gcloud_main exception handling

  Attributes:
    argument: str, The argument name(s) causing the error.
    error_extra_info: {str: str}, Extra info dict for error_format.
    error_format: str, A .format() string for constructng the error message
      from error_extra_info.
    extra_path_arg: str, Dotted command path to append to the command path.
    parser: ArgmentParser, Used to generate the usage string for the command.
      This could be a different subparser than the command parser.
  """

  def __init__(self, error_format, argument=None, extra_path_arg=None,
               parser=None, **kwargs):
    self.error_format = error_format
    self.argument = argument
    self.extra_path_arg = extra_path_arg
    self.parser = parser
    self.error_extra_info = kwargs
    super(ArgumentError, self).__init__(None, six.text_type(self))

  def __str__(self):
    keys = dict(**self.error_extra_info)
    while True:
      try:
        message = self.error_format.format(**keys)
        break
      except KeyError as e:
        # Format {unknown_key} as itself instead of throwing an exception.
        key = e.args[0]
        keys[key] = '{' + key + '}'
      except (IndexError, ValueError):
        # Disable formatting on any other error.
        message = self.error_format
        break
    if self.argument:
      message = 'argument {argument}: {message}'.format(
          argument=self.argument, message=message)
    return message


class OtherParsingError(ArgumentError):
  """Some other parsing error that is not any of the above."""


class TooFewArgumentsError(ArgumentError):
  """Argparse didn't use all the Positional objects."""


class UnknownCommandError(ArgumentError):
  """Unknown command error."""


class UnrecognizedArgumentsError(ArgumentError):
  """User entered arguments that were not recognized by argparse."""


class DetailedArgumentError(ArgumentError):
  """A DetailedArgumentError is preferable to an ArgumentError."""


class ModalGroupError(DetailedArgumentError):
  """Modal group conflict error."""

  def __init__(self, conflict, **kwargs):
    super(ModalGroupError, self).__init__(
        '{conflict} must be specified.',
        conflict=conflict,
        **kwargs)


class OptionalMutexError(DetailedArgumentError):
  """Optional mutex conflict error."""

  def __init__(self, conflict, **kwargs):
    super(OptionalMutexError, self).__init__(
        'At most one of {conflict} can be specified.',
        conflict=conflict,
        **kwargs)


class RequiredError(DetailedArgumentError):
  """Required error."""

  def __init__(self, **kwargs):
    super(RequiredError, self).__init__(
        'Must be specified.',
        **kwargs)


class RequiredMutexError(DetailedArgumentError):
  """Required mutex conflict error."""

  def __init__(self, conflict, **kwargs):
    super(RequiredMutexError, self).__init__(
        'Exactly one of {conflict} must be specified.',
        conflict=conflict,
        **kwargs)


class WrongTrackError(DetailedArgumentError):
  """For parsed commands in a different track."""


class ArgumentException(Exception):
  """ArgumentException is for problems with the declared arguments."""


class UnknownDestinationException(Exception):
  """Fatal error for an internal dest that has no associated arg."""
