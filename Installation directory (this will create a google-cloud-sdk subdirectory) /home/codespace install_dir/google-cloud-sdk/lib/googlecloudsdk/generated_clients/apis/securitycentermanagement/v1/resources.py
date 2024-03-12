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


BASE_URL = 'https://securitycentermanagement.googleapis.com/v1/'
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
  FOLDERS_LOCATIONS_EFFECTIVEEVENTTHREATDETECTIONCUSTOMMODULES = (
      'folders.locations.effectiveEventThreatDetectionCustomModules',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/'
              'effectiveEventThreatDetectionCustomModules/'
              '{effectiveEventThreatDetectionCustomModulesId}',
      },
      ['name'],
      True
  )
  FOLDERS_LOCATIONS_EFFECTIVESECURITYHEALTHANALYTICSCUSTOMMODULES = (
      'folders.locations.effectiveSecurityHealthAnalyticsCustomModules',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/'
              'effectiveSecurityHealthAnalyticsCustomModules/'
              '{effectiveSecurityHealthAnalyticsCustomModulesId}',
      },
      ['name'],
      True
  )
  FOLDERS_LOCATIONS_EVENTTHREATDETECTIONCUSTOMMODULES = (
      'folders.locations.eventThreatDetectionCustomModules',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/'
              'eventThreatDetectionCustomModules/'
              '{eventThreatDetectionCustomModulesId}',
      },
      ['name'],
      True
  )
  FOLDERS_LOCATIONS_SECURITYHEALTHANALYTICSCUSTOMMODULES = (
      'folders.locations.securityHealthAnalyticsCustomModules',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/'
              'securityHealthAnalyticsCustomModules/'
              '{securityHealthAnalyticsCustomModulesId}',
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
  ORGANIZATIONS_LOCATIONS = (
      'organizations.locations',
      'organizations/{organizationsId}/locations/{locationsId}',
      {},
      ['organizationsId', 'locationsId'],
      True
  )
  ORGANIZATIONS_LOCATIONS_EFFECTIVEEVENTTHREATDETECTIONCUSTOMMODULES = (
      'organizations.locations.effectiveEventThreatDetectionCustomModules',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'effectiveEventThreatDetectionCustomModules/'
              '{effectiveEventThreatDetectionCustomModulesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_EFFECTIVESECURITYHEALTHANALYTICSCUSTOMMODULES = (
      'organizations.locations.effectiveSecurityHealthAnalyticsCustomModules',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'effectiveSecurityHealthAnalyticsCustomModules/'
              '{effectiveSecurityHealthAnalyticsCustomModulesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_EVENTTHREATDETECTIONCUSTOMMODULES = (
      'organizations.locations.eventThreatDetectionCustomModules',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'eventThreatDetectionCustomModules/'
              '{eventThreatDetectionCustomModulesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_SECURITYHEALTHANALYTICSCUSTOMMODULES = (
      'organizations.locations.securityHealthAnalyticsCustomModules',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'securityHealthAnalyticsCustomModules/'
              '{securityHealthAnalyticsCustomModulesId}',
      },
      ['name'],
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
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_EFFECTIVEEVENTTHREATDETECTIONCUSTOMMODULES = (
      'projects.locations.effectiveEventThreatDetectionCustomModules',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'effectiveEventThreatDetectionCustomModules/'
              '{effectiveEventThreatDetectionCustomModulesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_EFFECTIVESECURITYHEALTHANALYTICSCUSTOMMODULES = (
      'projects.locations.effectiveSecurityHealthAnalyticsCustomModules',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'effectiveSecurityHealthAnalyticsCustomModules/'
              '{effectiveSecurityHealthAnalyticsCustomModulesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_EVENTTHREATDETECTIONCUSTOMMODULES = (
      'projects.locations.eventThreatDetectionCustomModules',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'eventThreatDetectionCustomModules/'
              '{eventThreatDetectionCustomModulesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_SECURITYHEALTHANALYTICSCUSTOMMODULES = (
      'projects.locations.securityHealthAnalyticsCustomModules',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'securityHealthAnalyticsCustomModules/'
              '{securityHealthAnalyticsCustomModulesId}',
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
