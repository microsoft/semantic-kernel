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
"""General utilities using operations in Privateca commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.privateca import base
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources


class OperationError(exceptions.Error):
  """Exception for errors encountered from an operation."""


class OperationTimeoutError(OperationError):
  """Exception for when an operation times out."""


def GetOperationRef(operation):
  """Get a resource reference to a long running operation."""
  return resources.REGISTRY.ParseRelativeName(
      operation.name, 'privateca.projects.locations.operations'
  )


def Await(operation, progress_message, api_version='v1'):
  """Waits for operation to complete while displaying in-progress indicator.

  Args:
    operation: The Operation resource.
    progress_message: The message to display with the in-progress indicator.
    api_version: The API version.

  Returns:
    The resource that is the result of the operation.

  Raises:
    OperationError: if the operation did not complete successfully
  """
  if operation.done:
    if operation.error:
      raise OperationError(operation.error.message)
    return operation.response

  operation_ref = GetOperationRef(operation)
  poller = waiter.CloudOperationPollerNoResources(
      base.GetClientInstance(api_version).projects_locations_operations
  )
  try:
    return waiter.WaitFor(poller, operation_ref, progress_message)
  except waiter.TimeoutError:
    raise OperationTimeoutError(
        'Requested action timed out. Please run the describe command on your'
        ' resource to see if changes were successful, or try again in a few'
        ' minutes.'
    )


def GetMessageFromResponse(response, message_type):
  """Returns a message from the ResponseValue.

  Operations normally return a ResponseValue object in their response field that
  is somewhat difficult to use. This functions returns the corresponding
  message type to make it easier to parse the response.

  Args:
    response: The ResponseValue object that resulted from an Operation.
    message_type: The type of the message that should be returned

  Returns:
    An instance of message_type with the values from the response filled in.
  """
  message_dict = encoding.MessageToDict(response)
  # '@type' is not needed and not present in messages.
  if '@type' in message_dict:
    del message_dict['@type']
  return messages_util.DictToMessageWithErrorCheck(
      message_dict, message_type, throw_on_unexpected_fields=False
  )
