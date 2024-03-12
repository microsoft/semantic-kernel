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
"""Exceptions for cloud deploy libraries."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions

HTTP_ERROR_FORMAT = 'Status code: {status_code}. {status_message}.'


class ParserError(exceptions.Error):
  """Error parsing JSON into a dictionary."""

  def __init__(self, path, msg):
    """Initialize a exceptions.ParserError.

    Args:
      path: str, build artifacts file path.
      msg: str, error message.
    """
    msg = 'parsing {path}: {msg}'.format(
        path=path,
        msg=msg,
    )
    super(ParserError, self).__init__(msg)


class ReleaseInactiveError(exceptions.Error):
  """Error when a release is not deployed to any target."""

  def __init__(self):
    super(ReleaseInactiveError, self).__init__(
        'This release is not deployed to a target in the active delivery '
        'pipeline. Include the --to-target parameter to indicate which target '
        'to promote to.'
    )


class AbandonedReleaseError(exceptions.Error):
  """Error when an activity happens on an abandoned release."""

  def __init__(self, error_msg, release_name):
    error_template = '{} Release {} is abandoned.'.format(
        error_msg, release_name)
    super(AbandonedReleaseError, self).__init__(error_template)


class NoStagesError(exceptions.Error):
  """Error when a release doesn't contain any pipeline stages."""

  def __init__(self, release_name):
    super(NoStagesError, self).__init__(
        'No pipeline stages in the release {}.'.format(release_name))


class InvalidReleaseNameError(exceptions.Error):
  """Error when a release has extra $ signs after expanding template terms."""

  def __init__(self, release_name, error_indices):
    error_msg = ("Invalid character '$'"
                 " for release name '{}' at indices:"
                 ' {}. Did you mean to use $DATE or $TIME?')
    super(InvalidReleaseNameError,
          self).__init__(error_msg.format(release_name, error_indices))


class CloudDeployConfigError(exceptions.Error):
  """Error raised for errors in the cloud deploy yaml config."""


class ListRolloutsError(exceptions.Error):
  """Error when it failed to list the rollouts that belongs to a release."""

  def __init__(self, release_name):
    super(ListRolloutsError,
          self).__init__('Failed to list rollouts for {}.'.format(release_name))


class RedeployRolloutError(exceptions.Error):
  """Error when a rollout can't be redeployed.

  Redeploy can only be used for rollouts that are in a SUCCEEDED or FAILED
  state.
  """

  def __init__(self, target_name, rollout_name, rollout_state):
    error_msg = (
        'Unable to redeploy target {}. Rollout {} is in state {} that can\'t '
        'be redeployed'.format(target_name, rollout_name, rollout_state))
    super(RedeployRolloutError, self).__init__(error_msg)


class RolloutIDExhaustedError(exceptions.Error):
  """Error when there are too many rollouts for a given release."""

  def __init__(self, release_name):
    super(RolloutIDExhaustedError, self).__init__(
        'Rollout name space exhausted in release {}. Use --rollout-id to '
        'specify rollout ID.'.format(release_name)
    )


class RolloutInProgressError(exceptions.Error):
  """Error when there is a rollout in progress, no to-target value is given and a promote is attempted."""

  def __init__(self, release_name, target_name):
    super(RolloutInProgressError, self).__init__(
        'Unable to promote release {} to target {}. '
        'A rollout is already in progress.'.format(release_name, target_name)
    )


class RolloutNotInProgressError(exceptions.Error):
  """Error when a rollout is not in_progress, but is expected to be."""

  def __init__(self, rollout_name):
    super(RolloutNotInProgressError, self).__init__(
        'Rollout {} is not IN_PROGRESS.'.format(rollout_name))


class RolloutCannotAdvanceError(exceptions.Error):
  """Error when a rollout cannot be advanced because of a failed precondition."""

  def __init__(self, rollout_name, failed_activity_msg):
    error_msg = '{} Rollout {} cannot be advanced.'.format(
        failed_activity_msg, rollout_name
    )
    super(RolloutCannotAdvanceError, self).__init__(error_msg)


class PipelineSuspendedError(exceptions.Error):
  """Error when a user performs an activity on a suspended pipeline."""

  def __init__(self, pipeline_name, failed_activity_msg):
    error_msg = '{} DeliveryPipeline {} is suspended.'.format(
        failed_activity_msg, pipeline_name)
    super(PipelineSuspendedError, self).__init__(error_msg)


class AutomationNameFormatError(exceptions.Error):
  """Error when the name of the automation in the config file is not formatted correctly."""

  def __init__(self, automation_name):
    super(AutomationNameFormatError, self).__init__(
        'Automation name {} in the configuration should be in the format'
        'of pipeline_id/automation_id.'.format(automation_name)
    )


class AutomationWaitFormatError(exceptions.Error):
  """Error when the name of the automation in the config file is not formatted correctly."""

  def __init__(self):
    super(AutomationWaitFormatError, self).__init__(
        'Wait must be numbers with the last character m, e.g. 5m.'
    )
