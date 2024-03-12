# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Utilities for dealing with long-running operations (simple uri)."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def GetMessagesModule(version='v1'):
  return apis.GetMessagesModule('ml', version)


def GetClientInstance(version='v1', no_http=False):
  return apis.GetClientInstance('ml', version, no_http=no_http)


class CloudMlOperationPoller(waiter.CloudOperationPoller):
  """Poller for Cloud ML Engine operations API.

  This is necessary because the core operations library doesn't directly support
  simple_uri.
  """

  def __init__(self, client):
    self.client = client
    super(CloudMlOperationPoller, self).__init__(
        self.client.client.projects_operations,
        self.client.client.projects_operations)

  def Poll(self, operation_ref):
    return self.client.Get(operation_ref)

  def GetResult(self, operation):
    return operation


class OperationsClient(object):
  """Client for operations service in the Cloud ML Engine API."""

  def __init__(self, version='v1'):
    self.client = GetClientInstance(version)
    self.messages = self.client.MESSAGES_MODULE

  def List(self, project_ref):
    return list_pager.YieldFromList(
        self.client.projects_operations,
        self.messages.MlProjectsOperationsListRequest(
            name=project_ref.RelativeName()),
        field='operations',
        batch_size_attribute='pageSize')

  def Get(self, operation_ref):
    return self.client.projects_operations.Get(
        self.messages.MlProjectsOperationsGetRequest(
            name=operation_ref.RelativeName()))

  def Cancel(self, operation_ref):
    return self.client.projects_operations.Cancel(
        self.messages.MlProjectsOperationsCancelRequest(
            name=operation_ref.RelativeName()))

  def WaitForOperation(self, operation, message=None):
    """Wait until the operation is complete or times out.

    Args:
      operation: The operation resource to wait on
      message: str, the message to print while waiting.

    Returns:
      The operation resource when it has completed

    Raises:
      OperationTimeoutError: when the operation polling times out
      OperationError: when the operation completed with an error
    """
    poller = CloudMlOperationPoller(self)
    if poller.IsDone(operation):
      return operation

    operation_ref = resources.REGISTRY.Parse(
        operation.name,
        params={'projectsId': properties.VALUES.core.project.GetOrFail},
        collection='ml.projects.operations')
    if message is None:
      message = 'Waiting for operation [{}]'.format(operation_ref.Name())
    return waiter.WaitFor(
        poller, operation_ref, message,
        pre_start_sleep_ms=0,
        max_wait_ms=60*60*1000,
        exponential_sleep_multiplier=None,
        jitter_ms=None,
        wait_ceiling_ms=None,
        sleep_ms=5000)
