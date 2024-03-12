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

"""Client for interaction with Operations CRUD on API Gateway API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.api_gateway import base
from googlecloudsdk.api_lib.util import waiter


class OperationsClient(base.BaseClient):
  """Client for operation objects on Cloud API Gateway API."""

  def __init__(self, client=None):
    base.BaseClient.__init__(
        self,
        client=client,
        message_base='ApigatewayProjectsLocationsOperations',
        service_name='projects_locations_operations')

    self.DefineGet()
    self.DefineList('operations', is_operations=True)

  def Cancel(self, operation_ref):
    """Cancel an operation.

    Args:
      operation_ref: The message to process (expected to be of type Operation)

    Returns:
      (Empty) The response message.
    """
    req = self.messages.ApigatewayProjectsLocationsOperationsCancelRequest(
        name=operation_ref.RelativeName())

    return self.service.Cancel(req)

  def WaitForOperation(self, operation_ref, message=None, service=None):
    """Waits for the given google.longrunning.Operation to complete.

    Args:
      operation_ref: The operation to poll.
      message: String to display for default progress_tracker.
      service: The service to get the resource after the long running operation
        completes.

    Raises:
      apitools.base.py.HttpError: if the request returns an HTTP error

    Returns:
      The Operation or the Resource the Operation is associated with.
    """
    # Consumers of OperationsClient can be resource-aware and if so, they can
    # provide the service used for interacting with the Resource the Operation
    # is associated with.  In this case, OperationsClient#WaitForOperation  will
    # return the Resource the polled Operation is associated with.  Otherwise,
    # no service is provided and the Operation object itself is returned.
    #
    # Example: `gateways create` is resource-aware and returns an
    # ApigatewayGateway while `operations wait` is not resource-aware and will
    # return the Operation itself.
    if service is None:
      poller = waiter.CloudOperationPollerNoResources(
          self.service)
    else:
      poller = waiter.CloudOperationPoller(
          service,
          self.service)

    if message is None:
      message = 'Waiting for Operation [{}] to complete'.format(
          operation_ref.RelativeName())

    return waiter.WaitFor(poller, operation_ref, message)
