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
"""Resource definitions for Cloud Platform Apis generated from apitools."""

import enum


BASE_URL = 'https://securitycenter.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/security-command-center'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  FOLDERS_BIGQUERYEXPORTS = (
      'folders.bigQueryExports',
      '{+name}',
      {
          '':
              'folders/{foldersId}/bigQueryExports/{bigQueryExportsId}',
      },
      ['name'],
      True
  )
  FOLDERS_EVENTTHREATDETECTIONSETTINGS_CUSTOMMODULES = (
      'folders.eventThreatDetectionSettings.customModules',
      '{+name}',
      {
          '':
              'folders/{foldersId}/eventThreatDetectionSettings/'
              'customModules/{customModulesId}',
      },
      ['name'],
      True
  )
  FOLDERS_EVENTTHREATDETECTIONSETTINGS_EFFECTIVECUSTOMMODULES = (
      'folders.eventThreatDetectionSettings.effectiveCustomModules',
      '{+name}',
      {
          '':
              'folders/{foldersId}/eventThreatDetectionSettings/'
              'effectiveCustomModules/{effectiveCustomModulesId}',
      },
      ['name'],
      True
  )
  FOLDERS_LOCATIONS = (
      'folders.locations',
      'folders/{foldersId}/locations/{locationsId}',
      {},
      ['foldersId', 'locationsId'],
      True
  )
  FOLDERS_LOCATIONS_MUTECONFIGS = (
      'folders.locations.muteConfigs',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/muteConfigs/'
              '{muteConfigsId}',
      },
      ['name'],
      True
  )
  FOLDERS_MUTECONFIGS = (
      'folders.muteConfigs',
      '{+name}',
      {
          '':
              'folders/{foldersId}/muteConfigs/{muteConfigsId}',
      },
      ['name'],
      True
  )
  FOLDERS_NOTIFICATIONCONFIGS = (
      'folders.notificationConfigs',
      '{+name}',
      {
          '':
              'folders/{foldersId}/notificationConfigs/'
              '{notificationConfigsId}',
      },
      ['name'],
      True
  )
  FOLDERS_SECURITYHEALTHANALYTICSSETTINGS = (
      'folders.securityHealthAnalyticsSettings',
      'folders/{foldersId}',
      {},
      ['foldersId'],
      True
  )
  FOLDERS_SECURITYHEALTHANALYTICSSETTINGS_CUSTOMMODULES = (
      'folders.securityHealthAnalyticsSettings.customModules',
      '{+name}',
      {
          '':
              'folders/{foldersId}/securityHealthAnalyticsSettings/'
              'customModules/{customModulesId}',
      },
      ['name'],
      True
  )
  FOLDERS_SECURITYHEALTHANALYTICSSETTINGS_EFFECTIVECUSTOMMODULES = (
      'folders.securityHealthAnalyticsSettings.effectiveCustomModules',
      '{+name}',
      {
          '':
              'folders/{foldersId}/securityHealthAnalyticsSettings/'
              'effectiveCustomModules/{effectiveCustomModulesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS = (
      'organizations',
      'organizations/{organizationsId}',
      {},
      ['organizationsId'],
      True
  )
  ORGANIZATIONS_ASSETS = (
      'organizations.assets',
      'organizations/{organizationsId}/assets/{assetsId}',
      {},
      ['organizationsId', 'assetsId'],
      True
  )
  ORGANIZATIONS_BIGQUERYEXPORTS = (
      'organizations.bigQueryExports',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/bigQueryExports/'
              '{bigQueryExportId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_EVENTTHREATDETECTIONSETTINGS_CUSTOMMODULES = (
      'organizations.eventThreatDetectionSettings.customModules',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/eventThreatDetectionSettings/'
              'customModules/{customModulesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_EVENTTHREATDETECTIONSETTINGS_EFFECTIVECUSTOMMODULES = (
      'organizations.eventThreatDetectionSettings.effectiveCustomModules',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/eventThreatDetectionSettings/'
              'effectiveCustomModules/{effectiveCustomModulesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_FINDINGS = (
      'organizations.findings',
      'organizations/{organizationsId}/findings/{findingId}',
      {},
      ['organizationsId', 'findingId'],
      True
  )
  ORGANIZATIONS_LOCATIONS = (
      'organizations.locations',
      'organizations/{organizationsId}/locations/{locationsId}',
      {},
      ['organizationsId', 'locationsId'],
      True
  )
  ORGANIZATIONS_LOCATIONS_MUTECONFIGS = (
      'organizations.locations.muteConfigs',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'muteConfigs/{muteConfigsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_MUTECONFIGS = (
      'organizations.muteConfigs',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/muteConfigs/{muteConfigsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_NOTIFICATIONCONFIGS = (
      'organizations.notificationConfigs',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/notificationConfigs/'
              '{notificationConfigsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_OPERATIONS = (
      'organizations.operations',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/operations/{operationsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_RESOURCEVALUECONFIGS = (
      'organizations.resourceValueConfigs',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/resourceValueConfigs/'
              '{resourceValueConfigsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_SECURITYHEALTHANALYTICSSETTINGS_CUSTOMMODULES = (
      'organizations.securityHealthAnalyticsSettings.customModules',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/'
              'securityHealthAnalyticsSettings/customModules/'
              '{customModulesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_SECURITYHEALTHANALYTICSSETTINGS_EFFECTIVECUSTOMMODULES = (
      'organizations.securityHealthAnalyticsSettings.effectiveCustomModules',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/'
              'securityHealthAnalyticsSettings/effectiveCustomModules/'
              '{effectiveCustomModulesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_SIMULATIONS = (
      'organizations.simulations',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/simulations/{simulationsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_SIMULATIONS_VALUEDRESOURCES = (
      'organizations.simulations.valuedResources',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/simulations/{simulationsId}/'
              'valuedResources/{valuedResourcesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_SOURCES = (
      'organizations.sources',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/sources/{sourcesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_SOURCES_FINDINGS = (
      'organizations.sources.findings',
      'organizations/{organizationsId}/sources/{sourcesId}/findings/'
      '{findingId}',
      {},
      ['organizationsId', 'sourcesId', 'findingId'],
      True
  )
  PROJECTS_BIGQUERYEXPORTS = (
      'projects.bigQueryExports',
      '{+name}',
      {
          '':
              'projects/{projectsId}/bigQueryExports/{bigQueryExportsId}',
      },
      ['name'],
      True
  )
  PROJECTS_EVENTTHREATDETECTIONSETTINGS_CUSTOMMODULES = (
      'projects.eventThreatDetectionSettings.customModules',
      '{+name}',
      {
          '':
              'projects/{projectsId}/eventThreatDetectionSettings/'
              'customModules/{customModulesId}',
      },
      ['name'],
      True
  )
  PROJECTS_EVENTTHREATDETECTIONSETTINGS_EFFECTIVECUSTOMMODULES = (
      'projects.eventThreatDetectionSettings.effectiveCustomModules',
      '{+name}',
      {
          '':
              'projects/{projectsId}/eventThreatDetectionSettings/'
              'effectiveCustomModules/{effectiveCustomModulesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS = (
      'projects.locations',
      'projects/{projectsId}/locations/{locationsId}',
      {},
      ['projectsId', 'locationsId'],
      True
  )
  PROJECTS_LOCATIONS_MUTECONFIGS = (
      'projects.locations.muteConfigs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/muteConfigs/'
              '{muteConfigsId}',
      },
      ['name'],
      True
  )
  PROJECTS_MUTECONFIGS = (
      'projects.muteConfigs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/muteConfigs/{muteConfigsId}',
      },
      ['name'],
      True
  )
  PROJECTS_NOTIFICATIONCONFIGS = (
      'projects.notificationConfigs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/notificationConfigs/'
              '{notificationConfigsId}',
      },
      ['name'],
      True
  )
  PROJECTS_SECURITYHEALTHANALYTICSSETTINGS = (
      'projects.securityHealthAnalyticsSettings',
      'projects/{projectsId}',
      {},
      ['projectsId'],
      True
  )
  PROJECTS_SECURITYHEALTHANALYTICSSETTINGS_CUSTOMMODULES = (
      'projects.securityHealthAnalyticsSettings.customModules',
      '{+name}',
      {
          '':
              'projects/{projectsId}/securityHealthAnalyticsSettings/'
              'customModules/{customModulesId}',
      },
      ['name'],
      True
  )
  PROJECTS_SECURITYHEALTHANALYTICSSETTINGS_EFFECTIVECUSTOMMODULES = (
      'projects.securityHealthAnalyticsSettings.effectiveCustomModules',
      '{+name}',
      {
          '':
              'projects/{projectsId}/securityHealthAnalyticsSettings/'
              'effectiveCustomModules/{effectiveCustomModulesId}',
      },
      ['name'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
