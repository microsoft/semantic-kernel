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
"""API client library for Certificate Manager operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.certificate_manager import api_client
from googlecloudsdk.api_lib.util import waiter


class OperationClient(object):
  """API client for Certificate Manager operations."""

  def __init__(self, client=None, messages=None):
    self._client = client or api_client.GetClientInstance()
    self._service = self._client.projects_locations_operations
    self.messages = messages or self._client.MESSAGES_MODULE

  def Get(self, operation_ref):
    """Gets operation.

    Args:
      operation_ref: a Resource reference to a
        certificatemanager.projects.locations.operations resource to get.

    Returns:
      Operation API representation.
    """
    request = self.messages.CertificatemanagerProjectsLocationsOperationsGetRequest(
        name=operation_ref.RelativeName())
    return self._service.Get(request)

  def List(self, parent_ref, limit=None, page_size=None, list_filter=None):
    """List operations in a given project and location.

    Args:
      parent_ref: a Resource reference to a
        certificatemanager.projects.locations resource to list operations for.
      limit: int, the total number of results to return from the API.
      page_size: int, the number of results in each batch from the API.
      list_filter: str, filter to apply in the list request.

    Returns:
      A list of the operations in the project.
    """
    request = self.messages.CertificatemanagerProjectsLocationsOperationsListRequest(
        name=parent_ref.RelativeName(), filter=list_filter)
    return list_pager.YieldFromList(
        self._service,
        request,
        batch_size=page_size,
        limit=limit,
        field='operations',
        batch_size_attribute='pageSize')

  def WaitForOperation(self, operation_ref, message):
    """Waits until operation is complete.

    Args:
      operation_ref: a Resource reference to a
        certificatemanager.projects.locations.operations resource to wait for.
      message: str, message to be displayed while waiting.

    Returns:
      Operation result.
    """
    return waiter.WaitFor(
        waiter.CloudOperationPollerNoResources(self._service),
        operation_ref,
        message,
        wait_ceiling_ms=15 * 1000)
