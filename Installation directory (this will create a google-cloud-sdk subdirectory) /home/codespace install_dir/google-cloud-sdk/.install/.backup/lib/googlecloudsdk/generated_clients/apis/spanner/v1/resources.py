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


BASE_URL = 'https://spanner.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/spanner/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  PROJECTS = (
      'projects',
      'projects/{projectsId}',
      {},
      ['projectsId'],
      True
  )
  PROJECTS_INSTANCECONFIGS = (
      'projects.instanceConfigs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/instanceConfigs/{instanceConfigsId}',
      },
      ['name'],
      True
  )
  PROJECTS_INSTANCECONFIGS_OPERATIONS = (
      'projects.instanceConfigs.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/instanceConfigs/{instanceConfigsId}/'
              'operations/{operationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_INSTANCECONFIGS_SSDCACHES = (
      'projects.instanceConfigs.ssdCaches',
      '{+name}',
      {
          '':
              'projects/{projectsId}/instanceConfigs/{instanceConfigsId}/'
              'ssdCaches/{ssdCachesId}',
      },
      ['name'],
      True
  )
  PROJECTS_INSTANCECONFIGS_SSDCACHES_OPERATIONS = (
      'projects.instanceConfigs.ssdCaches.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/instanceConfigs/{instanceConfigsId}/'
              'ssdCaches/{ssdCachesId}/operations/{operationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_INSTANCES = (
      'projects.instances',
      '{+name}',
      {
          '':
              'projects/{projectsId}/instances/{instancesId}',
      },
      ['name'],
      True
  )
  PROJECTS_INSTANCES_BACKUPS = (
      'projects.instances.backups',
      '{+name}',
      {
          '':
              'projects/{projectsId}/instances/{instancesId}/backups/'
              '{backupsId}',
      },
      ['name'],
      True
  )
  PROJECTS_INSTANCES_BACKUPS_OPERATIONS = (
      'projects.instances.backups.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/instances/{instancesId}/backups/'
              '{backupsId}/operations/{operationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_INSTANCES_DATABASES = (
      'projects.instances.databases',
      '{+name}',
      {
          '':
              'projects/{projectsId}/instances/{instancesId}/databases/'
              '{databasesId}',
      },
      ['name'],
      True
  )
  PROJECTS_INSTANCES_DATABASES_OPERATIONS = (
      'projects.instances.databases.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/instances/{instancesId}/databases/'
              '{databasesId}/operations/{operationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_INSTANCES_DATABASES_ROLES = (
      'projects.instances.databases.roles',
      'projects/{projectsId}/instances/{instancesId}/databases/{databasesId}/'
      'databaseRoles/{rolesName}',
      {},
      ['projectsId', 'instancesId', 'databasesId', 'rolesName'],
      True
  )
  PROJECTS_INSTANCES_DATABASES_SESSIONS = (
      'projects.instances.databases.sessions',
      '{+name}',
      {
          '':
              'projects/{projectsId}/instances/{instancesId}/databases/'
              '{databasesId}/sessions/{sessionsId}',
      },
      ['name'],
      True
  )
  PROJECTS_INSTANCES_INSTANCEPARTITIONS = (
      'projects.instances.instancePartitions',
      '{+name}',
      {
          '':
              'projects/{projectsId}/instances/{instancesId}/'
              'instancePartitions/{instancePartitionsId}',
      },
      ['name'],
      True
  )
  PROJECTS_INSTANCES_INSTANCEPARTITIONS_OPERATIONS = (
      'projects.instances.instancePartitions.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/instances/{instancesId}/'
              'instancePartitions/{instancePartitionsId}/operations/'
              '{operationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_INSTANCES_OPERATIONS = (
      'projects.instances.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/instances/{instancesId}/operations/'
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
