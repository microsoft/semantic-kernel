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


BASE_URL = 'https://securityposture.googleapis.com/v1alpha/'
DOCS_URL = 'https://cloud.google.com/security-command-center'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  ORGANIZATIONS = (
      'organizations',
      'organizations/{organizationsId}',
      {},
      ['organizationsId'],
      True
  )
  ORGANIZATIONS_LOCATIONS = (
      'organizations.locations',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_OPERATIONS = (
      'organizations.locations.operations',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'operations/{operationsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_POSTUREDEPLOYMENTS = (
      'organizations.locations.postureDeployments',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'postureDeployments/{postureDeploymentsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_POSTURETEMPLATES = (
      'organizations.locations.postureTemplates',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'postureTemplates/{postureTemplatesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_POSTURES = (
      'organizations.locations.postures',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/'
              'postures/{posturesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_LOCATIONS_REPORTS = (
      'organizations.locations.reports',
      'organizations/{organizationsId}/locations/{locationsId}/reports',
      {},
      ['organizationsId', 'locationsId'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
