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


BASE_URL = 'https://baremetalsolution.googleapis.com/v2/'
DOCS_URL = 'https://cloud.google.com/bare-metal'


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
  PROJECTS_LOCATIONS_INSTANCES = (
      'projects.locations.instances',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/instances/'
              '{instancesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_NETWORKS = (
      'projects.locations.networks',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/networks/'
              '{networksId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_NFSSHARES = (
      'projects.locations.nfsShares',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/nfsShares/'
              '{nfsSharesId}',
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
  PROJECTS_LOCATIONS_OSIMAGES = (
      'projects.locations.osImages',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/osImages/'
              '{osImagesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_PROVISIONINGCONFIGS = (
      'projects.locations.provisioningConfigs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'provisioningConfigs/{provisioningConfigsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_SNAPSHOTSCHEDULEPOLICIES = (
      'projects.locations.snapshotSchedulePolicies',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'snapshotSchedulePolicies/{snapshotSchedulePoliciesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_SSHKEYS = (
      'projects.locations.sshKeys',
      'projects/{projectsId}/locations/{locationsId}/sshKeys/{sshKeysId}',
      {},
      ['projectsId', 'locationsId', 'sshKeysId'],
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
  PROJECTS_LOCATIONS_VOLUMES_LUNS = (
      'projects.locations.volumes.luns',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/volumes/'
              '{volumesId}/luns/{lunsId}',
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
