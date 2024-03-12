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


BASE_URL = 'https://netapp.googleapis.com/v1alpha1/'
DOCS_URL = 'https://cloud.google.com/netapp/'


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
  PROJECTS_LOCATIONS_ACTIVEDIRECTORIES = (
      'projects.locations.activeDirectories',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'activeDirectories/{activeDirectoriesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_BACKUPPOLICIES = (
      'projects.locations.backupPolicies',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/backupPolicies/'
              '{backupPoliciesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_BACKUPVAULTS = (
      'projects.locations.backupVaults',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/backupVaults/'
              '{backupVaultsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_BACKUPVAULTS_BACKUPS = (
      'projects.locations.backupVaults.backups',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/backupVaults/'
              '{backupVaultsId}/backups/{backupsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_KMSCONFIGS = (
      'projects.locations.kmsConfigs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/kmsConfigs/'
              '{kmsConfigsId}',
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
  PROJECTS_LOCATIONS_STORAGEPOOLS = (
      'projects.locations.storagePools',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/storagePools/'
              '{storagePoolsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_VOLUMES = (
      'projects.locations.volumes',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/volumes/'
              '{volumesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_VOLUMES_REPLICATIONS = (
      'projects.locations.volumes.replications',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/volumes/'
              '{volumesId}/replications/{replicationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_VOLUMES_SNAPSHOTS = (
      'projects.locations.volumes.snapshots',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/volumes/'
              '{volumesId}/snapshots/{snapshotsId}',
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
