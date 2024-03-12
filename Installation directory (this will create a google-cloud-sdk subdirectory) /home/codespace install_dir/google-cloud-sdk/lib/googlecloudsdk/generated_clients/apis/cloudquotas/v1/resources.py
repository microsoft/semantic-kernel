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


BASE_URL = 'https://cloudquotas.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/docs/quotas'


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
  FOLDERS_LOCATIONS_QUOTAPREFERENCES = (
      'folders.locations.quotaPreferences',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/quotaPreferences/'
              '{quotaPreferencesId}',
      },
      ['name'],
      True
  )
  FOLDERS_LOCATIONS_SERVICES = (
      'folders.locations.services',
      'folders/{foldersId}/locations/{locationsId}/services/{servicesId}',
      {},
      ['foldersId', 'locationsId', 'servicesId'],
      True
  )
  FOLDERS_LOCATIONS_SERVICES_QUOTAINFOS = (
      'folders.locations.services.quotaInfos',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/services/'
              '{servicesId}/quotaInfos/{quotaInfosId}',
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
  ORGANIZATIONS_LOCATIONS_QUOTAPREFERENCES = (
      'organizations.locations.quotaPreferences',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'quotaPreferences/{quotaPreferencesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_SERVICES = (
      'organizations.locations.services',
      'organizations/{organizationsId}/locations/{locationsId}/services/'
      '{servicesId}',
      {},
      ['organizationsId', 'locationsId', 'servicesId'],
      True
  )
  ORGANIZATIONS_LOCATIONS_SERVICES_QUOTAINFOS = (
      'organizations.locations.services.quotaInfos',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'services/{servicesId}/quotaInfos/{quotaInfosId}',
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
      'projects/{projectsId}/locations/{locationsId}',
      {},
      ['projectsId', 'locationsId'],
      True
  )
  PROJECTS_LOCATIONS_QUOTAPREFERENCES = (
      'projects.locations.quotaPreferences',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'quotaPreferences/{quotaPreferencesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_SERVICES = (
      'projects.locations.services',
      'projects/{projectsId}/locations/{locationsId}/services/{servicesId}',
      {},
      ['projectsId', 'locationsId', 'servicesId'],
      True
  )
  PROJECTS_LOCATIONS_SERVICES_QUOTAINFOS = (
      'projects.locations.services.quotaInfos',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/services/'
              '{servicesId}/quotaInfos/{quotaInfosId}',
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
