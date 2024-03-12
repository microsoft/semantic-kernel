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


BASE_URL = 'https://run.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/run/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  API_V1_NAMESPACES = (
      'api.v1.namespaces',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}',
      },
      ['name'],
      True
  )
  API_V1_NAMESPACES_SECRETS = (
      'api.v1.namespaces.secrets',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/secrets/{secretsId}',
      },
      ['name'],
      True
  )
  NAMESPACES_CONFIGURATIONS = (
      'namespaces.configurations',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/configurations/{configurationsId}',
      },
      ['name'],
      True
  )
  NAMESPACES_DOMAINMAPPINGS = (
      'namespaces.domainmappings',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/domainmappings/{domainmappingsId}',
      },
      ['name'],
      True
  )
  NAMESPACES_EXECUTIONS = (
      'namespaces.executions',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/executions/{executionsId}',
      },
      ['name'],
      True
  )
  NAMESPACES_JOBS = (
      'namespaces.jobs',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/jobs/{jobsId}',
      },
      ['name'],
      True
  )
  NAMESPACES_REVISIONS = (
      'namespaces.revisions',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/revisions/{revisionsId}',
      },
      ['name'],
      True
  )
  NAMESPACES_ROUTES = (
      'namespaces.routes',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/routes/{routesId}',
      },
      ['name'],
      True
  )
  NAMESPACES_SERVICES = (
      'namespaces.services',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/services/{servicesId}',
      },
      ['name'],
      True
  )
  NAMESPACES_TASKS = (
      'namespaces.tasks',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/tasks/{tasksId}',
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
  PROJECTS_LOCATIONS_CONFIGURATIONS = (
      'projects.locations.configurations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/configurations/'
              '{configurationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_DOMAINMAPPINGS = (
      'projects.locations.domainmappings',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/domainmappings/'
              '{domainmappingsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_JOBS = (
      'projects.locations.jobs',
      'projects/{projectsId}/locations/{locationsId}/jobs/{jobsId}',
      {},
      ['projectsId', 'locationsId', 'jobsId'],
      True
  )
  PROJECTS_LOCATIONS_NAMESPACES = (
      'projects.locations.namespaces',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/namespaces/'
              '{namespacesId}',
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
  PROJECTS_LOCATIONS_REVISIONS = (
      'projects.locations.revisions',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/revisions/'
              '{revisionsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_ROUTES = (
      'projects.locations.routes',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/routes/'
              '{routesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_SECRETS = (
      'projects.locations.secrets',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/secrets/'
              '{secretsId}',
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

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
