# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Base ResourceBuilder for Cloud Run Integrations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
from typing import Dict, Iterable, List, Optional, Set, TypedDict

from apitools.base.py import encoding
from googlecloudsdk.api_lib.run.integrations import types_utils
from googlecloudsdk.generated_clients.apis.runapps.v1alpha1 import runapps_v1alpha1_messages


class BindingData(object):
  """Binding data that represent a binding.

  Attributes:
    from_id: the resource id the binding is configured from
    to_id: the resource id the binding is pointing to
    config: the binding config if available
  """

  def __init__(
      self,
      from_id: runapps_v1alpha1_messages.ResourceID,
      to_id: runapps_v1alpha1_messages.ResourceID,
      config: Optional[runapps_v1alpha1_messages.Binding.ConfigValue] = None,
  ):
    self.from_id = from_id
    self.to_id = to_id
    self.config = config


class BindingFinder(object):
  """A map of bindings to help processing binding information.

  Attributes:
    bindings: the list of bindings.
  """

  def __init__(
      self,
      all_resources: List[runapps_v1alpha1_messages.Resource],
  ):
    """Returns list of bindings between the given resources.

    Args:
      all_resources: the resources to look for bindings from.

    Returns:
      list of ResourceID of the bindings.
    """
    self.bindings = []
    for res in all_resources:
      bindings = FindBindingsRecursive(res)
      for binding in bindings:
        binding_data = BindingData(
            from_id=res.id, to_id=binding.targetRef.id, config=binding.config
        )
        self.bindings.append(binding_data)

  def GetAllBindings(self) -> List[runapps_v1alpha1_messages.ResourceID]:
    """Returns all the bindings.

    Returns:
      the list of bindings
    """
    return self.bindings

  def GetBinding(
      self, res_id: runapps_v1alpha1_messages.ResourceID
  ) -> List[BindingData]:
    """Returns list of bindings that are associated with the res_id.

    Args:
      res_id: the ID that represents the resource.

    Returns:
      list of binding data
    """
    return [
        b for b in self.bindings if b.from_id == res_id or b.to_id == res_id
    ]

  def GetIDsBindedTo(
      self, res_id: runapps_v1alpha1_messages.ResourceID
  ) -> List[runapps_v1alpha1_messages.ResourceID]:
    """Returns list of resource IDs that are binded to the resource.

    Args:
      res_id: the ID that represents the resource.

    Returns:
      list of resource ID
    """
    return [
        bid.from_id for bid in self.GetBinding(res_id) if bid.to_id == res_id
    ]

  def GetBindingIDs(
      self, res_id: runapps_v1alpha1_messages.ResourceID
  ) -> List[runapps_v1alpha1_messages.ResourceID]:
    """Returns list of resource IDs that are binded to or from the resource.

    Args:
      res_id: the ID that represents the resource.

    Returns:
      list of resource ID
    """
    result = []
    for bid in self.GetBinding(res_id):
      if bid.from_id == res_id:
        result.append(bid.to_id)
      else:
        result.append(bid.from_id)
    return result


def FindBindings(
    resource: runapps_v1alpha1_messages.Resource,
    target_type: Optional[str] = None,
    target_name: Optional[str] = None,
) -> List[runapps_v1alpha1_messages.Binding]:
  """Returns list of bindings that match the target_type and target_name.

  Args:
    resource: the resource to look for bindings from.
    target_type: the type of bindings to match. If empty, will match all types.
    target_name: the name of the bindings to match. If empty, will match all
      names.

  Returns:
    list of ResourceID of the bindings.
  """
  result = []
  for binding in resource.bindings:
    name_match = not target_name or binding.targetRef.id.name == target_name
    type_match = not target_type or binding.targetRef.id.type == target_type
    if name_match and type_match:
      result.append(binding)
  return result


def FindBindingsRecursive(
    resource: runapps_v1alpha1_messages.Resource,
    target_type: Optional[str] = None,
    target_name: Optional[str] = None,
) -> List[runapps_v1alpha1_messages.Binding]:
  """Find bindings from the given resource and its subresource.

  Args:
    resource: the resource to look for bindings from.
    target_type: the type of bindings to match. If empty, will match all types.
    target_name: the name of the bindings to match. If empty, will match all
      names.

  Returns:
    list of ResourceID of the bindings.
  """
  svcs = FindBindings(resource, target_type, target_name)
  if resource.subresources:
    for subresource in resource.subresources:
      svcs.extend(FindBindingsRecursive(subresource, target_type, target_name))
  return svcs


