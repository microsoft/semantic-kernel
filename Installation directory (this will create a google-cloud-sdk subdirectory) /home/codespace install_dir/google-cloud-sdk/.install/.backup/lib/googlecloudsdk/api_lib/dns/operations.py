# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""API client library for Cloud DNS operatoins."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import waiter


class Poller(waiter.OperationPoller):
  """Manages a longrunning Operations.

  See https://cloud.google.com/speech/reference/rpc/google.longrunning
  """

  def __init__(self, operations_client, api_version='v1'):
    """Sets up poller for dns operations.

    Args:
      operations_client: Client, client for retrieving information about
          ongoing operation.
      api_version: Cloud DNS api version this poller should use.
    """
    self.operations_client = operations_client
    self.api_version = api_version

  def IsDone(self, operation):
    """Overrides."""
    done_enum = self.operations_client.messages.Operation.StatusValueValuesEnum.DONE if self.api_version == 'v2' else self.operations_client.messages.Operation.StatusValueValuesEnum.done
    if operation.status == done_enum:
      return True
    return False

  def Poll(self, operation_ref):
    """Overrides.

    Args:
      operation_ref: googlecloudsdk.core.resources.Resource.

    Returns:
      fetched operation message.
    """
    return self.operations_client.Get(operation_ref)

  def GetResult(self, operation):
    """Overrides.

    Args:
      operation: api_name_messages.Operation.

    Returns:
      result of result_service.Get request.
    """
    return operation.zoneContext.newValue


def WaitFor(version, operation_ref, message, location=None):
  operation_poller = Poller(Client.FromApiVersion(version, location), version)
  return waiter.WaitFor(operation_poller, operation_ref, message)


class Client(object):
  """API client for Cloud DNS operations."""

  _API_NAME = 'dns'

  def __init__(self, version, client, messages=None, location=None):
    self.version = version
    self.client = client
    self._service = self.client.managedZoneOperations
    self.messages = messages or client.MESSAGES_MODULE
    self.location = location

  @classmethod
  def FromApiVersion(cls, version, location=None):
    return cls(
        version, util.GetApiClient(version), messages=None, location=location)

  def Get(self, operation_ref):
    request = self.messages.DnsManagedZoneOperationsGetRequest(
        operation=operation_ref.Name(),
        managedZone=operation_ref.managedZone,
        project=operation_ref.project)
    if self.location:
      request.location = self.location
    return self._service.Get(request)

  def List(self, zone_ref, limit=None):
    request = self.messages.DnsManagedZoneOperationsListRequest(
        managedZone=zone_ref.Name(),
        project=zone_ref.project)
    if self.location:
      request.location = self.location
    return list_pager.YieldFromList(
        self._service, request, limit=limit, field='operations')
