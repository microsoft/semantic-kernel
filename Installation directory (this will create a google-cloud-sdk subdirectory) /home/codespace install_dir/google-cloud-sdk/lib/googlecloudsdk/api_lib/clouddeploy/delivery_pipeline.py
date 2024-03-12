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
"""Support library to handle the delivery-pipeline subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.clouddeploy import client_util


class DeliveryPipelinesClient(object):
  """Client for delivery pipeline service in the Cloud Deploy API."""

  def __init__(self, client=None, messages=None):
    """Initialize a delivery_pipeline.DeliveryPipelinesClient.

    Args:
      client: base_api.BaseApiClient, the client class for Cloud Deploy.
      messages: module containing the definitions of messages for Cloud Deploy.
    """
    self.client = client or client_util.GetClientInstance()
    self.messages = messages or client_util.GetMessagesModule(client)
    self._service = self.client.projects_locations_deliveryPipelines

  def Get(self, name):
    """Gets the delivery pipeline object by calling the delivery pipeline get API.

    Args:
      name: delivery pipeline name.

    Returns:
      a delivery pipeline object.
    """
    request = (
        self.messages.ClouddeployProjectsLocationsDeliveryPipelinesGetRequest(
            name=name
        )
    )
    return self._service.Get(request)

  def List(
      self, location, filter_str=None, order_by=None, page_size=0, limit=None
  ):
    """Lists Delivery Pipeline resources that belong to a location.

    Args:
      location: str, the full name of the location which owns the Delivery
        Pipelines.
      filter_str: optional[str], list filter.
      order_by: optional[str], field to sort by.
      page_size: optional[int], the maximum number of `DeliveryPipeline` objects
        to return.
      limit: int, The maximum number of records to yield. None if all available
        records should be yielded.

    Returns:
      Delivery Pipeline list response.
    """
    list_req = (
        self.messages.ClouddeployProjectsLocationsDeliveryPipelinesListRequest(
            parent=location, filter=filter_str, orderBy=order_by
        )
    )
    return list_pager.YieldFromList(
        self._service,
        list_req,
        field='deliveryPipelines',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize',
    )

  def RollbackTarget(self, name, request):
    """Creates a rollback for a given target.

    Args:
      name: pipeline name
      request: RollbackTargetRequest

    Returns:
      RollbackTargetResponse
    """
    msg = self.messages.ClouddeployProjectsLocationsDeliveryPipelinesRollbackTargetRequest(
        name=name,
        rollbackTargetRequest=request,
    )
    return self._service.RollbackTarget(msg)
