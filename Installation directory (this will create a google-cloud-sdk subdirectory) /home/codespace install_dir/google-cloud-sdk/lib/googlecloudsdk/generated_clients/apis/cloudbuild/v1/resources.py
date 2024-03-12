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


BASE_URL = 'https://cloudbuild.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/cloud-build/docs/'


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
  PROJECTS_BUILDS = (
      'projects.builds',
      'projects/{projectId}/builds/{id}',
      {},
      ['projectId', 'id'],
      True
  )
  PROJECTS_GITHUBENTERPRISECONFIGS = (
      'projects.githubEnterpriseConfigs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/githubEnterpriseConfigs/'
              '{githubEnterpriseConfigsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS = (
      'projects.locations',
      'projects/{projectsId}/locations/{locationsId}',
      {},
      ['projectsId', 'locationsId'],
      True
  )
  PROJECTS_LOCATIONS_BITBUCKETSERVERCONFIGS = (
      'projects.locations.bitbucketServerConfigs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'bitbucketServerConfigs/{bitbucketServerConfigsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_BUILDS = (
      'projects.locations.builds',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/builds/'
              '{buildsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_GITLABCONFIGS = (
      'projects.locations.gitLabConfigs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/gitLabConfigs/'
              '{gitLabConfigsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_GITHUBENTERPRISECONFIGS = (
      'projects.locations.githubEnterpriseConfigs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'githubEnterpriseConfigs/{githubEnterpriseConfigsId}',
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
  PROJECTS_LOCATIONS_TRIGGERS = (
      'projects.locations.triggers',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/triggers/'
              '{triggersId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_WORKERPOOLS = (
      'projects.locations.workerPools',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/workerPools/'
              '{workerPoolsId}',
      },
      ['name'],
      True
  )
  PROJECTS_TRIGGERS = (
      'projects.triggers',
      'projects/{projectId}/triggers/{triggerId}',
      {},
      ['projectId', 'triggerId'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
