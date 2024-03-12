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


class SHACustomModuleClient(object):
  """Client for SHA custom module interaction with the Security Center Management API."""

  def __init__(self):
    # Although this client looks specific to projects, this is a codegen
    # artifact. It can be used for any parent types.
    self._client = apis.GetClientInstance(
        'securitycentermanagement', 'v1'
    ).projects_locations_securityHealthAnalyticsCustomModules

  def Get(self, name: str) -> messages.SecurityHealthAnalyticsCustomModule:
    """Get a SHA custom module."""

    req = messages.SecuritycentermanagementProjectsLocationsSecurityHealthAnalyticsCustomModulesGetRequest(
        name=name
    )
    return self._client.Get(req)

  def Simulate(
      self, parent, custom_config, resource
  ) -> messages.SimulateSecurityHealthAnalyticsCustomModuleResponse:
    """Simulate a SHA custom module."""

    sim_req = messages.SimulateSecurityHealthAnalyticsCustomModuleRequest(
        customConfig=custom_config, resource=resource
    )
    req = messages.SecuritycentermanagementProjectsLocationsSecurityHealthAnalyticsCustomModulesSimulateRequest(
        parent=parent,
        simulateSecurityHealthAnalyticsCustomModuleRequest=sim_req,
    )
    return self._client.Simulate(req)

  def Update(
      self,
      name: str,
      validate_only: bool,
      custom_config: messages.CustomConfig,
      enablement_state: messages.SecurityHealthAnalyticsCustomModule.EnablementStateValueValuesEnum,
      update_mask: str,
  ) -> messages.SecurityHealthAnalyticsCustomModule:
    """Update a SHA custom module."""

    security_health_analytics_custom_module = (
        messages.SecurityHealthAnalyticsCustomModule(
            customConfig=custom_config,
            enablementState=enablement_state,
            name=name,
        )
    )

    req = messages.SecuritycentermanagementProjectsLocationsSecurityHealthAnalyticsCustomModulesPatchRequest(
        securityHealthAnalyticsCustomModule=security_health_analytics_custom_module,
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
      custom_config: messages.CustomConfig,
      enablement_state: messages.SecurityHealthAnalyticsCustomModule.EnablementStateValueValuesEnum,
      display_name: str,
  ) -> messages.SecurityHealthAnalyticsCustomModule:
    """Create an SHA custom module."""

    security_health_analytics_custom_module = (
        messages.SecurityHealthAnalyticsCustomModule(
            customConfig=custom_config,
            enablementState=enablement_state,
            displayName=display_name,
        )
    )

    req = messages.SecuritycentermanagementProjectsLocationsSecurityHealthAnalyticsCustomModulesCreateRequest(
        securityHealthAnalyticsCustomModule=security_health_analytics_custom_module,
        parent=parent,
        validateOnly=validate_only,
    )
    response = self._client.Create(req)
    if validate_only:
      log.status.Print('Request is valid.')
      return response
    log.CreatedResource(display_name)
    return response

  def Delete(self, name: str, validate_only: bool):
    """Delete a SHA custom module."""

    req = messages.SecuritycentermanagementProjectsLocationsSecurityHealthAnalyticsCustomModulesDeleteRequest(
        name=name, validateOnly=validate_only
    )
    response = self._client.Delete(req)
    if validate_only:
      log.status.Print('Request is valid.')
      return response
    log.DeletedResource(name)
    return response

  def List(
      self, page_size: int, parent: str, limit: int
  ) -> Generator[
      messages.SecurityHealthAnalyticsCustomModule,
      None,
      messages.ListSecurityHealthAnalyticsCustomModulesResponse,
  ]:
    """List the details of a SHA custom module."""

    req = messages.SecuritycentermanagementProjectsLocationsSecurityHealthAnalyticsCustomModulesListRequest(
        pageSize=page_size, parent=parent
    )
    return list_pager.YieldFromList(
        self._client,
        request=req,
        limit=limit,
        field='securityHealthAnalyticsCustomModules',
        batch_size=page_size,
        batch_size_attribute='pageSize',
    )

  def ListDescendant(
      self, page_size: int, parent: str, limit: int
  ) -> Generator[
      messages.SecurityHealthAnalyticsCustomModule,
      None,
      messages.ListDescendantSecurityHealthAnalyticsCustomModulesResponse,
  ]:
    """List the details of the resident and descendant SHA custom modules."""

    req = messages.SecuritycentermanagementProjectsLocationsSecurityHealthAnalyticsCustomModulesListDescendantRequest(
        pageSize=page_size, parent=parent
    )
    return list_pager.YieldFromList(
        self._client,
        method='ListDescendant',
        request=req,
        limit=limit,
        field='securityHealthAnalyticsCustomModules',
        batch_size=page_size,
        batch_size_attribute='pageSize',
    )


class EffectiveSHACustomModuleClient(object):
  """Client for SHA effective custom module interaction with the Security Center Management API."""

  def __init__(self):
    self._client = apis.GetClientInstance(
        'securitycentermanagement', 'v1'
    ).projects_locations_effectiveSecurityHealthAnalyticsCustomModules

  def Get(self,
          name: str) -> messages.EffectiveSecurityHealthAnalyticsCustomModule:
    """Get a SHA effective custom module."""

    req = messages.SecuritycentermanagementProjectsLocationsEffectiveSecurityHealthAnalyticsCustomModulesGetRequest(
        name=name
    )
    return self._client.Get(req)

  def List(
      self, page_size: int, parent: str, limit: int
  ) -> Generator[
      messages.EffectiveSecurityHealthAnalyticsCustomModule,
      None,
      messages.ListEffectiveSecurityHealthAnalyticsCustomModulesResponse,
  ]:
    """List the details of the resident and descendant SHA effective custom modules."""

    req = messages.SecuritycentermanagementProjectsLocationsEffectiveSecurityHealthAnalyticsCustomModulesListRequest(
        pageSize=page_size, parent=parent
    )
    return list_pager.YieldFromList(
        self._client,
        request=req,
        limit=limit,
        field='effectiveSecurityHealthAnalyticsCustomModules',
        batch_size=page_size,
        batch_size_attribute='pageSize',
    )
