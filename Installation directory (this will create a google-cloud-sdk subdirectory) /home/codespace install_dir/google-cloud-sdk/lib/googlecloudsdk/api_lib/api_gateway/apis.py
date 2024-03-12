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

"""Client for interaction with Api CRUD on API Gateway API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.api_gateway import base
from googlecloudsdk.command_lib.api_gateway import common_flags


class ApiClient(base.BaseClient):
  """Client for Api objects on Cloud API Gateway API."""

  def __init__(self, client=None):
    base.BaseClient.__init__(self,
                             client=client,
                             message_base='ApigatewayProjectsLocationsApis',
                             service_name='projects_locations_apis')
    self.DefineGet()
    self.DefineList('apis')
    self.DefineUpdate('apigatewayApi')
    self.DefineDelete()
    self.DefineIamPolicyFunctions()

  def DoesExist(self, api_ref):
    """Checks if an Api object exists.

    Args:
      api_ref: Resource, a resource reference for the api

    Returns:
      Boolean, indicating whether or not exists
    """
    try:
      self.Get(api_ref)
    except apitools_exceptions.HttpNotFoundError:
      return False

    return True

  def Create(self, api_ref, managed_service=None, labels=None,
             display_name=None):
    """Creates a new Api object.

    Args:
      api_ref: Resource, a resource reference for the api
      managed_service: Optional string, reference name for OP service
      labels: Optional cloud labels
      display_name: Optional display name

    Returns:
      Long running operation response object.
    """
    labels = common_flags.ProcessLabelsFlag(
        labels,
        self.messages.ApigatewayApi.LabelsValue)
    api = self.messages.ApigatewayApi(
        name=api_ref.RelativeName(),
        managedService=managed_service,
        labels=labels,
        displayName=display_name)

    req = self.create_request(
        apiId=api_ref.Name(),
        apigatewayApi=api,
        parent=api_ref.Parent().RelativeName())

    return self.service.Create(req)