def RemoveBinding(
    to_resource: runapps_v1alpha1_messages.Resource,
    from_resource: runapps_v1alpha1_messages.Resource,
):
  """Remove a binding from a resource that's pointing to another resource.

  Args:
    to_resource: the resource this binding is pointing to.
    from_resource: the resource this binding is configured from.
  """
  from_resource.bindings = [
      x for x in from_resource.bindings if x.targetRef.id != to_resource.id
  ]


class Selector(TypedDict):
  """Selects components by type.

  Attributes:
    type: Component type to select.
    name: Integration name.
  """

  type: str
  name: str


def GetComponentTypesFromSelectors(selectors: Iterable[Selector]) -> Set[str]:
  """Returns a list of component types included in a create/update deployment.

  Args:
    selectors: list of dict of type names (string) that will be deployed.

  Returns:
    set of component types as strings. The component types can also include
    hidden resource types that should be called out as part of the deployment
    progress output.
  """
  return {type_name['type'] for type_name in selectors}


class TypeKit(object):
  """An abstract class that represents a typekit."""

  def __init__(self, type_metadata: types_utils.TypeMetadata):
    self._type_metadata = type_metadata

  @property
  def integration_type(self):
    return self._type_metadata.integration_type

  @property
  def resource_type(self):
    return self._type_metadata.resource_type

  @property
  def is_singleton(self):
    return self._type_metadata.singleton_name is not None

  @property
  def singleton_name(self):
    return self._type_metadata.singleton_name

  @property
  def is_backing_service(self):
    return self._type_metadata.service_type == types_utils.ServiceType.BACKING

  @property
  def is_ingress_service(self):
    return self._type_metadata.service_type == types_utils.ServiceType.INGRESS

  def GetDeployMessage(self, create: bool = False) -> str:
    """Message that is shown to the user upon starting the deployment.

    Each TypeKit should override this method to at least tell the user how
    long the deployment is expected to take.

    Args:
      create: denotes if the command was a create deployment.

    Returns:
      The message displayed to the user.
    """
    del create  # Not use in this default implementation.
    if self._type_metadata.eta_in_min:
      return 'This might take up to {} minutes.'.format(
          self._type_metadata.eta_in_min
      )
    return ''

  def UpdateResourceConfig(
      self,
      parameters: Dict[str, str],
      resource: runapps_v1alpha1_messages.Resource,
  ) -> List[str]:
    """Updates config according to the parameters.

    Each TypeKit should override this method to update the resource config
    specific to the need of the typekit.

    Args:
      parameters: parameters from the command
      resource: the resource object of the integration

    Returns:
      list of service names referred in parameters.
    """
    metadata = self._type_metadata
    config_dict = {}
    if resource.config:
      config_dict = encoding.MessageToDict(resource.config)
    for param in metadata.parameters:
      param_value = parameters.get(param.name)
      if param_value:
        # TODO(b/303113714): Add value validation.
        if param.data_type == 'int':
          config_dict[param.config_name] = int(param_value)
        elif param.data_type == 'number':
          config_dict[param.config_name] = float(param_value)
        else:
          # default is string
          config_dict[param.config_name] = param_value
    resource.config = encoding.DictToMessage(
        config_dict, runapps_v1alpha1_messages.Resource.ConfigValue
    )
    return []

  def _SetBinding(
      self,
      to_resource: runapps_v1alpha1_messages.Resource,
      from_resource: runapps_v1alpha1_messages.Resource,
      parameters: Optional[Dict[str, str]] = None,
  ):
    """Add a binding from a resource to another resource.

    Args:
      to_resource: the resource this binding to be pointing to.
      from_resource: the resource this binding to be configured from.
      parameters: the binding config from parameter
    """
    from_ids = [x.targetRef.id for x in from_resource.bindings]
    if to_resource.id not in from_ids:
      from_resource.bindings.append(
          runapps_v1alpha1_messages.Binding(
              targetRef=runapps_v1alpha1_messages.ResourceRef(id=to_resource.id)
          )
      )
    if parameters:
      for binding in from_resource.bindings:
        if binding.targetRef.id == to_resource.id:
          binding_config = (
              encoding.MessageToDict(binding.config) if binding.config else {}
          )
          for key in parameters:
            binding_config[key] = parameters[key]
          binding.config = encoding.DictToMessage(
              binding_config, runapps_v1alpha1_messages.Binding.ConfigValue
          )

  def BindServiceToIntegration(
      self,
      integration: runapps_v1alpha1_messages.Resource,
      workload: runapps_v1alpha1_messages.Resource,
      parameters: Optional[Dict[str, str]] = None,
  ):
    """Bind a workload to an integration.

    Args:
      integration: the resource of the inetgration.
      workload: the resource the workload.
      parameters: the binding config from parameter.
    """
    if self._type_metadata.service_type == types_utils.ServiceType.INGRESS:
      self._SetBinding(workload, integration, parameters)
    else:
      self._SetBinding(integration, workload, parameters)

  def UnbindServiceFromIntegration(
      self,
      integration: runapps_v1alpha1_messages.Resource,
      workload: runapps_v1alpha1_messages.Resource,
  ):
    """Unbind a workload from an integration.

    Args:
      integration: the resource of the inetgration.
      workload: the resource the workload.
    """
    if self._type_metadata.service_type == types_utils.ServiceType.INGRESS:
      RemoveBinding(workload, integration)
    else:
      RemoveBinding(integration, workload)

  def NewIntegrationName(
      self, appconfig: runapps_v1alpha1_messages.Config
  ) -> str:
    """Returns a name for a new integration.

    Args:
      appconfig: the application config

    Returns:
      str, a new name for the integration.
    """
    name = '{}-{}'.format(self.integration_type, 1)
    existing_names = {
        res.id.name
        for res in appconfig.resourceList
        if (res.id.type == self.resource_type)
    }
    while name in existing_names:
      # If name already taken, tries adding an integer suffix to it.
      # If suffixed name also exists, tries increasing the number until finding
      # an available one.
      count = 1
      match = re.search(r'(.+)-(\d+)$', name)
      if match:
        name = match.group(1)
        count = int(match.group(2)) + 1
      name = '{}-{}'.format(name, count)
    return name

  def GetCreateSelectors(self, integration_name) -> List[Selector]:
    """Returns create selectors for given integration and service.

    Args:
      integration_name: str, name of integration.

    Returns:
      list of dict typed names.
    """

    return [{'type': self.resource_type, 'name': integration_name}]

  def GetDeleteSelectors(self, integration_name) -> List[Selector]:
    """Returns selectors for deleting the integration.

    Args:
      integration_name: str, name of integration.

    Returns:
      list of dict typed names.
    """
    return [{'type': self.resource_type, 'name': integration_name}]

  def GetBindedWorkloads(
      self,
      resource: runapps_v1alpha1_messages.Resource,
      # TODO(b/304638571): change this to app config to be consistent.
      all_resources: List[runapps_v1alpha1_messages.Resource],
      workload_type: str = 'service',
  ) -> List[runapps_v1alpha1_messages.ResourceID]:
    """Returns list of workloads that are associated to this resource.

    If the resource is a backing service, then it returns a list of workloads
    binding to the resource. If the resource is an ingress service, then all
    of the workloads it is binding to.

    Args:
      resource: the resource object of the integration.
      all_resources: all the resources in the application.
      workload_type: type of the workload to search for.

    Returns:
      list ResourceID of the binded workloads.
    """
    if self.is_backing_service:
      filtered_workloads = [
          res for res in all_resources if res.id.type == workload_type
      ]
      return [
          workload.id.name
          for workload in filtered_workloads
          if FindBindings(workload, resource.id.type, resource.id.name)
      ]
    return [
        res_id.targetRef.id.name
        for res_id in FindBindingsRecursive(resource, workload_type)
    ]

  def GetCreateComponentTypes(self, selectors: Iterable[Selector]):
    """Returns a list of component types included in a create/update deployment.

    Args:
      selectors: list of dict of type names (string) that will be deployed.

    Returns:
      set of component types as strings. The component types can also include
      hidden resource types that should be called out as part of the deployment
      progress output.
    """
    return GetComponentTypesFromSelectors(selectors)

  def GetDeleteComponentTypes(self, selectors: Iterable[Selector]):
    """Returns a list of component types included in a delete deployment.

    Args:
      selectors: list of dict of type names (string) that will be deployed.

    Returns:
      set of component types as strings. The component types can also include
      hidden resource types that should be called out as part of the deployment
      progress output.
    """
    return GetComponentTypesFromSelectors(selectors)
