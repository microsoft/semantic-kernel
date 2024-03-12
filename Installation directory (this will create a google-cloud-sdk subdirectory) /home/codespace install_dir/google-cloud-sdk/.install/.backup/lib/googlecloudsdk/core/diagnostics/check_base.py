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

"""Base classes for checks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import collections
import six


@six.add_metaclass(abc.ABCMeta)
class Checker(object):
  """Base class for a single check."""

  @abc.abstractproperty
  def issue(self):
    """The aspect of the user's machine that is being checked."""

  @abc.abstractmethod
  def Check(self):
    """Runs a single check and returns the result and an optional fix.

    Returns:
      A tuple of two elements. The first element should have the same attributes
      as a check_base.Result object. The second element should either be a fixer
      function that can used to fix an error (indicated by the "passed"
      attribute being False in the first element), or None if the check passed
      or if it failed with no applicable fix. If there is a fixer function it is
      assumed that calling it will return True if it makes changes that warrant
      running a check again.
    """


class Result(
    collections.namedtuple('Result', ['passed', 'message', 'failures'])):
  """Holds information about the result of a single check.

  Attributes:
    passed: Whether the check passed.
    message: A summary message about the result of the check.
    failures: A sequence of checkbase.Failure objects; may be empty if there
        were no failures.
  """

  def __new__(cls, passed, message='', failures=None):
    return super(Result, cls).__new__(cls, passed, message, failures or [])


class Failure(collections.namedtuple('Failure', ['message', 'exception'])):
  """Holds information about the failure of a check.

  Attributes:
    message: A message detailing the failure; to be shown to the user.
    exception: An Exception object associated with the failure.
  """

  def __new__(cls, message='', exception=None):
    return super(Failure, cls).__new__(cls, message, exception)
