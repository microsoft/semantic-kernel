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
"""Utils for common jobs API interactions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.transfer import name_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import retry


def _has_not_created_operation(result, retryer_state):
  """Takes TransferJob Apitools object and returns if it lacks an operation."""
  del retryer_state  # Unused.
  return not result.latestOperationName


def api_get(name):
  """Returns job details from API as Apitools object."""
  client = apis.GetClientInstance('transfer', 'v1')
  messages = apis.GetMessagesModule('transfer', 'v1')

  formatted_job_name = name_util.add_job_prefix(name)
  return client.transferJobs.Get(
      messages.StoragetransferTransferJobsGetRequest(
          jobName=formatted_job_name,
          projectId=properties.VALUES.core.project.Get()))


def block_until_operation_created(name):
  """Blocks until job creates an operation and returns operation name."""
  with progress_tracker.ProgressTracker(
      message='Polling for latest operation name'):
    return retry.Retryer().RetryOnResult(
        api_get,
        args=[name],
        should_retry_if=_has_not_created_operation,
        sleep_ms=(
            properties.VALUES.transfer.no_async_polling_interval_ms.GetInt()),
    ).latestOperationName
