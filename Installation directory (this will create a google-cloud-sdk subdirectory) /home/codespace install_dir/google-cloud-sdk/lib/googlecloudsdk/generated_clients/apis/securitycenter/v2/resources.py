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


BASE_URL = 'https://securitycenter.googleapis.com/v2/'
DOCS_URL = 'https://cloud.google.com/security-command-center'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  FOLDERS = (
      'folders',
      'folders/{foldersId}',
      {},
      ['foldersId'],
      True
  )
  FOLDERS_LOCATIONS = (
      'folders.locations',
      'folders/{foldersId}/locations/{locationsId}',
      {},
      ['foldersId', 'locationsId'],
      True
  )
  FOLDERS_LOCATIONS_BIGQUERYEXPORTS = (
      'folders.locations.bigQueryExports',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/bigQueryExports/'
              '{bigQueryExportsId}',
      },
      ['name'],
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
  FOLDERS_LOCATIONS_NOTIFICATIONCONFIGS = (
      'folders.locations.notificationConfigs',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/'
              'notificationConfigs/{notificationConfigsId}',
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
  ORGANIZATIONS = (
      'organizations',
      'organizations/{organizationsId}',
      {},
      ['organizationsId'],
      True
  )
  ORGANIZATIONS_BIGQUERYEXPORTS = (
      'organizations.bigQueryExports',
      'organizations/{organizationsId}/bigQueryExports/{bigQueryExportId}',
      {},
      ['organizationsId', 'bigQueryExportId'],
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
  ORGANIZATIONS_LOCATIONS_BIGQUERYEXPORTS = (
      'organizations.locations.bigQueryExports',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationId}/'
              'bigQueryExports/{bigQueryExportId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_FINDINGS = (
      'organizations.locations.findings',
      'organizations/{organizationsId}/locations/{locationId}/findings/'
      '{findingId}',
      {},
      ['organizationsId', 'locationId', 'findingId'],
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
  ORGANIZATIONS_LOCATIONS_NOTIFICATIONCONFIGS = (
      'organizations.locations.notificationConfigs',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationId}/'
              'notificationConfigs/{notificationConfigsId}',
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
      'organizations/{organizationsId}/notificationConfigs/'
      '{notificationConfigsId}',
      {},
      ['organizationsId', 'notificationConfigsId'],
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
  ORGANIZATIONS_SOURCES_LOCATIONS_FINDINGS = (
      'organizations.sources.locations.findings',
      'organizations/{organizationsId}/sources/{sourcesId}/locations/'
      '{locationId}/findings/{findingId}',
      {},
      ['organizationsId', 'sourcesId', 'locationId', 'findingId'],
      True
  )
  PROJECTS = (
      'projects',
      'projects/{projectsId}',
      {},
      ['projectsId'],
      True
  )
  PROJECTS_LOCATIONS = (
      'projects.locations',
      'projects/{projectsId}/locations/{locationsId}',
      {},
      ['projectsId', 'locationsId'],
      True
  )
  PROJECTS_LOCATIONS_BIGQUERYEXPORTS = (
      'projects.locations.bigQueryExports',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/bigQueryExports/'
              '{bigQueryExportsId}',
      },
      ['name'],
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
  PROJECTS_LOCATIONS_NOTIFICATIONCONFIGS = (
      'projects.locations.notificationConfigs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'notificationConfigs/{notificationConfigsId}',
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

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
