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


BASE_URL = 'https://privilegedaccessmanager.googleapis.com/v1alpha/'
DOCS_URL = 'https://cloud.google.com/'


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
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}',
      },
      ['name'],
      True
  )
  FOLDERS_LOCATIONS_ENTITLEMENTS = (
      'folders.locations.entitlements',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/entitlements/'
              '{entitlementsId}',
      },
      ['name'],
      True
  )
  FOLDERS_LOCATIONS_ENTITLEMENTS_GRANTS = (
      'folders.locations.entitlements.grants',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/entitlements/'
              '{entitlementsId}/grants/{grantsId}',
      },
      ['name'],
      True
  )
  FOLDERS_LOCATIONS_OPERATIONS = (
      'folders.locations.operations',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/operations/'
              '{operationsId}',
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
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_ENTITLEMENTS = (
      'organizations.locations.entitlements',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'entitlements/{entitlementsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_ENTITLEMENTS_GRANTS = (
      'organizations.locations.entitlements.grants',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'entitlements/{entitlementsId}/grants/{grantsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_OPERATIONS = (
      'organizations.locations.operations',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'operations/{operationsId}',
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
  PROJECTS_LOCATIONS_ENTITLEMENTS = (
      'projects.locations.entitlements',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/entitlements/'
              '{entitlementsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_ENTITLEMENTS_GRANTS = (
      'projects.locations.entitlements.grants',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/entitlements/'
              '{entitlementsId}/grants/{grantsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_OPERATIONS = (
      'projects.locations.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/operations/'
              '{operationsId}',
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
