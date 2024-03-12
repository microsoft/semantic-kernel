# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Utils for common agent pool API interactions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.transfer import name_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import retry


def _is_agent_pool_still_creating(result, retryer_state):
  """Takes AgentPool Apitools object and returns if it's state is "creating".

  When an AgentPool create request is sent to the backend, it takes a few
  moments for the pool's state to go from CREATING to CREATED. This check
  is useful to see if we can start acting like the pool exists yet.

  Args:
    result (messages.AgentPool): Object representing current state of AgentPool
      on the backend.
    retryer_state (retry.RetryerState): Unused. Contains info about trials and
      time passed.

  Returns:
    Boolean representing if AgentPool's state is "CREATING." False = "CREATED".
  """
  del retryer_state  # Unused.
  messages = apis.GetMessagesModule('transfer', 'v1')
  return result.state == messages.AgentPool.StateValueValuesEnum.CREATING


def api_get(name):
  """Returns agent pool details from API as Apitools object."""
  client = apis.GetClientInstance('transfer', 'v1')
  messages = apis.GetMessagesModule('transfer', 'v1')
  formatted_agent_pool_name = name_util.add_agent_pool_prefix(name)
  return client.projects_agentPools.Get(
      messages.StoragetransferProjectsAgentPoolsGetRequest(
          name=formatted_agent_pool_name))


def block_until_created(name):
  """Blocks until agent pool is created. Useful for scripting."""
  with progress_tracker.ProgressTracker(
      message='Waiting for backend to create agent pool'):
    result = retry.Retryer().RetryOnResult(
        api_get,
        args=[name],
        should_retry_if=_is_agent_pool_still_creating,
        sleep_ms=(
            properties.VALUES.transfer.no_async_polling_interval_ms.GetInt()),
    )
  return result
