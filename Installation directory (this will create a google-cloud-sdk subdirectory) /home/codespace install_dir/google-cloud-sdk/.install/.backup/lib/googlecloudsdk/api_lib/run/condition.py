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
"""Wraps a Cloud Run Condition messages, making fields easier to access."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import sys


_SEVERITY_ERROR = 'Error'
_SEVERITY_WARNING = 'Warning'

collections_abc = collections
if sys.version_info > (3, 8):
  collections_abc = collections.abc


def GetNonTerminalMessages(conditions, ignore_retry=False):
  """Get messages for non-terminal subconditions.

  Only show a message for some non-terminal subconditions:
  - if severity == warning
  - if message is provided
  Non-terminal subconditions that aren't warnings are effectively neutral,
  so messages for these aren't included unless provided.

  Args:
    conditions: Conditions
    ignore_retry: bool, if True, ignores the "Retry" condition

  Returns:
    list(str) messages of non-terminal subconditions
  """
  messages = []
  for c in conditions.NonTerminalSubconditions():
    if ignore_retry and c == 'Retry':
      continue
    if conditions[c]['severity'] == _SEVERITY_WARNING:
      messages.append('{}: {}'.format(
          c, conditions[c]['message'] or 'Unknown Warning.'))
    elif conditions[c]['message']:
      messages.append('{}: {}'.format(c, conditions[c]['message']))
  return messages


class Conditions(collections_abc.Mapping):
  """Represents the status Conditions of a resource in a dict-like way.

  Resource means a Cloud Run resource, e.g: Configuration.

  The conditions of a resource describe error, warning, and completion states of
  the last set of operations on the resource. True is success, False is failure,
  and "Unknown" is an operation in progress.

  The special "ready condition" describes the overall success state of the
  (last operation on) the resource.

  Other conditions may be "terminal", in which case they are required to be True
  for overall success of the operation, and being False indicates failure.

  If a condition has a severity of "info" or "warning" in the API, it's not
  terminal.

  More info: https://github.com/knative/serving/blob/master/docs/spec/errors.md

  Note, status field of conditions is converted to boolean type.
  """

  def __init__(
      self, conditions, ready_condition=None,
      observed_generation=None, generation=None):
    """Constructor.

    Args:
      conditions: A list of objects of condition_class.
      ready_condition: str, The one condition type that indicates it is ready.
      observed_generation: The observedGeneration field of the status object
      generation: The generation of the object. Incremented every time a user
        changes the object directly.
    """
    self._conditions = {}
    for cond in conditions:
      status = None  # Unset or Unknown
      if cond.status.lower() == 'true':
        status = True
      elif cond.status.lower() == 'false':
        status = False
      self._conditions[cond.type] = {
          'severity': cond.severity,
          'reason': cond.reason,
          'message': cond.message,
          'lastTransitionTime': cond.lastTransitionTime,
          'status': status
      }
    self._ready_condition = ready_condition
    self._fresh = (observed_generation is None or
                   (observed_generation == generation))

  def __getitem__(self, key):
    """Implements evaluation of `self[key]`."""
    return self._conditions[key]

  def __contains__(self, item):
    """Implements evaluation of `item in self`."""
    return any(cond_type == item for cond_type in self._conditions)

  def __len__(self):
    """Implements evaluation of `len(self)`."""
    return len(self._conditions)

  def __iter__(self):
    """Returns a generator yielding the condition types."""
    for cond_type in self._conditions:
      yield cond_type

  def TerminalSubconditions(self):
    """Yields keys of the conditions which if all True, Ready should be true."""
    for k in self:
      if (k != self._ready_condition and
          (not self[k]['severity'] or self[k]['severity'] == _SEVERITY_ERROR)):
        yield k

  def NonTerminalSubconditions(self):
    """Yields keys of the conditions which do not directly affect Ready."""
    for k in self:
      if (k != self._ready_condition and self[k]['severity'] and
          self[k]['severity'] != _SEVERITY_ERROR):
        yield k

  def TerminalCondition(self):
    return self._ready_condition

  def TerminalConditionReason(self):
    """Returns the reason of the terminal condition."""
    if (
        self._ready_condition
        and self._ready_condition in self
        and self[self._ready_condition]['reason']
    ):
      return self[self._ready_condition]['reason']
    return None

  def DescriptiveMessage(self):
    """Descriptive message about what's happened to the last user operation."""
    if (self._ready_condition and
        self._ready_condition in self and
        self[self._ready_condition]['message']):
      return self[self._ready_condition]['message']
    return None

  def IsTerminal(self):
    """True if the resource has finished the last operation, for good or ill.

    conditions are considered terminal if and only if the ready condition is
    either true or false.

    Returns:
      A bool representing if terminal.
    """
    if not self._ready_condition:
      raise NotImplementedError()
    if not self._fresh:
      return False
    if self._ready_condition not in self._conditions:
      return False
    return self._conditions[self._ready_condition]['status'] is not None

  def IsReady(self):
    """Return True if the resource has succeeded its current operation."""
    if not self.IsTerminal():
      return False
    return self._conditions[self._ready_condition]['status']

  def IsFailed(self):
    """"Return True if the resource has failed its current operation."""
    return self.IsTerminal() and not self.IsReady()

  def IsFresh(self):
    return self._fresh
