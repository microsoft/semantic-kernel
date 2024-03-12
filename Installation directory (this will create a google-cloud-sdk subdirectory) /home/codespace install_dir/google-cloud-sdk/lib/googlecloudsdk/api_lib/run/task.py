# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Wraps a Cloud Run Task message with convenience methods."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum
from googlecloudsdk.api_lib.run import container_resource
from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.core.console import console_attr

AUTHOR_ANNOTATION = k8s_object.RUN_GROUP + '/creator'

STARTED_CONDITION = 'Started'
COMPLETED_CONDITION = 'Completed'

EXECUTION_LABEL = 'run.googleapis.com/execution'
STATE_LABEL = 'run.googleapis.com/runningState'


class RestartPolicy(enum.Enum):
  NEVER = 'Never'
  ON_FAILURE = 'OnFailure'


class Task(container_resource.ContainerResource):
  """Wraps a Cloud Run Execution message, making fields more convenient."""

  API_CATEGORY = 'run.googleapis.com'
  KIND = 'Task'
  READY_CONDITION = COMPLETED_CONDITION
  TERMINAL_CONDITIONS = frozenset({STARTED_CONDITION, READY_CONDITION})

  @classmethod
  def New(cls, client, namespace):
    """Produces a new Task object.

    Args:
      client: The Cloud Run API client.
      namespace: str, The serving namespace.

    Returns:
      A new Task object.
    """
    ret = super(Task, cls).New(client, namespace)
    ret.spec.template.spec.containers = [client.MESSAGES_MODULE.Container()]
    return ret

  @property
  def author(self):
    return self.annotations.get(AUTHOR_ANNOTATION)

  @property
  def index(self):
    return self.status.index or 0

  @property
  def execution_name(self):
    return self.labels[EXECUTION_LABEL]

  @property
  def running_state(self):
    return self.labels[STATE_LABEL] if STATE_LABEL in self.labels else None

  @property
  def service_account(self):
    """The service account to use as the container identity."""
    return self.spec.serviceAccountName

  def ReadySymbolAndColor(self):
    """Return a tuple of ready_symbol and display color for this object."""
    encoding = console_attr.GetConsoleAttr().GetEncoding()
    if self.running_state == 'Running':
      return self._PickSymbol('\N{HORIZONTAL ELLIPSIS}', '.',
                              encoding), 'yellow'
    elif self.running_state == 'Succeeded':
      return self._PickSymbol('\N{HEAVY CHECK MARK}', '+', encoding), 'green'
    elif self.running_state == 'Failed':
      return 'X', 'red'
    elif self.running_state == 'Cancelled':
      return '!', 'yellow'
    elif self.running_state == 'Abandoned':
      return '-', 'yellow'
    return '.', 'yellow'

  @property
  def start_time(self):
    return self.status.startTime

  @property
  def completion_time(self):
    return self.status.completionTime

  @property
  def retries(self):
    if self.status.startTime is not None:
      return self.status.retried or 0
    return None

  @property
  def last_exit_code(self):
    if (self.status.lastAttemptResult is not None and
        self.status.lastAttemptResult.exitCode is not None):
      return self.status.lastAttemptResult.exitCode
    elif self.status.completionTime is not None:
      return 0
    return None

  @property
  def last_exit_message(self):
    if (self.status.lastAttemptResult is not None and
        self.status.lastAttemptResult.status.message is not None):
      return self.status.lastAttemptResult.status.message
    return ''
