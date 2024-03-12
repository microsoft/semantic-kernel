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

"""Client for interaction with Api Config CRUD on API Gateway API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.api_gateway import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.api_gateway import common_flags


class ApiConfigClient(base.BaseClient):
  """Client for Api Config objects on Cloud API Gateway API."""

  def __init__(self, client=None):
    base.BaseClient.__init__(
        self,
        client=client,
        message_base='ApigatewayProjectsLocationsApisConfigs',
        service_name='projects_locations_apis_configs')
    self.DefineDelete()
    self.DefineList('apiConfigs')
    self.DefineUpdate('apigatewayApiConfig')
    self.supported_views = {
        'FULL':
            self.messages.ApigatewayProjectsLocationsApisConfigsGetRequest
            .ViewValueValuesEnum.FULL,
        'BASIC':
            self.messages.ApigatewayProjectsLocationsApisConfigsGetRequest
            .ViewValueValuesEnum.BASIC
    }

  def Create(self, api_config_ref, display_name=None, labels=None,
             backend_auth=None, managed_service_configs=None,
             grpc_service_defs=None, open_api_docs=None):
    """Creates an Api Config object.

    Args:
      api_config_ref: A parsed resource reference for the api
      display_name: Optional string display name
      labels: Optional cloud labels (as provided in the labels argument)
      backend_auth: Optional string to set the service account for backend auth
      managed_service_configs: Optional field to send in a list of managed
       service configurations. Should be in the form of the
       ApigatewayApiConfigFileMessage's generated from the discovery document
      grpc_service_defs: Optional field to send in a list of GRPC service
       definitions. Should be in the form of
       ApigatewayApiConfigGrpcServiceDefinition's generated from the discovery
       document
      open_api_docs: Optional field to send in a list of Open API documents.
       Should be in the form of ApigatewayApiConfigOpenApiDocument's generated
       from the discovery document


    Returns:
      Long running operation
    """
    labels = common_flags.ProcessLabelsFlag(
        labels,
        self.messages.ApigatewayApiConfig.LabelsValue)
    api_config = self.messages.ApigatewayApiConfig(
        name=api_config_ref.RelativeName(),
        displayName=display_name,
        labels=labels,
        gatewayServiceAccount=backend_auth,
        managedServiceConfigs=managed_service_configs,
        grpcServices=grpc_service_defs,
        openapiDocuments=open_api_docs)

    req = self.create_request(
        apiConfigId=api_config_ref.Name(),
        apigatewayApiConfig=api_config,
        parent=api_config_ref.Parent().RelativeName())

    return self.service.Create(req)

  def Get(self, api_config_ref, view=None):
    """Returns an API Config object.

    Args:
      api_config_ref: A parsed resource reference for the API.
      view: Optional string. If specified as FULL, the source config files will
        be returned.

    Returns:
      An API Config object.

    Raises:
      calliope.InvalidArgumentException: If an invalid view (i.e. not FULL,
      BASIC, or none) was
      provided.
    """

    view_enum = None
    if view is not None:
      try:
        view_enum = self.supported_views[view.upper()]
      except KeyError:
        raise calliope_exceptions.InvalidArgumentException(
            '--view', 'View must be one of: "FULL" or "BASIC".')
    req = self.get_request(name=api_config_ref.RelativeName(), view=view_enum)

    return self.service.Get(req)
