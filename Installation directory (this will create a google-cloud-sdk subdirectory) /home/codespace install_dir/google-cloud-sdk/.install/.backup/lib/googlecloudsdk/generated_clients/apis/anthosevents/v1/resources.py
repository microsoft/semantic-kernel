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


BASE_URL = 'https://anthosevents.googleapis.com/apis/eventing.knative.dev/v1/'
DOCS_URL = ''


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
      'projects/{projectsId}/locations/{locationsId}',
      {},
      ['projectsId', 'locationsId'],
      True
  )
  PROJECTS_LOCATIONS_CONFIGMAPS = (
      'projects.locations.configmaps',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/configmaps/'
              '{configmapsId}',
      },
      ['name'],
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
  PROJECTS_LOCATIONS_SERVICEACCOUNTS = (
      'projects.locations.serviceaccounts',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/serviceaccounts/'
              '{serviceaccountsId}',
      },
      ['name'],
      True
  )
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
  API_V1_NAMESPACES_CONFIGMAPS = (
      'api.v1.namespaces.configmaps',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/configmaps/{configmapsId}',
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
  API_V1_NAMESPACES_SERVICEACCOUNTS = (
      'api.v1.namespaces.serviceaccounts',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/serviceaccounts/{serviceaccountsId}',
      },
      ['name'],
      True
  )
  CUSTOMRESOURCEDEFINITIONS = (
      'customresourcedefinitions',
      '{+name}',
      {
          '':
              'customresourcedefinitions/{customresourcedefinitionsId}',
      },
      ['name'],
      True
  )
  NAMESPACES_BROKERS = (
      'namespaces.brokers',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/brokers/{brokersId}',
      },
      ['name'],
      True
  )
  NAMESPACES_TRIGGERS = (
      'namespaces.triggers',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/triggers/{triggersId}',
      },
      ['name'],
      True
  )
  NAMESPACES_CLOUDAUDITLOGSSOURCES = (
      'namespaces.cloudauditlogssources',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/cloudauditlogssources/'
              '{cloudauditlogssourcesId}',
      },
      ['name'],
      True
  )
  NAMESPACES_CLOUDPUBSUBSOURCES = (
      'namespaces.cloudpubsubsources',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/cloudpubsubsources/'
              '{cloudpubsubsourcesId}',
      },
      ['name'],
      True
  )
  NAMESPACES_CLOUDSCHEDULERSOURCES = (
      'namespaces.cloudschedulersources',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/cloudschedulersources/'
              '{cloudschedulersourcesId}',
      },
      ['name'],
      True
  )
  NAMESPACES_CLOUDSTORAGESOURCES = (
      'namespaces.cloudstoragesources',
      '{+name}',
      {
          '':
              'namespaces/{namespacesId}/cloudstoragesources/'
              '{cloudstoragesourcesId}',
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
