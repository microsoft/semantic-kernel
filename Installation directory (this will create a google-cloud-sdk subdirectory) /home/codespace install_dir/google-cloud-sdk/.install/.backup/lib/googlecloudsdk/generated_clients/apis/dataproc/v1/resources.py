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


BASE_URL = 'https://dataproc.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/dataproc/'


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
  PROJECTS_LOCATIONS_AUTOSCALINGPOLICIES = (
      'projects.locations.autoscalingPolicies',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'autoscalingPolicies/{autoscalingPoliciesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_BATCHES = (
      'projects.locations.batches',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/batches/'
              '{batchesId}',
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
  PROJECTS_LOCATIONS_SESSIONTEMPLATES = (
      'projects.locations.sessionTemplates',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'sessionTemplates/{sessionTemplatesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_SESSIONS = (
      'projects.locations.sessions',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/sessions/'
              '{sessionsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_WORKFLOWTEMPLATES = (
      'projects.locations.workflowTemplates',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'workflowTemplates/{workflowTemplatesId}',
      },
      ['name'],
      True
  )
  PROJECTS_REGIONS = (
      'projects.regions',
      'projects/{projectId}/regions/{regionId}',
      {},
      ['projectId', 'regionId'],
      True
  )
  PROJECTS_REGIONS_AUTOSCALINGPOLICIES = (
      'projects.regions.autoscalingPolicies',
      '{+name}',
      {
          '':
              'projects/{projectsId}/regions/{regionsId}/autoscalingPolicies/'
              '{autoscalingPoliciesId}',
      },
      ['name'],
      True
  )
  PROJECTS_REGIONS_CLUSTERS = (
      'projects.regions.clusters',
      'projects/{projectId}/regions/{region}/clusters/{clusterName}',
      {
          '':
              'projects/{projectId}/regions/{region}/clusters/{clusterName}',
      },
      ['projectId', 'region', 'clusterName'],
      True
  )
  PROJECTS_REGIONS_CLUSTERS_GCENODEPOOLS = (
      'projects.regions.clusters.gceNodePools',
      'projects/{projectId}/regions/{region}/clusters/{clusterName}/'
      'gceNodePools/{gceNodePoolsId}',
      {},
      ['projectId', 'region', 'clusterName', 'gceNodePoolsId'],
      True
  )
  PROJECTS_REGIONS_CLUSTERS_NODEGROUPS = (
      'projects.regions.clusters.nodeGroups',
      '{+name}',
      {
          '':
              'projects/{projectId}/regions/{region}/clusters/{clusterName}/'
              'nodeGroups/{nodeGroupsId}',
      },
      ['name'],
      True
  )
  PROJECTS_REGIONS_JOBS = (
      'projects.regions.jobs',
      'projects/{projectId}/regions/{region}/jobs/{jobId}',
      {},
      ['projectId', 'region', 'jobId'],
      True
  )
  PROJECTS_REGIONS_OPERATIONS = (
      'projects.regions.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/regions/{regionsId}/operations/'
              '{operationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_REGIONS_OPERATIONS_LIST = (
      'projects.regions.operations_list',
      'projects/{projectId}/regions/{regionId}/operations',
      {},
      ['projectId', 'regionId'],
      True
  )
  PROJECTS_REGIONS_WORKFLOWTEMPLATES = (
      'projects.regions.workflowTemplates',
      '{+name}',
      {
          '':
              'projects/{projectsId}/regions/{regionsId}/workflowTemplates/'
              '{workflowTemplatesId}',
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
