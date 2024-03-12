# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.ai import constants


def GetClientInstance(api_version=None, no_http=False):
  return apis.GetClientInstance(
      constants.AI_PLATFORM_API_NAME, api_version, no_http=no_http)


class AiPlatformOperationPoller(waiter.CloudOperationPoller):
  """Poller for AI Platform operations API.

  This is necessary because the core operations library doesn't directly support
  simple_uri.
  """

  def __init__(self, client):
    self.client = client
    super(AiPlatformOperationPoller, self).__init__(
        self.client.client.projects_locations_operations,
        self.client.client.projects_locations_operations)

  def Poll(self, operation_ref):
    return self.client.Get(operation_ref)

  def GetResult(self, operation):
    return operation


class OperationsClient(object):
  """High-level client for the AI Platform operations surface."""

  def __init__(self,
               client=None,
               messages=None,
               version=constants.BETA_VERSION):
    self.client = client or GetClientInstance(
        constants.AI_PLATFORM_API_VERSION[version])
    self.messages = messages or self.client.MESSAGES_MODULE

  def Get(self, operation_ref):
    return self.client.projects_locations_operations.Get(
        self.messages.AiplatformProjectsLocationsOperationsGetRequest(
            name=operation_ref.RelativeName()))

  def WaitForOperation(self, operation, operation_ref, message=None):
    """Wait until the operation is complete or times out.

    Args:
      operation: The operation resource to wait on
      operation_ref: The operation reference to the operation resource. It's the
        result by calling resources.REGISTRY.Parse
      message: str, the message to print while waiting.

    Returns:
      The operation resource when it has completed

    Raises:
      OperationTimeoutError: when the operation polling times out
      OperationError: when the operation completed with an error
    """
    poller = AiPlatformOperationPoller(self)
    if poller.IsDone(operation):
      return operation

    if message is None:
      message = 'Waiting for operation [{}]'.format(operation_ref.Name())
    return waiter.WaitFor(poller, operation_ref, message)
