# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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

# pylint: disable=raise-missing-from
"""Pollers for Serverless operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
from googlecloudsdk.core import exceptions


class DomainMappingResourceRecordPoller(waiter.OperationPoller):
  """Poll for when a DomainMapping first has resourceRecords."""

  def __init__(self, ops):
    self._ops = ops

  def IsDone(self, mapping):
    if getattr(mapping.status, 'resourceRecords', None):
      return True
    conditions = mapping.conditions
    # pylint: disable=g-bool-id-comparison
    # False (indicating failure) as distinct from None (indicating not sure yet)
    if conditions and conditions['Ready']['status'] is False:
      return True
    # pylint: enable=g-bool-id-comparison
    return False

  def GetResult(self, mapping):
    return mapping

  def Poll(self, domain_mapping_ref):
    return self._ops.GetDomainMapping(domain_mapping_ref)


class ConditionPoller(waiter.OperationPoller):
  """A poller for CloudRun resource creation or update.

  Takes in a reference to a StagedProgressTracker, and updates it with progress.
  """

  def __init__(
      self, resource_getter, tracker, dependencies=None, ready_message='Done.'
  ):
    """Initialize the ConditionPoller.

    Start any unblocked stages in the tracker immediately.

    Arguments:
      resource_getter: function, returns a resource with conditions.
      tracker: a StagedProgressTracker to keep updated. It must contain a stage
        for each condition in the dependencies map, if the dependencies map is
        provided.  The stage represented by each key can only start when the set
        of conditions in the corresponding value have all completed. If a
        condition should be managed by this ConditionPoller but depends on
        nothing, it should map to an empty set. Conditions in the tracker but
        *not* managed by the ConditionPoller should not appear in the dict.
      dependencies: Dict[str, Set[str]], The dependencies between conditions
        that are managed by this ConditionPoller. The values are the set of
        conditions that must become true before the key begins being worked on
        by the server.  If the entire dependencies dict is None, the poller will
        assume that all keys in the tracker are relevant and none have
        dependencies.
      ready_message: str, message to display in header of tracker when
        conditions are ready.
    """
    # _dependencies is a map of condition -> {preceding conditions}
    # It is meant to be checked off as we finish things.
    self._dependencies = {k: set() for k in tracker}
    if dependencies is not None:
      for k in dependencies:
        # Add dependencies, only if they're still not complete. If a stage isn't
        # in the tracker. consider it "already complete".
        self._dependencies[k] = {
            c
            for c in dependencies[k]
            if c in tracker and not tracker.IsComplete(c)
        }
    self._resource_getter = resource_getter
    self._tracker = tracker
    self._resource_fail_type = exceptions.Error
    self._ready_message = ready_message
    self._StartUnblocked()

  def _IsBlocked(self, condition):
    return condition in self._dependencies and self._dependencies[condition]

  def IsDone(self, conditions):
    """Overrides.

    Args:
      conditions: A condition.Conditions object.

    Returns:
      a bool indicates whether `conditions` is terminal.
    """
    if conditions is None:
      return False
    return conditions.IsTerminal()

  def _PollTerminalSubconditions(self, conditions, conditions_message):
    for condition in conditions.TerminalSubconditions():
      if condition not in self._dependencies:
        continue
      message = conditions[condition]['message']
      status = conditions[condition]['status']
      self._PossiblyUpdateMessage(condition, message, conditions_message)
      if status is None:
        continue
      elif status:
        if self._PossiblyCompleteStage(condition, message):
          # Check all terminal subconditions again to ensure any stages that
          # were unblocked by this stage completing are re-checked before we
          # check the ready condition
          self._PollTerminalSubconditions(conditions, conditions_message)
          break
      else:
        self._PossiblyFailStage(condition, message)

  def Poll(self, unused_ref):
    """Overrides.

    Args:
      unused_ref: A string representing the operation reference. Currently it
        must be 'deploy'.

    Returns:
      A condition.Conditions object.
    """
    conditions = self.GetConditions()

    if conditions is None or not conditions.IsFresh():
      return None

    conditions_message = conditions.DescriptiveMessage()
    self._tracker.UpdateHeaderMessage(conditions_message)

    self._PollTerminalSubconditions(conditions, conditions_message)

    terminal_condition = conditions.TerminalCondition()
    if conditions.IsReady():
      self._tracker.UpdateHeaderMessage(self._ready_message)
      if terminal_condition in self._dependencies:
        self._PossiblyCompleteStage(terminal_condition, None)
      self._tracker.Tick()
    elif conditions.IsFailed():
      if terminal_condition in self._dependencies:
        self._PossiblyFailStage(terminal_condition, None)
      raise self._resource_fail_type(conditions_message)

    return conditions

  def GetResource(self):
    return self._resource_getter()

  def _PossiblyUpdateMessage(self, condition, message, conditions_message):
    """Update the stage message.

    Args:
      condition: str, The name of the status condition.
      message: str, The new message to display
      conditions_message: str, The message from the conditions object we're
        displaying..
    """
    if condition not in self._tracker or self._tracker.IsComplete(condition):
      return

    if self._IsBlocked(condition):
      return

    if message != conditions_message:
      self._tracker.UpdateStage(condition, message)

  def _RecordConditionComplete(self, condition):
    """Take care of the internal-to-this-class bookkeeping stage complete."""
    # Unblock anything that was blocked on this.

    # Strategy: "check off" each dependency as we complete it by removing from
    # the set in the value.
    for requirements in self._dependencies.values():
      requirements.discard(condition)

  def _PossiblyCompleteStage(self, condition, message):
    """Complete the stage if it's not already complete.

    Make sure the necessary internal bookkeeping is done.

    Args:
      condition: str, The name of the condition whose stage should be completed.
      message: str, The detailed message for the condition.

    Returns:
      bool: True if stage was completed, False if no action taken
    """
    if condition not in self._tracker or self._tracker.IsComplete(condition):
      return False
    # A blocked condition is likely to remain True (indicating the previous
    # operation concerning it was successful) until the blocking condition(s)
    # finish and it's time to switch to Unknown (the current operation
    # concerning it is in progress). Don't mark those done before they switch to
    # Unknown.
    if not self._tracker.IsRunning(condition):
      return False
    self._RecordConditionComplete(condition)
    self._StartUnblocked()
    self._tracker.CompleteStage(condition, message)
    return True

  def _StartUnblocked(self):
    """Call StartStage in the tracker for any not-started not-blocked tasks.

    Record the fact that they're started in our internal bookkeeping.
    """
    # The set of stages that aren't marked started and don't have unsatisfied
    # dependencies are newly unblocked.
    for c in self._dependencies:
      if c not in self._tracker:
        continue
      if self._tracker.IsWaiting(c) and not self._IsBlocked(c):
        self._tracker.StartStage(c)
    # TODO(b/120679874): Should not have to manually call Tick()
    self._tracker.Tick()

  def _PossiblyFailStage(self, condition, message):
    """Possibly fail the stage.

    Args:
      condition: str, The name of the status whose stage failed.
      message: str, The detailed message for the condition.

    Raises:
      DeploymentFailedError: If the 'Ready' condition failed.
    """
    # Don't fail an already failed stage.
    if condition not in self._tracker or self._tracker.IsComplete(condition):
      return

    self._tracker.FailStage(
        condition, self._resource_fail_type(message), message
    )

  def GetResult(self, conditions):
    """Overrides.

    Get terminal conditions as the polling result.

    Args:
      conditions: A condition.Conditions object.

    Returns:
      A condition.Conditions object.
    """
    return conditions

  def GetConditions(self):
    """Returns the resource conditions wrapped in condition.Conditions.

    Returns:
      A condition.Conditions object.
    """
    resource = self._resource_getter()

    if resource is None:
      return None
    return resource.conditions


class ServiceConditionPoller(ConditionPoller):
  """A ConditionPoller for services."""

  def __init__(self, getter, tracker, dependencies=None, serv=None):
    super().__init__(getter, tracker, dependencies)
    self._resource_fail_type = serverless_exceptions.DeploymentFailedError


class RevisionNameBasedPoller(waiter.OperationPoller):
  """Poll for the revision with the given name to exist."""

  def __init__(self, operations, revision_ref_getter):
    self._operations = operations
    self._revision_ref_getter = revision_ref_getter

  def IsDone(self, revision_obj):
    return bool(revision_obj)

  def Poll(self, revision_name):
    revision_ref = self._revision_ref_getter(revision_name)
    return self._operations.GetRevision(revision_ref)

  def GetResult(self, revision_obj):
    return revision_obj


class NonceBasedRevisionPoller(waiter.OperationPoller):
  """To poll for exactly one revision with the given nonce to appear."""

  def __init__(self, operations, namespace_ref):
    self._operations = operations
    self._namespace = namespace_ref

  def IsDone(self, revisions):
    return bool(revisions)

  def Poll(self, nonce):
    return self._operations.GetRevisionsByNonce(self._namespace, nonce)

  def GetResult(self, revisions):
    if len(revisions) == 1:
      return revisions[0]
    return None


class ExecutionConditionPoller(ConditionPoller):
  """A ConditionPoller for jobs."""

  def __init__(self, getter, tracker, terminal_condition, dependencies=None):
    super().__init__(getter, tracker, dependencies)
    self._resource_fail_type = serverless_exceptions.ExecutionFailedError
    self._terminal_condition = terminal_condition

  def _PotentiallyUpdateInstanceCompletions(self, job_obj, conditions):
    """Maybe update the terminal condition stage message with number of completions."""
    terminal_condition = conditions.TerminalCondition()
    if terminal_condition not in self._tracker or self._IsBlocked(
        terminal_condition
    ):
      return

    self._tracker.UpdateStage(
        terminal_condition,
        '{} / {} complete'.format(
            job_obj.status.succeededCount or 0, job_obj.task_count
        ),
    )

  def GetConditions(self):
    """Returns the resource conditions wrapped in condition.Conditions.

    Returns:
      A condition.Conditions object.
    """
    job_obj = self._resource_getter()

    if job_obj is None:
      return None

    conditions = job_obj.GetConditions(self._terminal_condition)

    # This is a bit of a cheat to hook into the polling method. This is done
    # because this is only place where the resource is gotten from the server,
    # so reusing it saves an api call. This is also simpler than attempting to
    # override the Poll method which would likely lead to duplicate code and/or
    # complicated error handling.
    self._PotentiallyUpdateInstanceCompletions(job_obj, conditions)

    return conditions


class WaitOperationPoller(waiter.CloudOperationPoller):
  """Poll for a long running operation using Wait instead of Get."""

  def Poll(self, operation_ref):
    """Overrides.

    Args:
      operation_ref: googlecloudsdk.core.resources.Resource.

    Returns:
      fetched operation message.
    """
    request_type = self.operation_service.GetRequestType('Wait')
    return self.operation_service.Wait(
        request_type(name=operation_ref.RelativeName())
    )
