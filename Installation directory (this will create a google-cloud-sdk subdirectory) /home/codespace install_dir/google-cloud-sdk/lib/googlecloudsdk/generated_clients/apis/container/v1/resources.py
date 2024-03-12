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


BASE_URL = 'https://container.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/container-engine/'


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
  PROJECTS_LOCATIONS_CLUSTERS = (
      'projects.locations.clusters',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/clusters/'
              '{clustersId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_CLUSTERS_NODEPOOLS = (
      'projects.locations.clusters.nodePools',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/clusters/'
              '{clustersId}/nodePools/{nodePoolsId}',
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
  PROJECTS_ZONES = (
      'projects.zones',
      'projects/{projectId}/zones/{zoneId}',
      {},
      ['projectId', 'zoneId'],
      True
  )
  PROJECTS_ZONES_CLUSTERS = (
      'projects.zones.clusters',
      'projects/{projectId}/zones/{zone}/clusters/{clusterId}',
      {},
      ['projectId', 'zone', 'clusterId'],
      True
  )
  PROJECTS_ZONES_CLUSTERS_NODEPOOLS = (
      'projects.zones.clusters.nodePools',
      'projects/{projectId}/zones/{zone}/clusters/{clusterId}/nodePools/'
      '{nodePoolId}',
      {},
      ['projectId', 'zone', 'clusterId', 'nodePoolId'],
      True
  )
  PROJECTS_ZONES_OPERATIONS = (
      'projects.zones.operations',
      'projects/{projectId}/zones/{zone}/operations/{operationId}',
      {},
      ['projectId', 'zone', 'operationId'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
