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


BASE_URL = 'https://cloudkms.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/kms/'


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
  PROJECTS_LOCATIONS_EKMCONNECTIONS = (
      'projects.locations.ekmConnections',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/ekmConnections/'
              '{ekmConnectionsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_KEYRINGS = (
      'projects.locations.keyRings',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/keyRings/'
              '{keyRingsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_KEYRINGS_CRYPTOKEYS = (
      'projects.locations.keyRings.cryptoKeys',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/keyRings/'
              '{keyRingsId}/cryptoKeys/{cryptoKeysId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_KEYRINGS_CRYPTOKEYS_CRYPTOKEYVERSIONS = (
      'projects.locations.keyRings.cryptoKeys.cryptoKeyVersions',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/keyRings/'
              '{keyRingsId}/cryptoKeys/{cryptoKeysId}/cryptoKeyVersions/'
              '{cryptoKeyVersionsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_KEYRINGS_IMPORTJOBS = (
      'projects.locations.keyRings.importJobs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/keyRings/'
              '{keyRingsId}/importJobs/{importJobsId}',
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
