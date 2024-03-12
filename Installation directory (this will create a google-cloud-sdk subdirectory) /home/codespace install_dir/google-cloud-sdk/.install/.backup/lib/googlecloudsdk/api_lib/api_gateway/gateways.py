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

"""Client for interaction with Gateway CRUD on API Gateway API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.api_gateway import base
from googlecloudsdk.command_lib.api_gateway import common_flags


class GatewayClient(base.BaseClient):
  """Client for gateway objects on Cloud API Gateway API."""

  def __init__(self, client=None):
    base.BaseClient.__init__(self,
                             client=client,
                             message_base='ApigatewayProjectsLocationsGateways',
                             service_name='projects_locations_gateways')
    self.DefineGet()
    self.DefineDelete()
    self.DefineList('gateways')
    self.DefineUpdate('apigatewayGateway')
    self.DefineIamPolicyFunctions()

  def Create(self, gateway_ref, api_config, display_name=None, labels=None):
    """Creates a new gateway object.

    Args:
      gateway_ref: Resource, a resource reference for the gateway
      api_config: Resource, a resource reference for the gateway
      display_name: Optional display name
      labels: Optional cloud labels

    Returns:
      Long running operation.
    """
    labels = common_flags.ProcessLabelsFlag(
        labels,
        self.messages.ApigatewayGateway.LabelsValue)

    gateway = self.messages.ApigatewayGateway(
        name=gateway_ref.RelativeName(),
        labels=labels,
        apiConfig=api_config.RelativeName(),
        displayName=display_name,
        )

    req = self.create_request(
        parent=gateway_ref.Parent().RelativeName(),
        gatewayId=gateway_ref.Name(),
        apigatewayGateway=gateway,
        )
    resp = self.service.Create(req)

    return resp
