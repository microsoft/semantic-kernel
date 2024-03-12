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


BASE_URL = 'https://policysimulator.googleapis.com/v1alpha/'
DOCS_URL = 'https://cloud.google.com/iam/docs/simulating-access'


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
  FOLDERS_LOCATIONS_ORGPOLICYVIOLATIONSPREVIEWS = (
      'folders.locations.orgPolicyViolationsPreviews',
      'folders/{foldersId}/locations/{locationsId}/'
      'orgPolicyViolationsPreviews/{orgPolicyViolationsPreviewsId}',
      {},
      ['foldersId', 'locationsId', 'orgPolicyViolationsPreviewsId'],
      True
  )
  FOLDERS_LOCATIONS_ORGPOLICYVIOLATIONSPREVIEWS_OPERATIONS = (
      'folders.locations.orgPolicyViolationsPreviews.operations',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/'
              'orgPolicyViolationsPreviews/{orgPolicyViolationsPreviewsId}/'
              'operations/{operationsId}',
      },
      ['name'],
      True
  )
  FOLDERS_LOCATIONS_REPLAYS = (
      'folders.locations.replays',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/replays/'
              '{replaysId}',
      },
      ['name'],
      True
  )
  FOLDERS_LOCATIONS_REPLAYS_OPERATIONS = (
      'folders.locations.replays.operations',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/replays/'
              '{replaysId}/operations/{operationsId}',
      },
      ['name'],
      True
  )
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
  ORGANIZATIONS = (
      'organizations',
      'organizations/{organizationsId}',
      {},
      ['organizationsId'],
      True
  )
  ORGANIZATIONS_LOCATIONS = (
      'organizations.locations',
      'organizations/{organizationsId}/locations/{locationsId}',
      {},
      ['organizationsId', 'locationsId'],
      True
  )
  ORGANIZATIONS_LOCATIONS_ORGPOLICYVIOLATIONSPREVIEWS = (
      'organizations.locations.orgPolicyViolationsPreviews',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'orgPolicyViolationsPreviews/{orgPolicyViolationsPreviewsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_ORGPOLICYVIOLATIONSPREVIEWS_OPERATIONS = (
      'organizations.locations.orgPolicyViolationsPreviews.operations',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'orgPolicyViolationsPreviews/{orgPolicyViolationsPreviewsId}/'
              'operations/{operationsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_ORGPOLICYVIOLATIONSPREVIEWS_ORGPOLICYVIOLATIONS = (
      'organizations.locations.orgPolicyViolationsPreviews.orgPolicyViolations',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'orgPolicyViolationsPreviews/{orgPolicyViolationsPreviewsId}/'
              'orgPolicyViolations/{orgPolicyViolationsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_REPLAYS = (
      'organizations.locations.replays',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'replays/{replaysId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_REPLAYS_OPERATIONS = (
      'organizations.locations.replays.operations',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'replays/{replaysId}/operations/{operationsId}',
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
  PROJECTS_LOCATIONS_ORGPOLICYVIOLATIONSPREVIEWS = (
      'projects.locations.orgPolicyViolationsPreviews',
      'projects/{projectsId}/locations/{locationsId}/'
      'orgPolicyViolationsPreviews/{orgPolicyViolationsPreviewsId}',
      {},
      ['projectsId', 'locationsId', 'orgPolicyViolationsPreviewsId'],
      True
  )
  PROJECTS_LOCATIONS_ORGPOLICYVIOLATIONSPREVIEWS_OPERATIONS = (
      'projects.locations.orgPolicyViolationsPreviews.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'orgPolicyViolationsPreviews/{orgPolicyViolationsPreviewsId}/'
              'operations/{operationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_REPLAYS = (
      'projects.locations.replays',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/replays/'
              '{replaysId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_REPLAYS_OPERATIONS = (
      'projects.locations.replays.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/replays/'
              '{replaysId}/operations/{operationsId}',
      },
      ['name'],
      True
  )
  SIMULATOR = (
      'simulator',
      'simulator',
      {},
      [],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
