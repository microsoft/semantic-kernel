# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Useful commands for interacting with the Cloud SCC API."""

from typing import Generator
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.scc import util as scc_util
from googlecloudsdk.core import log
from googlecloudsdk.generated_clients.apis.securitycentermanagement.v1 import securitycentermanagement_v1_messages as messages


class ETDCustomModuleClient(object):
  """Client for ETD custom module interaction with the Security Center Management API."""

  def __init__(self):
    # Although this client looks specific to projects, this is a codegen
    # artifact. It can be used for any parent types.
    self._client = apis.GetClientInstance(
        'securitycentermanagement', 'v1'
    ).projects_locations_eventThreatDetectionCustomModules

  def Get(self, name: str) -> messages.EventThreatDetectionCustomModule:
    """Get a ETD custom module."""

    req = messages.SecuritycentermanagementProjectsLocationsEventThreatDetectionCustomModulesGetRequest(
        name=name
    )
    return self._client.Get(req)

  def Validate(
      self, parent: str, custom_config_json: str, module_type: str
  ) -> messages.ValidateEventThreatDetectionCustomModuleResponse:
    """Validate a ETD module."""

    validate_request = messages.ValidateEventThreatDetectionCustomModuleRequest(
        rawText=custom_config_json,
        type=module_type,
    )

    req = messages.SecuritycentermanagementProjectsLocationsEventThreatDetectionCustomModulesValidateRequest(
        parent=parent,
        validateEventThreatDetectionCustomModuleRequest=validate_request,
    )

    response = self._client.Validate(req)
    if not response.errors:
      log.status.Print('Module is valid.')
      return None
    else:
      log.status.Print(response)
      return response

  def Delete(self, name: str, validate_only: bool):
    """Delete a ETD custom module."""

    req = messages.SecuritycentermanagementProjectsLocationsEventThreatDetectionCustomModulesDeleteRequest(
        name=name, validateOnly=validate_only
    )
    response = self._client.Delete(req)
    if validate_only:
      log.status.Print('Request is valid.')
      return response
    log.DeletedResource(name)
    return response

  def Update(
      self,
      name: str,
      validate_only: bool,
      custom_config,
      enablement_state,
      update_mask: str,
  ) -> messages.EventThreatDetectionCustomModule:
    """Update an ETD custom module."""

    event_threat_detection_custom_module = (
        messages.EventThreatDetectionCustomModule(
            config=custom_config,
            enablementState=enablement_state,
            name=name,
        )
    )

    req = messages.SecuritycentermanagementProjectsLocationsEventThreatDetectionCustomModulesPatchRequest(
        eventThreatDetectionCustomModule=event_threat_detection_custom_module,
        name=name,
        updateMask=scc_util.CleanUpUserMaskInput(update_mask),
        validateOnly=validate_only,
    )
    response = self._client.Patch(req)
    if validate_only:
      log.status.Print('Request is valid.')
      return response
    log.UpdatedResource(name)
    return response

  def Create(
      self,
      parent: str,
      validate_only: bool,
      custom_config: messages.EventThreatDetectionCustomModule.ConfigValue,
      enablement_state: messages.EventThreatDetectionCustomModule.EnablementStateValueValuesEnum,
      module_type: str,
      display_name: str,
  ) -> messages.EventThreatDetectionCustomModule:
    """Create an ETD custom module."""

    event_threat_detection_custom_module = (
        messages.EventThreatDetectionCustomModule(
            config=custom_config,
            enablementState=enablement_state,
            displayName=display_name,
            type=module_type,
        )
    )

    req = messages.SecuritycentermanagementProjectsLocationsEventThreatDetectionCustomModulesCreateRequest(
        eventThreatDetectionCustomModule=event_threat_detection_custom_module,
        parent=parent,
        validateOnly=validate_only,
    )

    response = self._client.Create(req)
    if validate_only:
      log.status.Print('Request is valid.')
      return response
    log.CreatedResource(display_name)
    return response

  def List(
      self, page_size: int, parent: str, limit: int
  ) -> Generator[
      messages.EventThreatDetectionCustomModule,
      None,
      messages.ListEventThreatDetectionCustomModulesResponse,
  ]:
    """List details of resident and inherited Event Threat Detection Custom Modules."""

    req = messages.SecuritycentermanagementProjectsLocationsEventThreatDetectionCustomModulesListRequest(
        pageSize=page_size, parent=parent
    )
    return list_pager.YieldFromList(
        self._client,
        request=req,
        limit=limit,
        field='eventThreatDetectionCustomModules',
        batch_size=page_size,
        batch_size_attribute='pageSize',
    )

  def ListDescendant(
      self, page_size: int, parent: str, limit: int
  ) -> Generator[
      messages.EventThreatDetectionCustomModule,
      None,
      messages.ListEventThreatDetectionCustomModulesResponse,
  ]:
    """List the details of the resident and descendant ETD custom modules."""

    req = messages.SecuritycentermanagementProjectsLocationsEventThreatDetectionCustomModulesListDescendantRequest(
        pageSize=page_size, parent=parent
    )
    return list_pager.YieldFromList(
        self._client,
        method='ListDescendant',
        request=req,
        limit=limit,
        field='eventThreatDetectionCustomModules',
        batch_size=page_size,
        batch_size_attribute='pageSize',
    )


class EffectiveETDCustomModuleClient(object):
  """Client for effective ETD custom module interaction with the Security Center Management API."""

  def __init__(self):
    self._client = apis.GetClientInstance(
        'securitycentermanagement', 'v1'
    ).projects_locations_effectiveEventThreatDetectionCustomModules

  def Get(
      self, name: str) -> messages.EffectiveEventThreatDetectionCustomModule:
    """Get a ETD effective custom module."""

    req = messages.SecuritycentermanagementProjectsLocationsEffectiveEventThreatDetectionCustomModulesGetRequest(
        name=name
    )
    return self._client.Get(req)

  def List(
      self, page_size: int, parent: str, limit: int
  ) -> Generator[
      messages.EffectiveEventThreatDetectionCustomModule,
      None,
      messages.ListEffectiveEventThreatDetectionCustomModulesResponse,
  ]:
    """List the details of the resident and descendant ETD effective custom modules."""

    req = messages.SecuritycentermanagementProjectsLocationsEffectiveEventThreatDetectionCustomModulesListRequest(
        pageSize=page_size, parent=parent
    )
    return list_pager.YieldFromList(
        self._client,
        request=req,
        limit=limit,
        field='effectiveEventThreatDetectionCustomModules',
        batch_size=page_size,
        batch_size_attribute='pageSize',
    )
