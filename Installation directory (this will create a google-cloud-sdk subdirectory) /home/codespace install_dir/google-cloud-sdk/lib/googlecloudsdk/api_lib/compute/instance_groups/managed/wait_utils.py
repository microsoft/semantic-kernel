# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""API library for waiting for managed instance groups state transition."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.command_lib.compute.instance_groups.managed import wait_info
from googlecloudsdk.core import log
from googlecloudsdk.core.util import retry


class IgmState(enum.Enum):
  """Represents IGM state to wait for."""
  STABLE = 0
  VERSION_TARGET_REACHED = 1
  ALL_INSTANCES_CONFIG_EFFECTIVE = 2

_TIME_BETWEEN_POLLS_MS = 10000


def WaitForIgmState(client, group_ref, desired_igm_state, timeout_sec=None):
  """Waits until the desired state of managed instance group is reached."""
  try:
    max_wait_ms = timeout_sec*1000 if timeout_sec else None
    retry.Retryer(max_wait_ms=max_wait_ms).RetryOnResult(
        _IsStateReached,
        [client, group_ref, desired_igm_state],
        should_retry_if=False,
        sleep_ms=_TIME_BETWEEN_POLLS_MS)
    if desired_igm_state == IgmState.STABLE:
      log.out.Print('Group is stable')
    elif desired_igm_state == IgmState.VERSION_TARGET_REACHED:
      log.out.Print('Version target is reached')
    elif desired_igm_state == IgmState.ALL_INSTANCES_CONFIG_EFFECTIVE:
      log.out.Print('All-instances config is effective')

  except retry.WaitException:
    if desired_igm_state == IgmState.STABLE:
      raise utils.TimeoutError('Timeout while waiting for group to '
                               'become stable.')
    if desired_igm_state == IgmState.VERSION_TARGET_REACHED:
      raise utils.TimeoutError('Timeout while waiting for group to reach '
                               'version target.')
    if desired_igm_state == IgmState.ALL_INSTANCES_CONFIG_EFFECTIVE:
      raise utils.TimeoutError('Timeout while waiting for group to reach '
                               'effective all-instances config.')


def _IsStateReached(client, group_ref, desired_igm_state):
  """Checks if the desired state is reached."""
  responses, errors = _GetResources(client, group_ref)
  if errors:
    utils.RaiseToolException(errors)
  if desired_igm_state == IgmState.STABLE:
    is_stable = responses[0].status.isStable
    if not is_stable:
      log.out.Print(wait_info.CreateWaitText(responses[0]))
    return is_stable
  elif desired_igm_state == IgmState.VERSION_TARGET_REACHED:
    is_version_target_reached = responses[0].status.versionTarget.isReached
    if not is_version_target_reached:
      log.out.Print('Waiting for group to reach version target')
    return is_version_target_reached
  elif desired_igm_state == IgmState.ALL_INSTANCES_CONFIG_EFFECTIVE:
    all_instances_config_effective = responses[
        0].status.allInstancesConfig.effective
    if not all_instances_config_effective:
      log.out.Print('Waiting for group to reach all-instances config effective')
    return all_instances_config_effective
  else:
    raise Exception('Incorrect desired_igm_state')


def _GetResources(client, group_ref):
  """Retrieves group and potential errors."""
  service, request = _GetRequestForGroup(client, group_ref)
  errors = []
  results = client.MakeRequests(
      requests=[(service, 'Get', request)],
      errors_to_collect=errors)

  return results, errors


def _GetRequestForGroup(client, group_ref):
  """Executes a request for a group - either zonal or regional one."""
  if group_ref.Collection() == 'compute.instanceGroupManagers':
    service = client.apitools_client.instanceGroupManagers
    request = service.GetRequestType('Get')(
        instanceGroupManager=group_ref.Name(),
        zone=group_ref.zone,
        project=group_ref.project)
  elif group_ref.Collection() == 'compute.regionInstanceGroupManagers':
    service = client.apitools_client.regionInstanceGroupManagers
    request = service.GetRequestType('Get')(
        instanceGroupManager=group_ref.Name(),
        region=group_ref.region,
        project=group_ref.project)
  else:
    raise ValueError('Unknown reference type {0}'.format(
        group_ref.Collection()))
  return (service, request)
