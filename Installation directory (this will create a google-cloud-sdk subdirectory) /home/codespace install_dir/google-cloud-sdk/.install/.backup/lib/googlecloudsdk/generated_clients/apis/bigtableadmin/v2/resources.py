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


BASE_URL = 'https://bigtableadmin.googleapis.com/v2/'
DOCS_URL = 'https://cloud.google.com/bigtable/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  OPERATIONS = (
      'operations',
      '{+name}',
      {
          '':
              'operations/{operationsId}',
      },
      ['name'],
      True
  )
  PROJECTS = (
      'projects',
      'projects/{projectId}',
      {},
      ['projectId'],
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
  PROJECTS_INSTANCES_APPPROFILES = (
      'projects.instances.appProfiles',
      '{+name}',
      {
          '':
              'projects/{projectsId}/instances/{instancesId}/appProfiles/'
              '{appProfilesId}',
      },
      ['name'],
      True
  )
  PROJECTS_INSTANCES_CLUSTERS = (
      'projects.instances.clusters',
      '{+name}',
      {
          '':
              'projects/{projectsId}/instances/{instancesId}/clusters/'
              '{clustersId}',
      },
      ['name'],
      True
  )
  PROJECTS_INSTANCES_CLUSTERS_BACKUPS = (
      'projects.instances.clusters.backups',
      '{+name}',
      {
          '':
              'projects/{projectsId}/instances/{instancesId}/clusters/'
              '{clustersId}/backups/{backupsId}',
      },
      ['name'],
      True
  )
  PROJECTS_INSTANCES_TABLES = (
      'projects.instances.tables',
      '{+name}',
      {
          '':
              'projects/{projectsId}/instances/{instancesId}/tables/'
              '{tablesId}',
      },
      ['name'],
      True
  )
  PROJECTS_INSTANCES_TABLES_AUTHORIZEDVIEWS = (
      'projects.instances.tables.authorizedViews',
      '{+name}',
      {
          '':
              'projects/{projectsId}/instances/{instancesId}/tables/'
              '{tablesId}/authorizedViews/{authorizedViewsId}',
      },
      ['name'],
      True
  )
  PROJECTS_INSTANCES_TABLES_VIEWS = (
      'projects.instances.tables.views',
      '{+name}',
      {
          '':
              'projects/{projectsId}/instances/{instancesId}/tables/'
              '{tablesId}/views/{viewsId}',
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
