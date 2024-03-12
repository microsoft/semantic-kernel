# -*- coding: utf-8 -*-
# Copyright 2010 Google Inc. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
"""gsutil exceptions.

The exceptions in this module are for use across multiple different classes.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import six

NO_URLS_MATCHED_PREFIX = 'No URLs matched'
NO_URLS_MATCHED_GENERIC = (NO_URLS_MATCHED_PREFIX +
                           '. Do the files you\'re operating on exist?')
NO_URLS_MATCHED_TARGET = NO_URLS_MATCHED_PREFIX + ': %s'

if six.PY3:
  # StandardError was removed, so use the base exception type instead
  StandardError = Exception


class AbortException(StandardError):
  """Exception raised when a user aborts a command that needs to do cleanup."""

  def __init__(self, reason):
    StandardError.__init__(self)
    self.reason = reason

  def __repr__(self):
    return 'AbortException: %s' % self.reason

  def __str__(self):
    return 'AbortException: %s' % self.reason


class CommandException(StandardError):
  """Exception raised when a problem is encountered running a gsutil command.

  This exception should be used to signal user errors or system failures
  (like timeouts), not bugs (like an incorrect param value). For the
  latter you should raise Exception so we can see where/how it happened
  via gsutil -D (which will include a stack trace for raised Exceptions).
  """

  def __init__(self, reason, informational=False):
    """Instantiate a CommandException.

    Args:
      reason: Text describing the problem.
      informational: Indicates reason should be printed as FYI, not a failure.
    """
    StandardError.__init__(self)
    self.reason = reason
    self.informational = informational

  def __repr__(self):
    return str(self)

  def __str__(self):
    return 'CommandException: %s' % self.reason


class ControlCException(Exception):
  """Exception to report to analytics when the user exits via ctrl-C.

  This exception is never actually raised, but is used by analytics collection
  to provide a more descriptive name for user exit.
  """
  pass


class GcloudStorageTranslationError(Exception):
  """Exception raised when a gsutil command can't be translated to gcloud."""
  pass


class HashMismatchException(Exception):
  """Exception raised when data integrity validation fails."""
  pass


class IamChOnResourceWithConditionsException(Exception):
  """Raised when trying to use "iam ch" on an IAM policy with conditions.

  Because the syntax for conditions is fairly complex, it doesn't make sense to
  specify them on the command line using a colon-delimited set of values in the
  same way you'd specify simple bindings - it would be a complex and potentially
  surprising interface, which isn't what you want when dealing with permissions.

  Additionally, providing partial functionality -- e.g. if a policy contains
  bindings with conditions, still allow users to interact with bindings that
  don't contain conditions -- might sound tempting, but results in a bad user
  experience. Bindings can be thought of as a mapping from (role, condition) ->
  [members]. Thus, a user might think they're editing the binding for (role1,
  condition1), but they'd really be editing the binding for (role1, None). Thus,
  we just raise an error if we encounter a binding with conditions present, and
  encourage users to use "iam {get,set}" instead.
  """

  def __init__(self, message):
    Exception.__init__(self, message)
    self.message = message

  def __repr__(self):
    return str(self)

  def __str__(self):
    return 'IamChOnResourceWithConditionsException: %s' % self.message


class InvalidUrlError(Exception):
  """Exception raised when URL is invalid."""

  def __init__(self, message):
    Exception.__init__(self, message)
    self.message = message

  def __repr__(self):
    return str(self)

  def __str__(self):
    return 'InvalidUrlError: %s' % self.message


class ExternalBinaryError(Exception):
  """Exception raised when gsutil runs an external binary, and it fails."""

  def __init__(self, message):
    Exception.__init__(self, message)
    self.message = message

  def __repr__(self):
    return 'ExternalBinaryError: %s' % self.message
