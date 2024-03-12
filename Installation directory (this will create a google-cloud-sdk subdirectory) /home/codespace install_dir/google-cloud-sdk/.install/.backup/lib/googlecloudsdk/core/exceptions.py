# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Base exceptions for the Cloud SDK."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import sys
import traceback

from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import platforms

import six


class _Error(Exception):
  """A base exception for all Cloud SDK errors.

  This exception should not be used directly.
  """
  pass


class InternalError(_Error):
  """A base class for all non-recoverable internal errors."""
  pass


class Error(_Error):
  """A base exception for all user recoverable errors.

  Any exception that extends this class will not be printed with a stack trace
  when running from CLI mode.  Instead it will be shows with a message of how
  the user can correct this problem.

  All exceptions of this type must have a message for the user.
  """

  def __init__(self, *args, **kwargs):
    """Initialize a core.Error.

    Args:
      *args: positional args for exceptions.
      **kwargs: keyword args for exceptions, and additional arguments:
        - exit_code: int, The desired exit code for the CLI.
    """
    super(Error, self).__init__(*args)
    self.exit_code = kwargs.get('exit_code', 1)


class MultiError(Error):
  """Collection of Error instances as single exception."""

  def __init__(self, errors):
    super(MultiError,
          self).__init__(', '.join(six.text_type(e) for e in errors))


class RequiresAdminRightsError(Error):
  """An exception for when you don't have permission to modify the SDK.

  This tells the user how to run their command with administrator rights so that
  they can perform the operation.
  """

  def __init__(self, sdk_root):
    message = (
        'You cannot perform this action because you do not have permission '
        'to modify the Google Cloud SDK installation directory [{root}].\n\n'
        .format(root=sdk_root))
    if (platforms.OperatingSystem.Current() ==
        platforms.OperatingSystem.WINDOWS):
      message += (
          'Click the Google Cloud SDK Shell icon and re-run the command in '
          'that window, or re-run the command with elevated privileges by '
          'right-clicking cmd.exe and selecting "Run as Administrator".')
    else:
      # Specify the full path because sudo often uses secure_path and won't
      # respect the user's $PATH settings.
      gcloud_path = os.path.join(sdk_root, 'bin', 'gcloud')
      message += (
          'Re-run the command with sudo: sudo {0} ...'.format(gcloud_path))
    super(RequiresAdminRightsError, self).__init__(message)


class NetworkIssueError(Error):
  """An error to wrap a general network issue."""

  def __init__(self, message):
    super(NetworkIssueError, self).__init__(
        '{message}\n'
        'This may be due to network connectivity issues. Please check your '
        'network settings, and the status of the service you are trying to '
        'reach.'.format(message=encoding.Decode(message)))


class ExceptionContext(object):
  """An exception context that can be re-raised outside of try-except.

  Usage:
    exception_context = None
    ...
    try:
      ...
    except ... e:
      # This MUST be called in the except: clause.
      exception_context = exceptions.ExceptionContext(e)
    ...
    if exception_context:
      exception_context.Reraise()
  """

  def __init__(self, e):
    self._exception = e
    self._traceback = sys.exc_info()[2]
    # This isn't fool-proof as Python 2 persists sys.exc_info() until exiting
    # the frame where the exception was caught (unlike Python 3 which clears it
    # upon exiting the exception handler, which is what we want). But it should
    # at least catch some cases of this class being initialized incorrectly.
    if not self._traceback:
      raise InternalError('Must set ExceptionContext within an except clause.')

  def Reraise(self):
    six.reraise(type(self._exception), self._exception, self._traceback)


def reraise(exc_value, tb=None):  # pylint: disable=invalid-name
  """Adds tb or the most recent traceback to exc_value and reraises."""
  tb = tb or sys.exc_info()[2]
  six.reraise(type(exc_value), exc_value, tb)


def _FormatException(exc_type, exc, exc_trace):
  """Returns a formatted exception message from an exception and traceback."""
  exc_msg_lines = []
  for line in traceback.format_exception(exc_type, exc, exc_trace):
    exc_msg_lines.append(encoding.Decode(line))
  return ''.join(exc_msg_lines)


def RaiseWithContext(
    orig_exc_type, orig_exc, orig_exc_trace,
    curr_exc_type, curr_exc, curr_exc_trace):
  """Raises an exception that occurs when handling another exception.

  Python 3 does this sort of exception chaining natively, but it's not supported
  in Python 2. So when running in Python 2, we manually reproduce the error
  message we would get it in Python 3. It won't look identical but it's good
  enough for debugging purposes so that we don't lose the exception context.

  Args:
    orig_exc_type: The type of the original exception being handled.
    orig_exc: The original exception.
    orig_exc_trace: The traceback of the original exception.
    curr_exc_type: The type of the current exception being handled.
    curr_exc: The current exception.
    curr_exc_trace: The traceback of the current exception.

  Raises:
    Exception: The current exception with added context from the original
      exception being handled.
  """
  if not six.PY2 or not orig_exc:
    raise curr_exc

  orig_exc_msg = _FormatException(orig_exc_type, orig_exc, orig_exc_trace)
  curr_exc_msg = _FormatException(curr_exc_type, curr_exc, curr_exc_trace)
  new_exc_msg = (
      '\n\n{}\n'
      'During handling of the above exception, another exception occurred:'
      '\n\n{}'.format(orig_exc_msg, curr_exc_msg))
  six.reraise(curr_exc_type, curr_exc_type(new_exc_msg), orig_exc_trace)
