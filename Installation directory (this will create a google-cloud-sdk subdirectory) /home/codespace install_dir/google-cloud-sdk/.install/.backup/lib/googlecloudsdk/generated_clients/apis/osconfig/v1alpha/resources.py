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


BASE_URL = 'https://osconfig.googleapis.com/v1alpha/'
DOCS_URL = 'https://cloud.google.com/compute/docs/osconfig/rest'


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
  PROJECTS_LOCATIONS_INSTANCEOSPOLICIESCOMPLIANCES = (
      'projects.locations.instanceOSPoliciesCompliances',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'instanceOSPoliciesCompliances/'
              '{instanceOSPoliciesCompliancesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_INSTANCES = (
      'projects.locations.instances',
      'projects/{projectsId}/locations/{locationsId}/instances/{instancesId}',
      {},
      ['projectsId', 'locationsId', 'instancesId'],
      True
  )
  PROJECTS_LOCATIONS_INSTANCES_INVENTORIES = (
      'projects.locations.instances.inventories',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/instances/'
              '{instancesId}/inventory',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_INSTANCES_OSPOLICYASSIGNMENTS = (
      'projects.locations.instances.osPolicyAssignments',
      'projects/{projectsId}/locations/{locationsId}/instances/{instancesId}/'
      'osPolicyAssignments/{osPolicyAssignmentsId}',
      {},
      ['projectsId', 'locationsId', 'instancesId', 'osPolicyAssignmentsId'],
      True
  )
  PROJECTS_LOCATIONS_INSTANCES_OSPOLICYASSIGNMENTS_REPORTS = (
      'projects.locations.instances.osPolicyAssignments.reports',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/instances/'
              '{instancesId}/osPolicyAssignments/{osPolicyAssignmentsId}/'
              'report',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_INSTANCES_VULNERABILITYREPORTS = (
      'projects.locations.instances.vulnerabilityReports',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/instances/'
              '{instancesId}/vulnerabilityReport',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_OSPOLICYASSIGNMENTS = (
      'projects.locations.osPolicyAssignments',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'osPolicyAssignments/{osPolicyAssignmentsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_OSPOLICYASSIGNMENTS_OPERATIONS = (
      'projects.locations.osPolicyAssignments.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'osPolicyAssignments/{osPolicyAssignmentsId}/operations/'
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
