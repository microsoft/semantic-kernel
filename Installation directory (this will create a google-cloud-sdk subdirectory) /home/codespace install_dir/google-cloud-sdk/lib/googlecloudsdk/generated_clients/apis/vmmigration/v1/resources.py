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


BASE_URL = 'https://vmmigration.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/migrate/virtual-machines'


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
  PROJECTS_LOCATIONS_GROUPS = (
      'projects.locations.groups',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/groups/'
              '{groupsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_IMAGEIMPORTS = (
      'projects.locations.imageImports',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/imageImports/'
              '{imageImportsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_IMAGEIMPORTS_IMAGEIMPORTJOBS = (
      'projects.locations.imageImports.imageImportJobs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/imageImports/'
              '{imageImportsId}/imageImportJobs/{imageImportJobsId}',
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
  PROJECTS_LOCATIONS_SOURCES = (
      'projects.locations.sources',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/sources/'
              '{sourcesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_SOURCES_DATACENTERCONNECTORS = (
      'projects.locations.sources.datacenterConnectors',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/sources/'
              '{sourcesId}/datacenterConnectors/{datacenterConnectorsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_SOURCES_MIGRATINGVMS = (
      'projects.locations.sources.migratingVms',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/sources/'
              '{sourcesId}/migratingVms/{migratingVmsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_SOURCES_MIGRATINGVMS_CLONEJOBS = (
      'projects.locations.sources.migratingVms.cloneJobs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/sources/'
              '{sourcesId}/migratingVms/{migratingVmsId}/cloneJobs/'
              '{cloneJobsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_SOURCES_MIGRATINGVMS_CUTOVERJOBS = (
      'projects.locations.sources.migratingVms.cutoverJobs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/sources/'
              '{sourcesId}/migratingVms/{migratingVmsId}/cutoverJobs/'
              '{cutoverJobsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_SOURCES_MIGRATINGVMS_REPLICATIONCYCLES = (
      'projects.locations.sources.migratingVms.replicationCycles',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/sources/'
              '{sourcesId}/migratingVms/{migratingVmsId}/replicationCycles/'
              '{replicationCyclesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_SOURCES_UTILIZATIONREPORTS = (
      'projects.locations.sources.utilizationReports',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/sources/'
              '{sourcesId}/utilizationReports/{utilizationReportsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_TARGETPROJECTS = (
      'projects.locations.targetProjects',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/targetProjects/'
              '{targetProjectsId}',
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
