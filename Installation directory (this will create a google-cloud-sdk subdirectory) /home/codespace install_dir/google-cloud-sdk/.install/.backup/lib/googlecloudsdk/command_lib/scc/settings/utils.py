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
"""A library that used to interact with CTD-IA backend services."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py import exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import exceptions as gcloud_exceptions
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.scc.settings import exceptions as scc_exceptions
from googlecloudsdk.core import properties

API_NAME = 'securitycenter'
DEFAULT_API_VERSION = 'v1beta2'

SERVICES_ENDPOINTS = {
    'container-threat-detection': 'containerThreatDetectionSettings',
    'event-threat-detection': 'eventThreatDetectionSettings',
    'security-health-analytics': 'securityHealthAnalyticsSettings',
    'rapid-vulnerability-detection': 'rapidVulnerabilityDetectionSettings',
    'virtual-machine-threat-detection': 'virtualMachineThreatDetectionSettings',
    'web-security-scanner': 'webSecurityScannerSettings',
}

SERVICE_STATUS_MASK = 'service_enablement_state'
MODULE_STATUS_MASK = 'modules'


def GetMessages(version=DEFAULT_API_VERSION):
  """Import and return the securitycenter settings message_module module.

  Args:
    version: the API version

  Returns:
    securitycenter settings message module.
  """
  return apis.GetMessagesModule(API_NAME, version)


def GetClient(version=DEFAULT_API_VERSION):
  """Import and return the securitycenter settings client module.

  Args:
    version: the API version

  Returns:
    securitycenter settings API client module.
  """
  return apis.GetClientInstance(API_NAME, version)


def GenerateParent(args):
  if args.organization:
    return 'organizations/{}/'.format(args.organization)
  elif args.project:
    return 'projects/{}/'.format(args.project)
  elif args.folder:
    return 'folders/{}/'.format(args.folder)


def FallBackFlags(args):
  if (not args.organization and not args.folder and not args.project):
    args.organization = properties.VALUES.scc.organization.Get()
    if not args.organization:
      args.project = properties.VALUES.core.project.Get()
  if (not args.organization and not args.folder and not args.project):
    raise calliope_exceptions.MinimumArgumentException(
        ['--organization', '--folder', '--project'])


class SettingsClient(object):
  """Client for securitycenter settings service."""

  def __init__(self, api_version=DEFAULT_API_VERSION):
    self.message_module = GetMessages(api_version)
    self.service_client = GetClient(api_version)

  def DescribeExplicit(self, args):
    """Describe settings of organization."""

    path = GenerateParent(args) + 'securityCenterSettings'

    try:
      request_message = self.message_module.SecuritycenterOrganizationsGetSecurityCenterSettingsRequest(
          name=path)
      return self.service_client.organizations.GetSecurityCenterSettings(
          request_message)
    except exceptions.HttpNotFoundError:
      raise scc_exceptions.SecurityCenterSettingsException(
          'Invalid argument {}'.format(path))

  def DescribeServiceExplicit(self, args):
    """Describe effective service settings of organization/folder/project."""

    FallBackFlags(args)
    path = GenerateParent(args) + SERVICES_ENDPOINTS[args.service]

    try:
      if args.organization:
        if args.service == 'web-security-scanner':
          request_message = self.message_module.SecuritycenterOrganizationsGetWebSecurityScannerSettingsRequest(
              name=path)
          return self.service_client.organizations.GetWebSecurityScannerSettings(
              request_message)
        elif args.service == 'security-health-analytics':
          request_message = self.message_module.SecuritycenterOrganizationsGetSecurityHealthAnalyticsSettingsRequest(
              name=path)
          return self.service_client.organizations.GetSecurityHealthAnalyticsSettings(
              request_message)
        elif args.service == 'container-threat-detection':
          request_message = self.message_module.SecuritycenterOrganizationsGetContainerThreatDetectionSettingsRequest(
              name=path)
          return self.service_client.organizations.GetContainerThreatDetectionSettings(
              request_message)
        elif args.service == 'event-threat-detection':
          request_message = self.message_module.SecuritycenterOrganizationsGetEventThreatDetectionSettingsRequest(
              name=path)
          return self.service_client.organizations.GetEventThreatDetectionSettings(
              request_message)
        elif args.service == 'virtual-machine-threat-detection':
          request_message = self.message_module.SecuritycenterOrganizationsGetVirtualMachineThreatDetectionSettingsRequest(
              name=path)
          return self.service_client.organizations.GetVirtualMachineThreatDetectionSettings(
              request_message)
        elif args.service == 'rapid-vulnerability-detection':
          request_message = self.message_module.SecuritycenterOrganizationsGetRapidVulnerabilityDetectionSettingsRequest(
              name=path)
          return self.service_client.organizations.GetRapidVulnerabilityDetectionSettings(
              request_message)
      elif args.project:
        if args.service == 'web-security-scanner':
          request_message = self.message_module.SecuritycenterProjectsGetWebSecurityScannerSettingsRequest(
              name=path)
          return self.service_client.projects.GetWebSecurityScannerSettings(
              request_message)
        elif args.service == 'security-health-analytics':
          request_message = self.message_module.SecuritycenterProjectsGetSecurityHealthAnalyticsSettingsRequest(
              name=path)
          return self.service_client.projects.GetSecurityHealthAnalyticsSettings(
              request_message)
        elif args.service == 'container-threat-detection':
          request_message = self.message_module.SecuritycenterProjectsGetContainerThreatDetectionSettingsRequest(
              name=path)
          return self.service_client.projects.GetContainerThreatDetectionSettings(
              request_message)
        elif args.service == 'event-threat-detection':
          request_message = self.message_module.SecuritycenterProjectsGetEventThreatDetectionSettingsRequest(
              name=path)
          return self.service_client.projects.GetEventThreatDetectionSettings(
              request_message)
        elif args.service == 'virtual-machine-threat-detection':
          request_message = self.message_module.SecuritycenterProjectsGetVirtualMachineThreatDetectionSettingsRequest(
              name=path)
          return self.service_client.projects.GetVirtualMachineThreatDetectionSettings(
              request_message)
        elif args.service == 'rapid-vulnerability-detection':
          request_message = self.message_module.SecuritycenterProjectsGetRapidVulnerabilityDetectionSettingsRequest(
              name=path)
          return self.service_client.projects.GetRapidVulnerabilityDetectionSettings(
              request_message)
      elif args.folder:
        if args.service == 'web-security-scanner':
          request_message = self.message_module.SecuritycenterFoldersGetWebSecurityScannerSettingsRequest(
              name=path)
          return self.service_client.folders.GetWebSecurityScannerSettings(
              request_message)
        elif args.service == 'security-health-analytics':
          request_message = self.message_module.SecuritycenterFoldersGetSecurityHealthAnalyticsSettingsRequest(
              name=path)
          return self.service_client.folders.GetSecurityHealthAnalyticsSettings(
              request_message)
        elif args.service == 'container-threat-detection':
          request_message = self.message_module.SecuritycenterFoldersGetContainerThreatDetectionSettingsRequest(
              name=path)
          return self.service_client.folders.GetContainerThreatDetectionSettings(
              request_message)
        elif args.service == 'event-threat-detection':
          request_message = self.message_module.SecuritycenterFoldersGetEventThreatDetectionSettingsRequest(
              name=path)
          return self.service_client.folders.GetEventThreatDetectionSettings(
              request_message)
        elif args.service == 'virtual-machine-threat-detection':
          request_message = self.message_module.SecuritycenterFoldersGetVirtualMachineThreatDetectionSettingsRequest(
              name=path)
          return self.service_client.folders.GetVirtualMachineThreatDetectionSettings(
              request_message)
        elif args.service == 'rapid-vulnerability-detection':
          request_message = self.message_module.SecuritycenterFoldersGetRapidVulnerabilityDetectionSettingsRequest(
              name=path)
          return self.service_client.folders.GetRapidVulnerabilityDetectionSettings(
              request_message)
    except exceptions.HttpError as err:
      gcloud_exceptions.core_exceptions.reraise(
          gcloud_exceptions.HttpException(
              err, error_format='Status code [{status_code}]. {message}.'))

  def DescribeService(self, args):
    """Describe service settings of organization/folder/project."""

    FallBackFlags(args)
    path = GenerateParent(args) + SERVICES_ENDPOINTS[args.service]

    try:
      if args.organization:
        if args.service == 'web-security-scanner':
          request_message = self.message_module.SecuritycenterOrganizationsWebSecurityScannerSettingsCalculateRequest(
              name=path)
          return self.service_client.organizations_webSecurityScannerSettings.Calculate(
              request_message)
        elif args.service == 'security-health-analytics':
          request_message = self.message_module.SecuritycenterOrganizationsSecurityHealthAnalyticsSettingsCalculateRequest(
              name=path)
          return self.service_client.organizations_securityHealthAnalyticsSettings.Calculate(
              request_message)
        elif args.service == 'container-threat-detection':
          request_message = self.message_module.SecuritycenterOrganizationsContainerThreatDetectionSettingsCalculateRequest(
              name=path)
          return self.service_client.organizations_containerThreatDetectionSettings.Calculate(
              request_message)
        elif args.service == 'event-threat-detection':
          request_message = self.message_module.SecuritycenterOrganizationsEventThreatDetectionSettingsCalculateRequest(
              name=path)
          return self.service_client.organizations_eventThreatDetectionSettings.Calculate(
              request_message)
        elif args.service == 'virtual-machine-threat-detection':
          request_message = self.message_module.SecuritycenterOrganizationsVirtualMachineThreatDetectionSettingsCalculateRequest(
              name=path)
          return self.service_client.organizations_virtualMachineThreatDetectionSettings.Calculate(
              request_message)
        elif args.service == 'rapid-vulnerability-detection':
          request_message = self.message_module.SecuritycenterOrganizationsRapidVulnerabilityDetectionSettingsCalculateRequest(
              name=path)
          return self.service_client.organizations_rapidVulnerabilityDetectionSettings.Calculate(
              request_message)
      elif args.project:
        if args.service == 'web-security-scanner':
          request_message = self.message_module.SecuritycenterProjectsWebSecurityScannerSettingsCalculateRequest(
              name=path)
          return self.service_client.projects_webSecurityScannerSettings.Calculate(
              request_message)
        elif args.service == 'security-health-analytics':
          request_message = self.message_module.SecuritycenterProjectsSecurityHealthAnalyticsSettingsCalculateRequest(
              name=path)
          return self.service_client.projects_securityHealthAnalyticsSettings.Calculate(
              request_message)
        elif args.service == 'container-threat-detection':
          request_message = self.message_module.SecuritycenterProjectsContainerThreatDetectionSettingsCalculateRequest(
              name=path)
          return self.service_client.projects_containerThreatDetectionSettings.Calculate(
              request_message)
        elif args.service == 'event-threat-detection':
          request_message = self.message_module.SecuritycenterProjectsEventThreatDetectionSettingsCalculateRequest(
              name=path)
          return self.service_client.projects_eventThreatDetectionSettings.Calculate(
              request_message)
        elif args.service == 'virtual-machine-threat-detection':
          request_message = self.message_module.SecuritycenterProjectsVirtualMachineThreatDetectionSettingsCalculateRequest(
              name=path)
          return self.service_client.projects_virtualMachineThreatDetectionSettings.Calculate(
              request_message)
        elif args.service == 'rapid-vulnerability-detection':
          request_message = self.message_module.SecuritycenterProjectsRapidVulnerabilityDetectionSettingsCalculateRequest(
              name=path)
          return self.service_client.projects_rapidVulnerabilityDetectionSettings.Calculate(
              request_message)
      elif args.folder:
        if args.service == 'web-security-scanner':
          request_message = self.message_module.SecuritycenterFoldersWebSecurityScannerSettingsCalculateRequest(
              name=path)
          return self.service_client.folders_webSecurityScannerSettings.Calculate(
              request_message)
        elif args.service == 'security-health-analytics':
          request_message = self.message_module.SecuritycenterFoldersSecurityHealthAnalyticsSettingsCalculateRequest(
              name=path)
          return self.service_client.folders_securityHealthAnalyticsSettings.Calculate(
              request_message)
        elif args.service == 'container-threat-detection':
          request_message = self.message_module.SecuritycenterFoldersContainerThreatDetectionSettingsCalculateRequest(
              name=path)
          return self.service_client.folders_containerThreatDetectionSettings.Calculate(
              request_message)
        elif args.service == 'event-threat-detection':
          request_message = self.message_module.SecuritycenterFoldersEventThreatDetectionSettingsCalculateRequest(
              name=path)
          return self.service_client.folders_eventThreatDetectionSettings.Calculate(
              request_message)
        elif args.service == 'virtual-machine-threat-detection':
          request_message = self.message_module.SecuritycenterFoldersVirtualMachineThreatDetectionSettingsCalculateRequest(
              name=path)
          return self.service_client.folders_virtualMachineThreatDetectionSettings.Calculate(
              request_message)
        elif args.service == 'rapid-vulnerability-detection':
          request_message = self.message_module.SecuritycenterFoldersRapidVulnerabilityDetectionSettingsCalculateRequest(
              name=path)
          return self.service_client.folders_rapidVulnerabilityDetectionSettings.Calculate(
              request_message)
    except exceptions.HttpNotFoundError:
      raise scc_exceptions.SecurityCenterSettingsException(
          'Invalid argument {}'.format(path))

  def EnableService(self, args):
    """Enable service of organization/folder/project."""
    if args.service == 'web-security-scanner':
      web_security_center_settings = self.message_module.WebSecurityScannerSettings(
          serviceEnablementState=self.message_module.WebSecurityScannerSettings
          .ServiceEnablementStateValueValuesEnum.ENABLED)
      return self._UpdateService(args, web_security_center_settings,
                                 SERVICE_STATUS_MASK)
    elif args.service == 'security-health-analytics':
      security_health_analytics_settings = self.message_module.SecurityHealthAnalyticsSettings(
          serviceEnablementState=self.message_module
          .SecurityHealthAnalyticsSettings.ServiceEnablementStateValueValuesEnum
          .ENABLED)
      return self._UpdateService(args, security_health_analytics_settings,
                                 SERVICE_STATUS_MASK)
    elif args.service == 'container-threat-detection':
      container_threat_detection_settings = self.message_module.ContainerThreatDetectionSettings(
          serviceEnablementState=self.message_module
          .ContainerThreatDetectionSettings
          .ServiceEnablementStateValueValuesEnum.ENABLED)
      return self._UpdateService(args, container_threat_detection_settings,
                                 SERVICE_STATUS_MASK)
    elif args.service == 'event-threat-detection':
      event_threat_detection_settings = self.message_module.EventThreatDetectionSettings(
          serviceEnablementState=self.message_module
          .EventThreatDetectionSettings.ServiceEnablementStateValueValuesEnum
          .ENABLED)
      return self._UpdateService(args, event_threat_detection_settings,
                                 SERVICE_STATUS_MASK)
    elif args.service == 'virtual-machine-threat-detection':
      virtual_machine_threat_detection_settings = self.message_module.VirtualMachineThreatDetectionSettings(
          serviceEnablementState=self.message_module
          .VirtualMachineThreatDetectionSettings
          .ServiceEnablementStateValueValuesEnum.ENABLED)
      return self._UpdateService(args,
                                 virtual_machine_threat_detection_settings,
                                 SERVICE_STATUS_MASK)
    elif args.service == 'rapid-vulnerability-detection':
      rapid_vulnerability_detection_settings = self.message_module.RapidVulnerabilityDetectionSettings(
          serviceEnablementState=self.message_module
          .RapidVulnerabilityDetectionSettings
          .ServiceEnablementStateValueValuesEnum.ENABLED)
      return self._UpdateService(args, rapid_vulnerability_detection_settings,
                                 SERVICE_STATUS_MASK)

  def DisableService(self, args):
    """Disable service of organization/folder/project."""
    if args.service == 'web-security-scanner':
      web_security_center_settings = self.message_module.WebSecurityScannerSettings(
          serviceEnablementState=self.message_module.WebSecurityScannerSettings
          .ServiceEnablementStateValueValuesEnum.DISABLED)
      return self._UpdateService(args, web_security_center_settings,
                                 SERVICE_STATUS_MASK)
    elif args.service == 'security-health-analytics':
      security_health_analytics_settings = self.message_module.SecurityHealthAnalyticsSettings(
          serviceEnablementState=self.message_module
          .SecurityHealthAnalyticsSettings.ServiceEnablementStateValueValuesEnum
          .DISABLED)
      return self._UpdateService(args, security_health_analytics_settings,
                                 SERVICE_STATUS_MASK)
    elif args.service == 'container-threat-detection':
      container_threat_detection_settings = self.message_module.ContainerThreatDetectionSettings(
          serviceEnablementState=self.message_module
          .ContainerThreatDetectionSettings
          .ServiceEnablementStateValueValuesEnum.DISABLED)
      return self._UpdateService(args, container_threat_detection_settings,
                                 SERVICE_STATUS_MASK)
    elif args.service == 'event-threat-detection':
      event_threat_detection_settings = self.message_module.EventThreatDetectionSettings(
          serviceEnablementState=self.message_module
          .EventThreatDetectionSettings.ServiceEnablementStateValueValuesEnum
          .DISABLED)
      return self._UpdateService(args, event_threat_detection_settings,
                                 SERVICE_STATUS_MASK)
    elif args.service == 'virtual-machine-threat-detection':
      virtual_machine_threat_detection_settings = self.message_module.VirtualMachineThreatDetectionSettings(
          serviceEnablementState=self.message_module
          .VirtualMachineThreatDetectionSettings
          .ServiceEnablementStateValueValuesEnum.DISABLED)
      return self._UpdateService(args,
                                 virtual_machine_threat_detection_settings,
                                 SERVICE_STATUS_MASK)
    elif args.service == 'rapid-vulnerability-detection':
      rapid_vulnerability_detection_settings = self.message_module.RapidVulnerabilityDetectionSettings(
          serviceEnablementState=self.message_module
          .RapidVulnerabilityDetectionSettings
          .ServiceEnablementStateValueValuesEnum.DISABLED)
      return self._UpdateService(args, rapid_vulnerability_detection_settings,
                                 SERVICE_STATUS_MASK)

  def InheritService(self, args):
    """Set service enablement state of folder/project to "inherited"."""
    if args.service == 'web-security-scanner':
      web_security_center_settings = self.message_module.WebSecurityScannerSettings(
          serviceEnablementState=self.message_module.WebSecurityScannerSettings
          .ServiceEnablementStateValueValuesEnum.INHERITED)
      return self._UpdateService(args, web_security_center_settings,
                                 SERVICE_STATUS_MASK)
    elif args.service == 'security-health-analytics':
      security_health_analytics_settings = self.message_module.SecurityHealthAnalyticsSettings(
          serviceEnablementState=self.message_module
          .SecurityHealthAnalyticsSettings.ServiceEnablementStateValueValuesEnum
          .INHERITED)
      return self._UpdateService(args, security_health_analytics_settings,
                                 SERVICE_STATUS_MASK)
    elif args.service == 'container-threat-detection':
      container_threat_detection_settings = self.message_module.ContainerThreatDetectionSettings(
          serviceEnablementState=self.message_module
          .ContainerThreatDetectionSettings
          .ServiceEnablementStateValueValuesEnum.INHERITED)
      return self._UpdateService(args, container_threat_detection_settings,
                                 SERVICE_STATUS_MASK)
    elif args.service == 'event-threat-detection':
      event_threat_detection_settings = self.message_module.EventThreatDetectionSettings(
          serviceEnablementState=self.message_module
          .EventThreatDetectionSettings.ServiceEnablementStateValueValuesEnum
          .INHERITED)
      return self._UpdateService(args, event_threat_detection_settings,
                                 SERVICE_STATUS_MASK)
    elif args.service == 'virtual-machine-threat-detection':
      virtual_machine_threat_detection_settings = self.message_module.VirtualMachineThreatDetectionSettings(
          serviceEnablementState=self.message_module
          .VirtualMachineThreatDetectionSettings
          .ServiceEnablementStateValueValuesEnum.INHERITED)
      return self._UpdateService(args,
                                 virtual_machine_threat_detection_settings,
                                 SERVICE_STATUS_MASK)
    elif args.service == 'rapid-vulnerability-detection':
      rapid_vulnerability_detection_settings = self.message_module.RapidVulnerabilityDetectionSettings(
          serviceEnablementState=self.message_module
          .RapidVulnerabilityDetectionSettings
          .ServiceEnablementStateValueValuesEnum.INHERITED)
      return self._UpdateService(args, rapid_vulnerability_detection_settings,
                                 SERVICE_STATUS_MASK)

  def _UpdateService(self, args, service_settings, update_mask):
    """Update service settings of organization/folder/project."""

    FallBackFlags(args)
    path = GenerateParent(args) + SERVICES_ENDPOINTS[args.service]

    if args.service == 'web-security-scanner':
      if args.organization:
        request_message = self.message_module.SecuritycenterOrganizationsUpdateWebSecurityScannerSettingsRequest(
            name=path,
            updateMask=update_mask,
            webSecurityScannerSettings=service_settings)
        return self.service_client.organizations.UpdateWebSecurityScannerSettings(
            request_message)
      elif args.folder:
        request_message = self.message_module.SecuritycenterFoldersUpdateWebSecurityScannerSettingsRequest(
            name=path,
            updateMask=update_mask,
            webSecurityScannerSettings=service_settings)
        return self.service_client.folders.UpdateWebSecurityScannerSettings(
            request_message)
      elif args.project:
        request_message = self.message_module.SecuritycenterProjectsUpdateWebSecurityScannerSettingsRequest(
            name=path,
            updateMask=update_mask,
            webSecurityScannerSettings=service_settings)
        return self.service_client.projects.UpdateWebSecurityScannerSettings(
            request_message)
    elif args.service == 'security-health-analytics':
      if args.organization:
        request_message = self.message_module.SecuritycenterOrganizationsUpdateSecurityHealthAnalyticsSettingsRequest(
            name=path,
            updateMask=update_mask,
            securityHealthAnalyticsSettings=service_settings)
        return self.service_client.organizations.UpdateSecurityHealthAnalyticsSettings(
            request_message)
      elif args.folder:
        request_message = self.message_module.SecuritycenterFoldersUpdateSecurityHealthAnalyticsSettingsRequest(
            name=path,
            updateMask=update_mask,
            securityHealthAnalyticsSettings=service_settings)
        return self.service_client.folders.UpdateSecurityHealthAnalyticsSettings(
            request_message)
      elif args.project:
        request_message = self.message_module.SecuritycenterProjectsUpdateSecurityHealthAnalyticsSettingsRequest(
            name=path,
            updateMask=update_mask,
            securityHealthAnalyticsSettings=service_settings)
        return self.service_client.projects.UpdateSecurityHealthAnalyticsSettings(
            request_message)
    elif args.service == 'container-threat-detection':
      if args.organization:
        request_message = self.message_module.SecuritycenterOrganizationsUpdateContainerThreatDetectionSettingsRequest(
            name=path,
            updateMask=update_mask,
            containerThreatDetectionSettings=service_settings)
        return self.service_client.organizations.UpdateContainerThreatDetectionSettings(
            request_message)
      if args.folder:
        request_message = self.message_module.SecuritycenterFoldersUpdateContainerThreatDetectionSettingsRequest(
            name=path,
            updateMask=update_mask,
            containerThreatDetectionSettings=service_settings)
        return self.service_client.folders.UpdateContainerThreatDetectionSettings(
            request_message)
      if args.project:
        request_message = self.message_module.SecuritycenterProjectsUpdateContainerThreatDetectionSettingsRequest(
            name=path,
            updateMask=update_mask,
            containerThreatDetectionSettings=service_settings)
        return self.service_client.projects.UpdateContainerThreatDetectionSettings(
            request_message)
    elif args.service == 'event-threat-detection':
      if args.organization:
        request_message = self.message_module.SecuritycenterOrganizationsUpdateEventThreatDetectionSettingsRequest(
            name=path,
            updateMask=update_mask,
            eventThreatDetectionSettings=service_settings)
        return self.service_client.organizations.UpdateEventThreatDetectionSettings(
            request_message)
      elif args.folder:
        request_message = self.message_module.SecuritycenterFoldersUpdateEventThreatDetectionSettingsRequest(
            name=path,
            updateMask=update_mask,
            eventThreatDetectionSettings=service_settings)
        return self.service_client.folders.UpdateEventThreatDetectionSettings(
            request_message)
      elif args.project:
        request_message = self.message_module.SecuritycenterProjectsUpdateEventThreatDetectionSettingsRequest(
            name=path,
            updateMask=update_mask,
            eventThreatDetectionSettings=service_settings)
        return self.service_client.projects.UpdateEventThreatDetectionSettings(
            request_message)
    elif args.service == 'virtual-machine-threat-detection':
      if args.organization:
        request_message = self.message_module.SecuritycenterOrganizationsUpdateVirtualMachineThreatDetectionSettingsRequest(
            name=path,
            updateMask=update_mask,
            virtualMachineThreatDetectionSettings=service_settings)
        return self.service_client.organizations.UpdateVirtualMachineThreatDetectionSettings(
            request_message)
      if args.folder:
        request_message = self.message_module.SecuritycenterFoldersUpdateVirtualMachineThreatDetectionSettingsRequest(
            name=path,
            updateMask=update_mask,
            virtualMachineThreatDetectionSettings=service_settings)
        return self.service_client.folders.UpdateVirtualMachineThreatDetectionSettings(
            request_message)
      if args.project:
        request_message = self.message_module.SecuritycenterProjectsUpdateVirtualMachineThreatDetectionSettingsRequest(
            name=path,
            updateMask=update_mask,
            virtualMachineThreatDetectionSettings=service_settings)
        return self.service_client.projects.UpdateVirtualMachineThreatDetectionSettings(
            request_message)
    elif args.service == 'rapid-vulnerability-detection':
      if args.organization:
        request_message = self.message_module.SecuritycenterOrganizationsUpdateRapidVulnerabilityDetectionSettingsRequest(
            name=path,
            updateMask=update_mask,
            rapidVulnerabilityDetectionSettings=service_settings)
        return self.service_client.organizations.UpdateRapidVulnerabilityDetectionSettings(
            request_message)
      if args.folder:
        request_message = self.message_module.SecuritycenterFoldersUpdateRapidVulnerabilityDetectionSettingsRequest(
            name=path,
            updateMask=update_mask,
            rapidVulnerabilityDetectionSettings=service_settings)
        return self.service_client.folders.UpdateRapidVulnerabilityDetectionSettings(
            request_message)
      if args.project:
        request_message = self.message_module.SecuritycenterProjectsUpdateRapidVulnerabilityDetectionSettingsRequest(
            name=path,
            updateMask=update_mask,
            rapidVulnerabilityDetectionSettings=service_settings)
        return self.service_client.projects.UpdateRapidVulnerabilityDetectionSettings(
            request_message)

  def EnableModule(self, args):
    """Enable a module for a service of organization/folder/project."""
    return self._UpdateModules(args, True)

  def DisableModule(self, args):
    """Disable a module for a service of organization/folder/project."""
    return self._UpdateModules(args, False)

  def UpdateModuleConfig(self, args):
    """Update a config within a module."""
    if args.clear_config or args.config is None:
      config = None
    else:
      try:
        config = encoding.JsonToMessage(self.message_module.Config.ValueValue,
                                        args.config)
      except Exception:
        raise scc_exceptions.SecurityCenterSettingsException(
            'Invalid argument {}. Check help text for an example json.'.format(
                args.config))
    enabled = args.enablement_state == 'enabled'
    return self._UpdateModules(args, enabled, args.clear_config, config)

  def _UpdateModules(self, args, enabled, clear_config=False, config=None):
    """Update modules within service settings."""
    # TODO(b/264680929): Python 3.10 typing.TypeAlias
    StateEnum = self.message_module.Config.ModuleEnablementStateValueValuesEnum  # pylint: disable=invalid-name
    state = StateEnum.ENABLED if enabled else StateEnum.DISABLED
    curr_modules = None

    try:
      curr_modules = self.DescribeServiceExplicit(args).modules
    except gcloud_exceptions.HttpException as err:
      if err.payload.status_code == 404:
        curr_modules = None
        config = None
      else:
        raise err
    if not clear_config and config is None and curr_modules is not None:
      module = [
          p for p in curr_modules.additionalProperties if p.key == args.module
      ]
      if len(module) == 1:
        config = module[0].value.value
    if args.service == 'web-security-scanner':
      settings = self.message_module.WebSecurityScannerSettings(
          modules=self.message_module.WebSecurityScannerSettings.ModulesValue(
              additionalProperties=[
                  self.message_module.WebSecurityScannerSettings.ModulesValue
                  .AdditionalProperty(
                      key=args.module,
                      value=self.message_module.Config(
                          moduleEnablementState=state, value=config))
              ]))
    elif args.service == 'security-health-analytics':
      settings = self.message_module.SecurityHealthAnalyticsSettings(
          modules=self.message_module.SecurityHealthAnalyticsSettings
          .ModulesValue(additionalProperties=[
              self.message_module.SecurityHealthAnalyticsSettings.ModulesValue
              .AdditionalProperty(
                  key=args.module,
                  value=self.message_module.Config(
                      moduleEnablementState=state, value=config))
          ]))
    elif args.service == 'container-threat-detection':
      settings = self.message_module.ContainerThreatDetectionSettings(
          modules=self.message_module.ContainerThreatDetectionSettings
          .ModulesValue(additionalProperties=[
              self.message_module.ContainerThreatDetectionSettings.ModulesValue
              .AdditionalProperty(
                  key=args.module,
                  value=self.message_module.Config(
                      moduleEnablementState=state, value=config))
          ]))
    elif args.service == 'event-threat-detection':
      settings = self.message_module.EventThreatDetectionSettings(
          modules=self.message_module.EventThreatDetectionSettings.ModulesValue(
              additionalProperties=[
                  self.message_module.EventThreatDetectionSettings.ModulesValue
                  .AdditionalProperty(
                      key=args.module,
                      value=self.message_module.Config(
                          moduleEnablementState=state, value=config))
              ]))
    elif args.service == 'virtual-machine-threat-detection':
      settings = self.message_module.VirtualMachineThreatDetectionSettings(
          modules=self.message_module.VirtualMachineThreatDetectionSettings
          .ModulesValue(additionalProperties=[
              self.message_module.VirtualMachineThreatDetectionSettings
              .ModulesValue.AdditionalProperty(
                  key=args.module,
                  value=self.message_module.Config(
                      moduleEnablementState=state, value=config))
          ]))
    elif args.service == 'rapid-vulnerability-detection':
      settings = self.message_module.RapidVulnerabilityDetectionSettings(
          modules=self.message_module.RapidVulnerabilityDetectionSettings
          .ModulesValue(additionalProperties=[
              self.message_module.RapidVulnerabilityDetectionSettings
              .ModulesValue.AdditionalProperty(
                  key=args.module,
                  value=self.message_module.Config(
                      moduleEnablementState=state, value=config))
          ]))
    if curr_modules is not None:
      unmodified_additional_properties = [
          p for p in curr_modules.additionalProperties if p.key != args.module
      ]
      settings.modules.additionalProperties = (
          settings.modules.additionalProperties +
          unmodified_additional_properties)

    return self._UpdateService(args, settings, MODULE_STATUS_MASK)
