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
"""Utilities for the clouddeploy API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

_API_NAME = 'clouddeploy'
_API_VERSION = 'v1'


def GetMessagesModule(client=None):
  """Returns the messages module for Cloud Deploy.

  Args:
    client: base_api.BaseApiClient, the client class for Cloud Deploy.

  Returns:
    Module containing the definitions of messages for Cloud Deploy.
  """
  client = client or GetClientInstance()
  return client.MESSAGES_MODULE


def GetClientInstance(use_http=True):
  """Returns an instance of the Cloud Deploy client.

  Args:
    use_http: bool, True to create an http object for this client.

  Returns:
    base_api.BaseApiClient, An instance of the Cloud Deploy client.
  """
  return apis.GetClientInstance(_API_NAME, _API_VERSION, no_http=(not use_http))


class DeployOperationPoller(waiter.CloudOperationPoller):
  """Poller for Cloud Deploy operations API.

  This is necessary because the core operations library doesn't directly support
  simple_uri.
  """

  def __init__(self, client):
    """Initiates a DeployOperationPoller.

    Args:
      client: base_api.BaseApiClient, An instance of the Cloud Deploy client.
    """
    self.client = client
    super(DeployOperationPoller,
          self).__init__(self.client.client.projects_locations_operations,
                         self.client.client.projects_locations_operations)

  def Poll(self, operation_ref):
    return self.client.Get(operation_ref)

  def GetResult(self, operation):
    return operation


class OperationsClient(object):
  """High-level client for the cloud deploy operations surface."""

  def __init__(self, client=None, messages=None):
    """Initiates an OperationsClient.

    Args:
      client:  base_api.BaseApiClient, An instance of the Cloud Deploy client.
      messages: messages module for Cloud Deploy.
    """
    self.client = client or GetClientInstance()
    self.messages = messages or self.client.MESSAGES_MODULE

  def Get(self, operation_ref):
    return self.client.projects_locations_operations.Get(
        self.messages.ClouddeployProjectsLocationsOperationsGetRequest(
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
    poller = DeployOperationPoller(self)
    if poller.IsDone(operation):
      return operation

    if message is None:
      message = 'Waiting for operation [{}]'.format(operation_ref.Name())
    return waiter.WaitFor(poller, operation_ref, message)

  def CheckOperationStatus(self, operation_dict, msg_template):
    """Checks operations status.

    Only logs the errors instead of re-throwing them.

    Args:
     operation_dict: dict[str, oOptional[clouddeploy_messages.Operation],
       dictionary of resource name and clouddeploy_messages.Operation. The
       operation can be None if the operation isn't executed.
     msg_template: output string template.
    """
    for resource_name, operation in operation_dict.items():
      if not operation or not operation.name:
        continue
      try:
        operation_ref = resources.REGISTRY.ParseRelativeName(
            operation.name,
            collection='clouddeploy.projects.locations.operations')
        _ = self.WaitForOperation(
            operation, operation_ref,
            'Waiting for the operation on resource {}'.format(
                resource_name)).response

        log.status.Print(msg_template.format(resource_name))

      except core_exceptions.Error as e:
        log.status.Print('Operation failed: {}'.format(e))
