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
"""Functionality related to Cloud Run Integration API clients."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
from typing import List, Optional

from googlecloudsdk.command_lib.runapps import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.generated_clients.apis.runapps.v1alpha1 import runapps_v1alpha1_client
from googlecloudsdk.generated_clients.apis.runapps.v1alpha1 import runapps_v1alpha1_messages

BASELINE_APIS = ('runapps.googleapis.com',)
LATEST_DEPLOYMENT_FIELD = 'latestDeployment'
SERVICE_TYPE = 'service'
_TYPE_METADATA = None


class UpdateExclusiveGroup:
  def __init__(self, params, required=False):
    self.params = params
    self.required = required


class ServiceType:
  """Types of services supported by runapps."""
  BACKING = 'backing'
  INGRESS = 'ingress'
  WORKLOAD = 'workload'


def _ServiceTypeFromStr(s: str) -> ServiceType:
  """Converts string into service type."""
  types = {
      'backing': ServiceType.BACKING,
      'ingress': ServiceType.INGRESS,
      'workload': ServiceType.WORKLOAD,
  }

  service_type = types.get(s.lower(), None)
  if service_type is None:
    raise exceptions.ArgumentError('Service type {} is not supported'.format(s))

  return service_type


class Parameters:
  """Each integration has a list of parameters that are stored in this class.

  Attributes:
    name: Name of the parameter.
    description: Explanation of the parameter that is visible to the
      customer.
    data_type: Denotes what values are acceptable for the parameter.
    update_allowed: If false, the param can not be provided in an update
      command.
    required:  If true, the param must be provided on a create command.
    hidden: If true, the param will not show up in error messages, but can
      be provided by the user.
    create_allowed: If false, the param cannot be provided on a create
      command.
    default: The value provided for the param if the user has not provided one.
    config_name: The name of the associated field in the config. If not
      provided, it will default to camelcase of `name`.
    label: The descriptive name of the param.
  """

  def __init__(self, name: str, description: str, data_type: str,
               update_allowed: bool = True,
               required: bool = False,
               hidden: bool = False,
               create_allowed: bool = True,
               default: Optional[object] = None,
               config_name: Optional[str] = None,
               label: Optional[str] = None,
               ):
    self.name = name
    self.config_name = config_name if config_name else ToCamelCase(name)
    self.description = description
    self.data_type = data_type
    self.update_allowed = update_allowed
    self.required = required
    self.hidden = hidden
    self.create_allowed = create_allowed
    self.default = default
    self.label = label


class TypeMetadata:
  """Metadata for each integration type supported by Runapps.

  Attributes:
    integration_type: Name of integration type.
    resource_type: Name of resource type.
    description: Description of the integration that is visible to the user.
    example_command: Example commands that will be provided to the user.
    required_field: Field that must exist in the resource config.
    service_type: Denotes what type of service the integration is.
    parameters: What users can provide for the given integration.
    update_exclusive_groups: A list of groups, where each group contains
      parameters that cannot be provided at the same time.  Only one in the set
      can be provided by the user for each command.
    disable_service_flags: If true, the --service flag cannot be provided.
    singleton_name: If this field is provided, then the integration can only be
      a singleton.  The name is used as an identifier in the resource config.
    required_apis: APIs required for the integration to work.  The user will be
      prompted to enable these APIs if they are not already enabled.
    eta_in_min: estimate deploy time in minutes.
    cta: call to action template.
    label: the display name for the integration.
    product: the GCP product behind the integration.
    example_yaml: Example yaml blocks that will be provided to the user.
    visible: If true, then the integration is useable by anyone without any
      special configuration.
  """

  def __init__(self, integration_type: str, resource_type: str,
               description: str, example_command: str,
               service_type: ServiceType, required_apis: List[str],
               parameters: List[Parameters],
               update_exclusive_groups:
               Optional[List[UpdateExclusiveGroup]] = None,
               disable_service_flags: bool = False,
               singleton_name: Optional[str] = None,
               required_field: Optional[str] = None,
               eta_in_min: Optional[int] = None,
               cta: Optional[str] = None,
               label: Optional[str] = None,
               product: Optional[str] = None,
               example_yaml: Optional[str] = None,
               visible: bool = False):
    self.integration_type = integration_type
    self.resource_type = resource_type
    self.description = description
    self.example_command = example_command
    self.service_type = _ServiceTypeFromStr(service_type)
    self.required_apis = set(required_apis)
    self.parameters = [Parameters(**param) for param in parameters]
    self.disable_service_flags = disable_service_flags
    self.singleton_name = singleton_name
    self.required_field = required_field
    self.eta_in_min = eta_in_min
    self.cta = cta
    self.label = label
    self.product = product
    self.example_yaml = example_yaml
    self.visible = visible

    if update_exclusive_groups is None:
      update_exclusive_groups = []

    self.update_exclusive_groups = [
        UpdateExclusiveGroup(**group) for group in update_exclusive_groups]


def _GetAllTypeMetadata() -> List[TypeMetadata]:
  """Returns metadata for each integration type.

  This loads the metadata from a yaml file at most once and will return the
  same data stored in memory upon future calls.

  Returns:
    array, the type metadata list
  """
  global _TYPE_METADATA
  if _TYPE_METADATA is None:
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, 'metadata.yaml')
    metadata = yaml.load_path(filename)
    _TYPE_METADATA = [
        TypeMetadata(**integ) for integ in metadata['integrations']
    ]

  return _TYPE_METADATA


def IntegrationTypes(client: runapps_v1alpha1_client) -> List[TypeMetadata]:
  """Gets the type definitions for Cloud Run Integrations.

  Currently it's just returning some builtin defnitions because the API is
  not implemented yet.

  Args:
    client: The api client to use.

  Returns:
    array of integration type.
  """
  del client

  return [
      integration for integration in _GetAllTypeMetadata()
      if _IntegrationVisible(integration)
  ]


def GetTypeMetadata(integration_type: str) -> Optional[TypeMetadata]:
  """Returns metadata associated to an integration type.

  Args:
    integration_type: str

  Returns:
    If the integration does not exist or is not visible to the user,
    then None is returned.
  """
  for integration in _GetAllTypeMetadata():
    if (integration.integration_type == integration_type and
        _IntegrationVisible(integration)):
      return integration
  return None


def GetTypeMetadataByResourceType(
    resource_type: str,
) -> Optional[TypeMetadata]:
  """Returns metadata associated to an integration type.

  Args:
    resource_type: the resource type

  Returns:
    If the integration does not exist or is not visible to the user,
    then None is returned.
  """
  for integration in _GetAllTypeMetadata():
    if integration.resource_type == resource_type and _IntegrationVisible(
        integration
    ):
      return integration
  return None


def GetTypeMetadataByResource(
    resource: runapps_v1alpha1_messages.Resource,
) -> Optional[TypeMetadata]:
  """Returns metadata associated to an integration type.

  Args:
    resource: the resource object

  Returns:
    If the integration does not exist or is not visible to the user,
    then None is returned.
  """
  return GetTypeMetadataByResourceType(resource.id.type)


def _IntegrationVisible(integration: TypeMetadata) -> bool:
  """Returns whether or not the integration is visible.

  Args:
    integration: Each entry is defined in _INTEGRATION_TYPES

  Returns:
    True if the integration is set to visible, or if the property
      is set to true.  Otherwise it is False.
  """
  show_experimental_integrations = (
      properties.VALUES.runapps.experimental_integrations.GetBool())
  return integration.visible or show_experimental_integrations


def CheckValidIntegrationType(integration_type: str) -> None:
  """Checks if IntegrationType is supported.

  Args:
    integration_type: integration type to validate.
  Rasies: ArgumentError
  """
  if GetTypeMetadata(integration_type) is None:
    raise exceptions.ArgumentError(
        'Integration of type {} is not supported'.format(integration_type))


def ToCamelCase(name: str) -> str:
  """Turns a kebab case name into camel case.

  Args:
    name: the name string

  Returns:
    the string in camel case

  """
  pascal_case = name.replace('-', ' ').title().replace(' ', '')
  return pascal_case[0].lower() + pascal_case[1:]
