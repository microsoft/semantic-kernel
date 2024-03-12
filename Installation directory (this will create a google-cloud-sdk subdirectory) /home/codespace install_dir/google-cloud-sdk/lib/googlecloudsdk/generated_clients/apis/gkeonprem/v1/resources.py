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


BASE_URL = 'https://gkeonprem.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/anthos/clusters/docs/on-prem/'


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
  PROJECTS_LOCATIONS_BAREMETALADMINCLUSTERS = (
      'projects.locations.bareMetalAdminClusters',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'bareMetalAdminClusters/{bareMetalAdminClustersId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_BAREMETALADMINCLUSTERS_OPERATIONS = (
      'projects.locations.bareMetalAdminClusters.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'bareMetalAdminClusters/{bareMetalAdminClustersId}/operations/'
              '{operationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_BAREMETALCLUSTERS = (
      'projects.locations.bareMetalClusters',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'bareMetalClusters/{bareMetalClustersId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_BAREMETALCLUSTERS_BAREMETALNODEPOOLS = (
      'projects.locations.bareMetalClusters.bareMetalNodePools',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'bareMetalClusters/{bareMetalClustersId}/bareMetalNodePools/'
              '{bareMetalNodePoolsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_BAREMETALCLUSTERS_BAREMETALNODEPOOLS_OPERATIONS = (
      'projects.locations.bareMetalClusters.bareMetalNodePools.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'bareMetalClusters/{bareMetalClustersId}/bareMetalNodePools/'
              '{bareMetalNodePoolsId}/operations/{operationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_BAREMETALCLUSTERS_OPERATIONS = (
      'projects.locations.bareMetalClusters.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'bareMetalClusters/{bareMetalClustersId}/operations/'
              '{operationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_BAREMETALSTANDALONECLUSTERS = (
      'projects.locations.bareMetalStandaloneClusters',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'bareMetalStandaloneClusters/{bareMetalStandaloneClustersId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_BAREMETALSTANDALONECLUSTERS_BAREMETALSTANDALONENODEPOOLS = (
      'projects.locations.bareMetalStandaloneClusters.bareMetalStandaloneNodePools',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'bareMetalStandaloneClusters/{bareMetalStandaloneClustersId}/'
              'bareMetalStandaloneNodePools/{bareMetalStandaloneNodePoolsId}',
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
  PROJECTS_LOCATIONS_VMWAREADMINCLUSTERS = (
      'projects.locations.vmwareAdminClusters',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'vmwareAdminClusters/{vmwareAdminClustersId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_VMWAREADMINCLUSTERS_OPERATIONS = (
      'projects.locations.vmwareAdminClusters.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'vmwareAdminClusters/{vmwareAdminClustersId}/operations/'
              '{operationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_VMWARECLUSTERS = (
      'projects.locations.vmwareClusters',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/vmwareClusters/'
              '{vmwareClustersId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_VMWARECLUSTERS_OPERATIONS = (
      'projects.locations.vmwareClusters.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/vmwareClusters/'
              '{vmwareClustersId}/operations/{operationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_VMWARECLUSTERS_VMWARENODEPOOLS = (
      'projects.locations.vmwareClusters.vmwareNodePools',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/vmwareClusters/'
              '{vmwareClustersId}/vmwareNodePools/{vmwareNodePoolsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_VMWARECLUSTERS_VMWARENODEPOOLS_OPERATIONS = (
      'projects.locations.vmwareClusters.vmwareNodePools.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/vmwareClusters/'
              '{vmwareClustersId}/vmwareNodePools/{vmwareNodePoolsId}/'
              'operations/{operationsId}',
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
