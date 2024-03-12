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


BASE_URL = 'https://metastore.googleapis.com/v1alpha/'
DOCS_URL = 'https://cloud.google.com/dataproc-metastore/docs'


class Collections(enum.Enum):
  """Collections for all supported apis."""

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
  PROJECTS_LOCATIONS_FEDERATIONS = (
      'projects.locations.federations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/federations/'
              '{federationsId}',
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
  PROJECTS_LOCATIONS_SERVICES = (
      'projects.locations.services',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/services/'
              '{servicesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_SERVICES_BACKUPS = (
      'projects.locations.services.backups',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/services/'
              '{servicesId}/backups/{backupsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_SERVICES_DATABASES = (
      'projects.locations.services.databases',
      'projects/{projectsId}/locations/{locationsId}/services/{servicesId}/'
      'databases/{databasesId}',
      {},
      ['projectsId', 'locationsId', 'servicesId', 'databasesId'],
      True
  )
  PROJECTS_LOCATIONS_SERVICES_DATABASES_TABLES = (
      'projects.locations.services.databases.tables',
      'projects/{projectsId}/locations/{locationsId}/services/{servicesId}/'
      'databases/{databasesId}/tables/{tablesId}',
      {},
      ['projectsId', 'locationsId', 'servicesId', 'databasesId', 'tablesId'],
      True
  )
  PROJECTS_LOCATIONS_SERVICES_METADATAIMPORTS = (
      'projects.locations.services.metadataImports',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/services/'
              '{servicesId}/metadataImports/{metadataImportsId}',
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
