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


BASE_URL = 'https://apigeeregistry.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/apigee/docs/api-hub/what-is-api-hub'


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
  PROJECTS_LOCATIONS_APIS = (
      'projects.locations.apis',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/apis/{apisId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_APIS_ARTIFACTS = (
      'projects.locations.apis.artifacts',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/apis/{apisId}/'
              'artifacts/{artifactsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_APIS_DEPLOYMENTS = (
      'projects.locations.apis.deployments',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/apis/{apisId}/'
              'deployments/{deploymentsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_APIS_DEPLOYMENTS_ARTIFACTS = (
      'projects.locations.apis.deployments.artifacts',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/apis/{apisId}/'
              'deployments/{deploymentsId}/artifacts/{artifactsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_APIS_VERSIONS = (
      'projects.locations.apis.versions',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/apis/{apisId}/'
              'versions/{versionsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_APIS_VERSIONS_ARTIFACTS = (
      'projects.locations.apis.versions.artifacts',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/apis/{apisId}/'
              'versions/{versionsId}/artifacts/{artifactsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_APIS_VERSIONS_SPECS = (
      'projects.locations.apis.versions.specs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/apis/{apisId}/'
              'versions/{versionsId}/specs/{specsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_APIS_VERSIONS_SPECS_ARTIFACTS = (
      'projects.locations.apis.versions.specs.artifacts',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/apis/{apisId}/'
              'versions/{versionsId}/specs/{specsId}/artifacts/{artifactsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_ARTIFACTS = (
      'projects.locations.artifacts',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/artifacts/'
              '{artifactsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_INSTANCES = (
      'projects.locations.instances',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/instances/'
              '{instancesId}',
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
