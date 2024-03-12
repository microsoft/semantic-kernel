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
"""Common utility functions for Updater."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.util import time_util
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.resource import resource_printer


HTTP_ERROR_FORMAT = (
    'ResponseError: code={status_code}, message={status_message}')


def GetApiClientInstance():
  return core_apis.GetClientInstance('replicapoolupdater', 'v1beta1')


def GetApiMessages():
  return core_apis.GetMessagesModule('replicapoolupdater', 'v1beta1')


def WaitForOperation(client, operation_ref, message):
  """Waits until the given operation finishes.

  Wait loop terminates when the operation's status becomes 'DONE'.

  Args:
    client: interface to the Cloud Updater API
    operation_ref: operation to poll
    message: message to be displayed by progress tracker

  Returns:
    True iff the operation finishes with success
  """
  with progress_tracker.ProgressTracker(message, autotick=False) as pt:
    while True:
      operation = client.zoneOperations.Get(
          client.MESSAGES_MODULE.ReplicapoolupdaterZoneOperationsGetRequest(
              project=operation_ref.project,
              zone=operation_ref.zone,
              operation=operation_ref.operation))
      if operation.error:
        return False
      if operation.status == 'DONE':
        return True
      pt.Tick()
      time_util.Sleep(2)


def PrettyPrint(resource, print_format='json'):
  """Prints the given resource."""
  resource_printer.Print(resources=[resource], print_format=print_format)
