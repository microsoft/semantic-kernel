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


BASE_URL = 'https://auditmanager.googleapis.com/v1alpha/'
DOCS_URL = 'https://cloud.google.com/assured-workloads/docs/audit-manager'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  FOLDERS = (
      'folders',
      'folders/{foldersId}',
      {},
      ['foldersId'],
      True
  )
  FOLDERS_LOCATIONS = (
      'folders.locations',
      'folders/{foldersId}/locations/{locationsId}',
      {},
      ['foldersId', 'locationsId'],
      True
  )
  FOLDERS_LOCATIONS_AUDITREPORTS = (
      'folders.locations.auditReports',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/auditReports/'
              '{auditReportsId}',
      },
      ['name'],
      True
  )
  FOLDERS_LOCATIONS_AUDITREPORTS_CONTROLREPORTS = (
      'folders.locations.auditReports.controlReports',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/auditReports/'
              '{auditReportsId}/controlReports/{controlReportsId}',
      },
      ['name'],
      True
  )
  FOLDERS_LOCATIONS_OPERATIONDETAILS = (
      'folders.locations.operationDetails',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/operationDetails/'
              '{operationDetailsId}',
      },
      ['name'],
      True
  )
  FOLDERS_LOCATIONS_OPERATIONIDS = (
      'folders.locations.operationIds',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/operationIds/'
              '{operationIdsId}',
      },
      ['name'],
      True
  )
  FOLDERS_LOCATIONS_RESOURCEENROLLMENTSTATUSES = (
      'folders.locations.resourceEnrollmentStatuses',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/'
              'resourceEnrollmentStatuses/{resourceEnrollmentStatusesId}',
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
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_AUDITREPORTS = (
      'projects.locations.auditReports',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/auditReports/'
              '{auditReportsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_AUDITREPORTS_CONTROLREPORTS = (
      'projects.locations.auditReports.controlReports',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/auditReports/'
              '{auditReportsId}/controlReports/{controlReportsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_OPERATIONDETAILS = (
      'projects.locations.operationDetails',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'operationDetails/{operationDetailsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_OPERATIONIDS = (
      'projects.locations.operationIds',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/operationIds/'
              '{operationIdsId}',
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
  PROJECTS_LOCATIONS_RESOURCEENROLLMENTSTATUSES = (
      'projects.locations.resourceEnrollmentStatuses',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'resourceEnrollmentStatuses/{resourceEnrollmentStatusesId}',
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
